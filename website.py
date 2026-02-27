import os
import json
import time
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
from dotenv import load_dotenv
from og_client import init_client, run_verifiable_analysis
from sentiment_analyzer import analyze_token
from price_fetcher import get_chart_data, get_fear_greed

load_dotenv()

app = Flask(__name__)
client = None

# Signal history file
HISTORY_FILE = "signal_history.json"


def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_to_history(result):
    history = load_history()
    entry = {
        "symbol": result["price_data"]["symbol"],
        "token": result["price_data"]["token"],
        "price": result["price_data"]["price_usd"],
        "change_24h": result["price_data"]["change_24h_pct"],
        "signal": result["signal"].get("signal", "N/A"),
        "confidence": result["signal"].get("confidence", 0),
        "risk": result["signal"].get("risk_level", "N/A"),
        "reasoning": result["signal"].get("reasoning", ""),
        "tx_hash": result["verification"]["tx_hash"],
        "timestamp": datetime.now().isoformat(),
    }
    history.insert(0, entry)
    history = history[:100]  # Keep last 100
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    return entry


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentino</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Sora:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
    <style>
        :root {
            --bg: #08080c;
            --surface: #0f0f14;
            --surface-2: #16161e;
            --border: #1e1e2a;
            --border-hover: #2a2a3d;
            --text: #e8e8ed;
            --text-dim: #6b6b7b;
            --text-muted: #3d3d4d;
            --accent: #c8ff00;
            --accent-dim: #c8ff0015;
            --red: #ff4d4d;
            --red-dim: #ff4d4d12;
            --green: #00e676;
            --green-dim: #00e67612;
            --yellow: #ffd740;
            --yellow-dim: #ffd74012;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Sora', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            overflow-x: hidden;
        }

        body::after {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
            pointer-events: none;
            z-index: 9999;
        }

        nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 40px;
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            background: rgba(8,8,12,0.95);
            z-index: 100;
            backdrop-filter: blur(20px);
        }

        .logo {
            font-family: 'DM Mono', monospace;
            font-size: 20px;
            font-weight: 500;
            letter-spacing: -0.5px;
        }

        .logo em { font-style: normal; color: var(--accent); }

        .nav-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .nav-tag {
            font-family: 'DM Mono', monospace;
            font-size: 11px;
            color: var(--text-dim);
            letter-spacing: 1.5px;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .nav-dot {
            width: 6px; height: 6px;
            border-radius: 50%;
            background: var(--accent);
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

        /* Fear & Greed in nav */
        .fg-badge {
            font-family: 'DM Mono', monospace;
            font-size: 11px;
            padding: 6px 12px;
            border-radius: 3px;
            letter-spacing: 0.5px;
            border: 1px solid var(--border);
            cursor: default;
        }

        .fg-extreme-fear { color: var(--red); border-color: var(--red); background: var(--red-dim); }
        .fg-fear { color: #ff8a65; border-color: #ff8a65; background: #ff8a6512; }
        .fg-neutral { color: var(--yellow); border-color: var(--yellow); background: var(--yellow-dim); }
        .fg-greed { color: #66bb6a; border-color: #66bb6a; background: #66bb6a12; }
        .fg-extreme-greed { color: var(--green); border-color: var(--green); background: var(--green-dim); }

        .main {
            max-width: 800px;
            margin: 0 auto;
            padding: 60px 24px 40px;
        }

        .hero-label {
            font-family: 'DM Mono', monospace;
            font-size: 11px;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 16px;
        }

        .hero-title {
            font-size: 44px;
            font-weight: 300;
            line-height: 1.15;
            letter-spacing: -1.5px;
            margin-bottom: 12px;
        }

        .hero-title strong { font-weight: 600; color: var(--accent); }

        .hero-sub {
            font-size: 15px;
            color: var(--text-dim);
            line-height: 1.7;
            max-width: 480px;
            margin-bottom: 48px;
        }

        .input-group {
            position: relative;
            margin-bottom: 16px;
        }

        .input-group input {
            width: 100%;
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text);
            font-family: 'DM Mono', monospace;
            font-size: 15px;
            padding: 20px 24px;
            padding-right: 140px;
            border-radius: 4px;
            outline: none;
            transition: border-color 0.2s;
        }

        .input-group input::placeholder { color: var(--text-muted); }
        .input-group input:focus { border-color: var(--accent); }

        .input-group button {
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            background: var(--accent);
            color: var(--bg);
            border: none;
            font-family: 'DM Mono', monospace;
            font-size: 12px;
            font-weight: 500;
            padding: 10px 24px;
            border-radius: 3px;
            cursor: pointer;
            letter-spacing: 1px;
            text-transform: uppercase;
            transition: opacity 0.2s;
        }

        .input-group button:hover { opacity: 0.85; }
        .input-group button:disabled { opacity: 0.3; cursor: not-allowed; }

        .picks {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            margin-bottom: 48px;
        }

        .pick {
            font-family: 'DM Mono', monospace;
            font-size: 11px;
            color: var(--text-dim);
            background: transparent;
            border: 1px solid var(--border);
            padding: 7px 14px;
            border-radius: 3px;
            cursor: pointer;
            transition: all 0.2s;
            letter-spacing: 0.5px;
        }

        .pick:hover { border-color: var(--accent); color: var(--accent); }

        .pick-watchlist {
            background: var(--accent-dim);
            border-color: var(--accent);
            color: var(--accent);
        }

        /* Loading */
        .loading { display: none; padding: 48px 0; text-align: center; }

        .loading-bar {
            width: 200px; height: 2px;
            background: var(--surface-2);
            margin: 0 auto 20px;
            border-radius: 1px;
            overflow: hidden;
        }

        .loading-bar::after {
            content: '';
            display: block;
            width: 40%; height: 100%;
            background: var(--accent);
            animation: slide 1.2s ease-in-out infinite;
        }

        @keyframes slide { 0%{transform:translateX(-100%)} 100%{transform:translateX(350%)} }

        .loading-text {
            font-family: 'DM Mono', monospace;
            font-size: 12px;
            color: var(--text-muted);
            letter-spacing: 1px;
        }

        /* Result card */
        .result {
            display: none;
            animation: fadeUp 0.4s ease;
            margin-bottom: 32px;
        }

        @keyframes fadeUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }

        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 20px;
        }

        .result-symbol {
            font-family: 'DM Mono', monospace;
            font-size: 13px;
            color: var(--text-dim);
            letter-spacing: 1px;
            margin-bottom: 4px;
        }

        .result-price {
            font-size: 36px;
            font-weight: 600;
            letter-spacing: -1px;
        }

        .signal-tag {
            font-family: 'DM Mono', monospace;
            font-size: 12px;
            font-weight: 500;
            padding: 8px 16px;
            border-radius: 3px;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }

        .signal-BULLISH { color: var(--green); background: var(--green-dim); border: 1px solid var(--green); }
        .signal-BEARISH { color: var(--red); background: var(--red-dim); border: 1px solid var(--red); }
        .signal-NEUTRAL { color: var(--yellow); background: var(--yellow-dim); border: 1px solid var(--yellow); }

        /* Chart */
        .chart-wrap {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 20px;
            margin-bottom: 20px;
            position: relative;
        }

        .chart-label {
            font-family: 'DM Mono', monospace;
            font-size: 10px;
            color: var(--text-muted);
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 12px;
        }

        .chart-wrap canvas { width: 100% !important; height: 200px !important; }

        /* Metrics */
        .metrics {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1px;
            background: var(--border);
            border: 1px solid var(--border);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 20px;
        }

        .metric { background: var(--surface); padding: 18px; }

        .metric-label {
            font-family: 'DM Mono', monospace;
            font-size: 10px;
            color: var(--text-muted);
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .metric-val { font-size: 18px; font-weight: 500; letter-spacing: -0.3px; }
        .neg { color: var(--red); }
        .pos { color: var(--green); }

        .reasoning {
            font-size: 14px;
            line-height: 1.8;
            color: var(--text-dim);
            padding: 16px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 14px;
        }

        .verification {
            font-family: 'DM Mono', monospace;
            font-size: 11px;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .v-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--accent); }

        /* Watchlist section */
        .section-label {
            font-family: 'DM Mono', monospace;
            font-size: 11px;
            color: var(--text-muted);
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 16px;
            margin-top: 48px;
        }

        .watchlist-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 1px;
            background: var(--border);
            border: 1px solid var(--border);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 32px;
        }

        .wl-card {
            background: var(--surface);
            padding: 20px;
            cursor: pointer;
            transition: background 0.2s;
        }

        .wl-card:hover { background: var(--surface-2); }

        .wl-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .wl-symbol {
            font-family: 'DM Mono', monospace;
            font-size: 14px;
            font-weight: 500;
        }

        .wl-signal {
            font-family: 'DM Mono', monospace;
            font-size: 9px;
            padding: 3px 8px;
            border-radius: 2px;
            letter-spacing: 1px;
        }

        .wl-price { font-size: 20px; font-weight: 600; letter-spacing: -0.5px; margin-bottom: 4px; }

        .wl-change {
            font-family: 'DM Mono', monospace;
            font-size: 12px;
        }

        /* History */
        .h-item {
            display: grid;
            grid-template-columns: 60px 1fr 80px 80px 60px;
            align-items: center;
            padding: 14px 0;
            border-bottom: 1px solid var(--border);
            gap: 12px;
        }

        .h-symbol {
            font-family: 'DM Mono', monospace;
            font-size: 13px;
        }

        .h-reasoning {
            font-size: 12px;
            color: var(--text-dim);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .h-signal {
            font-family: 'DM Mono', monospace;
            font-size: 10px;
            letter-spacing: 1px;
            padding: 4px 8px;
            border-radius: 2px;
            text-align: center;
        }

        .h-price {
            font-family: 'DM Mono', monospace;
            font-size: 12px;
            color: var(--text-dim);
            text-align: right;
        }

        .h-time {
            font-family: 'DM Mono', monospace;
            font-size: 11px;
            color: var(--text-muted);
            text-align: right;
        }

        footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            border-top: 1px solid var(--border);
            padding: 14px 40px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            background: rgba(8,8,12,0.92);
            backdrop-filter: blur(16px);
            z-index: 100;
        }

        footer span {
            font-family: 'DM Mono', monospace;
            font-size: 11px;
            color: var(--text-muted);
            letter-spacing: 0.5px;
        }

        footer .sep { color: var(--border); font-size: 13px; }
        footer .brand { color: var(--text-dim); }
        footer .brand em { font-style: normal; color: var(--accent); }

        footer a {
            font-family: 'DM Mono', monospace;
            font-size: 11px;
            color: var(--accent);
            text-decoration: none;
            letter-spacing: 0.5px;
            transition: opacity 0.2s;
        }

        footer a:hover { opacity: 0.7; }
        footer .og { color: var(--text-dim); }

        .main { padding-bottom: 80px; }

        @media (max-width: 640px) {
            .hero-title { font-size: 32px; }
            .metrics { grid-template-columns: repeat(2, 1fr); }
            nav { padding: 16px 20px; }
            .main { padding: 36px 16px; }
            .h-item { grid-template-columns: 50px 1fr 70px; }
            .h-reasoning, .h-time { display: none; }
            .watchlist-grid { grid-template-columns: 1fr 1fr; }
        }
    </style>
</head>
<body>
    <nav>
        <div class="logo">sentino<em>.</em></div>
        <div class="nav-right">
            <div class="fg-badge" id="fgBadge" title="Crypto Fear & Greed Index">--</div>
            <div class="nav-tag"><div class="nav-dot"></div> Verified</div>
        </div>
    </nav>

    <div class="main">
        <div class="hero-label">Verifiable AI Sentiment</div>
        <h1 class="hero-title">Know the signal.<br><strong>Verify the source.</strong></h1>
        <p class="hero-sub">Crypto sentiment analysis powered by OpenGradient. Every signal is backed by cryptographic proof.</p>

        <div class="input-group">
            <input type="text" id="tokenInput" placeholder="enter token..." onkeypress="if(event.key==='Enter')analyze()">
            <button id="analyzeBtn" onclick="analyze()">Analyze</button>
        </div>

        <div class="picks">
            <span class="pick" onclick="q('bitcoin')">BTC</span>
            <span class="pick" onclick="q('ethereum')">ETH</span>
            <span class="pick" onclick="q('solana')">SOL</span>
            <span class="pick" onclick="q('dogecoin')">DOGE</span>
            <span class="pick" onclick="q('cardano')">ADA</span>
            <span class="pick" onclick="q('ripple')">XRP</span>
            <span class="pick" onclick="q('avalanche-2')">AVAX</span>
            <span class="pick" onclick="q('chainlink')">LINK</span>
            <span class="pick pick-watchlist" onclick="runWatchlist()">SCAN ALL</span>
        </div>

        <div class="loading" id="loading">
            <div class="loading-bar"></div>
            <div class="loading-text" id="loadingText">Running verifiable inference...</div>
        </div>

        <div class="result" id="result">
            <div class="result-header">
                <div>
                    <div class="result-symbol" id="rSymbol"></div>
                    <div class="result-price" id="rPrice"></div>
                </div>
                <div class="signal-tag" id="rSignal"></div>
            </div>

            <div class="chart-wrap">
                <div class="chart-label">7-Day Price</div>
                <canvas id="priceChart"></canvas>
            </div>

            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">24h</div>
                    <div class="metric-val" id="r24h"></div>
                </div>
                <div class="metric">
                    <div class="metric-label">7d</div>
                    <div class="metric-val" id="r7d"></div>
                </div>
                <div class="metric">
                    <div class="metric-label">Confidence</div>
                    <div class="metric-val" id="rConf"></div>
                </div>
                <div class="metric">
                    <div class="metric-label">Risk</div>
                    <div class="metric-val" id="rRisk"></div>
                </div>
            </div>

            <div class="reasoning" id="rReason"></div>
            <div class="verification" id="rVerify">
                <div class="v-dot"></div><span></span>
            </div>
        </div>

        <!-- Watchlist results -->
        <div id="watchlistSection" style="display:none">
            <div class="section-label">Watchlist</div>
            <div class="watchlist-grid" id="watchlistGrid"></div>
        </div>

        <!-- History -->
        <div id="historySection" style="display:none">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:48px;margin-bottom:16px;">
                <div class="section-label" style="margin:0">Signal History</div>
                <button onclick="clearHistory()" style="font-family:'DM Mono',monospace;font-size:10px;color:var(--red);background:var(--red-dim);border:1px solid var(--red);padding:5px 12px;border-radius:3px;cursor:pointer;letter-spacing:1px;text-transform:uppercase;transition:opacity 0.2s;" onmouseover="this.style.opacity='0.7'" onmouseout="this.style.opacity='1'">Clear</button>
            </div>
            <div id="historyList"></div>
        </div>
    </div>

    <footer>
        <span class="brand">sentino<em>.</em></span>
        <span class="sep">&middot;</span>
        <span>verifiable ai</span>
        <span class="sep">&middot;</span>
        <span>built by</span>
        <a href="https://x.com/NamedFarouk" target="_blank">@NamedFarouk</a>
        <span class="sep">&middot;</span>
        <span class="og">powered by opengradient</span>
    </footer>

    <script>
        let chartInstance = null;

        // Load Fear & Greed on page load
        async function loadFearGreed() {
            try {
                const res = await fetch('/fear-greed');
                const data = await res.json();
                if (data && data.value !== undefined) {
                    const badge = document.getElementById('fgBadge');
                    const v = data.value;
                    badge.textContent = 'F&G: ' + v + ' ' + data.label;
                    badge.className = 'fg-badge ' + (
                        v <= 20 ? 'fg-extreme-fear' :
                        v <= 40 ? 'fg-fear' :
                        v <= 60 ? 'fg-neutral' :
                        v <= 80 ? 'fg-greed' : 'fg-extreme-greed'
                    );
                }
            } catch(e) { console.log('F&G error:', e); }
        }

        // Load history on page load
        async function loadHistory() {
            try {
                const res = await fetch('/history');
                const data = await res.json();
                if (data.length > 0) renderHistory(data);
            } catch(e) {}
        }

        function q(token) {
            document.getElementById('tokenInput').value = token;
            analyze();
        }

        async function analyze() {
            const token = document.getElementById('tokenInput').value.trim();
            if (!token) return;

            document.getElementById('analyzeBtn').disabled = true;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('loadingText').textContent = 'Analyzing ' + token + '...';
            document.getElementById('result').style.display = 'none';

            try {
                // Fetch analysis + chart in parallel
                const [analysisRes, chartRes] = await Promise.all([
                    fetch('/analyze', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({token})
                    }),
                    fetch('/chart/' + encodeURIComponent(token))
                ]);

                const data = await analysisRes.json();
                const chartData = await chartRes.json();

                if (data.error) {
                    alert('Token not found. Try the full name (e.g. bitcoin)');
                    return;
                }

                const p = data.price_data;
                const s = data.signal;

                document.getElementById('rSymbol').textContent = p.symbol;
                document.getElementById('rPrice').textContent = '$' + p.price_usd.toLocaleString();

                const badge = document.getElementById('rSignal');
                badge.textContent = s.signal;
                badge.className = 'signal-tag signal-' + s.signal;

                const el24 = document.getElementById('r24h');
                el24.textContent = p.change_24h_pct + '%';
                el24.className = 'metric-val ' + (p.change_24h_pct >= 0 ? 'pos' : 'neg');

                const el7d = document.getElementById('r7d');
                el7d.textContent = p.change_7d_pct + '%';
                el7d.className = 'metric-val ' + (p.change_7d_pct >= 0 ? 'pos' : 'neg');

                document.getElementById('rConf').textContent = s.confidence + '%';
                document.getElementById('rRisk').textContent = s.risk_level;
                document.getElementById('rReason').textContent = s.reasoning;
                document.getElementById('rVerify').querySelector('span').textContent =
                    'Verified on OpenGradient \\u00b7 ' + data.verification.model + ' \\u00b7 ' + data.verification.tx_hash;

                // Draw chart
                drawChart(chartData, s.signal);

                document.getElementById('result').style.display = 'block';

                // Reload history
                loadHistory();

            } catch(e) {
                alert('Error: ' + e.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('analyzeBtn').disabled = false;
            }
        }

        function drawChart(data, signal) {
            const canvas = document.getElementById('priceChart');
            if (chartInstance) chartInstance.destroy();

            const color = signal === 'BULLISH' ? '#00e676' : signal === 'BEARISH' ? '#ff4d4d' : '#ffd740';

            const labels = data.map(d => {
                const date = new Date(d.time);
                return date.toLocaleDateString('en-US', {month:'short', day:'numeric'});
            });
            const prices = data.map(d => d.price);

            chartInstance = new Chart(canvas, {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        data: prices,
                        borderColor: color,
                        backgroundColor: color + '15',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0,
                        borderWidth: 2,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: {
                            grid: { color: '#1e1e2a' },
                            ticks: { color: '#3d3d4d', font: { family: 'DM Mono', size: 10 }, maxTicksLimit: 7 }
                        },
                        y: {
                            grid: { color: '#1e1e2a' },
                            ticks: {
                                color: '#3d3d4d',
                                font: { family: 'DM Mono', size: 10 },
                                callback: v => '$' + v.toLocaleString()
                            }
                        }
                    },
                    interaction: { intersect: false, mode: 'index' },
                }
            });
        }

        async function runWatchlist() {
            const tokens = ['bitcoin', 'ethereum', 'solana', 'dogecoin', 'cardano', 'ripple'];
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';

            const grid = document.getElementById('watchlistGrid');
            grid.innerHTML = '';
            document.getElementById('watchlistSection').style.display = 'block';

            for (let i = 0; i < tokens.length; i++) {
                document.getElementById('loadingText').textContent =
                    'Analyzing ' + tokens[i] + ' (' + (i+1) + '/' + tokens.length + ')...';

                try {
                    const res = await fetch('/analyze', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({token: tokens[i]})
                    });
                    const data = await res.json();
                    if (!data.error) {
                        const p = data.price_data;
                        const s = data.signal;
                        grid.innerHTML += `
                            <div class="wl-card" onclick="q('${p.token}')">
                                <div class="wl-top">
                                    <span class="wl-symbol">${p.symbol}</span>
                                    <span class="wl-signal signal-${s.signal}">${s.signal}</span>
                                </div>
                                <div class="wl-price">$${p.price_usd.toLocaleString()}</div>
                                <div class="wl-change ${p.change_24h_pct >= 0 ? 'pos' : 'neg'}">${p.change_24h_pct}%</div>
                            </div>`;
                    }
                } catch(e) { console.log('Error:', e); }
            }

            document.getElementById('loading').style.display = 'none';
            loadHistory();
        }

        function renderHistory(data) {
            if (!data || data.length === 0) return;
            document.getElementById('historySection').style.display = 'block';
            document.getElementById('historyList').innerHTML = data.slice(0, 15).map(h => {
                const time = new Date(h.timestamp).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
                const date = new Date(h.timestamp).toLocaleDateString([], {month:'short', day:'numeric'});
                return `<div class="h-item">
                    <span class="h-symbol">${h.symbol}</span>
                    <span class="h-reasoning">${h.reasoning || ''}</span>
                    <span class="h-signal signal-${h.signal}">${h.signal}</span>
                    <span class="h-price">$${h.price ? h.price.toLocaleString() : '--'}</span>
                    <span class="h-time">${time}</span>
                </div>`;
            }).join('');
        }

        // Init
        loadFearGreed();
        loadHistory();

        async function clearHistory() {
            if (!confirm('Clear all signal history?')) return;
            await fetch('/history', {method: 'DELETE'});
            document.getElementById('historySection').style.display = 'none';
            document.getElementById('historyList').innerHTML = '';
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
    try:
        data = request.get_json()
        token = data.get("token", "bitcoin")
        result = analyze_token(client, token)

        # Save to history if successful
        if "error" not in result:
            save_to_history(result)

        return jsonify(result)
    except Exception as e:
        print(f"Analysis error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/chart/<token>")
def api_chart(token):
    try:
        data = get_chart_data(token, days=7)
        return jsonify(data)
    except Exception as e:
        print(f"Chart error: {e}")
        return jsonify([])


@app.route("/fear-greed")
def api_fear_greed():
    data = get_fear_greed()
    return jsonify(data or {})


@app.route("/history")
def api_history():
    return jsonify(load_history())


@app.route("/history", methods=["DELETE"])
def api_clear_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)
    return jsonify({"ok": True})


# Initialize client for both gunicorn and direct run
client = init_client()

if __name__ == "__main__":
    print("\n  Sentino Dashboard: http://localhost:8080")
    print("  Open this link in your browser!\n")
    app.run(debug=False, port=8080, host="0.0.0.0")
