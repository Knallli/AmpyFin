from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse, HTMLResponse
from pymongo import MongoClient
from config import mongo_url
from backtesting_client import backtest, apply_strategy
from helper_files.client_helper import strategies, get_data
import logging
import json
from datetime import datetime

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <html>
        <head>
            <title>Strategy Rankings</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
                #main { padding: 20px; }
                .strategy-list { max-height: 400px; overflow-y: auto; margin-top: 20px; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; cursor: pointer; }
            </style>
        </head>
        <body>
            <div id="main">
                <h1>Strategy Rankings</h1>
                <div class="strategy-list">
                    <table>
                        <thead>
                            <tr>
                                <th onclick="sortTable(0)">Rank</th>
                                <th onclick="sortTable(1)">Strategy</th>
                                <th onclick="sortTable(2)">Points</th>
                                <th onclick="sortTable(3)">Last Updated</th>
                                <th onclick="sortTable(4)">Trades Won</th>
                                <th onclick="sortTable(5)">Trades Lost</th>
                                <th onclick="sortTable(6)">Win Rate (%)</th>
                            </tr>
                        </thead>
                        <tbody id="strategyList"></tbody>
                    </table>
                </div>
                <h2>Simulator</h2>
                <label for="ticker">Ticker:</label>
                <input type="text" id="ticker" name="ticker">
                <label for="timeframe">Timeframe:</label>
                <select id="timeframe" name="timeframe">
                    <option value="1d">1d</option>
                    <option value="5d">5d</option>
                    <option value="1mo">1mo</option>
                    <option value="3mo">3mo</option>
                    <option value="6mo">6mo</option>
                    <option value="1y">1y</option>
                    <option value="2y">2y</option>
                    <option value="5y">5y</option>
                    <option value="ytd">ytd</option>
                    <option value="max">max</option>
                </select>
                <button onclick="startSimulation()">Start Simulation</button>
                <div id="simulationOutput"></div>
            </div>
            <script>
                function fetchRankings() {
                    fetch('/rankings')
                        .then(response => response.json())
                        .then(data => {
                            const strategyList = document.getElementById('strategyList');
                            strategyList.innerHTML = '';
                            data.forEach(item => {
                                const row = document.createElement('tr');
                                row.innerHTML = `<td>${item.rank}</td><td>${item.strategy}</td><td>${item.points}</td><td>${item.last_updated}</td><td>${item.trades_won}</td><td>${item.trades_lost}</td><td>${item.win_rate}</td>`;
                                strategyList.appendChild(row);
                            });
                        });
                }

                function startSimulation() {
                    const ticker = document.getElementById('ticker').value;
                    const timeframe = document.getElementById('timeframe').value;
                    fetch(`/simulate?ticker=${ticker}&timeframe=${timeframe}`)
                        .then(response => response.json())
                        .then(data => {
                            const simulationOutput = document.getElementById('simulationOutput');
                            simulationOutput.innerHTML = '<h3>Simulation Results</h3>';
                            const table = document.createElement('table');
                            table.innerHTML = `
                                <thead>
                                    <tr>
                                        <th>Strategy</th>
                                        <th>Initial Portfolio Value</th>
                                        <th>Final Portfolio Value</th>
                                        <th>% Gain/Loss</th>
                                        <th>% Gain/Loss (Hold)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.map(result => `
                                        <tr>
                                            <td>${result.strategy}</td>
                                            <td>${result.initial_value}</td>
                                            <td>${result.final_value}</td>
                                            <td>${result.percentage_change}</td>
                                            <td>${result.hold_percentage_change}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            `;
                            simulationOutput.appendChild(table);
                        });
                }

                function sortTable(n) {
                    const table = document.querySelector("table");
                    let rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                    switching = true;
                    dir = "asc"; 
                    while (switching) {
                        switching = false;
                        rows = table.rows;
                        for (i = 1; i < (rows.length - 1); i++) {
                            shouldSwitch = false;
                            x = rows[i].getElementsByTagName("TD")[n];
                            y = rows[i + 1].getElementsByTagName("TD")[n];
                            if (dir == "asc") {
                                if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                                    shouldSwitch = true;
                                    break;
                                }
                            } else if (dir == "desc") {
                                if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                                    shouldSwitch = true;
                                    break;
                                }
                            }
                        }
                        if (shouldSwitch) {
                            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                            switching = true;
                            switchcount++;
                        } else {
                            if (switchcount == 0 && dir == "asc") {
                                dir = "desc";
                                switching = true;
                            }
                        }
                    }
                }

                setInterval(fetchRankings, 5000); // Fetch rankings every 5 seconds
                fetchRankings(); // Initial fetch
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/rankings", response_class=JSONResponse)
def get_rankings():
    client = MongoClient(mongo_url)
    db = client.trading_simulator
    rank_collection = db.rank
    points_collection = db.points_tally
    holdings_collection = db.algorithm_holdings

    rankings = []
    for rank_doc in rank_collection.find().sort("rank", 1):
        strategy = rank_doc["strategy"]
        points_doc = points_collection.find_one({"strategy": strategy})
        holdings_doc = holdings_collection.find_one({"strategy": strategy})
        points = points_doc["total_points"] if points_doc else 0
        last_updated = holdings_doc["last_updated"].strftime('%Y-%m-%d %H:%M:%S') if holdings_doc and "last_updated" in holdings_doc else "N/A"
        trades_won = holdings_doc["successful_trades"] if holdings_doc else 0
        trades_lost = holdings_doc["failed_trades"] if holdings_doc else 0
        total_trades = trades_won + trades_lost
        win_rate = (trades_won / total_trades * 100) if total_trades > 0 else 0
        rankings.append({
            "rank": rank_doc["rank"],
            "strategy": strategy,
            "points": points,
            "last_updated": last_updated,
            "trades_won": trades_won,
            "trades_lost": trades_lost,
            "win_rate": win_rate
        })

    client.close()
    return JSONResponse(content=rankings)

@app.get("/simulate", response_class=JSONResponse)
def simulate(ticker: str, timeframe: str):
    historical_data = get_data(ticker, timeframe)
    initial_cash = 10000
    results = []

    for strategy in strategies:
        portfolio_values, trades, win_percentage, max_drawdown, max_drawdown_euro = apply_strategy(strategy, ticker, historical_data, initial_cash)
        initial_value = initial_cash
        final_value = portfolio_values[-1]
        percentage_change = ((final_value - initial_value) / initial_value) * 100

        # Calculate the gain/loss if just holding the ticker
        hold_initial_price = historical_data['Close'].iloc[0]
        hold_final_price = historical_data['Close'].iloc[-1]
        hold_percentage_change = ((hold_final_price - hold_initial_price) / hold_initial_price) * 100

        results.append({
            "strategy": strategy.__name__,
            "initial_value": initial_value,
            "final_value": final_value,
            "percentage_change": percentage_change,
            "hold_percentage_change": hold_percentage_change
        })

    return JSONResponse(content=results)

if __name__ == "__main__":
    logging.basicConfig(filename='system.log', level=logging.INFO, format='%(asctime)s - %(message)s')
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
