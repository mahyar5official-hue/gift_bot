#!/usr/bin/env python3
import threading
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home(): return "Bot is alive!"

def run_flask(): app.run(host="0.0.0.0", port=7860)

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN, log_event, is_admin, load_logs, register_pending_referral, find_uid_by_ref_code, get_or_create_ref_code, load_referrals, save_referrals
from shop import main_menu, check_user_joined, force_join_keyboard
from handlers.btn_handler import btn_handler
from messages import msg_handler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def mark_ref_processed(uid):
    d = load_referrals(); d.setdefault("processed_refs", {})[str(uid)] = True; save_referrals(d)
def is_ref_processed(uid): return load_referrals().get("processed_refs", {}).get(str(uid), False)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logs_before = load_logs(); is_new_user = str(user.id) not in logs_before.get("users", {})
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        if arg.startswith("ref_") or arg.startswith("ref-"):
            ref_code = arg.replace("ref_", "").replace("ref-", "")
            inviter_id = int(ref_code) if ref_code.isdigit() else find_uid_by_ref_code(ref_code)
            if inviter_id and inviter_id != user.id and is_new_user:
                track = register_pending_referral(user.id, inviter_id)
                if track:
                    try: await context.bot.send_message(chat_id=inviter_id, text="🎉 <b>دعوت جدید!</b>\n\n👤 " + (user.full_name or user.first_name) + " با لینک تو وارد ربات شد.\n🎫 کد رهگیری: <code>" + track + "</code>\n\n⚠️ <b>هنوز استارزی بهت اضافه نشده!</b>\n💡 به محض اینکه این کاربر اولین خریدش رو انجام بده، استارز بهت داده می‌شه.", parse_mode="HTML")
                    except: pass
    log_event(user, "/start"); get_or_create_ref_code(user.id)
    for k in ["gift_count", "gift_selected", "recipient", "stars_selected", "custom_toman", "custom_dollar", "premium_selected"]: context.user_data.pop(k, None)
    text = f"سلام {user.first_name} 👋\n\n🛒 <b>خرید استارز، گیفت و تلگرام پریمیوم به ساده‌ترین و سریع‌ترین روش ممکن!</b>\n\n👇 یکی از دکمه‌های زیر را انتخاب کنید"
    old_menu_id = context.user_data.get("menu_message_id")
    if old_menu_id:
        try: await context.bot.delete_message(chat_id=user.id, message_id=old_menu_id)
        except: pass
    import time; msg = await update.message.reply_text(text, reply_markup=main_menu(user.id, is_admin), parse_mode="HTML")
    context.user_data["last_activity"] = time.time(); context.user_data["menu_message_id"] = msg.message_id

async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(f"🆔 {update.effective_user.id}")

async def error_handler(update, context):
    from telegram.error import TimedOut, NetworkError
    import traceback
    err = context.error
    if isinstance(err, (TimedOut, NetworkError)):
        print(f"⚠️ خطای شبکه: {err}")
    else:
        print(f"❌ خطای ربات: {err}")
        traceback.print_exc()

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CallbackQueryHandler(btn_handler))
    from messages import photo_handler
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))
    threading.Thread(target=run_flask, daemon=True).start()
    print("🤖 ربات روشن شد!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
