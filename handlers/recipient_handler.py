import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
logger = logging.getLogger(__name__)
NL = chr(10)

async def handle_recipient(query, data, user, context):
    if data in ("stars_set_recipient", "gift_set_recipient", "premium_set_recipient"):
        context.user_data["waiting_recipient"] = True
        if data == "stars_set_recipient": context.user_data["recipient_from"] = "stars"; back = "buy_stars"
        elif data == "gift_set_recipient": context.user_data["recipient_from"] = "gift"; back = "buy_gifts"
        else: context.user_data["recipient_from"] = "premium"; back = "buy_premium"
        await query.edit_message_text("✏️ <b>نام کاربری را وارد کنید:</b>" + NL + "اگر برای خودتان است، عبارت <code>me</code> را تایپ کنید", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data=back, style="danger")]]))
        return True
    return False
