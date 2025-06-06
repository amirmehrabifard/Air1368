import os
import json
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from web3 import Web3

# ----------------------------------------
# Configurations
# ----------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
AIRDROP_WALLET = "0xd5F168CFa6a68C21d7849171D6Aa5DDc9307E544"
CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181"
CHANNEL_USERNAME = "@benjaminfranklintoken"
TOKEN_DECIMALS = 18
TOKEN_AMOUNT_MAIN = 500
TOKEN_AMOUNT_REFERRAL = 100

# Path to JSON file for persisting users
USERS_FILE = "users.json"

# ----------------------------------------
# Logging
# ----------------------------------------
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------
# Web3 setup
# ----------------------------------------
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

# ----------------------------------------
# In-memory DB (loaded from JSON)
# ----------------------------------------
# users: user_id -> {
#     "wallet": <str>, 
#     "claimed": <bool>, 
#     "ref_by": <int>, 
#     "referral_rewarded": <bool>
# }
users = {}

# referrals: referrer_id -> [list of referred user_ids]
referrals = {}

# ----------------------------------------
# JSON Persistence Functions
# ----------------------------------------
def load_users():
    global users, referrals
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                data = json.load(f)
                users = data.get("users", {})
                referrals = data.get("referrals", {})
                # JSON keys are strings; convert referrals' inner lists to ints
                referrals = {int(k): v for k, v in referrals.items()}
                # Convert users' keys to int (user_id)
                users = {int(k): v for k, v in users.items()}
                logger.info(f"Loaded {len(users)} users and {len(referrals)} referrers from {USERS_FILE}.")
        except Exception as e:
            logger.error(f"Failed to load {USERS_FILE}: {e}")
            users = {}
            referrals = {}
    else:
        users = {}
        referrals = {}

def save_users():
    try:
        data = {
            "users": users,
            "referrals": referrals
        }
        # Convert keys to str for JSON
        data_to_dump = {
            "users": {str(k): v for k, v in users.items()},
            "referrals": {str(k): v for k, v in referrals.items()}
        }
        with open(USERS_FILE, "w") as f:
            json.dump(data_to_dump, f, indent=2)
        logger.info(f"Saved {len(users)} users and {len(referrals)} referrers to {USERS_FILE}.")
    except Exception as e:
        logger.error(f"Failed to save {USERS_FILE}: {e}")

# ----------------------------------------
# Utility: Check Telegram Channel Membership
# ----------------------------------------
async def is_member(user_id, bot):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ----------------------------------------
# Utility: Send BJF Token via Web3
# ----------------------------------------
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
        return tx_hash.hex()
    except Exception as e:
        logger.error(f"Token send error: {e}")
        return None

# ----------------------------------------
# /start Command Handler
# ----------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if user_id not in users:
        users[user_id] = {"claimed": False}
        save_users()

    if args:
        try:
            referrer_id = int(args[0])
            if referrer_id != user_id and "ref_by" not in users[user_id]:
                users[user_id]["ref_by"] = referrer_id
                referrals.setdefault(referrer_id, []).append(user_id)
                save_users()
                logger.info(f"User {user_id} was referred by {referrer_id}")
        except ValueError:
            pass

    invite_link = f"https://t.me/{context.bot.username}?start={user_id}"
    await update.message.reply_text(
        "👋 Welcome to the BJF Airdrop!\n\n"
        "✅ To participate, please join our official channel:\n"
        "👉 https://t.me/benjaminfranklintoken\n\n"
        "💸 After joining, send your *BSC wallet address* to receive *500 BJF tokens*.\n\n"
        f"👥 Share your unique invite link to earn *100 BJF tokens* for each valid referral:\n"
        f"{invite_link}",
        parse_mode="Markdown"
    )

# ----------------------------------------
# Handle Incoming Wallet Address
# ----------------------------------------
async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = update.message.text.strip()

    if not Web3.is_address(wallet):
        await update.message.reply_text("❌ Invalid wallet address. Please send a valid BSC address.")
        return

    if users.get(user_id, {}).get("claimed"):
        await update.message.reply_text("✅ You have already claimed your airdrop.")
        return

    if not await is_member(user_id, context.bot):
        await update.message.reply_text(
            "📛 You must join our channel before claiming tokens:\n"
            "👉 https://t.me/benjaminfranklintoken"
        )
        return

    tx = send_token(wallet, TOKEN_AMOUNT_MAIN)
    if tx:
        users[user_id]["wallet"] = wallet
        users[user_id]["claimed"] = True
        save_users()

        await update.message.reply_text(
            f"🎉 Airdrop sent successfully! Transaction hash:\n`{tx}`",
            parse_mode="Markdown"
        )

        referrer_id = users[user_id].get("ref_by")
        if referrer_id and users.get(referrer_id, {}).get("wallet"):
            if not users[user_id].get("referral_rewarded"):
                tx2 = send_token(users[referrer_id]["wallet"], TOKEN_AMOUNT_REFERRAL)
                if tx2:
                    users[user_id]["referral_rewarded"] = True
                    save_users()
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=(
                            f"🎁 You received 100 BJF tokens for inviting user {user_id}!\n"
                            f"TX: `{tx2}`"
                        ),
                        parse_mode="Markdown"
                    )
    else:
        await update.message.reply_text("⚠️ Failed to send tokens. Please try again later.")

# ----------------------------------------
# Main: load data and run bot
# ----------------------------------------
def main():
    load_users()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
