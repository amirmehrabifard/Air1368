import os
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Configs (use your environment variables)
BOT_TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181"
BSC_RPC = "https://bsc-dataseed.binance.org/"

# Load ABI from hardcoded string (paste your actual ABI here)
CONTRACT_ABI = [
    {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
    {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"owner","type":"address"},
                                {"indexed":True,"internalType":"address","name":"spender","type":"address"},
                                {"indexed":False,"internalType":"uint256","name":"value","type":"uint256"}],
     "name":"Approval","type":"event"},
    {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"from","type":"address"},
                                {"indexed":True,"internalType":"address","name":"to","type":"address"},
                                {"indexed":False,"internalType":"uint256","name":"value","type":"uint256"}],
     "name":"Transfer","type":"event"},
    {"inputs":[],"name":"airdropPortion","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],
     "name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"spender","type":"address"},
               {"internalType":"uint256","name":"amount","type":"uint256"}],
     "name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],
     "stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"","type":"address"}],
     "name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"developmentPortion","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"publicSalePortion","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"taxPercent","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"teamPortion","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"to","type":"address"},
               {"internalType":"uint256","name":"amount","type":"uint256"}],
     "name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],
     "stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"from","type":"address"},
               {"internalType":"address","name":"to","type":"address"},
               {"internalType":"uint256","name":"amount","type":"uint256"}],
     "name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],
     "stateMutability":"nonpayable","type":"function"}
]

USERS_FILE = "users.json"

# Initialize web3 and contract
w3 = Web3(Web3.HTTPProvider(BSC_RPC))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
contract = w3.eth.contract(address=Web3.toChecksumAddress(CONTRACT_ADDRESS), abi=CONTRACT_ABI)

# Load users data
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        users[user_id] = {
            "wallet": None,
            "referred_by": None,
            "invited_users": [],
            "tokens": 500  # signup bonus
        }
        save_users()
        await update.message.reply_text(
            "Welcome! You received 500 tokens as a signup bonus.\n"
            "Invite your friends to get 100 tokens each.\n"
            "Use /balance to check your tokens.\n"
            "Use /withdraw to send tokens.\n"
            f"Your referral link:\nhttps://t.me/{context.bot.username}?start={user_id}"
        )
        # Try to send signup bonus token (optional - handle silently if error)
        if users[user_id]["wallet"]:
            try:
                send_tokens(users[user_id]["wallet"], 500)
            except Exception:
                pass
    else:
        await update.message.reply_text("You already registered.")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users or not users[user_id].get("wallet"):
        await update.message.reply_text("Wallet not set. Please send your wallet address.")
        return
    wallet = users[user_id]["wallet"]
    try:
        balance = contract.functions.balanceOf(Web3.toChecksumAddress(wallet)).call()
        decimals = contract.functions.decimals().call()
        readable_balance = balance / (10 ** decimals)
        await update.message.reply_text(f"Your token balance: {readable_balance}")
    except Exception as e:
        await update.message.reply_text("Error fetching balance.")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users or not users[user_id].get("wallet"):
        await update.message.reply_text("Wallet not set. Please send your wallet address.")
        return
    args = context.args
    if not args or len(args) != 2:
        await update.message.reply_text("Usage: /withdraw <recipient_address> <amount>")
        return
    recipient = args[0]
    amount_str = args[1]
    try:
        amount = float(amount_str)
    except ValueError:
        await update.message.reply_text("Invalid amount.")
        return
    wallet = users[user_id]["wallet"]
    decimals = contract.functions.decimals().call()
    token_amount = int(amount * (10 ** decimals))
    balance = contract.functions.balanceOf(Web3.toChecksumAddress(wallet)).call()
    if token_amount > balance:
        await update.message.reply_text("Insufficient balance.")
        return
    try:
        tx_hash = send_tokens(recipient, token_amount, from_private_key=PRIVATE_KEY)
        await update.message.reply_text(f"Tokens sent! Tx hash: {tx_hash.hex()}")
    except Exception as e:
        await update.message.reply_text(f"Transaction failed: {str(e)}")

async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    # Validate wallet address
    if not w3.isAddress(text):
        await update.message.reply_text("Invalid wallet address. Please try again.")
        return
    wallet = Web3.toChecksumAddress(text)
    if user_id not in users:
        users[user_id] = {
            "wallet": wallet,
            "referred_by": None,
            "invited_users": [],
            "tokens": 500
        }
    else:
        users[user_id]["wallet"] = wallet
    save_users()
    await update.message.reply_text(f"Wallet set to: {wallet}")

def send_tokens(to_address, amount, from_private_key=PRIVATE_KEY):
    from_address = w3.eth.account.privateKeyToAccount(from_private_key).address
    nonce = w3.eth.get_transaction_count(from_address)
    tx = contract.functions.transfer(Web3.toChecksumAddress(to_address), amount).buildTransaction({
        'chainId': 56,
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=from_private_key
