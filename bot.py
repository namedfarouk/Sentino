import json
import time
from datetime import datetime
from og_client import init_client
from sentiment_analyzer import analyze_token


def analyze_single(client, token_id):
    print(f"\nAnalyzing {token_id}...")
    print("-" * 40)

    result = analyze_token(client, token_id)

    if "error" not in result:
        signal = result["signal"]
        price = result["price_data"]

        print(f"  Token:      {price['symbol']}")
        print(f"  Price:      ${price['price_usd']:,.2f}")
        print(f"  24h Change: {price['change_24h_pct']}%")
        print(f"  Signal:     {signal.get('signal', 'N/A')}")
        print(f"  Confidence: {signal.get('confidence', 'N/A')}%")
        print(f"  Risk:       {signal.get('risk_level', 'N/A')}")
        print(f"  Reasoning:  {signal.get('reasoning', 'N/A')}")
    else:
        print(f"  Error: {result['error']}")

    return result


def run_analysis_round(client, tokens):
    print("=" * 60)
    print("  SENTI-BOT ANALYSIS ROUND")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = []
    for token in tokens:
        result = analyze_single(client, token)
        results.append(result)
        time.sleep(2)

    filename = f"signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {filename}")

    return results


if __name__ == "__main__":
    client = init_client()

    print("\nWelcome to Senti-Bot!")
    print("Type a token name (bitcoin, ethereum, solana, cardano, etc.)")
    print("Type 'all' for BTC + ETH + SOL")
    print("Type 'quit' to exit\n")

    while True:
        user_input = input("Senti-Bot > ").strip().lower()

        if user_input == "quit":
            print("Senti-Bot signing off!")
            break
        elif user_input == "all":
            run_analysis_round(client, ["bitcoin", "ethereum", "solana"])
        elif user_input:
            analyze_single(client, user_input)
        else:
            print("Type a token name or 'quit'")
