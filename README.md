# Sentino

AI-powered crypto sentiment analysis bot built on OpenGradient's verifiable inference network.

Every trade signal is backed by on-chain proof — not just promises.

## Features
- Live crypto price data for any token
- AI sentiment analysis (BULLISH / BEARISH / NEUTRAL)
- Verifiable inference via OpenGradient (x402 + TEE)
- Three interfaces: Terminal, Telegram, Web Dashboard

## Setup
1. Clone this repo
2. `python3.12 -m venv venv && source venv/bin/activate`
3. `pip install opengradient requests python-dotenv python-telegram-bot flask`
4. Create `.env` with your keys (see .env.example)
5. Get $OPG tokens from https://faucet.opengradient.ai

## Run
- Terminal: `python bot.py`
- Telegram: `python telegram_bot.py`
- Website: `python website.py` → http://localhost:5000

## Built With
- OpenGradient SDK (verifiable AI inference)
- CoinGecko API (live price data)
- Flask (web dashboard)
- python-telegram-bot (Telegram integration)

## Powered By
OpenGradient — Trustless, Verifiable AI Infrastructure
