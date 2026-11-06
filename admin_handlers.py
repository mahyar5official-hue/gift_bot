#!/usr/bin/env python3
import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import OWNER_ID, is_owner, is_admin, get_all_open_tickets, get_ticket, close_ticket, create_ticket, add_ticket_message, send_ticket_to_admins
from admin import admin_menu, admins_manage_menu, format_admin_list, format_admin_stats, format_admin_logs, format_admin_users, format_price_panel, format_premium_price_panel, format_custom_star_panel, format_gift_price_panel, format_stars_price_panel

logger = logging.getLogger(__name__)

async def handle_admin(query, data, user, context):
    if data == "adm_panel":
        if not is_admin(user.id): await query.answer("❌ دسترسی نداری", show_alert=True); return True
        title = "👑 <b>پنل مالک</b>" if is_owner(user.id) else "🛠 <b>پنل مدیریت</b>"
        await query.edit_message_text(title + "\n\n👇 یکی از گزینه‌ها رو انتخاب کن:", reply_markup=admin_menu(user.id), parse_mode="HTML")
        return True

    if data == "adm_stats":
        if not is_admin(user.id): await query.answer("❌", show_alert=True); return True
        await query.edit_message_text(format_admin_stats(), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 آپدیت", callback_data="adm_stats")], [InlineKeyboardButton("🔙 بازگشت", callback_data="adm_panel")]]))
        return True

    if data == "adm_logs":
        if not is_admin(user.id): await query.answer("❌", show_alert=True); return True
        await query.edit_message_text(format_admin_logs(), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 آپدیت", callback_data="adm_logs")], [InlineKeyboardButton("🔙 بازگشت", callback_data="adm_panel")]]))
        return True

    if data == "adm_users":
        if not is_admin(user.id): await query.answer("❌", show_alert=True); return True
        await query.edit_message_text(format_admin_users(), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 آپدیت", callback_data="adm_users")], [InlineKeyboardButton("🔙 بازگشت", callback_data="adm_panel")]]))
        return True

    if data == "adm_ticket":
        if not is_admin(user.id): await query.answer("❌", show_alert=True); return True
        tickets = get_all_open_tickets()
        if not tickets:
            await query.edit_message_text("📩 <b>تیکت‌ها</b>\n\n✅ هیچ تیکت بازی نیست!", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_panel")]]))
            return True
        text = f"📩 <b>تیکت‌های باز ({len(tickets)})</b>\n━━━━━━━━━━━━━━━━\n\n"; kb = []
        for t in tickets[:10]:
            name = t.get("user_name", "کاربر"); uname = t.get("user_username", ""); tid = t.get("id", 0); msgs = len(t.get("messages", []))
            label = f"🎫 #{tid} — {name} (@{uname}) — {msgs} پیام" if uname else f"🎫 #{tid} — {name} — {msgs} پیام"
            kb.append([InlineKeyboardButton(label[:60], callback_data=f"adm_tv_{tid}")])
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="adm_panel")])
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
        return True

    if data.startswith("adm_tv_"):
        if not is_admin(user.id): await query.answer("❌", show_alert=True); return True
        try: tid = int(data.replace("adm_tv_", ""))
        except: return True
        t = get_ticket(tid)
        if not t: await query.answer("❌ تیکت پیدا نشد", show_alert=True); return True
        from config import format_ticket_header, format_ticket_body
        text = format_ticket_header(t) + format_ticket_body(t)
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("✉️ پاسخ", callback_data=f"adm_tr_{tid}", style="primary")], [InlineKeyboardButton("✅ بستن تیکت", callback_data=f"adm_tc_{tid}", style="danger")], [InlineKeyboardButton("🔙 بازگشت", callback_data="adm_ticket")]])
        try: await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            if "no text" in str(e).lower() or "There is no text" in str(e):
                try: await query.message.delete()
                except: pass
                await query.message.chat.send_message(text, parse_mode="HTML", reply_markup=kb)
            else: raise
        return True

    if data.startswith("adm_tr_"):
        if not is_admin(user.id): await query.answer("❌", show_alert=True); return True
        try: tid = int(data.replace("adm_tr_", ""))
        except: return True
        context.user_data["replying_ticket"] = tid
        text = "✉️ <b>پاسخ به تیکت #" + str(tid) + "</b>" + chr(10) + chr(10) + "پیام خود را بنویسید:"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data=f"adm_tv_{tid}")]])
        try: await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            if "no text" in str(e).lower() or "There is no text" in str(e):
                try: await query.message.delete()
                except: pass
                await query.message.chat.send_message(text, parse_mode="HTML", reply_markup=kb)
            else: raise
        return True

    if data.startswith("adm_tc_"):
        if not is_admin(user.id): await query.answer("❌", show_alert=True); return True
        try: tid = int(data.replace("adm_tc_", ""))
        except: return True
        t = get_ticket(tid)
        if t:
            close_ticket(tid)
            try: await query.get_bot().send_message(chat_id=t["user_id"], text=f"🔴 <b>تیکت #{tid} بسته شد</b>\n\nاگه سوال دیگه‌ای داری، دوباره پیام بده.", parse_mode="HTML")
            except: pass
        await query.answer("✅ تیکت بسته شد")
        await query.edit_message_text("📩 <b>تیکت‌ها</b>\n\n✅ تیکت بسته شد!", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_ticket")]]))
        return True

    if data == "adm_manage":
        if not is_owner(user.id): await query.answer("❌ فقط مالک", show_alert=True); return True
        await query.edit_message_text(format_admin_list() + "\n\n👇 یکی از گزینه‌ها:", reply_markup=admins_manage_menu(), parse_mode="HTML")
        return True

    if data == "adm_list":
        if not is_owner(user.id): await query.answer("❌", show_alert=True); return True
        await query.edit_message_text(format_admin_list(), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_manage")]]), parse_mode="HTML")
        return True

    if data == "adm_add":
        if not is_owner(user.id): await query.answer("❌", show_alert=True); return True
        context.user_data["waiting_admin_id"] = True
        await query.edit_message_text("➕ <b>افزودن ادمین</b>\n\n🆔 آیدی عددی کاربر رو بفرست:\n\n💡 مثال: <code>123456789</code>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_manage")]]), parse_mode="HTML")
        return True

    if data == "adm_remove":
        if not is_owner(user.id): await query.answer("❌", show_alert=True); return True
        context.user_data["waiting_remove_id"] = True
        await query.edit_message_text("➖ <b>حذف ادمین</b>\n\n🆔 آیدی عددی ادمین رو بفرست:\n\n💡 مثال: <code>123456789</code>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_manage")]]), parse_mode="HTML")
        return True

    if data == "support":
        context.user_data["waiting_ticket"] = True
        text = "💬 <b>پشتیبانی</b>\n━━━━━━━━━━━━━━━━\n\n📝 <b>پیام خود را بفرستید:</b>\n\nپیام شما مستقیم برای مدیریت ارسال میشه و به زودی جواب می‌گیرید.\n\n✍️ پیامت رو همینجا بنویس و بفرست:"
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]))
        return True

    if data == "adm_premium_price":
        if not is_admin(user.id): await query.answer("❌", show_alert=True); return True
        from config import PREMIUM_PLANS
        rows = [[InlineKeyboardButton("⚡ " + str(months) + " ماهه", callback_data="adm_pp_" + str(months), style="primary")] for months in sorted(PREMIUM_PLANS.keys())]
        rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="adm_panel", style="danger")])
        await query.edit_message_text(format_premium_price_panel(), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
        return True

    if data.startswith("adm_pp_") and data[7:].isdigit():
        if not is_admin(user.id): await query.answer("❌", show_alert=True); return True
        months = int(data[7:]); from config import get_premium_price; current = get_premium_price(months)
        context.user_data["waiting_premium_price_for"] = months
        await query.edit_message_text("⚡ <b>تغییر قیمت پرمیوم " + str(months) + " ماهه</b>" + chr(10) + chr(10) + "💵 قیمت فعلی: <b>" + f"{current:,}" + " تومان</b>" + chr(10) + chr(10) + "✏️ قیمت جدید (تومان) رو بفرست:" + chr(10) + "💡 مثال: <code>500000</code>" + chr(10) + chr(10) + "🗑 برای پاک کردن قیمت دستی، کلمه <code>reset</code> رو بفرست.", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_premium_price", style="danger")]]))
        return True

    if data == "adm_gift_price":
        if not is_admin(user.id): await query.answer("❌", show_alert=True); return True
        from config import GIFTS
        rows, row = [], []
        for key, (name, stars) in GIFTS.items():
            row.append(InlineKeyboardButton(name, callback_data="adm_gp_" + key))
            if len(row) == 2: rows.append(row); row = []
        if row: rows.append(row)
        rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="adm_panel", style="danger")])
        await query.edit_message_text(format_gift_price_panel(), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
        return True

    if data.startswith("adm_gp_"):
        if not is_admin(user.id): await query.answer("❌", show_alert=True); return True
        gift_key = data.replace("adm_gp_", ""); from config import GIFTS, get_gift_price
        if gift_key not in GIFTS: await query.answer("❌ پیدا نشد", show_alert=True); return True
        name, stars = GIFTS[gift_key]; current = get_gift_price(gift_key); context.user_data["waiting_gift_price_for"] = gift_key
        await query.edit_message_text("🎁 <b>تغییر قیمت " + name + "</b>" + chr(10) + chr(10) + "💵 قیمت فعلی: <b>" + f"{current:,}" + " تومان</b>" + chr(10) + chr(10) + "✏️ قیمت جدید (تومان) رو بفرست:" + chr(10) + "💡 مثال: <code>60000</code>" + chr(10) + chr(10) + "🗑 برای پاک کردن، کلمه <code>reset</code> رو بفرست.", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_gift_price", style="danger")]]))
        return True

    if data == "adm_stars_price":
        if not is_admin(user.id): await query.answer("❌", show_alert=True); return True
        from config import STAR_PACKS, get_star_pack_price, get_star_price
        rows = [[InlineKeyboardButton("💰 قیمت پایه (دلخواه): " + (f"{get_star_price():,} تومان" if get_star_price() > 0 else "❌ تنظیم نشده"), callback_data="adm_custom_star_price", style="success")]]
        for stars in STAR_PACKS.keys():
            price = get_star_pack_price(stars)
            rows.append([InlineKeyboardButton("⭐ " + str(stars) + " — " + (f"{price:,} تومان" if price > 0 else "❌ تنظیم نشده"), callback_data="adm_sp_" + str(stars), style="primary")])
        rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="adm_panel", style="danger")])
        await query.edit_message_text(format_stars_price_panel(), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
        return True

    if data == "adm_custom_star_price":
        if not is_admin(user.id): await query.answer("❌", show_alert=True); return True
        context.user_data["waiting_custom_star_base"] = True
        await query.edit_message_text(format_custom_star_panel(), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_stars_price", style="danger")]]))
        return True

    if data.startswith("adm_sp_"):
        if not is_admin(user.id): await query.answer("❌", show_alert=True); return True
        try: stars = int(data.replace("adm_sp_", ""))
        except: return True
        from config import STAR_PACKS, get_star_pack_price
        if stars not in STAR_PACKS: await query.answer("❌ پیدا نشد", show_alert=True); return True
        current = get_star_pack_price(stars); context.user_data["waiting_stars_pack_price_for"] = stars
        price_text = "💵 قیمت فعلی: <b>" + f"{current:,}" + " تومان</b>" if current > 0 else "💵 قیمت فعلی: ❌ تنظیم نشده"
        await query.edit_message_text("⭐ <b>تنظیم قیمت پکیج " + str(stars) + " استارز</b>" + chr(10) + "━━━━━━━━━━━━━━━━" + chr(10) + chr(10) + price_text + chr(10) + chr(10) + "✏️ قیمت جدید (تومان) رو بفرست:" + chr(10) + "💡 مثال: <code>200000</code>" + chr(10) + chr(10) + "🗑 برای پاک کردن قیمت، کلمه <code>reset</code> رو بفرست.", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_stars_price", style="danger")]]))
        return True

    if data.startswith("approve_"):
        if not is_admin(user.id): await query.answer("❌ دسترسی نداری", show_alert=True); return True
        tid = int(data.replace("approve_", "")); t = get_ticket(tid)
        if not t: await query.answer("❌ تیکت پیدا نشد", show_alert=True); return True
        uid = t.get("user_id")
        try:
            from config import load_purchases, save_purchases
            d = load_purchases()
            if str(uid) in d.get("purchases", {}):
                for p in d["purchases"][str(uid)]:
                    if p.get("status") == "registered": p["status"] = "paid"; break
                save_purchases(d)
        except: pass
        try: await context.bot.send_message(chat_id=uid, text="✅ <b>رسید شما تایید شد!</b>" + chr(10) + chr(10) + "🛠 سفارش شما در حال آماده‌سازیه." + chr(10) + "📦 به زودی محصول برات ارسال می‌شه.", parse_mode="HTML")
        except: pass
        from config import load_ticket_messages, get_username
        admin_username = get_username(user); ticket_msgs = load_ticket_messages(tid)
        for admin_id_str, msg_id in ticket_msgs.items():
            try: await context.bot.edit_message_reply_markup(chat_id=int(admin_id_str), message_id=int(msg_id), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تایید شد توسط @" + admin_username, callback_data="noop", style="success")], [InlineKeyboardButton("📣 ارسال رسید به کانال", callback_data="send_receipt_" + str(tid), style="primary")], [InlineKeyboardButton("✉️ پاسخ به تیکت #" + str(tid), callback_data="adm_tv_" + str(tid), style="primary")]]))
            except Exception as e: print(f"[approve] edit err {admin_id_str}: {e}")
        await query.answer("✅ تایید شد", show_alert=False)
        return True

    if data.startswith("reject_"):
        if not is_admin(user.id): await query.answer("❌ دسترسی نداری", show_alert=True); return True
        tid = int(data.replace("reject_", "")); t = get_ticket(tid)
        if not t: await query.answer("❌ تیکت پیدا نشد", show_alert=True); return True
        uid = t.get("user_id")
        try:
            from config import load_purchases, save_purchases
            d = load_purchases()
            if str(uid) in d.get("purchases", {}):
                for p in d["purchases"][str(uid)]:
                    if p.get("status") == "registered": p["status"] = "rejected"; break
                save_purchases(d)
        except Exception as e: print(f"[reject] purchase err: {e}")
        try: await context.bot.send_message(chat_id=uid, text="❌ <b>رسید شما رد شد</b>" + chr(10) + chr(10) + "🎫 تیکت #" + str(tid) + chr(10) + chr(10) + "💬 اگه اعتراض داری، پیام بده به پشتیبانی.", parse_mode="HTML")
        except Exception as e: print(f"[reject] notify err: {e}")
        from config import load_ticket_messages, get_username
        admin_username = get_username(user); ticket_msgs = load_ticket_messages(tid)
        for admin_id_str, msg_id in ticket_msgs.items():
            try: await context.bot.edit_message_reply_markup(chat_id=int(admin_id_str), message_id=int(msg_id), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ رد شد توسط @" + admin_username, callback_data="noop", style="danger")], [InlineKeyboardButton("✉️ پاسخ به تیکت #" + str(tid), callback_data="adm_tv_" + str(tid), style="primary")]]))
            except Exception as e: print(f"[reject] edit err {admin_id_str}: {e}")
        await query.answer("❌ رد شد", show_alert=False)
        return True

    if data == "noop":
        await query.answer()
        return True

    if data == "adm_broadcast":
        if not is_owner(user.id): await query.answer("❌ فقط مالک", show_alert=True); return True
        context.user_data["waiting_broadcast"] = True
        await query.edit_message_text("📢 <b>پیام همگانی</b>" + chr(10) + "━━━━━━━━━━━━━━━━" + chr(10) + chr(10) + "✍️ پیام خود رو بفرستید:" + chr(10) + chr(10) + "📝 می‌تونید متن، عکس، ویدیو، فایل یا هر چیزی بفرستید." + chr(10) + "📌 پیام دقیقاً همون‌طوری که می‌فرستید برای همه ارسال می‌شه." + chr(10) + chr(10) + "⚠️ این پیام برای <b>همه کاربران ربات</b> ارسال می‌شه!", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data="adm_panel", style="danger")]]))
        return True

    if data == "adm_wallet_config":
        if not is_owner(user.id): await query.answer("❌ فقط مالک", show_alert=True); return True
        from config import get_wallet_config
        cfg = get_wallet_config(); min_amt = cfg.get("min_amount", 100000); first_amt = cfg.get("first_amount", min_amt)
        text = "💳 <b>تنظیمات شارژ ولت</b>" + chr(10) + "━━━━━━━━━━━━━━━━" + chr(10) + chr(10) + "💰 <b>حداقل مبلغ واریز:</b> " + f"{min_amt:,}" + " تومان" + chr(10) + "📌 <b>مبلغ اولین بار:</b> " + f"{first_amt:,}" + " تومان" + chr(10) + chr(10) + "👇 برای تغییر، روی دکمه‌های زیر بزن:"
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 تغییر حداقل مبلغ", callback_data="adm_wallet_min", style="primary")], [InlineKeyboardButton("📌 تغییر مبلغ اولین بار", callback_data="adm_wallet_first_amt", style="primary")], [InlineKeyboardButton("🔙 بازگشت", callback_data="adm_panel", style="danger")]]))
        return True

    if data == "adm_wallet_first_amt":
        if not is_owner(user.id): await query.answer("❌", show_alert=True); return True
        context.user_data["waiting_wallet_first_amt"] = True
        await query.edit_message_text("📌 <b>مبلغ اولین بار (تومان)</b>" + chr(10) + chr(10) + "✏️ عدد جدید رو بفرست (حداقل مبلغی که برای اولین بار باید واریز بشه):" + chr(10) + "💡 مثال: <code>100000</code>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_wallet_config", style="danger")]]))
        return True

    if data == "adm_wallet_min":
        if not is_owner(user.id): await query.answer("❌", show_alert=True); return True
        context.user_data["waiting_wallet_min"] = True
        await query.edit_message_text("💰 <b>حداقل مبلغ واریز (تومان)</b>" + chr(10) + chr(10) + "✏️ عدد جدید رو بفرست:" + chr(10) + "💡 مثال: <code>100000</code>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_wallet_config", style="danger")]]))
        return True

    return False
