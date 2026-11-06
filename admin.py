from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, load_logs, load_admins, GIFTS, STAR_PACKS, PREMIUM_PLANS, get_gift_price, get_star_pack_price, get_premium_price, get_star_price
from datetime import datetime, timezone, timedelta

def admin_menu(uid=None):
    buttons = [[InlineKeyboardButton("📊 آمار ربات", callback_data="adm_stats")], [InlineKeyboardButton("📋 لاگ کاربران", callback_data="adm_logs")], [InlineKeyboardButton("👥 لیست کاربران", callback_data="adm_users")], [InlineKeyboardButton("🎁 تنظیم قیمت گیفت‌ها", callback_data="adm_gift_price", style="primary")], [InlineKeyboardButton("⭐ تنظیم قیمت پکیج‌های استارز", callback_data="adm_stars_price", style="primary")], [InlineKeyboardButton("⚡ تنظیم قیمت پرمیوم", callback_data="adm_premium_price", style="primary")]]
    if uid and uid == OWNER_ID:
        buttons.append([InlineKeyboardButton("📢 پیام همگانی", callback_data="adm_broadcast", style="success")])
        buttons.append([InlineKeyboardButton("💳 تنظیمات شارژ ولت", callback_data="adm_wallet_config", style="primary")])
        buttons.append([InlineKeyboardButton("👑 مدیریت ادمین‌ها", callback_data="adm_manage", style="primary")])
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

def admins_manage_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("➕ افزودن ادمین", callback_data="adm_add", style="success")], [InlineKeyboardButton("➖ حذف ادمین", callback_data="adm_remove", style="danger")], [InlineKeyboardButton("📋 لیست ادمین‌ها", callback_data="adm_list")], [InlineKeyboardButton("🔙 بازگشت", callback_data="adm_panel")]])

def format_admin_list():
    admins = load_admins(); text = "👥 <b>لیست ادمین‌ها</b>\n━━━━━━━━━━━━━━━━\n\n" + f"👑 مالک: <code>{OWNER_ID}</code>\n\n"
    if not admins: return text + "📭 هیچ ادمینی اضافه نشده."
    text += f"<b>ادمین‌ها ({len(admins)}):</b>\n\n"
    for i, a in enumerate(admins, 1): text += f"{i}. <a href=\"tg://user?id={a.get('uid', 0)}\">{a.get('uid', 0)}</a>\n"
    return text

def format_admin_stats():
    d = load_logs(); users = d.get("users", {}); events = d.get("events", [])
    active_today = sum(1 for u in users.values() if (datetime.fromisoformat(u.get("last_seen", "")).date() if u.get("last_seen") else None) == datetime.now().date())
    return "📊 <b>آمار ربات</b>\n━━━━━━━━━━━━━━━━\n\n" + f"👥 <b>کل کاربران:</b> <code>{len(users)}</code>\n" + f"🟢 <b>فعال امروز:</b> <code>{active_today}</code>\n" + f"📈 <b>کل فعالیت‌ها:</b> <code>{len(events)}</code>\n" + f"🚀 <b>کل /start‌ها:</b> <code>{sum(u.get('starts', 0) for u in users.values())}</code>\n"

def format_admin_logs():
    d = load_logs(); users = d.get("users", {}); events = d.get("events", [])
    iran_tz = timezone(timedelta(hours=3, minutes=30)); today_date = datetime.now(iran_tz).date()
    today_events = []
    for e in events:
        try:
            t = datetime.fromisoformat(e.get("time", ""))
            if t.tzinfo is None: t = t.replace(tzinfo=timezone.utc)
            if t.astimezone(iran_tz).date() == today_date: today_events.append({"uid": e.get("uid"), "name": e.get("name", "?"), "username": e.get("username", ""), "action": e.get("action", "?"), "time_ir": t.astimezone(iran_tz)})
        except: pass
    users_today = {}
    for e in today_events:
        uid = e["uid"]
        if uid not in users_today: users_today[uid] = {"name": e["name"], "username": e["username"], "count": 0, "first_time": e["time_ir"], "last_time": e["time_ir"], "last_action": e["action"]}
        users_today[uid]["count"] += 1
        if e["time_ir"] > users_today[uid]["last_time"]: users_today[uid]["last_time"] = e["time_ir"]; users_today[uid]["last_action"] = e["action"]
        if e["time_ir"] < users_today[uid]["first_time"]: users_today[uid]["first_time"] = e["time_ir"]
    sorted_users = sorted(users_today.items(), key=lambda x: x[1]["last_time"], reverse=True)
    text = "📋 <b>گزارش کاربران</b>\n📅 " + str(today_date) + "\n━━━━━━━━━━━━━━━━\n\n" + "👥 <b>کل کاربران ربات:</b> <code>" + str(len(users)) + "</code>\n" + "🟢 <b>فعال امروز:</b> <code>" + str(len(users_today)) + "</code>\n" + "📊 <b>کل فعالیت‌های امروز:</b> <code>" + str(len(today_events)) + "</code>\n\n━━━━━━━━━━━━━━━━\n\n"
    if not sorted_users: return text + "❌ امروز هنوز فعالیتی نبوده."
    text += "👤 <b>لیست کاربران فعال امروز:</b>\n\n"
    for i, (uid, u) in enumerate(sorted_users[:50], 1):
        user_line = '<a href="tg://user?id=' + str(uid) + '">' + u["name"] + '</a> <code>@' + u["username"] + '</code>' if u["username"] else '<a href="tg://user?id=' + str(uid) + '">' + u["name"] + '</a>'
        text += str(i) + ". " + user_line + "\n   📊 " + str(u["count"]) + " فعالیت\n   🕐 اولین: " + u["first_time"].strftime("%H:%M") + " | آخرین: " + u["last_time"].strftime("%H:%M") + "\n   📌 آخرین کار: " + {"\/start": "🚀 استارت", "\/msg": "💬 پیام", "profile": "👤 پروفایل", "shop": "🛍 فروشگاه", "buy_gifts": "🎁 گیفت‌ها", "buy_stars": "⭐ استارز", "buy_premium": "⚡ پرمیوم", "support": "💬 پشتیبانی", "faq": "❓ سوالات", "main_menu": "🏠 منوی اصلی"}.get(u["last_action"], "🔘 " + str(u["last_action"])[:20]) + "\n\n"
    if len(sorted_users) > 50: text += "... و " + str(len(sorted_users) - 50) + " نفر دیگه"
    return text

def format_admin_users():
    d = load_logs(); users = d.get("users", {})
    if not users: return "👥 <b>لیست کاربران</b>\n\n❌ هنوز کاربری نیست."
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("last_seen", ""), reverse=True)
    text = "👥 <b>همه کاربران (" + str(len(users)) + " نفر)</b>\n━━━━━━━━━━━━━━━━\n\n"; iran_tz = timezone(timedelta(hours=3, minutes=30))
    for i, (uid, u) in enumerate(sorted_users[:50], 1):
        last = (datetime.fromisoformat(u.get("last_seen", "")).replace(tzinfo=timezone.utc) if datetime.fromisoformat(u.get("last_seen", "")).tzinfo is None else datetime.fromisoformat(u.get("last_seen", ""))).astimezone(iran_tz).strftime("%m/%d %H:%M") if u.get("last_seen") else "?"
        user_line = '<a href="tg://user?id=' + str(uid) + '">' + u.get("first_name", "?") + '</a> <code>@' + u.get("username", "") + '</code>' if u.get("username") else '<a href="tg://user?id=' + str(uid) + '">' + u.get("first_name", "?") + '</a>'
        text += str(i) + ". " + user_line + "\n   🆔 <code>" + str(uid) + "</code> | 🚀 " + str(u.get("starts", 0)) + " | 🕐 " + last + "\n"
    if len(users) > 50: text += "\n... و " + str(len(users) - 50) + " نفر دیگه"
    return text

def format_gift_price_panel():
    text = "🎁 <b>تنظیم قیمت گیفت‌ها</b>\n━━━━━━━━━━━━━━━━\n\n💵 قیمت هر گیفت (به تومان):\n\n"
    for key, (name, stars) in GIFTS.items(): text += "   " + name + " = <b>" + f"{get_gift_price(key):,}" + " تومان</b>\n"
    text += "\n━━━━━━━━━━━━━━━━\n👇 یه گیفت رو انتخاب کن تا قیمتش رو تغییر بدی:"
    return text

def format_premium_price_panel():
    text = "⚡ <b>تنظیم قیمت پرمیوم</b>\n━━━━━━━━━━━━━━━━\n\n💵 قیمت هر پلن (به تومان):\n\n"
    for months in sorted(PREMIUM_PLANS.keys()): text += "   ⚡ " + str(months) + " ماهه = <b>" + f"{get_premium_price(months):,}" + " تومان</b>\n"
    text += "\n━━━━━━━━━━━━━━━━\n👇 یه پلن رو انتخاب کن تا قیمتش رو تغییر بدی:"
    return text

def format_custom_star_panel():
    price = get_star_price()
    text = "💰 <b>قیمت پایه هر استارز</b>\n━━━━━━━━━━━━━━━━\n\n📌 <i>این قیمت <b>فقط</b> برای تعداد دلخواه استفاده می‌شه</i>\n\n"
    text += "💵 قیمت فعلی: <b>" + f"{price:,}" + " تومان</b>\n" if price > 0 else "💵 قیمت فعلی: ❌ <i>تنظیم نشده</i>\n"
    text += "\n💡 مثال: اگه <code>5000</code> بذاری:\n   • ۵۱ استارز دلخواه = " + f"{(51 * price):,}" + " تومان\n   • ۱۰۰ استارز دلخواه = " + f"{(100 * price):,}" + " تومان\n\n━━━━━━━━━━━━━━━━\n✏️ قیمت جدید (تومان) رو بفرست:"
    return text

def format_stars_price_panel():
    text = "⭐ <b>تنظیم قیمت پکیج‌های استارز</b>\n━━━━━━━━━━━━━━━━\n\n💵 <b>قیمت هر پکیج:</b>\n\n"
    for stars in STAR_PACKS.keys():
        price = get_star_pack_price(stars)
        text += "   " + str(stars) + "⭐ = " + (f"<b>{price:,} تومان</b>\n" if price > 0 else "❌ <i>تنظیم نشده</i>\n")
    text += "\n💰 <b>قیمت هر استارز (دلخواه):</b> " + (f"<b>{get_star_price():,} تومان</b>\n" if get_star_price() > 0 else "❌ <i>قیمت پکیج 50 رو تنظیم کن</i>\n")
    text += "\n━━━━━━━━━━━━━━━━\n👇 روی هر پکیج بزن تا قیمتش رو تنظیم کنی:"
    return text

def format_price_panel():
    return "💰 <b>تنظیم قیمت استارز</b>\n\n👇 یه گزینه رو انتخاب کن:"
