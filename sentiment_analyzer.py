import json
from price_fetcher import get_crypto_data, get_fear_greed
from og_client import init_client, run_verifiable_analysis

SYSTEM_PROMPT = """You are a crypto market analyst. Given price data and market sentiment,
provide a structured sentiment analysis. Be concise and data-driven.

Always respond in this exact JSON format:
{
  "signal": "BULLISH" or "BEARISH" or "NEUTRAL",
  "confidence": 0-100,
  "reasoning": "Brief 1-2 sentence explanation",
  "key_factors": ["factor1", "factor2"],
  "risk_level": "LOW" or "MEDIUM" or "HIGH"
}

Base your analysis on price momentum, volume patterns, market cap context,
and the Fear & Greed Index if provided. Do not provide financial advice."""


def analyze_token(client, token_id="bitcoin"):
    print(f"Fetching price data for {token_id}...")
    price_data = get_crypto_data(token_id)

    if not price_data:
        return {"error": f"Could not fetch data for {token_id}"}

    # Get Fear & Greed Index
    fear_greed = get_fear_greed()

    fg_text = ""
    if fear_greed:
        fg_text = f"\nFear & Greed Index: {fear_greed['value']}/100 ({fear_greed['label']})"

    prompt = f"""Analyze this crypto data and provide your sentiment signal:

Token: {price_data['symbol']}
Current Price: ${price_data['price_usd']:,.2f}
24h Change: {price_data['change_24h_pct']}%
7d Change: {price_data['change_7d_pct']}%
Market Cap: ${price_data['market_cap']:,.0f}
24h Volume: ${price_data['volume_24h']:,.0f}{fg_text}

Respond with JSON only."""

    print("Running verifiable sentiment analysis...")
    tx_hash, response = run_verifiable_analysis(client, prompt, SYSTEM_PROMPT)

    try:
        clean = response.strip().strip("`").strip()
        if clean.startswith("json"):
            clean = clean[4:].strip()
        signal = json.loads(clean)
    except json.JSONDecodeError:
        signal = {"signal": "PARSE_ERROR", "raw_response": response}

    result = {
        "price_data": price_data,
        "signal": signal,
        "verification": {
            "tx_hash": tx_hash,
            "model": "openai/gpt-4.1",
            "infrastructure": "OpenGradient Verifiable Inference"
        }
    }

    if fear_greed:
        result["fear_greed"] = fear_greed

    return result


if __name__ == "__main__":
    client = init_client()
    result = analyze_token(client, "bitcoin")
    print(json.dumps(result, indent=2))
