import os 
import json 
from telegram import Update 
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters 
from web3 import Web3 
from web3.middleware import geth_poa_middleware

Configuration 

BOT_TOKEN = os.getenv("BOT_TOKEN") PRIVATE_KEY = os.getenv("PRIVATE_KEY") INFURA_URL = "https://bsc-dataseed.binance.org/" CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181" CHANNEL_USERNAME = "@benjaminfranklintoken" SIGNUP_BONUS = 500 REFERRAL_BONUS = 100

Initialize Web3 

w3 = Web3(Web3.HTTPProvider(INFURA_URL)) w3.middleware_onion.inject(geth_poa_middleware, layer=0) contract_abi = [...] # PLACE YOUR FULL ABI HERE contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=contract_abi) OWNER_ADDRESS = w3.eth.account.from_key(PRIVATE_KEY).address

In-memory database 

users = {}

Utils 

def is_valid_wallet(address): return w3.is_address(address) and address.startswith("0x")

def send_tokens(to_address, amount): to = Web3.to_checksum_address(to_address) nonce = w3.eth.get_transaction_count(OWNER_ADDRESS) tx = contract.functions.transfer(to, amount).build_transaction({ 'from': OWNER_ADDRESS, 'nonce': nonce, 'gas': 200000, 'gasPrice': w3.to_wei('5', 'gwei') }) signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY) tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction) return w3.to_hex(tx_hash)

Handlers 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id if not await is_user_in_channel(update, context): await update.message.reply_text("Please join our channel first: https://t.me/benjaminfranklintoken") return

if user_id in users: await update.message.reply_text("You already signed up! Use /balance to check your tokens.") return ref_id = None if context.args: try: ref_id = int(context.args[0]) except: pass users[user_id] = {"tokens": SIGNUP_BONUS, "wallet": None, "ref": ref_id} tx = "Wallet not set" await update.message.reply_text( f"Welcome! You received {SIGNUP_BONUS} tokens as a signup bonus.\nTransaction: {tx}\n\nYour referral link:\nhttps://t.me/{context.bot.username}?start={user_id}" ) if ref_id and ref_id in users: users[ref_id]["tokens"] += REFERRAL_BONUS await context.bot.send_message(ref_id, f"You received {REFERRAL_BONUS} tokens for inviting a user!") 

async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id address = update.message.text.strip() if not is_valid_wallet(address): await update.message.reply_text("Invalid wallet address. Please send a valid BNB wallet.") return

if user_id not in users: await update.message.reply_text("Please use /start first.") return if users[user_id]["wallet"]: await update.message.reply_text("Wallet already set.") return tx_hash = send_tokens(address, SIGNUP_BONUS * (10 ** 18)) users[user_id]["wallet"] = address await update.message.reply_text(f"Tokens sent to your wallet!\nTransaction: https://bscscan.com/tx/{tx_hash}") 

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id tokens = users.get(user_id, {}).get("tokens", 0) await update.message.reply_text(f"Your balance: {tokens} tokens")

async def is_user_in_channel(update: Update, context: ContextTypes.DEFAULT_TYPE): try: member = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id) return member.status in ["member", "creator", "administrator"] except: return False

Main 

app = ApplicationBuilder().token(BOT_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("balance", balance)) app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_wallet))

if name == "main": app.run_polling()

