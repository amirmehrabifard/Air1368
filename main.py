import os
import sqlite3
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from web3 import Web3

BOT_TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
SENDER_ADDRESS = "0xd5F168CFa6a68C21d7849171D6Aa5DDc9307E544"
TOKEN_CONTRACT = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181"
BSC_RPC = "https://bsc-dataseed.binance.org/"
CHANNEL_USERNAME = "@benjaminfranklintoken"

w3 = Web3(Web3.HTTPProvider(BSC_RPC))
contract_abi = [{
    "constant": False,
    "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
    "name": "transfer",
    "outputs": [{"name": "", "type": "bool"}],
    "type": "function"
}]
contract = w3.eth.contract(address=Web3.toChecksumAddress(TOKEN_CONTRACT), abi=contract_abi)

conn = sqlite3.connect("bot_database.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    wallet_address TEXT,
    language TEXT DEFAULT 'en',
    has_received_airdrop INTEGER DEFAULT 0,
    invite_code TEXT UNIQUE)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS invites (
    inviter_id INTEGER,
    invitee_id INTEGER,
    reward_given INTEGER DEFAULT 0,
    PRIMARY KEY (inviter_id, invitee_id))''')
conn.commit()

LANGUAGES = {
    "fa": {
        "welcome": "خوش آمدید! لطفا آدرس کیف پول BEP-20 خود را ارسال کنید:",
        "wallet_received": "آدرس کیف پول ثبت شد!",
        "already_received": "شما قبلا ایردراپ را دریافت کرده‌اید.",
        "airdrop_sent": "ایردراپ با موفقیت ارسال شد!",
        "invite_message": "لینک دعوت شما:
https://t.me/Bjfairdrop_bot?start={invite_code}",
        "invite_reward": "شما بابت دعوت یک کاربر ۱۰۰ توکن دریافت کردید!",
        "invalid_wallet": "آدرس کیف پول معتبر نیست.",
        "not_member": "شما عضو کانال نیستید.",
        "verify_prompt": "دستور /verify را ارسال کنید.",
        "help": "آدرس کیف پول را ارسال کنید. با /invite لینک دعوت بگیرید. با /verify عضویت را تأیید کنید."
    },
    "en": {
        "welcome": "Welcome! Please send your BEP-20 wallet address:",
        "wallet_received": "Wallet address saved!",
        "already_received": "You have already received the airdrop.",
        "airdrop_sent": "Airdrop sent successfully!",
        "invite_message": "Your invite link:
https://t.me/Bjfairdrop_bot?start={invite_code}",
        "invite_reward": "You received 100 tokens for a successful referral!",
        "invalid_wallet": "Invalid wallet address.",
        "not_member": "You are not a member of the channel.",
        "verify_prompt": "Send /verify after joining the channel.",
        "help": "Send your wallet address. Use /invite to get your referral link. Use /verify after joining the channel."
    },
    "ar": {
        "welcome": "مرحبًا! الرجاء إرسال عنوان محفظة BEP-20 الخاص بك:",
        "wallet_received": "تم حفظ عنوان المحفظة!",
        "already_received": "لقد استلمت التوزيع بالفعل.",
        "airdrop_sent": "تم إرسال التوزيع بنجاح!",
        "invite_message": "رابط الدعوة الخاص بك:
https://t.me/Bjfairdrop_bot?start={invite_code}",
        "invite_reward": "لقد حصلت على 100 توكن لدعوتك مستخدمًا جديدًا!",
        "invalid_wallet": "عنوان المحفظة غير صالح.",
        "not_member": "أنت لست عضوًا في القناة.",
        "verify_prompt": "أرسل /verify بعد الانضمام للقناة.",
        "help": "أرسل عنوان المحفظة. استخدم /invite للحصول على رابط الإحالة. استخدم /verify بعد الانضمام للقناة."
    },
    "ru": {
        "welcome": "Добро пожаловать! Пожалуйста, отправьте свой BEP-20 адрес кошелька:",
        "wallet_received": "Адрес кошелька сохранён!",
        "already_received": "Вы уже получили airdrop.",
        "airdrop_sent": "Airdrop успешно отправлен!",
        "invite_message": "Ваша ссылка приглашения:
https://t.me/Bjfairdrop_bot?start={invite_code}",
        "invite_reward": "Вы получили 100 токенов за приглашение пользователя!",
        "invalid_wallet": "Недействительный адрес кошелька.",
        "not_member": "Вы не являетесь участником канала.",
        "verify_prompt": "Отправьте /verify после вступления в канал.",
        "help": "Отправьте адрес кошелька. Используйте /invite для получения ссылки. Используйте /verify после вступления в канал."
    },
    "zh": {
        "welcome": "欢迎！请发送您的 BEP-20 钱包地址：",
        "wallet_received": "钱包地址已保存！",
        "already_received": "您已经领取过空投。",
        "airdrop_sent": "空投成功发送！",
        "invite_message": "您的邀请链接：
https://t.me/Bjfairdrop_bot?start={invite_code}",
        "invite_reward": "您因邀请新用户获得了 100 个代币！",
        "invalid_wallet": "无效的钱包地址。",
        "not_member": "您尚未加入频道。",
        "verify_prompt": "加入频道后请发送 /verify。",
        "help": "发送钱包地址。使用 /invite 获取邀请链接。加入频道后使用 /verify。"
    },
    "fr": {
        "welcome": "Bienvenue ! Veuillez envoyer votre adresse de portefeuille BEP-20 :",
        "wallet_received": "Adresse du portefeuille enregistrée !",
        "already_received": "Vous avez déjà reçu l'airdrop.",
        "airdrop_sent": "Airdrop envoyé avec succès !",
        "invite_message": "Votre lien d'invitation :
https://t.me/Bjfairdrop_bot?start={invite_code}",
        "invite_reward": "Vous avez reçu 100 tokens pour une invitation réussie !",
        "invalid_wallet": "Adresse de portefeuille invalide.",
        "not_member": "Vous n'êtes pas membre du canal.",
        "verify_prompt": "Envoyez /verify après avoir rejoint le canal.",
        "help": "Envoyez votre adresse de portefeuille. Utilisez /invite pour obtenir votre lien. Envoyez /verify après avoir rejoint le canal."
    }
}

def get_user_language(user_id):
    cursor.execute("SELECT language FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else "fa"

def send_tokens(to_address, amount):
    nonce = w3.eth.get_transaction_count(SENDER_ADDRESS)
    tx = contract.functions.transfer(Web3.toChecksumAddress(to_address), amount).buildTransaction({
        'chainId': 56, 'gas': 100000, 'gasPrice': w3.toWei('5', 'gwei'), 'nonce': nonce
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash.hex()

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    args = context.args
    if args and args[0].isdigit():
        inviter_id = int(args[0])
        if inviter_id != user_id:
            cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (user_id,))
            cursor.execute("INSERT OR IGNORE INTO invites(inviter_id, invitee_id) VALUES (?, ?)", (inviter_id, user_id))
            conn.commit()
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (user_id,))
    update.message.reply_text(LANGUAGES["fa"]["welcome"])

def handle_wallet(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    wallet = update.message.text.strip()
    lang = get_user_language(user_id)
    if not w3.isAddress(wallet):
        update.message.reply_text(LANGUAGES[lang]["invalid_wallet"])
        return
    cursor.execute("SELECT has_received_airdrop FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if row and row[0] == 1:
        update.message.reply_text(LANGUAGES[lang]["already_received"])
        return
    cursor.execute("UPDATE users SET wallet_address=?, has_received_airdrop=1 WHERE user_id=?", (wallet, user_id))
    conn.commit()
    try:
        tx_hash = send_tokens(wallet, 500 * 10**18)
        update.message.reply_text(LANGUAGES[lang]["airdrop_sent"] + f" https://bscscan.com/tx/{tx_hash}")
        cursor.execute("SELECT inviter_id FROM invites WHERE invitee_id=?", (user_id,))
        inviter = cursor.fetchone()
        if inviter:
            inviter_id = inviter[0]
            cursor.execute("SELECT wallet_address FROM users WHERE user_id=?", (inviter_id,))
            inv_wallet = cursor.fetchone()
            if inv_wallet and inv_wallet[0]:
                tx = send_tokens(inv_wallet[0], 100 * 10**18)
                cursor.execute("UPDATE invites SET reward_given=1 WHERE inviter_id=? AND invitee_id=?", (inviter_id, user_id))
                conn.commit()
                context.bot.send_message(chat_id=inviter_id, text=LANGUAGES[get_user_language(inviter_id)]["invite_reward"] + f" https://bscscan.com/tx/{tx}")
    except Exception as e:
        update.message.reply_text(f"خطا در ارسال توکن: {e}")

def invite(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    update.message.reply_text(LANGUAGES[lang]["invite_message"].format(invite_code=user_id))

def verify(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    try:
        member = context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            update.message.reply_text("عضویت تأیید شد ✅")
        else:
            update.message.reply_text(LANGUAGES[lang]["not_member"])
    except:
        update.message.reply_text(LANGUAGES[lang]["not_member"])

def help_cmd(update: Update, context: CallbackContext):
    lang = get_user_language(update.effective_user.id)
    update.message.reply_text(LANGUAGES[lang]["help"])

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("invite", invite))
    dp.add_handler(CommandHandler("verify", verify))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_wallet))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()