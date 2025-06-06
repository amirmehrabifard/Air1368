import json
import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.helpers import escape_markdown
from web3 import Web3

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

USERS_FILE = "users.json"
CHAIN_RPC = "https://polygon-rpc.com"  # Polygon mainnet RPC

web3 = Web3(Web3.HTTPProvider(CHAIN_RPC))
account = web3.eth.account.from_key(PRIVATE_KEY)

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user_id = str(update.effective_user.id)
    if user_id not in users:
        users[user_id] = {"tokens": 500, "invited": 0}
        save_users(users)

    text = (
        "Welcome! You received 500 tokens as a signup bonus.\n"
        "Invite your friends to get 100 tokens each.\n"
        "Use /balance to check your tokens.\n"
        "Use /withdraw to send tokens."
    )
    await update.message.reply_text(text)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user_id = str(update.effective_user.id)
    tokens = users.get(user_id, {}).get("tokens", 0)
    await update.message.reply_text(f"Your balance: {tokens} tokens.")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user_id = str(update.effective_user.id)
    user_data = users.get(user_id)
    if not user_data or user_data.get("tokens", 0) < 100:
        await update.message.reply_text("You need at least 100 tokens to withdraw.")
        return

    # For simplicity, withdraw fixed 100 tokens
    try:
        nonce = web3.eth.get_transaction_count(account.address)
        tx = {
            "nonce": nonce,
            "to": account.address,  # In real use, should be user wallet address
            "value": web3.to_wei(0, "ether"),
            "gas": 21000,
            "gasPrice": web3.eth.gas_price,
            "data": b"",
        }
        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash_hex = tx_hash.hex()

        user_data["tokens"] -= 100
        save_users(users)

        safe_tx = escape_markdown(tx_hash_hex, version=2)
        await update.message.reply_text(
            f"🎉 Airdrop sent successfully! Transaction hash:\n`{safe_tx}`",
            parse_mode="MarkdownV2",
        )
    except Exception as e:
        logging.error(f"Withdraw error: {e}")
        await update.message.reply_text("An error occurred while processing withdrawal.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "/start - Register and get tokens\n"
        "/balance - Show your token balance\n"
        "/withdraw - Withdraw tokens\n"
    )
    await update.message.reply_text(text)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("help", help_command))

    app.run_polling()

if __name__ == "__main__":
    main()
