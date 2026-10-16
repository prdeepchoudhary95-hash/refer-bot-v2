import telebot, sqlite3, random, datetime

# ====== FINAL CONFIG - READY ======
BOT_TOKEN = "8674871518:AAGGQpI6gf38028IzUuztBCoLrVMchNIHN4"
BOT_USERNAME = "sxearningbot"
ADMIN_ID = 8226423765

CHANNEL_1_ID = "-1003543754313"
CHANNEL_1_LINK = "https://t.me/+E2b5VIy1AAtmOGI1"

CHANNEL_2_ID = "-1003847877781"
CHANNEL_2_LINK = "https://t.me/+L1Wzq1ZSK54yNGQ1"

CHANNEL_3_ID = "-1003452695618"
CHANNEL_3_LINK = "https://t.me/+8eE6KE8s2FJiMjdl"
# ===================================

ALL_IDS = [CHANNEL_1_ID, CHANNEL_2_ID, CHANNEL_3_ID]
ALL_LINKS = [CHANNEL_1_LINK, CHANNEL_2_LINK, CHANNEL_3_LINK]

bot = telebot.Bot(BOT_TOKEN)
conn = sqlite3.connect('users.db', check_same_thread=False)
conn.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER, refer_count INTEGER, referred_by TEXT, last_daily TEXT)''')
conn.commit()

def is_joined_all(uid):
    not_joined = []
    for i, ch_id in enumerate(ALL_IDS):
        try:
            m = bot.get_chat_member(ch_id, uid)
            if m.status not in ['member','administrator','creator']:
                not_joined.append(i)
        except:
            not_joined.append(i)
    return not_joined

def send_menu(uid):
    cur = conn.cursor()
    cur.execute("SELECT balance, refer_count FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if not row: return
    bal, cnt = row
    link = f"https://t.me/{BOT_USERNAME}?start={uid}"
    bot.send_message(uid, f"💰 Balance: {bal} Rs\n👥 Refers: {cnt}\n🔗 Link: {link}\n\n/daily - Daily 1Rs\n/balance - Balance Check\n/withdraw - Withdraw Min 30Rs")

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    not_joined = is_joined_all(uid)
    if not_joined:
        markup = telebot.types.InlineKeyboardMarkup()
        for i in not_joined:
            markup.add(telebot.types.InlineKeyboardButton(f"📢 Join Channel {i+1}", url=ALL_LINKS[i]))
        markup.add(telebot.types.InlineKeyboardButton("✅ Check - Maine Join Kar Liya", callback_data="check_join"))
        bot.send_message(uid, "⚠️ Bot use karne ke liye 3no Channels join karo:", reply_markup=markup)
        return

    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not cur.fetchone():
        a = random.randint(2,9); b = random.randint(2,9)
        correct = a+b
        markup = telebot.types.InlineKeyboardMarkup(row_width=3)
        ref = message.text.split()[1] if len(message.text.split())>1 else '0'
        opts = [correct, correct+1, correct+2]
        random.shuffle(opts)
        for o in opts:
            if o == correct:
                markup.add(telebot.types.InlineKeyboardButton(str(o), callback_data=f"ok_{ref}"))
            else:
                markup.add(telebot.types.InlineKeyboardButton(str(o), callback_data="fail"))
        bot.send_message(uid, f"🤖 Robot Check: {a} + {b} =?", reply_markup=markup)
        return
    send_menu(uid)

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    uid = c.from_user.id
    if c.data == "check_join":
        if not is_joined_all(uid):
            try: bot.delete_message(c.message.chat.id, c.message.message_id)
            except: pass
            start(c.message)
        else:
            bot.answer_callback_query(c.id, "❌ Abhi bhi 3no join karna baki hai!")
    elif c.data.startswith("ok_"):
        ref = c.data.split("_")[1]
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
        if not cur.fetchone():
            cur.execute("INSERT INTO users VALUES (?,?,?,?,?)", (uid, 2, 0, '', ''))
            if ref!= '0' and ref!= str(uid):
                cur.execute("SELECT * FROM users WHERE user_id=?", (ref,))
                if cur.fetchone():
                    cur.execute("UPDATE users SET balance=balance+2, refer_count=refer_count+1 WHERE user_id=?", (ref,))
                    try: bot.send_message(int(ref), f"🔥 +2Rs! New user {uid} joined via your link.")
                    except: pass
            conn.commit()
        try: bot.delete_message(c.message.chat.id, c.message.message_id)
        except: pass
        bot.send_message(uid, "✅ Verified! 2Rs Bonus mila 🎉")
        send_menu(uid)
    elif c.data == "fail":
        bot.answer_callback_query(c.id, "❌ Galat jawab! /start dabao")
    elif c.data.startswith("paid_"):
        if uid!= ADMIN_ID: return
        _, target_id, amt = c.data.split("_")
        bot.send_message(int(target_id), f"✅ Withdraw Success!\n💸 {amt}Rs tumhare UPI pe bhej diya hai! Check karo.")
        bot.answer_callback_query(c.id, "User ko Paid ka msg bhej diya!")
        try: bot.delete_message(c.message.chat.id, c.message.message_id)
        except: pass

@bot.message_handler(commands=['daily'])
def daily(m):
    cur = conn.cursor()
    cur.execute("SELECT last_daily FROM users WHERE user_id=?", (m.from_user.id,))
    row = cur.fetchone()
    today = str(datetime.date.today())
    if row and row[0] == today:
        bot.send_message(m.from_user.id, "❌ Aaj ka daily le liya hai, kal aana!")
    else:
        cur.execute("UPDATE users SET balance=balance+1, last_daily=? WHERE user_id=?", (today, m.from_user.id))
        conn.commit()
        bot.send_message(m.from_user.id, "✅ Daily Bonus +1Rs! 💰")

@bot.message_handler(commands=['balance'])
def balance(m):
    send_menu(m.from_user.id)

@bot.message_handler(commands=['withdraw'])
def wd(m):
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id=?", (m.from_user.id,))
    row = cur.fetchone()
    if not row: return
    bal = row[0]
    if bal < 30:
        bot.send_message(m.chat.id, f"❌ Min Withdraw 30Rs! Tera balance {bal}Rs hai.")
        return
    bot.send_message(m.chat.id, "💳 Apna UPI ID bhejo (jaise: 9876543210@paytm):")
    bot.register_next_step_handler(m, ask_upi)

def ask_upi(msg):
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id=?", (msg.from_user.id,))
    bal = cur.fetchone()[0]
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ Paid Kar Diya", callback_data=f"paid_{msg.from_user.id}_{bal}"))
    bot.send_message(ADMIN_ID, f"💸 NEW WITHDRAW REQUEST\n\nUser ID: {msg.from_user.id}\nUsername: @{msg.from_user.username}\nAmount: {bal}Rs\nUPI: {msg.text}", reply_markup=markup)
    conn.execute("UPDATE users SET balance=0 WHERE user_id=?", (msg.from_user.id,))
    conn.commit()
    bot.send_message(msg.from_user.id, "✅ Withdraw request Admin ko bhej diya! 24hr me payment hoga.")

bot.infinity_polling()
