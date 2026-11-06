import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import get_user_stars, get_user_ref_count, REFERRAL_REWARD, REFERRAL_MIN_WITHDRAW, REFERRAL_MILESTONE, get_or_create_ref_code, get_display_name
logger = logging.getLogger(__name__)
NL = chr(10)

async def handle_referral(query, data, user, context):
    if data == "free_stars":
        bot_username = (await query.get_bot().get_me()).username
        stars = get_user_stars(user.id); refs = get_user_ref_count(user.id)
        ref_code = get_or_create_ref_code(user.id); ref_link = "https://t.me/" + bot_username + "?start=ref_" + ref_code
        progress = min(stars, REFERRAL_MIN_WITHDRAW); bar = "🟩" * int((progress / REFERRAL_MIN_WITHDRAW) * 10) + "⬜" * (10 - int((progress / REFERRAL_MIN_WITHDRAW) * 10))
        can_withdraw = stars >= REFERRAL_MIN_WITHDRAW; milestone_progress = len(refs) % REFERRAL_MILESTONE
        next_milestone = REFERRAL_MILESTONE - milestone_progress if milestone_progress != 0 or len(refs) == 0 else 0
        text = "🎁 <b>استارز رایگان</b>" + NL + "━━━━━━━━━━━━━━━━" + NL + NL + "💫 دوستانت رو دعوت کن و استارز رایگان بگیر!" + NL + NL + "👥 <b>هر دعوت موفق:</b> +" + str(REFERRAL_REWARD) + " استارز" + NL + "🎁 <b>هر " + str(REFERRAL_MILESTONE) + " دعوت موفق:</b> یه گیفت جایزه!" + NL + NL + "⚠️ <i>دعوت فقط وقتی حساب می‌شه که دوستت اولین خریدش رو انجام بده</i>" + NL + NL + "━━━━━━━━━━━━━━━━" + NL + "📊 <b>وضعیت تو:</b>" + NL + "⭐ موجودی: <b>" + str(stars) + " استارز</b>" + NL + "👥 دعوت‌های موفق: <b>" + str(len(refs)) + " نفر</b>" + NL + NL + "🎯 <b>پیشرفت تا برداشت:</b>" + NL + bar + " " + str(stars) + "/" + str(REFERRAL_MIN_WITHDRAW) + NL + NL + "🎁 <b>پیشرفت تا گیفت جایزه:</b>" + NL + "🏆 " + str(milestone_progress) + "/" + str(REFERRAL_MILESTONE) + " دعوت موفق" + NL + "🎯 " + str(next_milestone) + " دعوت دیگه تا جایزه!" + NL + NL + "🔗 <b>لینک دعوت اختصاصی تو:</b>" + NL + "<code>" + ref_link + "</code>" + NL + NL + "🎫 کد دعوت تو: <code>" + ref_code + "</code>"
        rows = [[InlineKeyboardButton("🔗 اشتراک‌گذاری لینک", url="https://t.me/share/url?url=" + ref_link + "&text=" + "آنلاین استارز راحت و سریع")], [InlineKeyboardButton("🔄 آپدیت", callback_data="free_stars", style="primary")]]
        if can_withdraw: rows.append([InlineKeyboardButton("💸 برداشت " + str(stars) + " استارز", callback_data="withdraw_stars", style="success")])
        rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu", style="danger")])
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
        return True
    if data == "withdraw_stars":
        stars = get_user_stars(user.id)
        if stars < REFERRAL_MIN_WITHDRAW: await query.answer("❌ حداقل " + str(REFERRAL_MIN_WITHDRAW) + " استارز!", show_alert=True); return True
        from config import create_ticket, get_ticket, send_ticket_to_admins
        msg = "💸 درخواست برداشت استارز" + NL + NL + "👤 کاربر: " + get_display_name(user) + NL + "🆔 آیدی: " + str(user.id) + NL + "⭐ موجودی: " + str(stars) + " استارز"
        tid = create_ticket(user_id=user.id, user_name=get_display_name(user), user_username=user.username or "", message=msg)
        await send_ticket_to_admins(context.bot, get_ticket(tid), extra_text="🔔 <b>درخواست برداشت استارز</b>" + NL + NL)
        await query.edit_message_text("✅ <b>درخواست برداشت ثبت شد</b>" + NL + NL + "🎫 شماره: <code>#" + str(tid) + "</code>" + NL + "⭐ موجودی: <b>" + str(stars) + " استارز</b>" + NL + NL + "🛠 به زودی ادمین بررسی می‌کنه.", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="free_stars", style="danger")]]))
        return True
    return False
