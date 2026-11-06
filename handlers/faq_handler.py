import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
logger = logging.getLogger(__name__)
NL = chr(10)

FAQ_ITEMS = {
    "q1": {"q": "🛒 چطور خرید کنم؟", "a": "🛒 <b>راهنمای خرید</b>" + NL + "━━━━━━━━━━━━━━━━" + NL + NL + "1️⃣ از منوی اصلی روی <b>🛍 منوی فروشگاه</b> بزن" + NL + "2️⃣ محصول مورد نظر رو انتخاب کن" + NL + "3️⃣ تعداد و گیرنده رو مشخص کن" + NL + "4️⃣ روی <b>👆 ادامه</b> بزن" + NL + "5️⃣ مبلغ رو به کارت واریز کن" + NL + "6️⃣ فیش رو برای پشتیبانی بفرست" + NL + NL + "✅ بعد از تایید، محصول به گیرنده تحویل داده می‌شه."},
    "q2": {"q": "⏱ چقدر طول می‌کشه؟", "a": "⏱ <b>زمان تحویل</b>" + NL + "━━━━━━━━━━━━━━━━" + NL + NL + "🟢 <b>استارز:</b> ۱ تا ۵ دقیقه" + NL + "🟢 <b>گیفت‌ها:</b> ۱ تا ۵ دقیقه" + NL + "🟡 <b>تلگرام پرمیوم:</b> ۵ تا ۳۰ دقیقه" + NL + NL + "📌 <i>در ساعات شلوغی ممکنه کمی بیشتر طول بکشه.</i>"},
    "q3": {"q": "💳 چطور پرداخت کنم؟", "a": "💳 <b>روش‌های پرداخت</b>" + NL + "━━━━━━━━━━━━━━━━" + NL + NL + "✅ کارت به کارت" + NL + "✅ رمزارز (TON)"},
    "q4": {"q": "🎁 استارز رایگان چیه؟", "a": "🎁 <b>سیستم استارز رایگان</b>" + NL + "━━━━━━━━━━━━━━━━" + NL + NL + "💫 دوستات رو دعوت کن و استارز رایگان بگیر!"},
    "q5": {"q": "🔗 لینک دعوتم رو کجا ببینم؟", "a": "🔗 <b>لینک دعوت اختصاصی</b>" + NL + "━━━━━━━━━━━━━━━━" + NL + NL + "از منوی اصلی برو به: <b>🎁 استارز رایگان</b>"},
    "q6": {"q": "🎫 کد رهگیری چیه؟", "a": "🎫 <b>کد رهگیری سفارش</b>" + NL + "━━━━━━━━━━━━━━━━" + NL + NL + "بعد از هر خرید، یه کد رهگیری بهت داده می‌شه."},
    "q7": {"q": "💬 پشتیبانی چطور کار می‌کنه؟", "a": "💬 <b>پشتیبانی ربات</b>" + NL + "━━━━━━━━━━━━━━━━" + NL + NL + "از منوی اصلی روی <b>💬 پشتیبانی</b> بزن."},
}

async def handle_faq(query, data, user, context):
    if data == "faq":
        text = "❓ <b>سوالات متداول</b>" + NL + "━━━━━━━━━━━━━━━━" + NL + NL + "👇 یکی از سوالات زیر رو انتخاب کن:"
        rows, row = [], []
        for key, item in FAQ_ITEMS.items():
            row.append(InlineKeyboardButton(item["q"], callback_data="faq_" + key))
            if len(row) == 1: rows.append(row); row = []
        rows.append([InlineKeyboardButton("💬 پشتیبانی", callback_data="support", style="primary")])
        rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu", style="danger")])
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
        return True
    if data.startswith("faq_q"):
        key = data.replace("faq_", "")
        if key in FAQ_ITEMS:
            await query.edit_message_text(FAQ_ITEMS[key]["a"], parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 پشتیبانی", callback_data="support", style="primary")], [InlineKeyboardButton("🔙 سوالات دیگه", callback_data="faq", style="danger")]]))
        return True
    return False
