import opengradient as og
from dotenv import load_dotenv
import os

load_dotenv()


def init_client():
    private_key = os.getenv("OG_PRIVATE_KEY")

    if not private_key:
        raise ValueError("Missing OG_PRIVATE_KEY in .env file")

    client = og.Client(private_key=private_key)
    print("Senti-Bot connected to OpenGradient!")
    return client


def run_verifiable_analysis(client, prompt, system_prompt=None):
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    result = client.llm.chat(
        model="openai/gpt-4.1",
        messages=messages,
        max_tokens=500,
        temperature=0.3
    )

    tx_hash = result.transaction_hash
    response_text = result.chat_output.get("content", "")

    return tx_hash, response_text


if __name__ == "__main__":
    client = init_client()
    tx_hash, response = run_verifiable_analysis(
        client,
        "Say hello and confirm you are running on OpenGradient."
    )
    print(f"Transaction Hash: {tx_hash}")
    print(f"Response: {response}")
