import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from og_client import init_client, run_verifiable_analysis
from sentiment_analyzer import analyze_token

load_dotenv()

client = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Senti-Bot!\n\n"
        "Send me any crypto token and I'll analyze it.\n\n"
        "Examples: bitcoin, eth, sol, ada, doge\n\n"
        "Powered by OpenGradient Verifiable AI"
    )


async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip().lower()
    await update.message.reply_text(f"Analyzing {token}... this may take a moment.")

    try:
        result = analyze_token(client, token)

        if "error" in result:
            await update.message.reply_text(f"Could not find '{token}'. Try the full name (e.g. 'bitcoin' not 'btc')... or check spelling.")
            return

        signal = result["signal"]
        price = result["price_data"]
        verification = result["verification"]

        msg = (
            f"**SENTI-BOT SIGNAL**\n\n"
            f"Token: {price['symbol']}\n"
            f"Price: ${price['price_usd']:,.2f}\n"
            f"24h Change: {price['change_24h_pct']}%\n"
            f"7d Change: {price['change_7d_pct']}%\n\n"
            f"Signal: {signal.get('signal', 'N/A')}\n"
            f"Confidence: {signal.get('confidence', 'N/A')}%\n"
            f"Risk: {signal.get('risk_level', 'N/A')}\n\n"
            f"Reasoning: {signal.get('reasoning', 'N/A')}\n\n"
            f"Verified on OpenGradient"
        )

        await update.message.reply_text(msg)

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


def main():
    global client
    client = init_client()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN in .env")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze))

    print("Senti-Bot Telegram is live! Send a message to your bot.")
    app.run_polling()


if __name__ == "__main__":
    main()
