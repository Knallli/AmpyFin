from polygon import RESTClient
from config import POLYGON_API_KEY, FINANCIAL_PREP_API_KEY, MONGO_DB_USER, MONGO_DB_PASS, API_KEY, API_SECRET, BASE_URL, mongo_url
import json
import certifi
from urllib.request import urlopen
from zoneinfo import ZoneInfo
from pymongo import MongoClient
import time
from datetime import datetime, timedelta
from helper_files.client_helper import place_order, get_ndaq_tickers, market_status, strategies, get_latest_price, dynamic_period_selector, process_delayed_orders
from alpaca.trading.client import TradingClient
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from strategies.archived_strategies.trading_strategies_v1 import get_historical_data
import yfinance as yf
import logging
from collections import Counter
from statistics import median, mode
import statistics
import heapq
import requests
from strategies.talib_indicators import *
import concurrent.futures
from functools import lru_cache

# Trading Konfiguration
MIN_ACCOUNT_BALANCE = 1000  # Minimaler Kontostand in USD
MAX_POSITION_SIZE = 0.5     # Maximale Positionsgröße als Anteil am Portfolio (50%)

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('system.log'),  # Log messages to a file
        logging.StreamHandler()             # Log messages to the console
    ]
)

# Preisabfrage-Pool für parallele Verarbeitung
price_fetch_pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

@lru_cache(maxsize=1000)
def get_historical_data_cached(ticker, timestamp):
    """
    Cached Version von get_historical_data mit Zeitstempel für Invalidierung
    """
    return get_data(ticker)

def get_latest_prices_parallel(tickers):
    """
    Holt die aktuellen Preise für mehrere Tickers parallel
    """
    def fetch_single_price(ticker):
        try:
            return ticker, get_latest_price(ticker)
        except Exception as e:
            logging.error(f"Error fetching price for {ticker}: {e}")
            return ticker, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_single_price, tickers))
    return {ticker: price for ticker, price in results if price is not None}

def weighted_majority_decision_and_median_quantity(decisions_and_quantities):  
    """  
    Determines the majority decision (buy, sell, or hold) and returns the weighted median quantity for the chosen action.  
    Groups 'strong buy' with 'buy' and 'strong sell' with 'sell'.
    Applies weights to quantities based on strategy coefficients.  
    """  
    buy_decisions = ['buy', 'strong buy']  
    sell_decisions = ['sell', 'strong sell']  

    weighted_buy_quantities = []
    weighted_sell_quantities = []
    buy_weight = 0
    sell_weight = 0
    hold_weight = 0
    
    # Process decisions with weights
    for decision, quantity, weight in decisions_and_quantities:
        if decision in buy_decisions:
            weighted_buy_quantities.extend([quantity])
            buy_weight += weight
        elif decision in sell_decisions:
            weighted_sell_quantities.extend([quantity])
            sell_weight += weight
        elif decision == 'hold':
            hold_weight += weight
    
    # Determine the majority decision based on the highest accumulated weight
    if buy_weight > sell_weight and buy_weight > hold_weight:
        return 'buy', median(weighted_buy_quantities) if weighted_buy_quantities else 0, buy_weight, sell_weight, hold_weight
    elif sell_weight > buy_weight and sell_weight > hold_weight:
        return 'sell', median(weighted_sell_quantities) if weighted_sell_quantities else 0, buy_weight, sell_weight, hold_weight
    else:
        logging.debug(f"Decision: hold | Weights: Buy: {buy_weight}, Sell: {sell_weight}, Hold: {hold_weight}")
        return 'hold', 0, buy_weight, sell_weight, hold_weight

def main():
    """
    Main function to control the workflow based on the market's status.
    """
    ndaq_tickers = []
    early_hour_first_iteration = True
    post_hour_first_iteration = True
    client = RESTClient(api_key=POLYGON_API_KEY)
    trading_client = TradingClient(API_KEY, API_SECRET)
    data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
    mongo_client = MongoClient(mongo_url)
    db = mongo_client.trades
    asset_collection = db.assets_quantities
    strategy_to_coefficient = {}

    while True:
        try:
            status = market_status(client)
            market_db = mongo_client.market_data
            market_collection = market_db.market_status
            market_collection.update_one({}, {"$set": {"market_status": status}})

            if status == "open":
                logging.info("Market is open. Processing delayed orders and regular trading.")
                process_delayed_orders(trading_client, mongo_url)

                if not ndaq_tickers:
                    ndaq_tickers = get_ndaq_tickers(mongo_url, FINANCIAL_PREP_API_KEY)
                    sim_db = mongo_client.trading_simulator
                    rank_collection = sim_db.rank
                    r_t_c_collection = sim_db.rank_to_coefficient
                    for strategy in strategies:
                        rank = rank_collection.find_one({'strategy': strategy.__name__})['rank']
                        coefficient = r_t_c_collection.find_one({'rank': rank})['coefficient']
                        strategy_to_coefficient[strategy.__name__] = coefficient
                        early_hour_first_iteration = False
                        post_hour_first_iteration = True

                account = trading_client.get_account()
                
                # Hole aktuelle Preise für QQQ und SPY
                current_prices = get_latest_prices_parallel(['QQQ', 'SPY'])
                qqq_latest = current_prices.get('QQQ')
                spy_latest = current_prices.get('SPY')

                if qqq_latest and spy_latest:
                    portfolio_collection = db.portfolio_values
                    portfolio_value = float(account.portfolio_value)
                    portfolio_collection.update_one({"name": "portfolio_percentage"}, {"$set": {"portfolio_value": (portfolio_value-50000)/50000}})
                    portfolio_collection.update_one({"name": "ndaq_percentage"}, {"$set": {"portfolio_value": (qqq_latest-503.17)/503.17}})
                    portfolio_collection.update_one({"name": "spy_percentage"}, {"$set": {"portfolio_value": (spy_latest-590.50)/590.50}})

                buy_heap = []
                # Verarbeite Tickers in Batches von 10
                for i in range(0, len(ndaq_tickers), 10):
                    batch = ndaq_tickers[i:i+10]
                    # Hole Preise für den aktuellen Batch parallel
                    current_prices = get_latest_prices_parallel(batch)
                    
                    # Timestamp für Cache-Invalidierung
                    timestamp = int(time.time() / 300)  # Alle 5 Minuten
                    
                    for ticker in batch:
                        try:
                            current_price = current_prices.get(ticker)
                            if current_price is None:
                                continue

                            historical_data = get_historical_data_cached(ticker, timestamp)
                            
                            asset_info = asset_collection.find_one({'symbol': ticker})
                            portfolio_qty = asset_info['quantity'] if asset_info else 0.0
                            
                            decisions_and_quantities = []
                            for strategy in strategies:
                                decision, quantity = simulate_strategy(strategy, ticker, current_price, historical_data,
                                                            float(account.cash), portfolio_qty, portfolio_value)
                                weight = strategy_to_coefficient[strategy.__name__]
                                decisions_and_quantities.append((decision, quantity, weight))

                            decision, quantity, buy_weight, sell_weight, hold_weight = weighted_majority_decision_and_median_quantity(decisions_and_quantities)
                            print(f"Ticker: {ticker}, Decision: {decision}, Quantity: {quantity}, Weights: Buy: {buy_weight}, Sell: {sell_weight}, Hold: {hold_weight}")

                            if decision == "buy" and float(account.cash) > MIN_ACCOUNT_BALANCE and (((quantity + portfolio_qty) * current_price) / portfolio_value) < MAX_POSITION_SIZE:
                                heapq.heappush(buy_heap, (-(buy_weight-(sell_weight + (hold_weight * 0.5))), quantity, ticker))
                            elif decision == "sell" and portfolio_qty > 0:
                                print(f"Executing SELL order for {ticker}")
                                order = place_order(trading_client, ticker, OrderSide.SELL, qty=quantity, mongo_url=mongo_url)
                                if order:
                                    logging.info(f"Executed SELL order for {ticker}: {order}")
                                else:
                                    logging.info(f"SELL order for {ticker} wurde für späteren Zeitpunkt vorgemerkt")

                        except Exception as e:
                            logging.error(f"Error processing {ticker}: {e}")

                while buy_heap and float(account.cash) > MIN_ACCOUNT_BALANCE:
                    try:
                        buy_coeff, quantity, ticker = heapq.heappop(buy_heap)
                        # Hole aktuellen Preis erneut für die finale Ausführung
                        current_price = get_latest_price(ticker)
                        
                        if current_price and float(account.cash) - (quantity * current_price) >= MIN_ACCOUNT_BALANCE:
                            print(f"Executing BUY order for {ticker}")
                            order = place_order(trading_client, ticker, OrderSide.BUY, qty=quantity, mongo_url=mongo_url)
                            if order:
                                logging.info(f"Executed BUY order for {ticker}: {order}")
                            else:
                                logging.info(f"BUY order for {ticker} wurde für späteren Zeitpunkt vorgemerkt")
                            
                            trading_client = TradingClient(API_KEY, API_SECRET)
                            account = trading_client.get_account()
                        else:
                            logging.info(f"Skipping BUY order for {ticker} due to insufficient funds or missing price data")

                    except Exception as e:
                        logging.error(f"Error executing buy order: {e}")
                        break

                time.sleep(30)  # Reduzierte Wartezeit von 60 auf 30 Sekunden

            elif status == "early_hours":
                if early_hour_first_iteration:
                    ndaq_tickers = get_ndaq_tickers(mongo_url, FINANCIAL_PREP_API_KEY)
                    sim_db = mongo_client.trading_simulator
                    rank_collection = sim_db.rank
                    r_t_c_collection = sim_db.rank_to_coefficient
                    for strategy in strategies:
                        rank = rank_collection.find_one({'strategy': strategy.__name__})['rank']
                        coefficient = r_t_c_collection.find_one({'rank': rank})['coefficient']
                        strategy_to_coefficient[strategy.__name__] = coefficient
                        early_hour_first_iteration = False
                        post_hour_first_iteration = True
                time.sleep(30)

            elif status == "closed":
                if post_hour_first_iteration:
                    early_hour_first_iteration = True
                    post_hour_first_iteration = False
                    # Cache leeren am Ende des Handelstages
                    get_historical_data_cached.cache_clear()
                time.sleep(30)

            else:
                logging.error("An error occurred while checking market status.")
                time.sleep(30)

        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()