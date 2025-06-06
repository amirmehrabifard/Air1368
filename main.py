import os import json from telegram import Update from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes from web3 import Web3 from web3.middleware import geth_poa_middleware

BOT_TOKEN = os.environ.get("BOT_TOKEN") PRIVATE_KEY = os.environ.get("PRIVATE_KEY") TOKEN_AMOUNT = 500 # Initial reward REFERRAL_BONUS = 100 # Bonus per referral CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181" CHANNEL_LINK = "https://t.me/benjaminfranklintoken" INFURA_URL = "https://rpc.ankr.com/polygon"

w3 = Web3(Web3.HTTPProvider(INFURA_URL)) w3.middleware_onion.inject(geth_poa_middleware, layer=0)

with open("users.json", "r") as f: users = json.load(f)

def save_users(): with open("users.json", "w") as f: json.dump(users, f, indent=2)

def send_tokens(to_address, amount): if not w3.isAddress(to_address): return "Invalid address" contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=[ { "constant": False, "inputs": [ {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"} ], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function" } ]) acct = w3.eth.account.from_key(PRIVATE_KEY) nonce = w3.eth.get_transaction_count(acct.address) txn = contract.functions.transfer(to_address, amount * 10**18).build_transaction({ 'chainId': 137, 'gas': 100000, 'gasPrice': w3.to_wei('2', 'gwei'), 'nonce': nonce }) signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY) tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction) return w3.to_hex(tx_hash)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if user_id not in users: users[user_id] = { "wallet": None, "invited_by": None, "invites": [], "rewarded": False } if context.args: inviter_id = context.args[0] if inviter_id in users and user_id not in users[inviter_id]["invites"]: users[user_id]["invited_by"] = inviter_id users[inviter_id]["invites"].append(user_id) save_users()

await update.message.reply_text( "Welcome! You received 500 tokens as a signup bonus.\n" "Please set your wallet address using /setwallet <address>.\n\n" "Your referral link:\n" f"https://t.me/{context.bot.username}?start={user_id}" ) 

async def set_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) if len(context.args) != 1: await update.message.reply_text("Usage: /setwallet <your_wallet_address>") return

wallet = context.args[0] if not w3.is_address(wallet): await update.message.reply_text("Invalid wallet address.") return users[user_id]["wallet"] = w3.to_checksum_address(wallet) message = "Wallet set. " if not users[user_id]["rewarded"]: tx_hash = send_tokens(users[user_id]["wallet"], TOKEN_AMOUNT) message += f"\n\nSent you {TOKEN_AMOUNT} tokens.\nTransaction: https://polygonscan.com/tx/{tx_hash}" users[user_id]["rewarded"] = True inviter_id = users[user_id].get("invited_by") if inviter_id and users[inviter_id].get("wallet"): tx_hash = send_tokens(users[inviter_id]["wallet"], REFERRAL_BONUS) message += f"\n\nReferral bonus sent to your inviter.\nTransaction: https://polygonscan.com/tx/{tx_hash}" save_users() await update.message.reply_text(message) 

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = str(update.effective_user.id) count = len(users[user_id].get("invites", [])) await update.message.reply_text(f"You invited {count} users.\nYour total tokens: {TOKEN_AMOUNT + count * REFERRAL_BONUS}")

app = ApplicationBuilder().token(BOT_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("setwallet", set_wallet)) app.add_handler(CommandHandler("balance", balance))

app.run_polling()

