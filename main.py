import os import json from telegram import Update from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters from web3 import Web3 from web3.middleware import geth_poa_middleware

--- Configuration --- 

BOT_TOKEN = os.getenv("BOT_TOKEN") PRIVATE_KEY = os.getenv("PRIVATE_KEY") CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181" CHANNEL_USERNAME = "@benjaminfranklintoken"

w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/")) w3.middleware_onion.inject(geth_poa_middleware, layer=0) OWNER_ADDRESS = w3.eth.account.from_key(PRIVATE_KEY).address

--- Load Contract ABI --- 

contract_abi = [...] # REPLACE with full ABI JSON you've given above contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

--- In-memory data storage --- 

user_data = {} referrals = {}

--- Helper Functions --- 

def send_tokens(to_address, amount): nonce = w3.eth.get_transaction_count(OWNER_ADDRESS) tx = contract.functions.transfer(to_address, amount).build_transaction({ 'from': OWNER_ADDRESS, 'gas': 200000, 'gasPrice': w3.to_wei('5', 'gwei'), 'nonce': nonce }) signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY) tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction) return tx_hash.hex()

--- Telegram Bot Handlers --- 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) wallet = user_data.get(user_id, {}).get("wallet") ref_code = context.args[0] if context.args else None

if user_id not in user_data: user_data[user_id] = {"joined": True, "bonus_given": False, "referrer": ref_code} await update.message.reply_text( "Welcome! You received 500 tokens as a signup bonus.\n" "Use /wallet <address> to register your wallet." ) else: await update.message.reply_text("You are already registered.") invite_link = f"https://t.me/{context.bot.username}?start={user_id}" await update.message.reply_text(f"Your referral link:\n{invite_link}") 

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if len(context.args) != 1: return await update.message.reply_text("Usage: /wallet <your_BEP20_address>")

address = context.args[0] if not w3.is_address(address): return await update.message.reply_text("Invalid wallet address.") user_data[user_id]["wallet"] = address if not user_data[user_id].get("bonus_given"): tx_hash = send_tokens(address, 500 * (10 ** 18)) user_data[user_id]["bonus_given"] = True await update.message.reply_text(f"✅ 500 tokens sent!\nTx: {tx_hash}") # Handle referral referrer = user_data[user_id].get("referrer") if referrer and referrer != user_id and referrer in user_data: ref_wallet = user_data[referrer].get("wallet") if ref_wallet: tx2 = send_tokens(ref_wallet, 100 * (10 ** 18)) await context.bot.send_message( chat_id=referrer, text=f"🎉 You received 100 tokens for referring {user_id}!\nTx: {tx2}" ) else: await update.message.reply_text("Wallet updated. Bonus already sent.") 

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) wallet = user_data.get(user_id, {}).get("wallet") if not wallet: return await update.message.reply_text("No wallet found. Use /wallet to register.")

balance = contract.functions.balanceOf(wallet).call() await update.message.reply_text(f"Your token balance: {balance / 1e18:.2f}") --- Main --- 

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("wallet", wallet)) app.add_handler(CommandHandler("balance", balance))

app.run_polling()

