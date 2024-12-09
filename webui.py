from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse, HTMLResponse
import subprocess
import os
from backtesting_client import backtest
from testing_client import test_strategies
from trading_client import main as trading_main
from threading import Thread
import logging
import json

app = FastAPI()

processes = {}
results_cache = {}
selected_strategy = None

def run_in_thread(func):
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
    return wrapper

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <html>
        <head>
            <title>AmpyFin Trading Bot</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
                #main { padding: 20px; }
                label { display: block; margin-top: 10px; }
                button { margin-top: 10px; }
                #output, #results { margin-top: 20px; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .non-profitable { background-color: #f8d7da; }
            </style>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
        </head>
        <body>
            <div id="main">
                <h1>AmpyFin Trading Bot</h1>
                <label for="ticker">Ticker:</label>
                <input type="text" id="ticker" name="ticker" value="AAPL">
                <label for="period">Period:</label>
                <select id="period" name="period">
                    <option value="1d">1d</option>
                    <option value="5d">5d</option>
                    <option value="1mo">1mo</option>
                    <option value="3mo">3mo</option>
                    <option value="6mo">6mo</option>
                    <option value="1y">1y</option>
                    <option value="2y">2y</option>
                    <option value="5y">5y</option>
                    <option value="10y">10y</option>
                    <option value="ytd">ytd</option>
                    <option value="max">max</option>
                </select>
                <button onclick="startBacktest()">Start Backtest</button>
                <button onclick="startTestingClient()">Start Testing Client</button>
                <button onclick="startTradingClient()">Start Trading Client</button>
                <button onclick="stopAll()">Stop All</button>
                <div id="output"></div>
                <canvas id="performanceChart" width="400" height="200"></canvas>
                <div id="results"></div>
            </div>
            <script>
                let chartInstance = null;
                let selectedStrategy = null;

                function startBacktest() {
                    const ticker = document.getElementById('ticker').value;
                    const period = document.getElementById('period').value;
                    fetch(`/start-backtest?ticker=${ticker}&period=${period}`)
                        .then(response => response.text())
                        .then(data => {
                            document.getElementById('output').innerHTML = data;
                            console.log('Backtest started');
                        });
                }
                function startTestingClient() {
                    fetch('/start-testing-client')
                        .then(response => response.text())
                        .then(data => {
                            document.getElementById('output').innerHTML = data;
                            console.log('Testing client started');
                        });
                }
                function startTradingClient() {
                    fetch('/start-trading-client')
                        .then(response => response.text())
                        .then(data => {
                            document.getElementById('output').innerHTML = data;
                            console.log('Trading client started');
                        });
                }
                function stopAll() {
                    fetch('/stop-all')
                        .then(response => response.text())
                        .then(data => {
                            document.getElementById('output').innerHTML = data;
                            console.log('All processes stopped');
                        });
                }
                function fetchResults() {
                    fetch('/results')
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                document.getElementById('results').innerHTML = data.error;
                            } else {
                                const resultsDiv = document.getElementById('results');
                                const currentScrollPosition = window.scrollY;
                                resultsDiv.innerHTML = data.non_profitable_table;
                                const checkboxes = document.querySelectorAll("input[name='strategy']");
                                checkboxes.forEach(checkbox => {
                                    checkbox.addEventListener('change', function() {
                                        if (this.checked) {
                                            selectedStrategy = this.value;
                                            updateChart(data.chart_data);
                                        }
                                    });
                                });
                                if (selectedStrategy) {
                                    updateChart(data.chart_data);
                                }
                                window.scrollTo(0, currentScrollPosition);
                            }
                        });
                }
                function updateChart(chartData) {
                    const selectedData = chartData.datasets.find(dataset => dataset.label.includes(selectedStrategy));
                    const baselineData = chartData.datasets.find(dataset => dataset.label === 'Baseline');
                    const ctx = document.getElementById('performanceChart').getContext('2d');
                    if (chartInstance) {
                        chartInstance.destroy();
                    }
                    if (selectedData && baselineData) {
                        chartInstance = new Chart(ctx, {
                            type: 'line',
                            data: {
                                labels: chartData.labels,
                                datasets: [selectedData, baselineData]
                            },
                            options: {
                                responsive: true,
                                scales: {
                                    x: {
                                        type: 'time',
                                        time: {
                                            unit: 'auto'
                                        },
                                        display: true,
                                        title: {
                                            display: true,
                                            text: 'Date'
                                        }
                                    },
                                    y: {
                                        beginAtZero: true,
                                        display: true,
                                        title: {
                                            display: true,
                                            text: 'Portfolio Value'
                                        }
                                    }
                                }
                            }
                        });
                    }
                }
                setInterval(fetchResults, 5000); // Fetch results every 5 seconds
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/start-backtest")
def start_backtest(request: Request, background_tasks: BackgroundTasks):
    ticker = request.query_params.get('ticker', 'AAPL')
    period = request.query_params.get('period', '1y')
    background_tasks.add_task(run_backtest, ticker, period)
    logging.info(f"Backtest started for {ticker} with period {period}.")
    return f"Backtest started for {ticker} with period {period}."

@app.get("/results", response_class=JSONResponse)
def get_results():
    return JSONResponse(content=results_cache.get('results', {}))

@app.get("/start-testing-client")
def start_testing_client(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_testing_client)
    logging.info("Testing client started.")
    return "Testing client started."

@app.get("/start-trading-client")
def start_trading_client(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_trading_client)
    logging.info("Trading client started.")
    return "Trading client started."

@app.get("/stop-all")
def stop_all():
    for name, process in processes.items():
        process.terminate()
        process.wait()  # Ensure the process has terminated
    processes.clear()
    logging.info("All processes stopped.")
    return "All processes stopped."

@run_in_thread
def run_backtest(ticker, period):
    try:
        chart_data, non_profitable_table, strategy_performances, non_profitable_strategies = backtest(ticker, period)
        
        # Sort strategies by final portfolio value
        sorted_strategies = sorted(strategy_performances.items(), key=lambda x: x[1]['portfolio_values'].iloc[-1], reverse=True)
        sorted_non_profitable = sorted(non_profitable_strategies.items(), key=lambda x: x[1]['final_value'], reverse=True)
        
        # Create HTML table for results with checkboxes
        table_html = "<table><tr><th>Select</th><th>Strategy</th><th>Final Portfolio Value</th><th>Trades</th><th>Win%</th><th>Max Drawdown (EUR)</th></tr>"
        for strategy_name, performance in sorted_strategies:
            table_html += f"<tr><td><input type='checkbox' name='strategy' value='{strategy_name}'></td><td>{strategy_name}</td><td>{performance['portfolio_values'].iloc[-1]:.2f}</td><td>{performance['trades']}</td><td>{performance['win_percentage']:.2f}%</td><td>{performance['max_drawdown_euro']:.2f} EUR</td></tr>"
        for strategy_name, performance in sorted_non_profitable:
            table_html += f"<tr class='non-profitable'><td><input type='checkbox' name='strategy' value='{strategy_name}'></td><td>{strategy_name}</td><td>{performance['final_value']:.2f}</td><td>{performance['trades']}</td><td>{performance['win_percentage']:.2f}%</td><td>{performance['max_drawdown_euro']:.2f} EUR</td></tr>"
        table_html += "</table>"
        
        results = {
            'chart_data': chart_data,
            'non_profitable_table': table_html
        }
        
        results_cache['results'] = results
        
        # Log final portfolio values for consistency
        for strategy_name, performance in strategy_performances.items():
            logging.info(f"Final portfolio value for {strategy_name}: {performance['portfolio_values'].iloc[-1]}, Trades: {performance['trades']}, Win%: {performance['win_percentage']:.2f}%, Max Drawdown: {performance['max_drawdown']:.2f}")
        for strategy_name, performance in non_profitable_strategies.items():
            logging.info(f"Final portfolio value for {strategy_name}: {performance['final_value']}, Trades: {performance['trades']}, Win%: {performance['win_percentage']:.2f}%, Max Drawdown: {performance['max_drawdown']:.2f}")
    except Exception as e:
        results_cache['results'] = {'error': f"Error during backtest: {str(e)}"}

@run_in_thread
def run_testing_client():
    test_strategies()

@run_in_thread
def run_trading_client():
    trading_main()

if __name__ == "__main__":
    logging.basicConfig(filename='system.log', level=logging.INFO, format='%(asctime)s - %(message)s')
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
