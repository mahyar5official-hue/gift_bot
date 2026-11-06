#!/usr/bin/env python3
import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import calc_toman
from shop import shop_menu

from handlers.gift_handler import handle_gift
from handlers.stars_handler import handle_stars
from handlers.premium_handler import handle_premium
from handlers.profile_handler import handle_profile
from handlers.referral_handler import handle_referral
from handlers.recipient_handler import handle_recipient
from handlers.faq_handler import handle_faq

logger = logging.getLogger(__name__)
NL = chr(10)

def format_toman(amount): return f"{amount:,}"

CARD_NUMBER = "6219861482441127"

def _make_link(u):
    u = str(u).strip().lstrip("@")
    return '<a href="tg://resolve?domain=' + u + '">' + u + '</a>' if u and u != "—" else "—"

def payment_text(title, amount_toman, recipient=None, extra_lines="", track_code=None):
    amount_rial = amount_toman * 10
    text = "💳 <b>پرداخت</b>" + NL + "━━━━━━━━━━━━━━━━" + NL + NL + "📦 <b>محصول:</b> " + title + NL
    if recipient: text += "🎁 <b>گیرنده:</b> " + _make_link(recipient) + NL
    if extra_lines: text += extra_lines
    text += NL + "💰 <b>مبلغ قابل پرداخت:</b>" + NL + "<code>" + f"{amount_rial:,}" + "</code> <b>ریال</b>" + NL + NL
    text += "💳 <b>شماره کارت:</b>" + NL + "<code>" + CARD_NUMBER + "</code>" + NL + NL
    text += "📌 <i>برای کپی، روی مبلغ یا شماره کارت ضربه بزن</i>" + NL + NL + "━━━━━━━━━━━━━━━━" + NL
    text += "✅ بعد از واریز، روی دکمه <b>📩 ارسال رسید</b> بزن و فیش رو بفرست." + NL
    text += "🛠 بعد از تایید ادمین، محصول برات ارسال می‌شه."
    return text

def payment_keyboard(amount_toman=0):
    return InlineKeyboardMarkup([[InlineKeyboardButton("📩 ارسال رسید", callback_data="support", style="success")], [InlineKeyboardButton("🔙 بازگشت", callback_data="shop", style="danger")]])

async def handle_shop(query, data, user, context):
    if data == "shop":
        for k in ["gift_count", "gift_selected", "recipient", "stars_selected", "custom_toman", "custom_dollar", "premium_selected"]:
            context.user_data.pop(k, None)
        await query.edit_message_text("🛍 منوی فروشگاه" + NL + NL + "محصول مورد نظر خود را برای خرید انتخاب کنید.", reply_markup=shop_menu())
        return True
    if await handle_gift(query, data, user, context): return True
    if await handle_stars(query, data, user, context): return True
    if await handle_premium(query, data, user, context): return True
    if await handle_profile(query, data, user, context): return True
    if await handle_referral(query, data, user, context): return True
    if await handle_recipient(query, data, user, context): return True
    if await handle_faq(query, data, user, context): return True
    return False
