import requests
import time
from datetime import datetime

TICKER_MAP = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "ada": "cardano",
    "dot": "polkadot",
    "avax": "avalanche-2",
    "matic": "polygon-ecosystem-token",
    "link": "chainlink",
    "doge": "dogecoin",
    "shib": "shiba-inu",
    "xrp": "ripple",
    "bnb": "binancecoin",
    "atom": "cosmos",
    "near": "near",
    "sui": "sui",
    "apt": "aptos",
    "arb": "arbitrum",
    "op": "optimism",
    "sei": "sei-network",
    "inj": "injective-protocol",
    "bera": "berachain-bera",
    "pepe": "pepe",
    "wif": "dogwifcoin",
    "bonk": "bonk",
    "jup": "jupiter-exchange-solana",
    "ondo": "ondo-finance",
    "render": "render-token",
    "fet": "fetch-ai",
    "vet": "vechain",
    "algo": "algorand",
    "ftm": "fantom",
    "fil": "filecoin",
    "grt": "the-graph",
    "allo": "allora",
    "zama": "zama",
}


def resolve_token(user_input):
    cleaned = user_input.strip().lower()
    if cleaned in TICKER_MAP:
        return TICKER_MAP[cleaned]
    return cleaned


def search_token(query):
    try:
        time.sleep(1.5)
        url = "https://api.coingecko.com/api/v3/search"
        response = requests.get(url, params={"query": query}, timeout=10)
        response.raise_for_status()
        data = response.json()

        coins = data.get("coins", [])
        if coins:
            return coins[0]["id"]
        return None
    except requests.RequestException:
        return None


def get_crypto_data(token_id="bitcoin"):
    resolved = resolve_token(token_id)

    time.sleep(1.5)

    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": resolved,
        "order": "market_cap_desc",
        "sparkline": "false",
        "price_change_percentage": "24h,7d"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            print(f"  '{resolved}' not found directly, searching...")
            found = search_token(token_id)
            if found:
                print(f"  Found: {found}")
                return get_crypto_data(found)
            print(f"  Could not find '{token_id}' on CoinGecko")
            return None

        coin = data[0]
        return {
            "token": coin["id"],
            "symbol": coin["symbol"].upper(),
            "price_usd": coin["current_price"],
            "change_24h_pct": round(coin.get("price_change_percentage_24h", 0), 2),
            "change_7d_pct": round(coin.get("price_change_percentage_7d_in_currency", 0), 2),
            "market_cap": coin["market_cap"],
            "volume_24h": coin["total_volume"],
            "timestamp": datetime.now().isoformat()
        }

    except requests.RequestException as e:
        print(f"  Error fetching data: {e}")
        return None


if __name__ == "__main__":
    data = get_crypto_data("btc")
    if data:
        for key, value in data.items():
            print(f"  {key}: {value}")
