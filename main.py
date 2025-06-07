import os 
import json 
from telegram import Update 
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters 
from web3 import Web3 
from web3.middleware import geth_poa_middleware

--- Configuration --- 

BOT_TOKEN = os.getenv("BOT_TOKEN") PRIVATE_KEY = os.getenv("PRIVATE_KEY") INFURA_URL = "https://bsc-dataseed.binance.org/" CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181" CHANNEL_USERNAME = "@benjaminfranklintoken" SIGNUP_BONUS = 500 REFERRAL_BONUS = 100

--- Web3 Setup --- 

w3 = Web3(Web3.HTTPProvider(INFURA_URL)) w3.middleware_onion.inject(geth_poa_middleware, layer=0) contract_abi = json.loads('[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"}, {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"}, {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"}, {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}, {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}, {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}, {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}, {"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]') contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=contract_abi) OWNER_ADDRESS = w3.eth.account.from_key(PRIVATE_KEY).address

--- User Data --- 

users = {}

--- Handlers --- 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id referrer_id = None if context.args: referrer_id = int(context.args[0]) if context.args[0].isdigit() else None

if user_id not in users: users[user_id] = { "wallet": None, "balance": 0, "invites": [], "rewarded": False } users[user_id]["balance"] += SIGNUP_BONUS if referrer_id and referrer_id in users: users[referrer_id]["balance"] += REFERRAL_BONUS users[referrer_id]["invites"].append(user_id) referral_link = f"https://t.me/{context.bot.username}?start={user_id}" await update.message.reply_text( f"Welcome! You received {SIGNUP_BONUS} tokens as a signup bonus.\n" f"Invite your friends to get {REFERRAL_BONUS} tokens each.\n\n" f"Your referral link:\n{referral_link}" ) 

async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id text = update.message.text if text.startswith("0x") and len(text) == 42: users[user_id]["wallet"] = text await update.message.reply_text("Wallet address saved.") else: await update.message.reply_text("Please send a valid BNB wallet address.")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id bal = users.get(user_id, {}).get("balance", 0) await update.message.reply_text(f"Your token balance: {bal}")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id user = users.get(user_id) if not user: await update.message.reply_text("User not found.") return if not user["wallet"]: await update.message.reply_text("Wallet not set.") return if user["balance"] <= 0: await update.message.reply_text("No tokens to withdraw.") return

to_address = Web3.to_checksum_address(user["wallet"]) amount = user["balance"] * (10 ** contract.functions.decimals().call()) nonce = w3.eth.get_transaction_count(OWNER_ADDRESS) gas_price = w3.eth.gas_price tx = { 'nonce': nonce, 'to': CONTRACT_ADDRESS, 'value': 0, 'gas': 200000, 'gasPrice': gas_price, 'data': contract.encodeABI(fn_name='transfer', args=[to_address, amount]), } signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY) tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction) users[user_id]["balance"] = 0 await update.message.reply_text(f"Withdrawal successful. TX Hash: {tx_hash.hex()}") --- App Initialization --- 

app = ApplicationBuilder().token(BOT_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("balance", balance)) app.add_handler(CommandHandler("withdraw", withdraw)) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet))

app.run_polling()

