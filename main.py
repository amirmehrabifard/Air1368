import os import json from telegram import Update from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes from web3 import Web3 from web3.middleware import geth_poa_middleware

BOT_TOKEN = os.getenv("BOT_TOKEN") PRIVATE_KEY = os.getenv("PRIVATE_KEY") CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181" CHANNEL_USERNAME = "@benjaminfranklintoken"

web3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/")) web3.middleware_onion.inject(geth_poa_middleware, layer=0) account = web3.eth.account.from_key(PRIVATE_KEY) TOKEN_DECIMALS = 18

with open("users.json", "r") as f: users = json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if user_id in users: await update.message.reply_text("You already joined. Use /balance or /link.") return

if not await is_member(update): await update.message.reply_text(f"You must join our channel first: {CHANNEL_USERNAME}") return wallet = context.args[0] if context.args else None if not wallet or not web3.is_address(wallet): await update.message.reply_text("Send your wallet: /start <wallet_address>") return users[user_id] = { "wallet": wallet, "ref": None, "bonus": 500, "invited": [] } if update.message.text and len(update.message.text.split()) > 2: ref_id = update.message.text.split()[2] if ref_id != user_id and ref_id in users and user_id not in users[ref_id]["invited"]: users[ref_id]["bonus"] += 100 users[ref_id]["invited"].append(user_id) users[user_id]["ref"] = ref_id with open("users.json", "w") as f: json.dump(users, f) await update.message.reply_text( "Welcome! You received 500 tokens as a signup bonus.\n" "Invite your friends to get 100 tokens each.\n" "Use /balance to check your tokens.\nUse /withdraw to send tokens." ) 

async def is_member(update): try: member = await update.get_bot().get_chat_member(CHANNEL_USERNAME, update.effective_user.id) return member.status in ["member", "administrator", "creator"] except: return False

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if user_id not in users: await update.message.reply_text("You are not registered. Use /start <wallet_address>") return bonus = users[user_id]["bonus"] await update.message.reply_text(f"Your balance: {bonus} tokens")

async def link(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if user_id not in users: await update.message.reply_text("You are not registered. Use /start <wallet_address>") return await update.message.reply_text(f"Your invite link: https://t.me/{context.bot.username}?start={user_id}")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if user_id not in users: await update.message.reply_text("You are not registered.") return

amount = users[user_id]["bonus"] if amount <= 0: await update.message.reply_text("You have no tokens to withdraw.") return wallet = users[user_id]["wallet"] contract = web3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=[ { "constant": False, "inputs": [ {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"} ], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function" } ]) try: nonce = web3.eth.get_transaction_count(account.address) tx = contract.functions.transfer(wallet, amount * 10**TOKEN_DECIMALS).build_transaction({ 'from': account.address, 'nonce': nonce, 'gas': 100000, 'gasPrice': web3.to_wei('5', 'gwei') }) signed_tx = web3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY) tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction) users[user_id]["bonus"] = 0 with open("users.json", "w") as f: json.dump(users, f) await update.message.reply_text(f"Sent {amount} tokens!\nTx: https://bscscan.com/tx/{web3.to_hex(tx_hash)}") except Exception as e: await update.message.reply_text(f"Error: {e}") 

if name == 'main': app = ApplicationBuilder().token(BOT_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("balance", balance)) app.add_handler(CommandHandler("link", link)) app.add_handler(CommandHandler("withdraw", withdraw)) app.run_polling()

