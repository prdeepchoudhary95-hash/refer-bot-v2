import telebot
import sqlite3
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8674871518:AAEuKgPVIIwuMrXQHGd7J_example_put_real_token")
BOT_USERNAME = "sxearningbot"
ADMIN_ID = 8226423765

CHANNEL_1_ID = "-1003543754313"
CHANNEL_1_LINK = "https://t.me/+2b5VIy1AAtc1NmY1"

CHANNEL_2_ID = "-1003847877781"
CHANNEL_2_LINK = "https://t.me/+L1wzq1ZSK5AxY2E1"

CHANNEL_3_ID = "-1003452695618"
CHANNEL_3_LINK = "https://t.me/+8e6KE8s2fZExYjM1"

ALL_IDS = [CHANNEL_1_ID, CHANNEL_2_ID, CHANNEL_3_ID]
ALL_LINKS = [CHANNEL_1_LINK, CHANNEL_2_LINK, CHANNEL_3_LINK]

bot = telebot.TeleBot(BOT_TOKEN)

conn = sqlite3.connect('users.db', check_same_thread=False)
conn.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, refer_count INTEGER DEFAULT 0, referred_by INTEGER DEFAULT 0)')
conn.commit()

def is_joined_all(uid):
    not_joined = []
    for i, ch_id in enumerate(ALL_IDS):
        try:
            m = bot.get_chat_member(ch_id, uid)
            if m.status not in ['member', 'administrator', 'creator']:
                not_joined.append(i)
        except:
            not_joined.append(i)
    return not_joined

def send_menu(uid):
    cur = conn.cursor()
    cur.execute("SELECT balance, refer_count FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    bal = row[0] if row else 0
    ref = row[1] if row else 0
    text = f"Welcome to @{BOT_USERNAME}\n\nBalance: {bal} Rs\nReferrals: {ref}\n\nYour Refer Link:\nhttps://t.me/{BOT_USERNAME}?start={uid}\n\nPer Refer = 10 Rs"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Balance", callback_data="balance"))
    markup.add(telebot.types.InlineKeyboardButton("Refer & Earn", callback_data="refer"))
    markup.add(telebot.types.InlineKeyboardButton("Withdraw", callback_data="withdraw"))
    bot.send_message(uid, text, reply_markup=markup)

@bot.message_handler(commands=['start'])
def start_handler(message):
    uid = message.from_user.id
    args = message.text.split()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    exists = cur.fetchone()
    if not exists:
        referred_by = 0
        if len(args) > 1:
            try:
                referred_by = int(args[1])
                if referred_by!= uid:
                    cur.execute("UPDATE users SET balance = balance + 10, refer_count = refer_count + 1 WHERE user_id=?", (referred_by,))
                    conn.commit()
            except:
                pass
        cur.execute("INSERT INTO users (user_id, referred_by) VALUES (?,?)", (uid, referred_by))
        conn.commit()
    not_joined = is_joined_all(uid)
    if not_joined:
        text = "Pehle ye 3 Channels Join Karo, fir /start dabao:"
        markup = telebot.types.InlineKeyboardMarkup()
        for idx in not_joined:
            markup.add(telebot.types.InlineKeyboardButton(f"Join Channel {idx+1}", url=ALL_LINKS[idx]))
        markup.add(telebot.types.InlineKeyboardButton("Joined - Check Again", callback_data="check_join"))
        bot.send_message(uid, text, reply_markup=markup)
        return
    send_menu(uid)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    if call.data == "check_join":
        not_joined = is_joined_all(uid)
        if not_joined:
            bot.answer_callback_query(call.id, "Abhi bhi join karna baaki hai!")
        else:
            bot.delete_message(uid, call.message.message_id)
            send_menu(uid)
    elif call.data == "balance":
        cur = conn.cursor()
        cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        row = cur.fetchone()
        bal = row[0] if row else 0
        bot.answer_callback_query(call.id, f"Balance: {bal} Rs")
    elif call.data == "refer":
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        bot.send_message(uid, f"Tera Refer Link:\n{link}\n\nShare kar aur kama 10 Rs per refer!")
    elif call.data == "withdraw":
        bot.send_message(uid, "Withdraw ke liye Admin se sampark karo. Minimum 100 Rs")

print("Bot is running...")
bot.infinity_polling()
