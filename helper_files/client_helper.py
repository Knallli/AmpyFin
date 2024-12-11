from pymongo import MongoClient
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from datetime import datetime, timedelta
import logging
import yfinance as yf

from strategies.talib_indicators import (get_data, BBANDS_indicator, DEMA_indicator, EMA_indicator, HT_TRENDLINE_indicator, KAMA_indicator, MA_indicator, MAMA_indicator, MAVP_indicator, MIDPOINT_indicator, MIDPRICE_indicator, SAR_indicator, SAREXT_indicator, SMA_indicator, T3_indicator, TEMA_indicator, TRIMA_indicator, WMA_indicator, ADX_indicator, ADXR_indicator, APO_indicator, AROON_indicator, AROONOSC_indicator, BOP_indicator, CCI_indicator, CMO_indicator, DX_indicator, MACD_indicator, MACDEXT_indicator, MACDFIX_indicator, MFI_indicator, MINUS_DI_indicator, MINUS_DM_indicator, MOM_indicator, PLUS_DI_indicator, PLUS_DM_indicator, PPO_indicator, ROC_indicator, ROCP_indicator, ROCR_indicator, ROCR100_indicator, RSI_indicator, STOCH_indicator, STOCHF_indicator, STOCHRSI_indicator, TRIX_indicator, ULTOSC_indicator, WILLR_indicator, AD_indicator, ADOSC_indicator, OBV_indicator, HT_DCPERIOD_indicator, HT_DCPHASE_indicator, HT_PHASOR_indicator, HT_SINE_indicator, HT_TRENDMODE_indicator, AVGPRICE_indicator, MEDPRICE_indicator, TYPPRICE_indicator, WCLPRICE_indicator, ATR_indicator, NATR_indicator, TRANGE_indicator, CDL2CROWS_indicator, CDL3BLACKCROWS_indicator, CDL3INSIDE_indicator, CDL3LINESTRIKE_indicator, CDL3OUTSIDE_indicator, CDL3STARSINSOUTH_indicator, CDL3WHITESOLDIERS_indicator, CDLABANDONEDBABY_indicator, CDLADVANCEBLOCK_indicator, CDLBELTHOLD_indicator, CDLBREAKAWAY_indicator, CDLCLOSINGMARUBOZU_indicator, CDLCONCEALBABYSWALL_indicator, CDLCOUNTERATTACK_indicator, CDLDARKCLOUDCOVER_indicator, CDLDOJI_indicator, CDLDOJISTAR_indicator, CDLDRAGONFLYDOJI_indicator, CDLENGULFING_indicator, CDLEVENINGDOJISTAR_indicator, CDLEVENINGSTAR_indicator, CDLGAPSIDESIDEWHITE_indicator, CDLGRAVESTONEDOJI_indicator, CDLHAMMER_indicator, CDLHANGINGMAN_indicator, CDLHARAMI_indicator, CDLHARAMICROSS_indicator, CDLHIGHWAVE_indicator, CDLHIKKAKE_indicator, CDLHIKKAKEMOD_indicator, CDLHOMINGPIGEON_indicator, CDLIDENTICAL3CROWS_indicator, CDLINNECK_indicator, CDLINVERTEDHAMMER_indicator, CDLKICKING_indicator, CDLKICKINGBYLENGTH_indicator, CDLLADDERBOTTOM_indicator, CDLLONGLEGGEDDOJI_indicator, CDLLONGLINE_indicator, CDLMARUBOZU_indicator, CDLMATCHINGLOW_indicator, CDLMATHOLD_indicator, CDLMORNINGDOJISTAR_indicator, CDLMORNINGSTAR_indicator, CDLONNECK_indicator, CDLPIERCING_indicator, CDLRICKSHAWMAN_indicator, CDLRISEFALL3METHODS_indicator, CDLSEPARATINGLINES_indicator, CDLSHOOTINGSTAR_indicator, CDLSHORTLINE_indicator, CDLSPINNINGTOP_indicator, CDLSTALLEDPATTERN_indicator, CDLSTICKSANDWICH_indicator, CDLTAKURI_indicator, CDLTASUKIGAP_indicator, CDLTHRUSTING_indicator, CDLTRISTAR_indicator, CDLUNIQUE3RIVER_indicator, CDLUPSIDEGAP2CROWS_indicator, CDLXSIDEGAP3METHODS_indicator, BETA_indicator, CORREL_indicator, LINEARREG_indicator, LINEARREG_ANGLE_indicator, LINEARREG_INTERCEPT_indicator, LINEARREG_SLOPE_indicator, STDDEV_indicator, TSF_indicator, VAR_indicator)
   
from urllib.request import urlopen
import json
import certifi
from zoneinfo import ZoneInfo
import time as time_module  # Umbenennen des time Moduls
from time import time  # Importiere nur die time Funktion
from functools import lru_cache
import random
import requests.adapters
import urllib3

overlap_studies = [BBANDS_indicator, DEMA_indicator, EMA_indicator, HT_TRENDLINE_indicator, KAMA_indicator, MA_indicator, MAMA_indicator, MAVP_indicator, MIDPOINT_indicator, MIDPRICE_indicator, SAR_indicator, SAREXT_indicator, SMA_indicator, T3_indicator, TEMA_indicator, TRIMA_indicator, WMA_indicator]
momentum_indicators = [ADX_indicator, ADXR_indicator, APO_indicator, AROON_indicator, AROONOSC_indicator, BOP_indicator, CCI_indicator, CMO_indicator, DX_indicator, MACD_indicator, MACDEXT_indicator, MACDFIX_indicator, MFI_indicator, MINUS_DI_indicator, MINUS_DM_indicator, MOM_indicator, PLUS_DI_indicator, PLUS_DM_indicator, PPO_indicator, ROC_indicator, ROCP_indicator, ROCR_indicator, ROCR100_indicator, RSI_indicator, STOCH_indicator, STOCHF_indicator, STOCHRSI_indicator, TRIX_indicator, ULTOSC_indicator, WILLR_indicator]
volume_indicators = [AD_indicator, ADOSC_indicator, OBV_indicator]
cycle_indicators = [HT_DCPERIOD_indicator, HT_DCPHASE_indicator, HT_PHASOR_indicator, HT_SINE_indicator, HT_TRENDMODE_indicator]
price_transforms = [AVGPRICE_indicator, MEDPRICE_indicator, TYPPRICE_indicator, WCLPRICE_indicator]
volatility_indicators = [ATR_indicator, NATR_indicator, TRANGE_indicator]
pattern_recognition = [CDL2CROWS_indicator, CDL3BLACKCROWS_indicator, CDL3INSIDE_indicator, CDL3LINESTRIKE_indicator, CDL3OUTSIDE_indicator, CDL3STARSINSOUTH_indicator, CDL3WHITESOLDIERS_indicator, CDLABANDONEDBABY_indicator, CDLADVANCEBLOCK_indicator, CDLBELTHOLD_indicator, CDLBREAKAWAY_indicator, CDLCLOSINGMARUBOZU_indicator, CDLCONCEALBABYSWALL_indicator, CDLCOUNTERATTACK_indicator, CDLDARKCLOUDCOVER_indicator, CDLDOJI_indicator, CDLDOJISTAR_indicator, CDLDRAGONFLYDOJI_indicator, CDLENGULFING_indicator, CDLEVENINGDOJISTAR_indicator, CDLEVENINGSTAR_indicator, CDLGAPSIDESIDEWHITE_indicator, CDLGRAVESTONEDOJI_indicator, CDLHAMMER_indicator, CDLHANGINGMAN_indicator, CDLHARAMI_indicator, CDLHARAMICROSS_indicator, CDLHIGHWAVE_indicator, CDLHIKKAKE_indicator, CDLHIKKAKEMOD_indicator, CDLHOMINGPIGEON_indicator, CDLIDENTICAL3CROWS_indicator, CDLINNECK_indicator, CDLINVERTEDHAMMER_indicator, CDLKICKING_indicator, CDLKICKINGBYLENGTH_indicator, CDLLADDERBOTTOM_indicator, CDLLONGLEGGEDDOJI_indicator, CDLLONGLINE_indicator, CDLMARUBOZU_indicator, CDLMATCHINGLOW_indicator, CDLMATHOLD_indicator, CDLMORNINGDOJISTAR_indicator, CDLMORNINGSTAR_indicator, CDLONNECK_indicator, CDLPIERCING_indicator, CDLRICKSHAWMAN_indicator, CDLRISEFALL3METHODS_indicator, CDLSEPARATINGLINES_indicator, CDLSHOOTINGSTAR_indicator, CDLSHORTLINE_indicator, CDLSPINNINGTOP_indicator, CDLSTALLEDPATTERN_indicator, CDLSTICKSANDWICH_indicator, CDLTAKURI_indicator, CDLTASUKIGAP_indicator, CDLTHRUSTING_indicator, CDLTRISTAR_indicator, CDLUNIQUE3RIVER_indicator, CDLUPSIDEGAP2CROWS_indicator, CDLXSIDEGAP3METHODS_indicator]
statistical_functions = [BETA_indicator, CORREL_indicator, LINEARREG_indicator, LINEARREG_ANGLE_indicator, LINEARREG_INTERCEPT_indicator, LINEARREG_SLOPE_indicator, STDDEV_indicator, TSF_indicator, VAR_indicator]

strategies = overlap_studies + momentum_indicators + volume_indicators + cycle_indicators + price_transforms + volatility_indicators + pattern_recognition + statistical_functions

# Konfiguriere den Connection Pool
urllib3.PoolManager(maxsize=50)
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
session.mount('http://', adapter)
session.mount('https://', adapter)

# MongoDB connection helper
def connect_to_mongo(mongo_url):
    """Connect to MongoDB and return the client."""
    return MongoClient(mongo_url)

# Helper to place an order
def place_order(trading_client, symbol, side, qty, mongo_url):
    """
    Platziert eine Market Order und protokolliert sie in MongoDB.
    Prüft zuvor den PDT-Status für Konten unter $25.000.

    :param trading_client: Die Alpaca Trading Client Instanz
    :param symbol: Das zu handelnde Symbol
    :param side: Orderseite (OrderSide.BUY oder OrderSide.SELL)
    :param qty: Handelsmenge
    :param mongo_url: MongoDB Verbindungs-URL
    :return: Orderergebnis von der Alpaca API oder None bei verzögerter Ausführung
    """
    # Hole aktuellen Kontostand
    account = trading_client.get_account()
    account_value = float(account.portfolio_value)
    
    # PDT-Status prüfen
    pdt_allowed, pdt_message = check_pdt_status(mongo_url, symbol, side, account_value)
    if not pdt_allowed:
        logging.warning(f"Order für {symbol} wird verzögert: {pdt_message}")
        queue_delayed_order(mongo_url, symbol, side, qty)
        return None

    market_order_data = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=side,
        time_in_force=TimeInForce.DAY
    )
    
    order = trading_client.submit_order(market_order_data)
    qty = round(qty, 3)
    
    # Trade-Details in MongoDB protokollieren
    mongo_client = connect_to_mongo(mongo_url)
    db = mongo_client.trades
    db.paper.insert_one({
        'symbol': symbol,
        'qty': qty,
        'side': side.name,
        'time_in_force': TimeInForce.DAY.name,
        'time': datetime.now(ZoneInfo("America/New_York")),
        'account_value': account_value,
        'price': current_price  # Speichere den aktuellen Preis
    })
    
    # Assets ebenfalls tracken
    assets = db.assets_quantities
    if side == OrderSide.BUY:
        assets.update_one(
            {'symbol': symbol}, 
            {
                '$inc': {'quantity': qty},
                '$set': {'buy_price': current_price}  # Speichere den Einkaufspreis
            }, 
            upsert=True
        )
    elif side == OrderSide.SELL:
        assets.update_one({'symbol': symbol}, {'$inc': {'quantity': -qty}}, upsert=True)
        if assets.find_one({'symbol': symbol})['quantity'] == 0:
            assets.delete_one({'symbol': symbol})

    mongo_client.close()    
    return order

# Helper to retrieve NASDAQ-100 tickers from MongoDB
def get_ndaq_tickers(mongo_url, FINANCIAL_PREP_API_KEY):
    """
    Connects to MongoDB and retrieves NASDAQ-100 tickers.

    :param mongo_url: MongoDB connection URL
    :return: List of NASDAQ-100 ticker symbols.
    """
    def call_ndaq_100():
        """
        Fetches the list of NASDAQ 100 tickers using the Financial Modeling Prep API and stores it in a MongoDB collection.
        The MongoDB collection is cleared before inserting the updated list of tickers.
        """
        logging.info("Calling NASDAQ 100 to retrieve tickers.")

        def get_jsonparsed_data(url):
            """
            Parses the JSON response from the provided URL.
            
            :param url: The API endpoint to retrieve data from.
            :return: Parsed JSON data as a dictionary.
            """
            response = urlopen(url)
            data = response.read().decode("utf-8")
            return json.loads(data)
        try:
            # API URL for fetching NASDAQ 100 tickers
            ndaq_url = f"https://financialmodelingprep.com/api/v3/nasdaq_constituent?apikey={FINANCIAL_PREP_API_KEY}"
            ndaq_stocks = get_jsonparsed_data(ndaq_url)
            logging.info("Successfully retrieved NASDAQ 100 tickers.")
        except Exception as e:
            logging.error(f"Error fetching NASDAQ 100 tickers: {e}")
            return
        try:
            # MongoDB connection details
            mongo_client = MongoClient(mongo_url)
            db = mongo_client.stock_list
            ndaq100_tickers = db.ndaq100_tickers

            ndaq100_tickers.delete_many({})  # Clear existing data
            ndaq100_tickers.insert_many(ndaq_stocks)  # Insert new data
            logging.info("Successfully inserted NASDAQ 100 tickers into MongoDB.")
        except Exception as e:
            logging.error(f"Error inserting tickers into MongoDB: {e}")
        finally:
            mongo_client.close()
            logging.info("MongoDB connection closed.")

    call_ndaq_100()
    mongo_client = connect_to_mongo(mongo_url) 
    tickers = [stock['symbol'] for stock in mongo_client.stock_list.ndaq100_tickers.find()]
    mongo_client.close()
    return tickers

# Market status checker helper
def market_status(polygon_client):
    """
    Check market status using the Polygon API.

    :param polygon_client: An instance of the Polygon RESTClient
    :return: Current market status ('open', 'early_hours', 'closed')
    """
    try:
        status = polygon_client.get_market_status()
        if status.exchanges.nasdaq == "open" and status.exchanges.nyse == "open":
            return "open"
        elif status.early_hours:
            return "early_hours"
        else:
            return "closed"
    except Exception as e:
        logging.error(f"Error retrieving market status: {e}")
        return "error"

# Helper to get latest price
from time import time
from functools import wraps

def timed_lru_cache(seconds: int, maxsize: int = 128):
    def wrapper_decorator(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = seconds
        func.expiration = time() + seconds

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if time() >= func.expiration:
                func.cache_clear()
                func.expiration = time() + func.lifetime
            return func(*args, **kwargs)

        return wrapped_func

    return wrapper_decorator

@timed_lru_cache(seconds=60, maxsize=100)
def get_latest_price(ticker):  
    """  
    Fetch the latest price for a given stock ticker using yfinance with retry logic.  
    
    :param ticker: The stock ticker symbol  
    :return: The latest price of the stock  
    """  
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            # Add random delay between requests
            time_module.sleep(random.uniform(0.1, 0.5))  # Verwende time_module.sleep statt time.sleep
            
            ticker_yahoo = yf.Ticker(ticker)
            ticker_yahoo.session = session  # Use our custom session
            data = ticker_yahoo.history()
            
            if not data.empty:
                return round(data['Close'].iloc[-1], 2)
            
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"Final error fetching price for {ticker}: {e}")
                return None
                
            logging.warning(f"Error fetching price for {ticker} (attempt {attempt + 1}): {e}")
            time_module.sleep(retry_delay * (attempt + 1))  # Verwende time_module.sleep statt time.sleep
    
    return None

def dynamic_period_selector(ticker):
    """
    Determines the best period to use for fetching historical data.
    
    Args:
    - ticker (str): Stock ticker symbol.
    
    Returns:
    - str: Optimal period for historical data retrieval.
    """
    periods = ['5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'ytd', 'max']
    volatility_scores = []

    for period in periods:
        try:
            data = yf.Ticker(ticker).history(period=period)
            if data.empty:
                continue
            
            # Calculate metrics for decision-making
            daily_changes = data['Close'].pct_change().dropna()
            volatility = daily_changes.std()
            trend_strength = abs(data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]
            
            # Combine metrics into a single score (weight them as desired)
            score = volatility * 0.7 + trend_strength * 0.3
            volatility_scores.append((period, score))
        except Exception as e:
            print(f"Error fetching data for period {period}: {e}")
            continue

    # Select the period with the highest score
    
    optimal_period = min(volatility_scores, key=lambda x: x[1])[0] if volatility_scores else '1y'
    return optimal_period

def check_pdt_status(mongo_url, symbol, side, account_value):
    """
    Überprüft den Pattern Day Trading (PDT) Status für ein Symbol.
    Ein Day Trade ist ein Kauf und Verkauf (oder umgekehrt) desselben Symbols am selben Handelstag.
    PDT-Regeln werden nur für Konten unter $25.000 angewendet.

    :param mongo_url: MongoDB Verbindungs-URL
    :param symbol: Das zu handelnde Symbol
    :param side: Orderseite (Kauf oder Verkauf)
    :param account_value: Aktueller Kontostand (Cash + Positionen)
    :return: (bool, str) Tuple mit PDT-Status und Erklärung
    """
    # Wenn das Konto $25.000 oder mehr hat, PDT-Regeln nicht anwenden
    if float(account_value) >= 25000:
        return True, "Konto über $25.000 - PDT-Regeln nicht anwendbar"
        
    try:
        mongo_client = connect_to_mongo(mongo_url)
        db = mongo_client.trades
        trades_collection = db.paper
        
        # Aktuelle Zeit in EST (US Eastern Time)
        current_time = datetime.now(ZoneInfo("America/New_York"))
        five_days_ago = current_time - timedelta(days=5)
        
        # Hole alle Trades der letzten 5 Tage für dieses Symbol
        recent_trades = list(trades_collection.find({
            'symbol': symbol,
            'time': {'$gte': five_days_ago}
        }).sort('time', 1))
        
        # Gruppiere Trades nach Handelstag
        day_trades_count = 0
        trades_by_day = {}
        
        for trade in recent_trades:
            trade_date = trade['time'].date()
            if trade_date not in trades_by_day:
                trades_by_day[trade_date] = []
            trades_by_day[trade_date].append(trade)
        
        # Zähle Day Trades
        for date, trades in trades_by_day.items():
            buys = [t for t in trades if t['side'] == 'BUY']
            sells = [t for t in trades if t['side'] == 'SELL']
            
            # Ein Day Trade ist ein Paar von Kauf und Verkauf am selben Tag
            day_trades_count += min(len(buys), len(sells))
        
        # Prüfe, ob der aktuelle Trade ein potenzieller Day Trade wäre
        today = current_time.date()
        if today in trades_by_day:
            todays_trades = trades_by_day[today]
            opposite_trades = [t for t in todays_trades if t['side'] != side.name]
            if opposite_trades and day_trades_count >= 3:
                return False, "PDT-Limit erreicht: Mehr als 3 Day Trades in 5 Tagen nicht erlaubt für Konten unter $25.000."
        
        return True, "PDT-Status OK"
        
    except Exception as e:
        logging.error(f"Fehler bei der PDT-Statusprüfung: {e}")
        return False, f"Fehler bei der PDT-Statusprüfung: {e}"
    finally:
        mongo_client.close()

def queue_delayed_order(mongo_url, symbol, side, qty):
    """
    Speichert eine Order in der Warteschlange für den nächsten Handelstag.
    
    :param mongo_url: MongoDB Verbindungs-URL
    :param symbol: Das zu handelnde Symbol
    :param side: Orderseite (OrderSide.BUY oder OrderSide.SELL)
    :param qty: Handelsmenge
    """
    try:
        mongo_client = connect_to_mongo(mongo_url)
        db = mongo_client.trades
        delayed_orders = db.delayed_orders
        
        # Berechne das Ausführungsdatum (nächster Handelstag)
        current_time = datetime.now(ZoneInfo("America/New_York"))
        next_trading_day = current_time + timedelta(days=1)
        # Wenn es Freitag ist, verschiebe auf Montag
        if next_trading_day.weekday() >= 5:
            days_to_add = 8 - next_trading_day.weekday()
            next_trading_day = current_time + timedelta(days=days_to_add)
            
        delayed_orders.insert_one({
            'symbol': symbol,
            'qty': qty,
            'side': side.name,
            'created_at': current_time,
            'execute_after': next_trading_day,
            'status': 'pending'
        })
        
        logging.info(f"Order für {symbol} wurde für den nächsten Handelstag ({next_trading_day.date()}) vorgemerkt")
        
    except Exception as e:
        logging.error(f"Fehler beim Speichern der verzögerten Order: {e}")
    finally:
        mongo_client.close()

def process_delayed_orders(trading_client, mongo_url):
    """
    Verarbeitet alle ausstehenden verzögerten Orders, die ausgeführt werden können.
    
    :param trading_client: Die Alpaca Trading Client Instanz
    :param mongo_url: MongoDB Verbindungs-URL
    """
    try:
        mongo_client = connect_to_mongo(mongo_url)
        db = mongo_client.trades
        delayed_orders = db.delayed_orders
        
        current_time = datetime.now(ZoneInfo("America/New_York"))
        
        # Hole alle fälligen Orders
        pending_orders = delayed_orders.find({
            'status': 'pending',
            'execute_after': {'$lte': current_time}
        })
        
        for order in pending_orders:
            # Prüfe PDT-Status für jede Order
            pdt_allowed, _ = check_pdt_status(mongo_url, order['symbol'], OrderSide[order['side']])
            
            if pdt_allowed:
                try:
                    # Führe die Order aus
                    market_order_data = MarketOrderRequest(
                        symbol=order['symbol'],
                        qty=order['qty'],
                        side=OrderSide[order['side']],
                        time_in_force=TimeInForce.DAY
                    )
                    
                    executed_order = trading_client.submit_order(market_order_data)
                    
                    # Aktualisiere den Order-Status
                    delayed_orders.update_one(
                        {'_id': order['_id']},
                        {'$set': {
                            'status': 'executed',
                            'executed_at': current_time,
                            'order_id': executed_order.id
                        }}
                    )
                    
                    logging.info(f"Verzögerte Order für {order['symbol']} wurde erfolgreich ausgeführt")
                    
                except Exception as e:
                    logging.error(f"Fehler bei der Ausführung der verzögerten Order: {e}")
                    
            else:
                # Verschiebe die Order um einen weiteren Tag
                next_trading_day = current_time + timedelta(days=1)
                if next_trading_day.weekday() >= 5:
                    days_to_add = 8 - next_trading_day.weekday()
                    next_trading_day = current_time + timedelta(days=days_to_add)
                
                delayed_orders.update_one(
                    {'_id': order['_id']},
                    {'$set': {'execute_after': next_trading_day}}
                )
                
    except Exception as e:
        logging.error(f"Fehler bei der Verarbeitung verzögerter Orders: {e}")
    finally:
        mongo_client.close()

