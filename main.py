import os import json from telegram import Update from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes from web3 import Web3 from web3.middleware import geth_poa_middleware

BOT_TOKEN = os.getenv("BOT_TOKEN") PRIVATE_KEY = os.getenv("PRIVATE_KEY") TOKEN_CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181" TOKEN_DECIMALS = 18

w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/")) w3.middleware_onion.inject(geth_poa_middleware, layer=0)

SENDER_ADDRESS = Web3.to_checksum_address(w3.eth.account.from_key(PRIVATE_KEY).address)

ERC20_ABI = [ { "constant": False, "inputs": [ {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"} ], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function" } ]

if os.path.exists("users.json"): with open("users.json", "r") as f: users = json.load(f) else: users = {}

def save_users(): with open("users.json", "w") as f: json.dump(users, f)

token_contract = w3.eth.contract(address=Web3.to_checksum_address(TOKEN_CONTRACT_ADDRESS), abi=ERC20_ABI)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): user = update.effective_user user_id = str(user.id)

if user_id not in users: users[user_id] = { "balance": 500, "wallet": "", "referrals": [], "invited_by": None } if context.args: ref_id = context.args[0] if ref_id != user_id and ref_id in users and user_id not in users[ref_id]["referrals"]: users[ref_id]["balance"] += 100 users[ref_id]["referrals"].append(user_id) users[user_id]["invited_by"] = ref_id save_users() await update.message.reply_text( "Welcome! You received 500 tokens as a signup bonus.\n" "Invite your friends to get 100 tokens each.\n" "Use /balance to check your tokens.\n" "Use /wallet <address> to register your wallet.\n" "Use /withdraw to send tokens." ) else: await update.message.reply_text("You have already started.") 

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) bal = users.get(user_id, {}).get("balance", 0) await update.message.reply_text(f"Your balance: {bal} tokens")

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if not context.args: await update.message.reply_text("Usage: /wallet <your_address>") return address = context.args[0] if not Web3.is_address(address): await update.message.reply_text("Invalid address") return users[user_id]["wallet"] = Web3.to_checksum_address(address) save_users() await update.message.reply_text("Wallet address registered successfully.")

async def link(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) await update.message.reply_text( f"Your referral link: https://t.me/{context.bot.username}?start={user_id}" )

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if user_id not in users: await update.message.reply_text("Please start first with /start") return wallet = users[user_id].get("wallet") balance = users[user_id].get("balance", 0) if not wallet: await update.message.reply_text("You must set your wallet address first using /wallet") return if balance <= 0: await update.message.reply_text("You have no tokens to withdraw.") return

amount_wei = int(balance * (10 ** TOKEN_DECIMALS)) nonce = w3.eth.get_transaction_count(SENDER_ADDRESS) try: txn = token_contract.functions.transfer(wallet, amount_wei).build_transaction({ "chainId": 56, "gas": 100000, "gasPrice": w3.to_wei('5', 'gwei'), "nonce": nonce }) signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY) tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction) users[user_id]["balance"] = 0 save_users() await update.message.reply_text(f"✅ Withdrawal successful!\nTx: https://bscscan.com/tx/{tx_hash.hex()}") except Exception as e: await update.message.reply_text(f"❌ Error: {str(e)}") 

def main(): app = ApplicationBuilder().token(BOT_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("balance", balance)) app.add_handler(CommandHandler("wallet", wallet)) app.add_handler(CommandHandler("link", link)) app.add_handler(CommandHandler("withdraw", withdraw)) app.run_polling()

if name == 'main': main()

