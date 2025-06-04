import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from web3 import Web3

# راه اندازی لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# اتصال به شبکه BNB (مثلا با RPC رایگان)
w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))

BOT_TOKEN = os.getenv('BOT_TOKEN')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

AIRDROP_WALLET = '0xd5F168CFa6a68C21d7849171D6Aa5DDc9307E544'
CONTRACT_ADDRESS = '0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181'

# آدرس ربات تلگرام برای لینک دعوت
BOT_USERNAME = 'Bjfairdrop_bot'

# ABI ساده شده توکن (ERC20 استاندارد)
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ERC20_ABI)

# ذخیره کاربران و وضعیت ها (در حافظه، برای راه اندازی مجدد نیاز به دیتابیس دارید)
users = {}
referrals = {}

# پیام ها به چند زبان
texts = {
    "en": {
        "welcome": "Welcome! Please send me your wallet address to receive 500 BJFairdrop tokens.",
        "invalid_wallet": "Invalid wallet address. Please try again.",
        "already_claimed": "You have already claimed your initial 500 tokens.",
        "transfer_success": "Successfully sent {amount} tokens to {wallet}.",
        "invite_message": "Your invitation link:\nhttps://t.me/{bot_username}?start={user_id}",
        "referral_bonus": "You received 100 tokens for a successful referral!",
        "unknown_command": "Unknown command.",
        "send_wallet": "Please send your wallet address.",
        "not_in_channel": "Please join our channel first: https://t.me/benjaminfranklintoken",
        "verify_success": "Verification successful! You got 500 tokens.",
        "already_verified": "You already verified and received your tokens.",
        "start": "Hello! Use /start to begin.",
    },
    "fa": {
        "welcome": "خوش آمدید! لطفا آدرس کیف پول خود را ارسال کنید تا ۵۰۰ توکن BJFairdrop دریافت کنید.",
        "invalid_wallet": "آدرس کیف پول نامعتبر است. لطفا دوباره تلاش کنید.",
        "already_claimed": "شما قبلا ۵۰۰ توکن اولیه را دریافت کرده اید.",
        "transfer_success": "{amount} توکن با موفقیت به {wallet} ارسال شد.",
        "invite_message": "لینک دعوت شما:\nhttps://t.me/{bot_username}?start={user_id}",
        "referral_bonus": "شما به ازای دعوت موفق ۱۰۰ توکن دریافت کردید!",
        "unknown_command": "دستور نامشخص.",
        "send_wallet": "لطفا آدرس کیف پول خود را ارسال کنید.",
        "not_in_channel": "لطفا ابتدا در کانال ما عضو شوید: https://t.me/benjaminfranklintoken",
        "verify_success": "تایید موفقیت آمیز! ۵۰۰ توکن به شما داده شد.",
        "already_verified": "شما قبلا تایید شدید و توکن دریافت کردید.",
        "start": "سلام! از /start برای شروع استفاده کنید.",
    },
    "ar": {
        "welcome": "مرحبا! الرجاء إرسال عنوان محفظتك لتلقي 500 توكن BJFairdrop.",
        "invalid_wallet": "عنوان المحفظة غير صالح. حاول مرة أخرى.",
        "already_claimed": "لقد استلمت 500 توكن أولية بالفعل.",
        "transfer_success": "تم إرسال {amount} توكن إلى {wallet} بنجاح.",
        "invite_message": "رابط الدعوة الخاص بك:\nhttps://t.me/{bot_username}?start={user_id}",
        "referral_bonus": "لقد حصلت على 100 توكن مقابل دعوة ناجحة!",
        "unknown_command": "أمر غير معروف.",
        "send_wallet": "الرجاء إرسال عنوان محفظتك.",
        "not_in_channel": "يرجى الانضمام إلى قناتنا أولاً: https://t.me/benjaminfranklintoken",
        "verify_success": "تم التحقق بنجاح! حصلت على 500 توكن.",
        "already_verified": "لقد تم التحقق منك مسبقاً واستلمت التوكن.",
        "start": "مرحباً! استخدم /start للبدء.",
    },
    "ru": {
        "welcome": "Добро пожаловать! Пожалуйста, отправьте адрес вашего кошелька, чтобы получить 500 токенов BJFairdrop.",
        "invalid_wallet": "Неверный адрес кошелька. Пожалуйста, попробуйте снова.",
        "already_claimed": "Вы уже получили начальные 500 токенов.",
        "transfer_success": "Успешно отправлено {amount} токенов на {wallet}.",
        "invite_message": "Ваша реферальная ссылка:\nhttps://t.me/{bot_username}?start={user_id}",
        "referral_bonus": "Вы получили 100 токенов за успешную рекомендацию!",
        "unknown_command": "Неизвестная команда.",
        "send_wallet": "Пожалуйста, отправьте адрес вашего кошелька.",
        "not_in_channel": "Пожалуйста, сначала присоединитесь к нашему каналу: https://t.me/benjaminfranklintoken",
        "verify_success": "Проверка успешна! Вы получили 500 токенов.",
        "already_verified": "Вы уже прошли проверку и получили токены.",
        "start": "Привет! Используйте /start для начала.",
    },
    "zh": {
        "welcome": "欢迎！请发送您的钱包地址以接收500个BJFairdrop代币。",
        "invalid_wallet": "钱包地址无效。请再试一次。",
        "already_claimed": "您已领取初始的500个代币。",
        "transfer_success": "成功发送{amount}个代币到{wallet}。",
        "invite_message": "您的邀请链接:\nhttps://t.me/{bot_username}?start={user_id}",
        "referral_bonus": "您因成功邀请获得100个代币！",
        "unknown_command": "未知命令。",
        "send_wallet": "请发送您的钱包地址。",
        "not_in_channel": "请先加入我们的频道：https://t.me/benjaminfranklintoken",
        "verify_success": "验证成功！您已获得500个代币。",
        "already_verified": "您已验证并获得代币。",
        "start": "你好！使用 /start 开始。",
    },
    "fr": {
        "welcome": "Bienvenue! Veuillez envoyer votre adresse de portefeuille pour recevoir 500 jetons BJFairdrop.",
        "invalid_wallet": "Adresse de portefeuille invalide. Veuillez réessayer.",
        "already_claimed": "Vous avez déjà réclamé vos 500 jetons initiaux.",
        "transfer_success": "{amount} jetons envoyés avec succès à {wallet}.",
        "invite_message": "Votre lien d'invitation:\nhttps://t.me/{bot_username}?start={user_id}",
        "referral_bonus": "Vous avez reçu 100 jetons pour un parrainage réussi!",
        "unknown_command": "Commande inconnue.",
        "send_wallet": "Veuillez envoyer votre adresse de portefeuille.",
        "not_in_channel": "Veuillez d'abord rejoindre notre chaîne : https://t.me/benjaminfranklintoken",
        "verify_success": "Vérification réussie! Vous avez reçu 500 jetons.",
        "already_verified": "Vous avez déjà été vérifié et reçu vos jetons.",
        "start": "Bonjour! Utilisez /start pour commencer.",
    }
}

def get_lang(update: Update):
    user_id = update.effective_user.id
    # ساده ترین حالت: همیشه انگلیسی (می توان پیشرفته تر کرد)
    # اگر بخواهیم بر اساس زبان تلگرام کاربر زبان انتخاب کنیم:
    lang_code = update.effective_user.language_code
    if lang_code and lang_code[:2] in texts:
        return lang_code[:2]
    return "en"  # پیش فرض انگلیسی

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.message.reply_text(texts[lang]["welcome"])

async def send_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = update.message.text.strip()
    if not Web3.isAddress(text):
        await update.message.reply_text(texts[lang]["invalid_wallet"])
        return

    user_id = update.effective_user.id
    user_wallet = Web3.to_checksum_address(text)

    # بررسی قبلی بودن دریافت اولیه
    if users.get(user_id, {}).get("claimed"):
        await update.message.reply_text(texts[lang]["already_claimed"])
        return

    # انتقال 500 توکن
    try:
        tx_hash = transfer_tokens(user_wallet, 500)
    except Exception as e:
        logger.error(f"Error sending tokens: {e}")
        await update.message.reply_text("Error sending tokens.")
        return

    # ذخیره وضعیت کاربر
    users[user_id] = {
        "wallet": user_wallet,
        "claimed": True,
        "referrals": set()
    }

    await update.message.reply_text(texts[lang]["transfer_success"].format(amount=500, wallet=user_wallet))

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    user_id = update.effective_user.id
    invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    await update.message.reply_text(texts[lang]["invite_message"].format(bot_username=BOT_USERNAME, user_id=user_id))

def transfer_tokens(to_address, amount):
    nonce = w3.eth.get_transaction_count(AIRDROP_WALLET)
    tx = contract.functions.transfer(
        Web3.to_checksum_address(to_address),
        amount * (10 ** 18)  # فرض بر 18 رقم اعشار توکن
    ).build_transaction({
        'chainId': 56,
        'gas': 200000,
        'gasPrice': w3.to_wei('5', 'gwei'),
        'nonce': nonce,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash.hex()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.message.reply_text(texts[lang]["start"])

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.message.reply_text(texts[lang]["unknown_command"])

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("invite", invite))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), send_wallet_address))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    application.run_polling()

if __name__ == '__main__':
    main()
