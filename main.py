import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from web3 import Web3
from web3.middleware import geth_poa_middleware

TOKEN_REWARD = 500
REFERRAL_REWARD = 100
CONTRACT_ADDRESS = '0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181'
CHANNEL_LINK = 'https://t.me/benjaminfranklintoken'

# BSC node
w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
private_key = os.getenv("PRIVATE_KEY")
sender_address = w3.eth.account.from_key(private_key).address

# ABI
ABI = [  # INSERTED YOUR REAL ABI HERE
  {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
  {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"from","type":"address"},{"indexed":True,"internalType":"address","name":"to","type":"address"},{"indexed":False,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},
  {"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
]

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

# User data
if not os.path.exists("users.json"):
    with open("users.json", "w") as f:
        json.dump({}, f)

with open("users.json") as f:
    users = json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    referred_by = args[0] if args else None

    if user_id in users:
        await update.message.reply_text("You are already registered.\nUse /balance to check your tokens.")
        return

    users[user_id] = {
        "wallet": None,
        "claimed": True,
        "referrer": referred_by if referred_by != user_id else None
    }

    with open("users.json", "w") as f:
        json.dump(users, f)

    await update.message.reply_text(
        f"Welcome! You received {TOKEN_REWARD} tokens as a signup bonus.\n"
        f"Please send your wallet address to receive the tokens.\n"
        f"Referral link: https://t.me/{context.bot.username}?start={user_id}"
    )

async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    wallet = update.message.text.strip()

    if not w3.is_address(wallet):
        await update.message.reply_text("Invalid wallet address.")
        return

    if user_id not in users or users[user_id].get("wallet"):
        await update.message.reply_text("You are already registered or wallet set.")
        return

    users[user_id]["wallet"] = wallet
    with open("users.json", "w") as f:
        json.dump(users, f)

    # Send signup tokens
    await send_tokens(wallet, TOKEN_REWARD)
    await update.message.reply_text(f"✅ Sent {TOKEN_REWARD} tokens to your wallet.")

    # Referral
    referrer = users[user_id].get("referrer")
    if referrer and referrer in users:
        ref_wallet = users[referrer].get("wallet")
        if ref_wallet:
            await send_tokens(ref_wallet, REFERRAL_REWARD)
            await context.bot.send_message(referrer, f"🎉 You received {REFERRAL_REWARD} tokens for a successful referral!")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users or not users[user_id].get("wallet"):
        await update.message.reply_text("You are not registered or wallet not set.")
        return

    wallet = users[user_id]["wallet"]
    balance = contract.functions.balanceOf(Web3.to_checksum_address(wallet)).call()
    decimals = contract.functions.decimals().call()
    human_balance = balance / (10 ** decimals)
    await update.message.reply_text(f"Your token balance: {human_balance}")

async def send_tokens(to_address, amount):
    nonce = w3.eth.get_transaction_count(sender_address)
    decimals = contract.functions.decimals().call()
    tx = contract.functions.transfer(
        Web3.to_checksum_address(to_address),
        int(amount * (10 ** decimals))
    ).build_transaction({
        'chainId': 56,
        'gas': 100000,
        'gasPrice': w3.to_wei('5', 'gwei'),
        'nonce': nonce,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)

app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(MessageHandler(None, handle_wallet))

if __name__ == "__main__":
    app.run_polling()
