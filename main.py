import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from web3 import Web3
from web3.middleware import geth_poa_middleware

TOKEN_AMOUNT_SIGNUP = 500
TOKEN_AMOUNT_REFERRAL = 100
TOKEN_CONTRACT_ADDRESS = '0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181'
CHANNEL_USERNAME = '@benjaminfranklintoken'

INFURA_URL = 'https://bsc-dataseed.binance.org/'  # Replace if needed
w3 = Web3(Web3.HTTPProvider(INFURA_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

BOT_TOKEN = os.getenv('BOT_TOKEN')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
SENDER_ADDRESS = w3.eth.account.from_key(PRIVATE_KEY).address

USERS_FILE = 'users.json'

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id in users:
        await update.message.reply_text("You are already registered.")
        return

    # Check channel membership
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id)
        if member.status not in ['member', 'creator', 'administrator']:
            await update.message.reply_text(f"Please join the channel {CHANNEL_USERNAME} first.")
            return
    except:
        await update.message.reply_text("Error checking channel membership.")
        return

    users[user_id] = {
        "wallet": None,
        "ref": None,
        "invited": [],
        "registered": True
    }

    # Handle referral
    if context.args:
        ref_id = context.args[0]
        if ref_id != user_id and ref_id in users:
            users[user_id]['ref'] = ref_id
            users[ref_id]['invited'].append(user_id)

    save_users(users)

    # Send signup reward
    tx_hash = send_tokens(update.effective_user.id, TOKEN_AMOUNT_SIGNUP)
    await update.message.reply_text(f"Welcome! You received {TOKEN_AMOUNT_SIGNUP} tokens as a signup bonus.\nTransaction: {tx_hash}\n\nYour referral link:\nhttps://t.me/{context.bot.username}?start={user_id}")

    # Send referral reward
    ref_id = users[user_id]['ref']
    if ref_id and ref_id in users:
        tx_hash_ref = send_tokens(ref_id, TOKEN_AMOUNT_REFERRAL)
        await context.bot.send_message(ref_id, f"You received {TOKEN_AMOUNT_REFERRAL} tokens for inviting a friend!\nTransaction: {tx_hash_ref}")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_users()
    if user_id not in users or not users[user_id].get('wallet'):
        await update.message.reply_text("Please register and set your wallet address first using /setwallet command.")
        return
    wallet = users[user_id]['wallet']
    balance = get_token_balance(wallet)
    await update.message.reply_text(f"Your wallet: {wallet}\nToken Balance: {balance}")

async def setwallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_users()
    if user_id not in users:
        await update.message.reply_text("Please use /start first.")
        return
    if not context.args:
        await update.message.reply_text("Please provide a wallet address: /setwallet <your_address>")
        return
    wallet = context.args[0]
    if not Web3.is_address(wallet):
        await update.message.reply_text("Invalid wallet address.")
        return
    users[user_id]['wallet'] = wallet
    save_users(users)
    await update.message.reply_text(f"Wallet set to: {wallet}")

def send_tokens(user_id, amount):
    users = load_users()
    user = users.get(str(user_id))
    if not user or not user.get("wallet"):
        return "Wallet not set."
    to_address = user['wallet']

    contract = w3.eth.contract(address=TOKEN_CONTRACT_ADDRESS, abi=[{
        "constant": False,
        "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }])

    nonce = w3.eth.get_transaction_count(SENDER_ADDRESS)
    tx = contract.functions.transfer(to_address, amount * (10**18)).build_transaction({
        'chainId': 56,
        'gas': 100000,
        'gasPrice': w3.to_wei('5', 'gwei'),
        'nonce': nonce
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return w3.to_hex(tx_hash)

def get_token_balance(address):
    contract = w3.eth.contract(address=TOKEN_CONTRACT_ADDRESS, abi=[{
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }])
    balance = contract.functions.balanceOf(address).call()
    return balance // (10**18)

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("setwallet", setwallet))
    app.run_polling()
