import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import PREMIUM_PLANS, get_username, get_premium_price, get_premium_dollar
from shop import premium_menu
logger = logging.getLogger(__name__)
NL = chr(10)

def _user_link_clean(u):
    u = str(u).strip().lstrip("@")
    return '<a href="tg://resolve?domain=' + u + '">' + u + '</a>' if u and u != "—" else "—"

async def handle_premium(query, data, user, context):
    if data == "buy_premium":
        selected = context.user_data.get("premium_selected")
        recipient_clean = context.user_data.get("recipient", get_username(user)).lstrip("@")
        if selected and selected in PREMIUM_PLANS:
            toman = get_premium_price(selected)
            text = "⚡ <b>خرید تلگرام پریمیوم</b>" + NL + NL + "👤 نام کاربری: " + get_username(user) + NL + "🎁 گیرنده: " + _user_link_clean(recipient_clean) + NL + "🕓 مدت زمان: <b>" + str(selected) + " ماه</b>" + NL + "💵 مبلغ: <b>" + f"{toman:,}" + "</b> تومان 💸" + NL + NL + "📍 آیکون‌های دارای ✏️ قابل تغییر هستند، با کلیک روشون" + NL + NL + "🔽 مدت زمان و گیرنده را انتخاب کرده، سپس روی دکمه ادامه کلیک کنید."
        else:
            text = "⚡ <b>پلن‌های تلگرام پریمیوم</b>" + NL + NL + "👇 مدت زمان را انتخاب کنید:"
        rows = premium_menu(selected)
        rows.append([InlineKeyboardButton("✏️ گیرنده: " + recipient_clean, callback_data="premium_set_recipient", style="primary")])
        rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="shop", style="danger"), InlineKeyboardButton("👆 ادامه", callback_data="premium_confirm", style="success")])
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
        return True
    if data.startswith("premium_") and data[8:].isdigit():
        months = int(data[8:])
        if months in PREMIUM_PLANS: context.user_data["premium_selected"] = months
        selected = context.user_data.get("premium_selected")
        recipient_clean = context.user_data.get("recipient", get_username(user)).lstrip("@")
        toman = get_premium_price(selected)
        text = "⚡ <b>خرید تلگرام پریمیوم</b>" + NL + NL + "👤 نام کاربری: " + get_username(user) + NL + "🎁 گیرنده: " + _user_link_clean(recipient_clean) + NL + "🕓 مدت زمان: <b>" + str(selected) + " ماه</b>" + NL + "💵 مبلغ: <b>" + f"{toman:,}" + "</b> تومان 💸" + NL + NL + "📍 آیکون‌های دارای ✏️ قابل تغییر هستند، با کلیک روشون" + NL + NL + "🔽 مدت زمان و گیرنده را انتخاب کرده، سپس روی دکمه ادامه کلیک کنید."
        rows = premium_menu(selected)
        rows.append([InlineKeyboardButton("✏️ گیرنده: " + recipient_clean, callback_data="premium_set_recipient", style="primary")])
        rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="shop", style="danger"), InlineKeyboardButton("👆 ادامه", callback_data="premium_confirm", style="success")])
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
        return True
    if data == "premium_confirm":
        months = context.user_data.get("premium_selected")
        if not months or months not in PREMIUM_PLANS: await query.answer("❌ اول یه پلن انتخاب کن!", show_alert=True); return True
        recipient = context.user_data.get("recipient", get_username(user))
        toman = get_premium_price(months)
        context.user_data["pending_purchase"] = {"type": "premium", "name": "تلگرام پریمیوم " + str(months) + " ماهه", "count": 1, "price_toman": toman, "recipient": recipient}
        from shop_handlers import payment_text, payment_keyboard
        await query.edit_message_text(payment_text(title="⚡ تلگرام پریمیوم " + str(months) + " ماهه", amount_toman=toman, recipient=recipient), parse_mode="HTML", reply_markup=payment_keyboard(toman))
        return True
    return False
