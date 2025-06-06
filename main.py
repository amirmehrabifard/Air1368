import os 
import json from telegram 
import Update from telegram.ext 
import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters from web3 
import Web3 from web3.middleware 
import geth_poa_middleware

BOT_TOKEN = os.getenv("BOT_TOKEN") PRIVATE_KEY = os.getenv("PRIVATE_KEY") CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181" CHANNEL_USERNAME = "@benjaminfranklintoken" RPC_URL = "https://bsc-dataseed.binance.org/"

w3 = Web3(Web3.HTTPProvider(RPC_URL)) w3.middleware_onion.inject(geth_poa_middleware, layer=0) WALLET_ADDRESS = w3.eth.account.from_key(PRIVATE_KEY).address

with open("users.json", "r") as f: users = json.load(f)

ABI = [...] # Paste the ABI you provided earlier here contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) joined = await has_joined_channel(update, context) if not joined: await update.message.reply_text(f"Please join the channel {CHANNEL_USERNAME} before using the bot.") return

if user_id not in users: users[user_id] = { "wallet": None, "referred_by": None, "referrals": [], "balance": 500 } if context.args: referrer_id = context.args[0] if referrer_id != user_id and referrer_id in users: users[user_id]["referred_by"] = referrer_id users[referrer_id]["referrals"].append(user_id) users[referrer_id]["balance"] += 100 await update.message.reply_text( "Welcome! You received 500 tokens as a signup bonus.\n" "Invite your friends to get 100 tokens each.\n" "Use /balance to check your tokens.\n" "Use /wallet <your_wallet_address> to set your wallet.\n" "Use /withdraw to send tokens.\n" f"\nYour referral link:\nhttps://t.me/{context.bot.username}?start={user_id}" ) else: await update.message.reply_text("You have already joined. Use /balance to check your tokens.") save_users() 

async def has_joined_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool: try: member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=update.effective_user.id) return member.status in ["member", "administrator", "creator"] except: return False

async def set_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if len(context.args) != 1: await update.message.reply_text("Usage: /wallet <your_wallet_address>") return

wallet = context.args[0] if not Web3.is_address(wallet): await update.message.reply_text("Invalid wallet address.") return users[user_id]["wallet"] = Web3.to_checksum_address(wallet) save_users() await update.message.reply_text("Your wallet address has been saved.") 

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if user_id not in users: await update.message.reply_text("Please use /start first.") return

await update.message.reply_text(f"Your current token balance: {users[user_id]['balance']}") 

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) user = users.get(user_id)

if not user or not user.get("wallet"): await update.message.reply_text("Wallet not set. Use /wallet <your_wallet_address> first.") return if user["balance"] < 100: await update.message.reply_text("You need at least 100 tokens to withdraw.") return amount = user["balance"] to_address = user["wallet"] success = send_tokens(user_id, amount, to_address) if success: users[user_id]["balance"] = 0 save_users() await update.message.reply_text(f"{amount} tokens were sent to your wallet.\nTx hash: {success}") else: await update.message.reply_text("Something went wrong during the transaction.") 

def send_tokens(user_id, amount, to_address): try: decimals = contract.functions.decimals().call() token_amount = int(amount * (10 ** decimals)) nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)

tx = contract.functions.transfer(to_address, token_amount).build_transaction({ "from": WALLET_ADDRESS, "nonce": nonce, "gas": 200000, "gasPrice": w3.to_wei("5", "gwei") }) signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY) tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction) return w3.to_hex(tx_hash) except Exception as e: print(f"Error in send_tokens: {e}") return False 

def save_users(): with open("users.json", "w") as f: json.dump(users, f, indent=4)

if name == "main": app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("wallet", set_wallet)) app.add_handler(CommandHandler("balance", balance)) app.add_handler(CommandHandler("withdraw", withdraw)) print("Bot is running...") app.run_polling() 
