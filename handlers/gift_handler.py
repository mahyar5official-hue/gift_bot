import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import GIFTS, get_username, get_gift_price
from shop import gifts_menu
logger = logging.getLogger(__name__)
NL = chr(10)

def _user_link(user):
    u = get_username(user).strip().lstrip("@")
    return '<a href="tg://resolve?domain=' + u + '">' + u + '</a>' if u and u != "—" else "—"

def _gift_text(user, gift_key, count, context=None):
    name, price = GIFTS[gift_key]
    gift_toman = get_gift_price(gift_key) * count
    emoji = name.split(" ", 1)[0]
    caption = context.user_data.get("gift_caption", "") if context else ""
    return "🎁 <b>خرید گیفت تلگرام</b>" + NL + NL + "👤 نام کاربری: " + _user_link(user) + NL + "🎁 گیرنده: " + _user_link(user) + NL + "🎁 تعداد: " + str(count) + "x " + emoji + NL + "💵 مبلغ: <b>" + f"{gift_toman:,}" + "</b> تومان 💸" + NL + "📝 کپشن: " + (caption or "-") + NL + NL + "📍 آیکون‌های دارای ✏️ قابل تغییر هستند، با کلیک روشون" + NL + NL + "🔽 گیرنده و تعداد را انتخاب کرده، سپس روی دکمه ادامه کلیک کنید."

async def handle_gift(query, data, user, context):
    if data == "buy_gifts":
        selected = context.user_data.get("gift_selected")
        if not selected or selected not in GIFTS:
            selected = list(GIFTS.keys())[0]; context.user_data["gift_selected"] = selected
        count = context.user_data.get("gift_count", 1)
        recipient_clean = context.user_data.get("recipient", get_username(user)).lstrip("@")
        await query.edit_message_text(_gift_text(user, selected, count, context), parse_mode="HTML", reply_markup=gifts_menu(selected, count, recipient_clean))
        return True
    if data.startswith("gift_") and data[5:] in GIFTS:
        gift_key = data.replace("gift_", ""); context.user_data["gift_selected"] = gift_key
        count = context.user_data.get("gift_count", 1)
        recipient_clean = context.user_data.get("recipient", get_username(user)).lstrip("@")
        await query.edit_message_text(_gift_text(user, gift_key, count, context), parse_mode="HTML", reply_markup=gifts_menu(gift_key, count, recipient_clean))
        return True
    if data == "gift_set_count":
        context.user_data["waiting_gift_count"] = True
        await query.edit_message_text("✏️ <b>تعداد گیفت</b>" + NL + NL + "🔢 عدد مورد نظر رو بفرست:" + NL + NL + "⚠️ حداقل: <b>1</b>" + NL + "💡 مثال: <code>3</code>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="buy_gifts", style="danger")]]))
        return True
    if data == "gift_confirm":
        gift_key = context.user_data.get("gift_selected")
        if not gift_key or gift_key not in GIFTS: await query.answer("❌ اول یه گیفت انتخاب کن!", show_alert=True); return True
        recipient = context.user_data.get("recipient", get_username(user))
        count = context.user_data.get("gift_count", 1); name, price = GIFTS[gift_key]
        toman = get_gift_price(gift_key) * count; caption = context.user_data.get("gift_caption", "")
        context.user_data["pending_purchase"] = {"type": "gift", "name": name + " × " + str(count), "count": count, "price_toman": toman, "recipient": recipient, "caption": caption}
        from shop_handlers import payment_text, payment_keyboard
        extra = "⭐ <b>هزینه:</b> " + str(price * count) + " استارز" + NL + ("📝 <b>کپشن:</b> " + caption + NL if caption else "")
        await query.edit_message_text(payment_text(title=name + " × " + str(count), amount_toman=toman, recipient=recipient, extra_lines=extra), parse_mode="HTML", reply_markup=payment_keyboard(toman))
        return True
    return False
