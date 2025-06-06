import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from web3 import Web3
from web3.middleware import geth_poa_middleware

BOT_TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

OWNER_ADDRESS = w3.eth.account.privateKeyToAccount(PRIVATE_KEY).address
CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181"

# ABI واقعی که دادی اینجاست 👇
contract_abi = [
    {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
    {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"owner","type":"address"},{"indexed":True,"internalType":"address","name":"spender","type":"address"},{"indexed":False,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},
    {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"from","type":"address"},{"indexed":True,"internalType":"address","name":"to","type":"address"},{"indexed":False,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},
    {"inputs":[],"name":"airdropPortion","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"developmentPortion","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"publicSalePortion","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"taxPercent","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"teamPortion","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}
]

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=contract_abi)

if os.path.exists("users.json"):
    with open("users.json", "r") as f:
        users = json.load(f)
else:
    users = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        users[user_id] = {
            "invited_by": None,
            "wallet": None,
            "bonus_received": False
        }
        if context.args:
            inviter_id = context.args[0]
            if inviter_id in users:
                users[user_id]["invited_by"] = inviter_id

        save_users()
        await send_tokens(update, 500, "Signup bonus")

        inviter = users[user_id]["invited_by"]
        if inviter:
            await send_tokens_by_id(inviter, 100, "Referral reward")

    await update.message.reply_text(
        "Welcome! You received 500 tokens as a signup bonus.\n"
        "Invite your friends to get 100 tokens each.\n"
        "Use /balance to check your tokens.\n"
        "Use /withdraw to send tokens.\n"
        f"Your referral link:\nhttps://t.me/Bjfairdrop_bot?start={user_id}"
    )

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    if text.startswith("0x") and len(text) == 42:
        users[user_id]["wallet"] = text
        save_users()
        await update.message.reply_text("Wallet address saved.")
    else:
        await update.message.reply_text("Please send a valid BNB wallet address (starting with 0x).")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    wallet = users.get(user_id, {}).get("wallet")
    if not wallet:
        await update.message.reply_text("Wallet not set.")
        return
    balance = contract.functions.balanceOf(wallet).call()
    await update.message.reply_text(f"Your token balance: {balance}")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    wallet = users.get(user_id, {}).get("wallet")
    if not wallet:
        await update.message.reply_text("Wallet not set.")
        return
    await send_tokens(update, 100, "Withdraw")

async def send_tokens(update: Update, amount: int, reason: str):
    user_id = str(update.effective_user.id)
    to_address = users[user_id].get("wallet")
    if not to_address:
        await update.message.reply_text("Please set your wallet address first.")
        return
    try:
        nonce = w3.eth.get_transaction_count(OWNER_ADDRESS)
        tx = contract.functions.transfer(to_address, amount).build_transaction({
            "chainId": 56,
            "gas": 200000,
            "gasPrice": w3.to_wei("5", "gwei"),
            "nonce": nonce
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_link = f"https://bscscan.com/tx/{tx_hash.hex()}"
        await update.message.reply_text(f"{reason} sent successfully!\nTransaction: {tx_link}")
    except Exception as e:
        await update.message.reply_text(f"Transaction failed: {e}")

async def send_tokens_by_id(user_id, amount: int, reason: str):
    class DummyMessage:
        async def reply_text(self, text): pass

    dummy_update = type('obj', (object,), {
        'message': DummyMessage(),
        'effective_user': type('obj', (object,), {'id': int(user_id)})()
    })()

    await send_tokens(dummy_update, amount, reason)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_wallet))
    app.run_polling()
