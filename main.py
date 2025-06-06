import os 
import json from telegram 
import Update from telegram.ext 
import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters from web3 
import Web3 from web3.middleware 
import geth_poa_middleware

--- Config --- 

BOT_TOKEN = os.getenv("BOT_TOKEN") PRIVATE_KEY = os.getenv("PRIVATE_KEY")

CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181" CHANNEL_USERNAME = "@benjaminfranklintoken"

--- ABI --- 

ABI = [ {"inputs":[],"stateMutability":"nonpayable","type":"constructor"}, {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"owner","type":"address"},{"indexed":True,"internalType":"address","name":"spender","type":"address"},{"indexed":False,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"}, {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"from","type":"address"},{"indexed":True,"internalType":"address","name":"to","type":"address"},{"indexed":False,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"}, {"inputs":[],"name":"airdropPortion","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}, {"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}, {"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}, {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}, {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}, {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}, {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}, {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}, {"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}, {"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"} ]

--- Blockchain Setup --- 

w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/")) w3.middleware_onion.inject(geth_poa_middleware, layer=0) contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI) OWNER_ADDRESS = w3.eth.account.from_key(PRIVATE_KEY).address

--- Users DB --- 

USERS_FILE = "users.json" def load_users(): if os.path.exists(USERS_FILE): with open(USERS_FILE, "r") as f: return json.load(f) return {}

def save_users(data): with open(USERS_FILE, "w") as f: json.dump(data, f)

users = load_users()

--- Handlers --- 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) referred_by = context.args[0] if context.args else None

if user_id not in users: users[user_id] = {"wallet": None, "tokens": 500, "ref": referred_by, "invites": []} save_users(users) await update.message.reply_text("Welcome! You received 500 tokens as a signup bonus.\nInvite your friends to get 100 tokens each.\nUse /balance to check your tokens.\nUse /withdraw to send tokens.") await update.message.reply_text(f"Your referral link:\nhttps://t.me/{context.bot.username}?start={user_id}") if referred_by and referred_by in users: if user_id not in users[referred_by]["invites"]: users[referred_by]["tokens"] += 100 users[referred_by]["invites"].append(user_id) save_users(users) else: await update.message.reply_text("You have already started the bot.") 

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if user_id in users: await update.message.reply_text(f"Your token balance: {users[user_id]['tokens']} tokens") else: await update.message.reply_text("Please use /start first.")

async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) text = update.message.text.strip()

if user_id not in users: await update.message.reply_text("Please use /start first.") return if not text.startswith("0x") or len(text) != 42: await update.message.reply_text("Invalid wallet address. Please send a valid BNB wallet address starting with 0x.") return users[user_id]["wallet"] = text save_users(users) await update.message.reply_text("Wallet saved successfully!") 

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if user_id not in users: await update.message.reply_text("Please use /start first.") return

wallet = users[user_id].get("wallet") tokens = users[user_id].get("tokens", 0) if not wallet: await update.message.reply_text("Wallet not set. Please send your wallet address.") return if tokens <= 0: await update.message.reply_text("You have no tokens to withdraw.") return decimals = contract.functions.decimals().call() amount = tokens * (10 ** decimals) nonce = w3.eth.get_transaction_count(OWNER_ADDRESS) tx = contract.functions.transfer(wallet, amount).build_transaction({ 'from': OWNER_ADDRESS, 'nonce': nonce, 'gas': 200000, 'gasPrice': w3.to_wei('5', 'gwei') }) signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY) tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction) users[user_id]["tokens"] = 0 save_users(users) await update.message.reply_text(f"Tokens sent!\nTransaction hash: {tx_hash.hex()}") --- Run Bot --- 

app = ApplicationBuilder().token(BOT_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("balance", balance)) app.add_handler(CommandHandler("withdraw", withdraw)) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet))

app.run_polling()

