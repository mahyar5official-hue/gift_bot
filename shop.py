#!/usr/bin/env python3
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import GIFTS, STAR_PACKS, PREMIUM_PLANS, get_username, CHANNEL_URL, calc_toman, calc_dollar

async def check_expiry_and_send_menu(query_or_msg, user, context, bot):
    import time
    if not context.user_data.get("last_activity"): context.user_data["last_activity"] = time.time(); return False
    if time.time() - context.user_data["last_activity"] < 300: context.user_data["last_activity"] = time.time(); return False
    msg_id = context.user_data.get("menu_message_id")
    if msg_id:
        try: await bot.delete_message(chat_id=user.id, message_id=msg_id)
        except: pass
    if hasattr(query_or_msg, "delete"):
        try: await query_or_msg.delete()
        except: pass
    from shop import main_menu
    from config import is_admin
    text = f"سلام {user.first_name} 👋\n\n🛒 <b>خرید استارز، گیفت و تلگرام پریمیوم به ساده‌ترین و سریع‌ترین روش ممکن!</b>\n\n👇 یکی از دکمه‌های زیر را انتخاب کنید"
    new_msg = await bot.send_message(chat_id=user.id, text=text, reply_markup=main_menu(user.id, is_admin), parse_mode="HTML")
    context.user_data["last_activity"] = time.time(); context.user_data["menu_message_id"] = new_msg.message_id; return True

async def check_user_joined(bot, user_id):
    from config import REQUIRED_CHANNEL
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e: print(f"[check_join] err: {e}"); return True

def force_join_keyboard():
    from config import CHANNEL_URL
    return InlineKeyboardMarkup([[InlineKeyboardButton("📣 عضویت در کانال", url=CHANNEL_URL, style="primary")], [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join", style="success")]])

def main_menu(uid=None, is_admin_func=None):
    buttons = [[InlineKeyboardButton("🛍 منوی فروشگاه", callback_data="shop", style="primary")], [InlineKeyboardButton("👤 پروفایل من", callback_data="profile")], [InlineKeyboardButton("💬 پشتیبانی", url="https://t.me/BOnlineStars?direct"), InlineKeyboardButton("❓ سوالات متداول", callback_data="faq")], [InlineKeyboardButton("📣 کانال ما", url=CHANNEL_URL)]]
    if uid and is_admin_func and is_admin_func(uid):
        from config import is_owner
        buttons.append([InlineKeyboardButton("👑 پنل مالک" if is_owner(uid) else "🛠 پنل مدیریت", callback_data="adm_panel", style="success")])
    return InlineKeyboardMarkup(buttons)

def shop_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⭐ استارز", callback_data="buy_stars")], [InlineKeyboardButton("⚡ پرمیوم", callback_data="buy_premium"), InlineKeyboardButton("🎁 گیفت‌ها", callback_data="buy_gifts")], [InlineKeyboardButton("💳 شارژ ولت تلگرام", callback_data="buy_wallet", style="primary")], [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]])

def gifts_menu(selected=None, count=1, recipient="—"):
    rows, row = [], []
    for key, (name, price) in GIFTS.items():
        row.append(InlineKeyboardButton(name, callback_data=f"gift_{key}", style="primary" if key == selected else None))
        if len(row) == 2: rows.append(row); row = []
    if row: rows.append(row)
    rows += [[InlineKeyboardButton("✏️ تعداد: " + str(count), callback_data="gift_set_count", style="primary")], [InlineKeyboardButton("✏️ گیرنده: " + recipient, callback_data="gift_set_recipient", style="primary")], [InlineKeyboardButton("📝 نوشتن کپشن", callback_data="gift_set_caption", style="primary")], [InlineKeyboardButton("🔙 بازگشت", callback_data="shop", style="danger"), InlineKeyboardButton("👆 ادامه", callback_data="gift_confirm", style="success")]]
    return InlineKeyboardMarkup(rows)

def stars_menu(user, selected_amount=100, recipient=None):
    recipient_clean = (recipient or get_username(user)).lstrip("@")
    amount_list = list(STAR_PACKS.keys()); rows = []
    for i in range(0, len(amount_list), 3):
        rows.append([InlineKeyboardButton(f"⭐ {amt}", callback_data=f"stars_{amt}", style="primary" if amt == selected_amount else None) for amt in amount_list[i:i+3]])
    rows += [[InlineKeyboardButton("✏️ تعداد دلخواه", callback_data="stars_custom", style="success")], [InlineKeyboardButton(f"تعداد: {selected_amount}", callback_data="stars_set_count", style="primary")], [InlineKeyboardButton(f"✏️ گیرنده: {recipient_clean}", callback_data="stars_set_recipient", style="primary")], [InlineKeyboardButton("🔙 بازگشت", callback_data="shop", style="danger"), InlineKeyboardButton("👆 ادامه", callback_data="stars_confirm", style="success")]]
    return InlineKeyboardMarkup(rows)

def premium_menu(selected=None):
    rows, row = [], []
    for months in PREMIUM_PLANS.keys():
        row.append(InlineKeyboardButton("⚡ " + str(months) + " ماهه", callback_data="premium_" + str(months), style="primary" if selected == months else None))
        if len(row) == 2: rows.append(row); row = []
    if row: rows.append(row)
    return rows

def stars_text(user, amount, toman, dollar, recipient=None):
    from config import get_star_pack_price, get_star_price, STAR_PACKS
    username = get_username(user); recipient = recipient or username
    toman = get_star_pack_price(amount) if amount in STAR_PACKS else amount * get_star_price()
    def make_link(u):
        u = str(u).strip().lstrip("@")
        return '<a href="tg://resolve?domain=' + u + '">' + u + '</a>' if u and u != "—" else "—"
    return "⭐ <b>خرید استارز تلگرام</b>\n\n👤 نام کاربری: " + make_link(username) + "\n⭐ تعداد: <b>" + str(amount) + "</b>\n💵 مبلغ: <b>" + f"{toman:,}" + "</b> تومان 💸\n🎁 گیرنده: " + make_link(recipient) + "\n\n📍 آیکون‌های دارای ✏️ قابل تغییر هستند، با کلیک روشون\n\n🔽 گیرنده و تعداد را انتخاب کرده، سپس روی دکمه ادامه کلیک کنید."
