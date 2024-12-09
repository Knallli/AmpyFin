from pymongo import MongoClient
from helper_files.client_helper import get_latest_price
from strategies.talib_indicators import get_data, simulate_strategy
from config import mongo_url, FINANCIAL_PREP_API_KEY
import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(level=logging.INFO)

def load_historical_data(ticker):
    """Load historical data for a given ticker in the finest resolution possible."""
    file_path = f"data/{ticker}_1min.csv"
    if os.path.exists(file_path):
        data = pd.read_csv(file_path, index_col='Date', parse_dates=True)
        last_date = data.index[-1]
        new_data = get_data(ticker, '1min')
        new_data = new_data[new_data.index > last_date]
        if not new_data.empty:
            data = pd.concat([data, new_data])
            data.to_csv(file_path)
    else:
        data = get_data(ticker, '1min')
        data.to_csv(file_path)
    
    if data.empty:
        raise ValueError(f"No historical data found for ticker {ticker}")
    logging.info(f"Loaded historical data for {ticker} with {len(data)} records.")
    return data

def apply_strategy(strategy, ticker, historical_data, initial_cash=10000):
    """Apply a strategy to historical data and calculate performance."""
    cash = initial_cash
    holdings = 0
    portfolio_values = []
    trades = 0
    wins = 0
    max_drawdown = 0
    peak = initial_cash
    max_drawdown_euro = 0

    for index, row in historical_data.iterrows():
        current_price = row['Close']
        action, quantity = simulate_strategy(strategy, ticker, current_price, historical_data.loc[:index], cash, holdings, cash + holdings * current_price)
        
        if action == 'buy' and cash >= quantity * current_price:
            cash -= quantity * current_price
            holdings += quantity
            trades += 1
        elif action == 'sell' and holdings >= quantity:
            cash += quantity * current_price
            holdings -= quantity
            trades += 1
            if quantity * current_price > initial_cash:
                wins += 1
        
        portfolio_value = cash + holdings * current_price
        portfolio_values.append(portfolio_value)
        peak = max(peak, portfolio_value)
        drawdown = (peak - portfolio_value) / peak
        max_drawdown = max(max_drawdown, drawdown)
        max_drawdown_euro = max(max_drawdown_euro, peak - portfolio_value)

    win_percentage = (wins / trades) * 100 if trades > 0 else 0
    logging.info(f"Applied strategy {strategy.__name__} on {ticker}. Final portfolio value: {portfolio_values[-1]}, Trades: {trades}, Win%: {win_percentage:.2f}%, Max Drawdown: {max_drawdown:.2f} ({max_drawdown_euro:.2f} EUR)")
    return portfolio_values, trades, win_percentage, max_drawdown, max_drawdown_euro

def plot_performance(ticker, strategy_performances, initial_cash):
    """Generate data for Chart.js to plot the performance of all strategies with a baseline."""
    if not strategy_performances:
        raise ValueError("No strategy performances available to plot.")
    
    labels = [str(date) for date in list(strategy_performances.values())[0]['portfolio_values'].index]
    datasets = []

    for strategy_name, performance in strategy_performances.items():
        datasets.append({
            'label': f'{strategy_name} Performance',
            'data': performance['portfolio_values'].tolist(),
            'borderColor': 'rgba(75, 192, 192, 1)',
            'fill': {                
                'target': {
                    'value': initial_cash,
                    'above': 'rgba(0, 255, 0, 0.3)',  # Green fill
                    'below': 'rgba(255, 0, 0, 0.3)'   # Red fill
                }
            }
        })

    # Add baseline
    baseline = [initial_cash] * len(labels)
    datasets.append({
        'label': 'Baseline',
        'data': baseline,
        'borderColor': 'rgba(0, 0, 0, 1)',
        'borderDash': [5, 5],
        'fill': False
    })

    chart_data = {
        'labels': labels,
        'datasets': datasets
    }
    return chart_data

def display_non_profitable_strategies(non_profitable_strategies):
    """Display a table of non-profitable strategies."""
    if non_profitable_strategies:
        table_html = "<table><tr><th>Strategy</th><th>Final Portfolio Value</th><th>Trades</th><th>Win%</th><th>Max Drawdown (%)</th><th>Max Drawdown (EUR)</th></tr>"
        for strategy_name, performance in non_profitable_strategies.items():
            table_html += f"<tr><td>{strategy_name}</td><td>{performance['final_value']:.2f}</td><td>{performance['trades']}</td><td>{performance['win_percentage']:.2f}%</td><td>{performance['max_drawdown']:.2f}%</td><td>{performance['max_drawdown_euro']:.2f} EUR</td></tr>"
        table_html += "</table>"
        return table_html
    return ""

def backtest(ticker):
    """Backtest all strategies on a given ticker."""
    historical_data = load_historical_data(ticker)
    if historical_data.empty:
        raise ValueError(f"No historical data available for ticker {ticker}")
    
    strategy_performances = {}
    non_profitable_strategies = {}
    initial_cash = 10000

    for strategy in strategies:
        try:
            portfolio_values, trades, win_percentage, max_drawdown, max_drawdown_euro = apply_strategy(strategy, ticker, historical_data, initial_cash)
            if trades > 0:  # Only include strategies that generate trades
                if portfolio_values[-1] > initial_cash:
                    strategy_performances[strategy.__name__] = {
                        'portfolio_values': pd.Series(portfolio_values, index=historical_data.index),
                        'trades': trades,
                        'win_percentage': win_percentage,
                        'max_drawdown': max_drawdown * 100,  # Convert to percentage
                        'max_drawdown_euro': max_drawdown_euro
                    }
                else:
                    non_profitable_strategies[strategy.__name__] = {
                        'final_value': portfolio_values[-1],
                        'trades': trades,
                        'win_percentage': win_percentage,
                        'max_drawdown': max_drawdown * 100,  # Convert to percentage
                        'max_drawdown_euro': max_drawdown_euro
                    }
        except Exception as e:
            logging.error(f"Error applying strategy {strategy.__name__} on {ticker}: {e}")

    chart_data = plot_performance(ticker, strategy_performances, initial_cash)
    non_profitable_table = display_non_profitable_strategies(non_profitable_strategies)
    
    # Log final portfolio values for consistency
    for strategy_name, performance in strategy_performances.items():
        logging.info(f"Final portfolio value for {strategy_name}: {performance['portfolio_values'].iloc[-1]}, Trades: {performance['trades']}, Win%: {performance['win_percentage']:.2f}%, Max Drawdown: {performance['max_drawdown']:.2f}% ({performance['max_drawdown_euro']:.2f} EUR)")
    for strategy_name, performance in non_profitable_strategies.items():
        logging.info(f"Final portfolio value for {strategy_name}: {performance['final_value']}, Trades: {performance['trades']}, Win%: {performance['win_percentage']:.2f}%, Max Drawdown: {performance['max_drawdown']:.2f}% ({performance['max_drawdown_euro']:.2f} EUR)")

    return chart_data, non_profitable_table, strategy_performances, non_profitable_strategies

if __name__ == "__main__":
    ticker = 'AAPL'  # Example ticker
    backtest(ticker)
