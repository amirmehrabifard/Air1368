import os
import json
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from web3 import Web3

# Configurations
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Set this in env vars
PRIVATE_KEY = os.getenv("PRIVATE_KEY")  # Set this in env vars
AIRDROP_WALLET = "0xd5F168CFa6a68C21d7849171D6Aa5DDc9307E544"
CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181"
CHANNEL_USERNAME = "@benjaminfranklintoken"
TOKEN_DECIMALS = 18
TOKEN_AMOUNT_MAIN = 500
TOKEN_AMOUNT_REFERRAL = 100

USERS_FILE = "users.json"

# Logging setup
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Web3 setup
w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))
ERC20_ABI = [{
    "constant": False,
    "inputs": [
        {"name": "_to", "type": "address"},
        {"name": "_value", "type": "uint256"}
    ],
    "name": "transfer",
    "outputs": [{"name": "", "type": "bool"}],
    "type": "function"
}]
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ERC20_ABI)

# In-memory users/referrals data
users = {}
referrals = {}

# Load users data from JSON
def load_users():
    global users, referrals
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                data = json.load(f)
                users = {int(k): v for k, v in data.get("users", {}).items()}
                referrals = {int(k): v for k, v in data.get("referrals", {}).items()}
            logger.info(f"Loaded {len(users)} users and {len(referrals)} referrers.")
        except Exception as e:
            logger.error(f"Error loading users.json: {e}")
            users.clear()
            referrals.clear()
    else:
        logger.info("users.json not found, starting fresh.")

# Save users data to JSON
def save_users():
    try:
        with open(USERS_FILE, "w") as f:
            data_to_save = {
                "users": {str(k): v for k, v in users.items()},
                "referrals": {str(k): v for k, v in referrals.items()}
            }
            json.dump(data_to_save, f, indent=2)
        logger.info(f"Saved {len(users)} users and {len(referrals)} referrers.")
    except Exception as e:
        logger.error(f"Error saving users.json: {e}")

# Check if user is member of the channel
async def is_member(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.warning(f"Failed to get chat member info: {e}")
        return False

# Send tokens function
def send_token(to_address, amount):
    try:
        nonce = w3.eth.get_transaction_count(AIRDROP_WALLET)
        tx = contract.functions.transfer(
            Web3.to_checksum_address(to_address),
            int(amount * 10**TOKEN_DECIMALS)
        ).build_transaction({
            "from": AIRDROP_WALLET,
            "nonce": nonce,
            "gas": 100000,
            "gasPrice": w3.to_wei("5", "gwei")
        })
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logger.info(f"Sent {amount} tokens to {to_address}, tx_hash: {tx_hash.hex()}")
        return tx_hash.hex()
    except Exception as e:
        logger.error(f"Error sending token: {e}")
        return None

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if user_id not in users:
        users[user_id] = {"claimed": False}
        save_users()

    # Handle referral if exists
    if args:
        try:
            referrer_id = int(args[0])
            if referrer_id != user_id and "ref_by" not in users[user_id]:
                users[user_id]["ref_by"] = referrer_id
                referrals.setdefault(referrer_id, []).append(user_id)
                save_users()
                logger.info(f"User {user_id} referred by {referrer_id}")
        except ValueError:
            pass

    invite_link = f"https://t.me/{context.bot.username}?start={user_id}"

    await update.message.reply_text(
        "👋 Welcome to the BJF Airdrop!\n\n"
        "✅ Join our official channel:\n"
        f"👉 https://t.me/benjaminfranklintoken\n\n"
        "💸 After joining, send your *BSC wallet address* to receive *500 BJF tokens*.\n\n"
        f"👥 Share your invite link to earn *100 BJF tokens* per referral:\n"
        f"{invite_link}",
        parse_mode="Markdown"
    )

# Wallet address handler
async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = update.message.text.strip()

    if not Web3.is_address(wallet):
        await update.message.reply_text("❌ Invalid wallet address. Please send a valid BSC address.")
        return

    if users.get(user_id, {}).get("claimed"):
        await update.message.reply_text("✅ You already claimed your airdrop.")
        return

    if not await is_member(user_id, context.bot):
        await update.message.reply_text(
            "📛 Please join our channel before claiming tokens:\n"
            "👉 https://t.me/benjaminfranklintoken"
        )
        return

    tx_hash = send_token(wallet, TOKEN_AMOUNT_MAIN)
    if tx_hash:
        users[user_id]["wallet"] = wallet
        users[user_id]["claimed"] = True
        save_users()
        await update.message.reply_text(f"🎉 Airdrop sent! TX hash:\n`{tx_hash}`", parse_mode="Markdown")

        referrer_id = users[user_id].get("ref_by")
        if referrer_id and users.get(referrer_id, {}).get("wallet") and not users[user_id].get("referral_rewarded"):
            tx_ref = send_token(users[referrer_id]["wallet"], TOKEN_AMOUNT_REFERRAL)
            if tx_ref:
                users[user_id]["referral_rewarded"] = True
                save_users()
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=f"🎁 You got 100 BJF tokens for referring user {user_id}!\nTX: `{tx_ref}`",
                    parse_mode="Markdown"
                )
    else:
        await update.message.reply_text("⚠️ Failed to send tokens. Try later.")

def main():
    load_users()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet))

    logger.info("Bot started.")
    app.run_polling()

if __name__ == "__main__":
    main()
