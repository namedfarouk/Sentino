import os
import json
from flask import Flask, render_template_string, jsonify, request
from dotenv import load_dotenv
from og_client import init_client, run_verifiable_analysis
from sentiment_analyzer import analyze_token

load_dotenv()

app = Flask(__name__)
client = None

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Senti-Bot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0a0f;
            color: #e0e0e0;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-bottom: 1px solid #1a73e8;
            padding: 24px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 28px;
            font-weight: 700;
            color: #fff;
        }
        .logo span { color: #1a73e8; }
        .badge {
            background: #1a73e820;
            border: 1px solid #1a73e8;
            color: #1a73e8;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
        }
        .container { max-width: 900px; margin: 0 auto; padding: 40px 20px; }
        .search-box {
            background: #12121a;
            border: 1px solid #2a2a3a;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            display: flex;
            gap: 12px;
        }
        .search-box input {
            flex: 1;
            background: #1a1a2e;
            border: 1px solid #2a2a3a;
            color: #fff;
            padding: 14px 18px;
            border-radius: 8px;
            font-size: 16px;
            outline: none;
        }
        .search-box input:focus { border-color: #1a73e8; }
        .search-box input::placeholder { color: #555; }
        .search-box button {
            background: #1a73e8;
            color: #fff;
            border: none;
            padding: 14px 28px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            font-weight: 600;
        }
        .search-box button:hover { background: #1557b0; }
        .search-box button:disabled { background: #333; cursor: not-allowed; }
        .quick-tokens {
            display: flex;
            gap: 8px;
            margin-top: 12px;
            flex-wrap: wrap;
        }
        .quick-token {
            background: #1a1a2e;
            border: 1px solid #2a2a3a;
            color: #aaa;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
        }
        .quick-token:hover { border-color: #1a73e8; color: #fff; }
        .loading {
            text-align: center;
            padding: 40px;
            color: #888;
            display: none;
        }
        .spinner {
            width: 40px; height: 40px;
            border: 3px solid #2a2a3a;
            border-top-color: #1a73e8;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .result-card {
            background: #12121a;
            border: 1px solid #2a2a3a;
            border-radius: 12px;
            padding: 28px;
            margin-bottom: 20px;
            display: none;
        }
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .token-name { font-size: 24px; font-weight: 700; }
        .token-price { font-size: 28px; font-weight: 700; color: #fff; }
        .signal-badge {
            padding: 8px 20px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 18px;
        }
        .signal-BULLISH { background: #0d3b1e; color: #34d058; border: 1px solid #34d058; }
        .signal-BEARISH { background: #3b0d0d; color: #f85149; border: 1px solid #f85149; }
        .signal-NEUTRAL { background: #3b3b0d; color: #d9d042; border: 1px solid #d9d042; }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }
        .metric {
            background: #1a1a2e;
            padding: 14px;
            border-radius: 8px;
        }
        .metric-label { font-size: 12px; color: #888; text-transform: uppercase; }
        .metric-value { font-size: 18px; font-weight: 600; margin-top: 4px; }
        .negative { color: #f85149; }
        .positive { color: #34d058; }
        .reasoning {
            background: #1a1a2e;
            padding: 16px;
            border-radius: 8px;
            margin-top: 16px;
            line-height: 1.6;
            color: #ccc;
        }
        .verification {
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #2a2a3a;
            font-size: 13px;
            color: #666;
        }
        .history { margin-top: 40px; }
        .history-title { font-size: 18px; margin-bottom: 16px; color: #888; }
        .history-item {
            background: #12121a;
            border: 1px solid #2a2a3a;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">Senti<span>-Bot</span></div>
        <div class="badge">Powered by OpenGradient</div>
    </div>
    <div class="container">
        <div class="search-box">
            <input type="text" id="tokenInput" placeholder="Enter token (e.g. bitcoin, eth, sol, doge...)" onkeypress="if(event.key==='Enter')analyze()">
            <button id="analyzeBtn" onclick="analyze()">Analyze</button>
        </div>
        <div class="quick-tokens">
            <span class="quick-token" onclick="quickAnalyze('bitcoin')">Bitcoin</span>
            <span class="quick-token" onclick="quickAnalyze('ethereum')">Ethereum</span>
            <span class="quick-token" onclick="quickAnalyze('solana')">Solana</span>
            <span class="quick-token" onclick="quickAnalyze('dogecoin')">Doge</span>
            <span class="quick-token" onclick="quickAnalyze('cardano')">Cardano</span>
            <span class="quick-token" onclick="quickAnalyze('ripple')">XRP</span>
        </div>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Senti-Bot is analyzing... verifiable inference in progress</p>
        </div>

        <div class="result-card" id="resultCard">
            <div class="result-header">
                <div>
                    <div class="token-name" id="tokenSymbol"></div>
                    <div class="token-price" id="tokenPrice"></div>
                </div>
                <div class="signal-badge" id="signalBadge"></div>
            </div>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">24h Change</div>
                    <div class="metric-value" id="change24h"></div>
                </div>
                <div class="metric">
                    <div class="metric-label">7d Change</div>
                    <div class="metric-value" id="change7d"></div>
                </div>
                <div class="metric">
                    <div class="metric-label">Confidence</div>
                    <div class="metric-value" id="confidence"></div>
                </div>
                <div class="metric">
                    <div class="metric-label">Risk Level</div>
                    <div class="metric-value" id="riskLevel"></div>
                </div>
            </div>
            <div class="reasoning" id="reasoning"></div>
            <div class="verification" id="verification"></div>
        </div>

        <div class="history" id="historySection" style="display:none">
            <div class="history-title">Recent Analyses</div>
            <div id="historyList"></div>
        </div>
    </div>

    <script>
        let history = [];

        function quickAnalyze(token) {
            document.getElementById('tokenInput').value = token;
            analyze();
        }

        async function analyze() {
            const token = document.getElementById('tokenInput').value.trim();
            if (!token) return;

            document.getElementById('analyzeBtn').disabled = true;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('resultCard').style.display = 'none';

            try {
                const res = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token: token})
                });
                const data = await res.json();

                if (data.error) {
                    alert('Could not find token: ' + token);
                    return;
                }

                const price = data.price_data;
                const signal = data.signal;

                document.getElementById('tokenSymbol').textContent = price.symbol;
                document.getElementById('tokenPrice').textContent = '$' + price.price_usd.toLocaleString();

                const badge = document.getElementById('signalBadge');
                badge.textContent = signal.signal;
                badge.className = 'signal-badge signal-' + signal.signal;

                const c24 = document.getElementById('change24h');
                c24.textContent = price.change_24h_pct + '%';
                c24.className = 'metric-value ' + (price.change_24h_pct >= 0 ? 'positive' : 'negative');

                const c7d = document.getElementById('change7d');
                c7d.textContent = price.change_7d_pct + '%';
                c7d.className = 'metric-value ' + (price.change_7d_pct >= 0 ? 'positive' : 'negative');

                document.getElementById('confidence').textContent = signal.confidence + '%';
                document.getElementById('riskLevel').textContent = signal.risk_level;
                document.getElementById('reasoning').textContent = signal.reasoning;
                document.getElementById('verification').textContent =
                    'Verified via OpenGradient | Model: ' + data.verification.model +
                    ' | TX: ' + data.verification.tx_hash;

                document.getElementById('resultCard').style.display = 'block';

                history.unshift({symbol: price.symbol, signal: signal.signal, price: price.price_usd, time: new Date().toLocaleTimeString()});
                updateHistory();

            } catch(e) {
                alert('Error: ' + e.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('analyzeBtn').disabled = false;
            }
        }

        function updateHistory() {
            if (history.length === 0) return;
            document.getElementById('historySection').style.display = 'block';
            const list = document.getElementById('historyList');
            list.innerHTML = history.slice(0, 10).map(h =>
                '<div class="history-item">' +
                '<span>' + h.symbol + ' - $' + h.price.toLocaleString() + '</span>' +
                '<span class="signal-badge signal-' + h.signal + '" style="padding:4px 12px;font-size:13px">' + h.signal + '</span>' +
                '<span style="color:#666;font-size:13px">' + h.time + '</span>' +
                '</div>'
            ).join('');
        }
    </script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json()
    token = data.get("token", "bitcoin")

    result = analyze_token(client, token)
    return jsonify(result)


if __name__ == "__main__":
    client = init_client()
    print("\nSenti-Bot Dashboard: http://localhost:5000")
    print("Open this link in your browser!\n")
    app.run(debug=False, port=5000)
