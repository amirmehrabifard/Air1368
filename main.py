import os
import json
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CHAIN_RPC = "https://bsc-dataseed.binance.org/"  # BNB Smart Chain Mainnet

# Initialize web3
w3 = Web3(Web3.HTTPProvider(CHAIN_RPC))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
ACCOUNT = w3.eth.account.from_key(PRIVATE_KEY)
WALLET_ADDRESS = ACCOUNT.address

# Contract info
CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181"
CONTRACT_ABI = [
    {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
    {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"owner","type":"address"},{"indexed":True,"internalType":"address","name":"spender","type":"address"},{"indexed":False,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},
    {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"from","type":"address"},{"indexed":True,"internalType":"address","name":"to","type":"address"},{"indexed":False,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},
    {"inputs":[],"name":"airdropPortion","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"developmentPortion","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"publicSalePortion","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"taxPercent","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"teamPortion","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}
]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

USERS_FILE = "users.json"

# Load or create users data
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def generate_referral_code():
    return str(random.randint(1000000000, 9999999999))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args

    if user_id not in users:
        referral_code = generate_referral_code()
        users[user_id] = {
            "wallet": None,
            "referral_code": referral_code,
            "referrer": None,
            "balance": 0,
            "referred": []
        }
        # Give signup bonus 500 tokens
        success = send_tokens(user_id, 500)
        if not success:
            await update.message.reply_text("Welcome! You received 500 tokens as a signup bonus, but the transfer failed.")
        else:
            users[user_id]["balance"] = 500
            save_users()
            await update.message.reply_text(
                "Welcome! You received 500 tokens as a signup bonus.\n"
                "Invite your friends to get 100 tokens each.\n"
                "Use /balance to check your tokens.\n"
                "Use /withdraw to send tokens."
            )
    else:
        await update.message.reply_text("You are already registered.")

    # If started with referral code
    if args:
        ref_code = args[0]
        # Find referrer by code
        referrer_id = None
        for uid, info in users.items():
            if info.get("referral_code") == ref_code:
                referrer_id = uid
                break

        if referrer_id and referrer_id != user_id:
            # If this user has no referrer yet
            if users[user_id].get("referrer") is None:
                users[user_id]["referrer"] = referrer_id
                users[referrer_id]["balance"] += 100
                users[referrer_id]["referred"].append(user_id)
                send_tokens(referrer_id, 100)
                save_users()
                await context.bot.send_message(chat_id=referrer_id,
                                               text=f"You got 100 tokens for referring a new user!")
    
    # Send referral link
    referral_link = f"https://t.me/{context.bot.username}?start={users[user_id]['referral_code']}"
    await update.message.reply_text(f"Your referral link:\n{referral_link}")

async def set_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        await update.message.reply_text("Please /start first.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /wallet YOUR_WALLET_ADDRESS")
        return

    wallet = context.args[0]
    if not w3.isAddress(wallet):
        await update.message.reply_text("Invalid wallet address.")
        return

    users[user_id]["wallet"] = wallet
    save_users()
    await update.message.reply_text(f"Your wallet address has been set to:\n{wallet}")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        await update.message.reply_text("Please /start first.")
        return

    bal = users[user_id].get("balance", 0)
    await update.message.reply_text(f"Your token balance is: {bal}")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        await update.message.reply_text("Please /start first.")
        return

    if users[user_id].get("wallet") is None:
        await update.message.reply_text("Please set your wallet address first with /wallet command.")
        return

    if users[user_id].get("balance", 0) <= 0:
        await update.message.reply_text("You have no tokens to withdraw.")
        return

    amount = users[user_id]["balance"]
    users[user_id]["balance"] = 0
