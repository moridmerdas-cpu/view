import telebot
from telebot import types
import json

# ---------- تنظیمات ----------
TOKEN = "8275637960:AAGVhL33pMp0vXRdgXzfaZqF5rYuHwDfrPw"
ADMIN_ID = 8588773170  # آیدی عددی مالک اصلی
DB_FILE = "db.json"
# ------------------------------

bot = telebot.TeleBot(TOKEN)

# ---------- بارگذاری دیتابیس ----------
try:
    with open(DB_FILE, "r") as f:
        db = json.load(f)
except:
    db = {"users": [], "groups": [], "channels": {}, "admins": []}

allowed_users = set(db["users"])
forward_groups = db["groups"]
user_channels = db["channels"]
admins = set(db["admins"])  # لیست ادمین‌ها

# ---------- ذخیره دیتابیس ----------
def save_db():
    db["users"] = list(allowed_users)
    db["groups"] = forward_groups
    db["channels"] = user_channels
    db["admins"] = list(admins)
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

# ---------- بررسی سطح دسترسی ----------
def is_owner(uid):
    return uid == ADMIN_ID

def is_admin(uid):
    return uid in admins or is_owner(uid)

# ---------- پنل ادمین ----------
def admin_panel(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ افزودن کاربر", "➖ حذف کاربر")
    kb.add("➕ افزودن گروه", "➖ حذف گروه")
    kb.add("➕ افزودن کانال", "➖ حذف کانال")
    kb.add("📋 لیست کل")
    if is_owner(uid):
        kb.add("➕ افزودن ادمین", "➖ حذف ادمین")
    return kb

# ---------- شروع ربات ----------
@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.from_user.id
    if is_admin(uid):
        bot.send_message(uid, "👑 پنل مدیریت", reply_markup=admin_panel(uid))
        return

    if uid not in allowed_users:
        bot.send_message(uid,
                         "❌ ربات برای شما فعال نیست\nبرای فعال‌سازی به @amele55 پیام دهید")
        return

    bot.send_message(uid, "✅ ربات فعال است\nلطفاً آیدی کانال خود را با @ ارسال کنید")

# ---------- دکمه‌ها ----------
@bot.message_handler(func=lambda m: True)
def handle_buttons(msg):
    uid = msg.from_user.id
    text = msg.text
    admin_name = msg.from_user.first_name  # اسم ادمین که عملیات انجام می‌ده

    if not is_admin(uid):
        # کاربران معمولی فقط آیدی کانال با @ میدن
        if text.startswith("@"):
            try:
                member = bot.get_chat_member(text, bot.get_me().id)
                user_channels[str(uid)] = text
                save_db()
                bot.send_message(uid, f"✅ کانال {text} ثبت شد")
            except:
                bot.send_message(uid, "❌ ربات ادمین نیست یا کانال اشتباه است")
        return

    # ادمین یا مالک
    if text == "➕ افزودن کاربر":
        bot.send_message(uid, "آیدی عددی کاربر را ارسال کنید برای افزودن")
        bot.register_next_step_handler(msg, lambda m: add_user(m, admin_name))

    elif text == "➖ حذف کاربر":
        bot.send_message(uid, "آیدی عددی کاربر را ارسال کنید برای حذف")
        bot.register_next_step_handler(msg, lambda m: remove_user(m, admin_name))

    elif text == "➕ افزودن گروه":
        bot.send_message(uid, "لطفاً لینک گروه با @ ارسال کنید")
        bot.register_next_step_handler(msg, lambda m: add_group(m, admin_name))

    elif text == "➖ حذف گروه":
        bot.send_message(uid, "لطفاً لینک گروه با @ ارسال کنید برای حذف")
        bot.register_next_step_handler(msg, lambda m: remove_group(m, admin_name))

    elif text == "➕ افزودن کانال":
        bot.send_message(uid, "لطفاً لینک کانال با @ ارسال کنید (ربات باید ادمین باشد)")
        bot.register_next_step_handler(msg, lambda m: add_channel(m, admin_name))

    elif text == "➖ حذف کانال":
        bot.send_message(uid, "لطفاً لینک کانال با @ برای حذف ارسال کنید")
        bot.register_next_step_handler(msg, lambda m: remove_channel(m, admin_name))

    elif text == "📋 لیست کل":
        users = "\n".join([str(u) for u in allowed_users]) or "هیچ کاربری ثبت نشده"
        groups = "\n".join(forward_groups) or "هیچ گروهی ثبت نشده"
        channels = "\n".join(user_channels.values()) or "هیچ کانالی ثبت نشده"
        admins_list = "\n".join([str(a) for a in admins]) or "هیچ ادمینی ثبت نشده"
        bot.send_message(uid, f"👤 کاربران:\n{users}\n\n👥 گروه‌ها:\n{groups}\n\n📢 کانال‌ها:\n{channels}\n\n🛡️ ادمین‌ها:\n{admins_list}")

    # افزودن/حذف ادمین فقط برای مالک
    elif text == "➕ افزودن ادمین" and is_owner(uid):
        bot.send_message(uid, "آیدی عددی کاربر را برای ادمین شدن ارسال کنید")
        bot.register_next_step_handler(msg, add_admin)
    elif text == "➖ حذف ادمین" and is_owner(uid):
        bot.send_message(uid, "آیدی عددی ادمین را برای حذف ارسال کنید")
        bot.register_next_step_handler(msg, remove_admin)

# ---------- توابع افزودن/حذف ----------
def add_user(msg, admin_name):
    try:
        uid = int(msg.text)
        allowed_users.add(uid)
        save_db()
        bot.send_message(msg.from_user.id, f"✅ کاربر {uid} اضافه شد")
        bot.send_message(ADMIN_ID, f"✅ کاربر {uid} توسط ادمین {admin_name} اضافه شد")
    except:
        bot.send_message(msg.from_user.id, "❌ لطفاً آیدی عددی صحیح وارد کنید")

def remove_user(msg, admin_name):
    try:
        uid = int(msg.text)
        if uid in allowed_users:
            allowed_users.remove(uid)
            save_db()
            bot.send_message(msg.from_user.id, f"❌ کاربر {uid} حذف شد")
            bot.send_message(ADMIN_ID, f"❌ کاربر {uid} توسط ادمین {admin_name} حذف شد")
        else:
            bot.send_message(msg.from_user.id, "کاربر یافت نشد")
    except:
        bot.send_message(msg.from_user.id, "❌ لطفاً آیدی عددی صحیح وارد کنید")

def add_group(msg, admin_name):
    text = msg.text.strip()
    if not text.startswith("@"):
        bot.send_message(msg.from_user.id, "❌ لینک گروه باید با @ شروع شود")
        return
    try:
        bot.get_chat_member(text, bot.get_me().id)
        if text not in forward_groups:
            forward_groups.append(text)
            save_db()
            bot.send_message(msg.from_user.id, f"✅ گروه {text} اضافه شد")
            bot.send_message(ADMIN_ID, f"✅ گروه {text} توسط ادمین {admin_name} اضافه شد")
    except:
        bot.send_message(msg.from_user.id, "❌ ربات ادمین نیست یا گروه اشتباه است")

def remove_group(msg, admin_name):
    text = msg.text.strip()
    if text in forward_groups:
        forward_groups.remove(text)
        save_db()
        bot.send_message(msg.from_user.id, f"❌ گروه {text} حذف شد")
        bot.send_message(ADMIN_ID, f"❌ گروه {text} توسط ادمین {admin_name} حذف شد")
    else:
        bot.send_message(msg.from_user.id, "گروه یافت نشد")

def add_channel(msg, admin_name):
    text = msg.text.strip()
    if not text.startswith("@"):
        bot.send_message(msg.from_user.id, "❌ لینک کانال باید با @ شروع شود")
        return
    try:
        bot.get_chat_member(text, bot.get_me().id)
        user_channels[str(ADMIN_ID)] = text
        save_db()
        bot.send_message(msg.from_user.id, f"✅ کانال {text} اضافه شد")
        bot.send_message(ADMIN_ID, f"✅ کانال {text} توسط ادمین {admin_name} اضافه شد")
    except:
        bot.send_message(msg.from_user.id, "❌ ربات ادمین نیست یا کانال اشتباه است")

def remove_channel(msg, admin_name):
    text = msg.text.strip()
    if str(ADMIN_ID) in user_channels and user_channels[str(ADMIN_ID)] == text:
        del user_channels[str(ADMIN_ID)]
        save_db()
        bot.send_message(msg.from_user.id, f"❌ کانال {text} حذف شد")
        bot.send_message(ADMIN_ID, f"❌ کانال {text} توسط ادمین {admin_name} حذف شد")
    else:
        bot.send_message(msg.from_user.id, "کانال یافت نشد یا ثبت نشده")

# ---------- افزودن/حذف ادمین ----------
def add_admin(msg):
    try:
        uid = int(msg.text)
        if uid != ADMIN_ID:
            admins.add(uid)
            save_db()
            bot.send_message(ADMIN_ID, f"✅ ادمین {uid} اضافه شد")
    except:
        bot.send_message(ADMIN_ID, "❌ لطفاً آیدی عددی صحیح وارد کنید")

def remove_admin(msg):
    try:
        uid = int(msg.text)
        if uid in admins:
            admins.remove(uid)
            save_db()
            bot.send_message(ADMIN_ID, f"❌ ادمین {uid} حذف شد")
        else:
            bot.send_message(ADMIN_ID, "ادمین یافت نشد")
    except:
        bot.send_message(ADMIN_ID, "❌ لطفاً آیدی عددی صحیح وارد کنید")

# ---------- فوروارد پیام کانال به گروه‌ها ----------
@bot.channel_post_handler()
def forward(msg):
    for group in forward_groups:
        try:
            bot.forward_message(group, msg.chat.id, msg.message_id)
        except:
            pass

# ---------- اجرا ----------
bot.infinity_polling()
