import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import get_username, get_display_name, get_user_stars, get_user_ref_count, get_user_purchases
logger = logging.getLogger(__name__)
NL = chr(10)

def _user_link(user):
    u = get_username(user).lstrip("@")
    return '<a href="tg://resolve?domain=' + u + '">' + u + '</a>' if u and u != "—" else "—"

async def handle_profile(query, data, user, context):
    if data == "profile":
        all_purchases = get_user_purchases(user.id); purchases = [p for p in all_purchases if p.get("status") in ("paid", "delivered")]
        total_toman = sum(p.get("price_toman", 0) for p in purchases)
        stars = get_user_stars(user.id); refs_count = len(get_user_ref_count(user.id))
        text = "👤 <b>پروفایل شما</b>" + NL + "━━━━━━━━━━━━━━━━" + NL + NL + "📛 نام: <b>" + get_display_name(user) + "</b>" + NL + "🔹 یوزرنیم: " + _user_link(user) + NL + "🆔 آیدی: <code>" + str(user.id) + "</code>" + NL + NL + "━━━━━━━━━━━━━━━━" + NL + "💫 <b>موجودی استارز:</b> <b>" + str(stars) + "</b>" + NL + "👥 <b>دعوت موفق:</b> <b>" + str(refs_count) + " نفر</b>" + NL + NL + "🛒 <b>سابقه خرید:</b>" + NL
        if not purchases: text += "📭 هنوز خریدی نداری." + NL
        else:
            text += "📦 تعداد کل خرید: <b>" + str(len(purchases)) + "</b>" + NL + "💰 مجموع: <b>" + f"{total_toman:,}" + " تومان</b>" + NL + NL
            for i, p in enumerate(purchases[-5:][::-1], 1):
                emoji = {"stars": "⭐", "premium": "⚡"}.get(p.get("type"), "🎁")
                text += str(i) + ". " + emoji + " <b>" + p.get("name", "?") + "</b>" + NL + "   📊 " + str(p.get("count", 1)) + " | 💵 " + f"{p.get('price_toman', 0):,}" + " تومان" + NL + "   🎫 <code>" + p.get("track_code", "?") + "</code> | " + {"paid": "🟢", "delivered": "✅"}.get(p.get("status"), "🟡") + NL
            if len(purchases) > 5: text += NL + "... و " + str(len(purchases) - 5) + " خرید دیگه"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📜 سابقه کامل خرید", callback_data="my_purchases", style="primary")], [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu", style="danger")]])
        sent = False
        try:
            photos = await query.get_bot().get_user_profile_photos(user.id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                try: await query.message.delete()
                except: pass
                await query.message.chat.send_photo(photo=file_id, caption=text, parse_mode="HTML", reply_markup=kb); sent = True
        except Exception as e: print(f"[profile] photo err: {e}")
        if not sent:
            try: await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
            except:
                try: await query.message.delete()
                except: pass
                await query.message.chat.send_message(text, parse_mode="HTML", reply_markup=kb)
        return True
    if data == "my_purchases":
        all_purchases = get_user_purchases(user.id); purchases = [p for p in all_purchases if p.get("status") in ("paid", "delivered")]
        if not purchases:
            await query.edit_message_text("📜 <b>سابقه خرید</b>" + NL + NL + "📭 هنوز خریدی نداری.", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="profile", style="danger")]])); return True
        total_toman = sum(p.get("price_toman", 0) for p in purchases)
        text = "📜 <b>سابقه کامل خرید</b>" + NL + "━━━━━━━━━━━━━━━━" + NL + NL + "📦 تعداد کل: <b>" + str(len(purchases)) + "</b>" + NL + "💰 مجموع: <b>" + f"{total_toman:,}" + " تومان</b>" + NL + NL + "━━━━━━━━━━━━━━━━" + NL
        for i, p in enumerate(purchases[::-1], 1):
            emoji = {"stars": "⭐", "premium": "⚡"}.get(p.get("type"), "🎁")
            text += str(i) + ". " + emoji + " <b>" + p.get("name", "?") + "</b>" + NL + "   📊 " + str(p.get("count", 1)) + " | 💵 " + f"{p.get('price_toman', 0):,}" + " تومان" + NL + "   🎫 <code>" + p.get("track_code", "?") + "</code>" + NL + "   📅 " + (p.get("created_at", "")[11:16] if len(p.get("created_at", "")) > 16 else "?") + " | " + {"pending": "🟡 در انتظار", "paid": "🟢 پرداخت شده", "delivered": "✅ تحویل شده"}.get(p.get("status"), "🟡") + NL + NL
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="profile", style="danger")]])
        try: await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
        except:
            try: await query.message.delete()
            except: pass
            await query.message.chat.send_message(text, parse_mode="HTML", reply_markup=kb)
        return True
    return False
