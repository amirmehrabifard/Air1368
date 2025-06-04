import os import logging from telegram import Update from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters from web3 import Web3

راه‌اندازی لاگینگ 

logging.basicConfig( format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO )

logger = logging.getLogger(name)

اتصال به شبکه BNB 

w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))

مقادیر محیطی 

BOT_TOKEN = os.getenv('BOT_TOKEN') PRIVATE_KEY = os.getenv('PRIVATE_KEY')

آدرس‌ها 

AIRDROP_WALLET = '0xd5F168CFa6a68C21d7849171D6Aa5DDc9307E544' CONTRACT_ADDRESS = '0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181' BOT_USERNAME = 'Bjfairdrop_bot'

ABI ساده‌شده توکن 

ERC20_ABI = [ { "constant": False, "inputs": [ {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"} ], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function" } ]

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ERC20_ABI)

users = {}

texts = { "fa": { "start": "سلام! از /start برای شروع استفاده کنید.", "welcome": "خوش آمدید! لطفا آدرس کیف پول خود را ارسال کنید تا ۵۰۰ توکن دریافت کنید.", "invalid_wallet": "آدرس کیف پول نامعتبر است.", "already_claimed": "شما قبلاً توکن دریافت کرده‌اید.", "transfer_success": "{amount} توکن به آدرس {wallet} ارسال شد.", "error": "خطا در ارسال توکن‌ها." } }

def get_lang(): return "fa"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): lang = get_lang() await update.message.reply_text(texts[lang]["welcome"])

async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE): lang = get_lang() wallet = update.message.text.strip() user_id = update.effective_user.id

if not Web3.is_address(wallet): await update.message.reply_text(texts[lang]["invalid_wallet"]) return if users.get(user_id, {}).get("claimed"): await update.message.reply_text(texts[lang]["already_claimed"]) return try: tx_hash = transfer_tokens(wallet, 500) users[user_id] = {"wallet": wallet, "claimed": True} await update.message.reply_text(texts[lang]["transfer_success"].format(amount=500, wallet=wallet)) except Exception as e: logger.error(e) await update.message.reply_text(texts[lang]["error"]) 

def transfer_tokens(to_address, amount): nonce = w3.eth.get_transaction_count(AIRDROP_WALLET) tx = contract.functions.transfer( Web3.to_checksum_address(to_address), amount * (10 ** 18) ).build_transaction({ 'chainId': 56, 'gas': 200000, 'gasPrice': w3.to_wei('5', 'gwei'), 'nonce': nonce, })

signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY) tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction) return tx_hash.hex() 

def main(): app = ApplicationBuilder().token(BOT_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_wallet)) app.run_polling()

if name == 'main': main()

