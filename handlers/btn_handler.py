import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import is_admin, log_event, get_ticket
from shop import main_menu
from shop_handlers import handle_shop
from admin_handlers import handle_admin
logger = logging.getLogger(__name__)

async def btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user
    logger.info(f"[BTN] {user.id} → {data}")
    try: log_event(user, data)
    except: pass
    from shop import check_expiry_and_send_menu
    if await check_expiry_and_send_menu(query.message, user, context, context.bot): return
    try: await query.answer()
    except: pass

    exempt_buttons = ("check_join", "main_menu", "adm_panel")
    if data not in exempt_buttons:
        from shop import check_user_joined, force_join_keyboard
        if not await check_user_joined(context.bot, user.id):
            try: await query.edit_message_text("⚠️ <b>برای استفاده از ربات، اول باید عضو کانال ما بشید!</b>" + chr(10) + chr(10) + "👇 روی دکمه زیر بزنید و عضو بشید، بعد روی «✅ عضو شدم» کلیک کنید:", parse_mode="HTML", reply_markup=force_join_keyboard())
            except: pass
            return

    if data == "main_menu":
        for k in ["gift_count", "gift_selected", "recipient", "stars_selected", "custom_toman", "custom_dollar", "premium_selected"]: context.user_data.pop(k, None)
        import time; context.user_data["last_activity"] = time.time()
        text = f"سلام {user.first_name} 👋\n\n🛒 <b>خرید استارز، گیفت و تلگرام پریمیوم به ساده‌ترین و سریع‌ترین روش ممکن!</b>\n\n👇 یکی از دکمه‌های زیر را انتخاب کنید"
        try: await query.edit_message_text(text, reply_markup=main_menu(user.id, is_admin), parse_mode="HTML")
        except Exception as e:
            if "no text" in str(e).lower() or "There is no text" in str(e):
                try: await query.message.delete()
                except: pass
                await query.message.chat.send_message(text, reply_markup=main_menu(user.id, is_admin), parse_mode="HTML")
            else: raise
        return

    if data == "support":
        pending = context.user_data.get("pending_purchase")
        if pending:
            context.user_data["waiting_ticket"] = True
            text = "📤 <b>تایید رسید خود را ارسال کنید</b>" + chr(10) + "━━━━━━━━━━━━━━━━" + chr(10) + chr(10) + "📦 <b>محصول:</b> " + str(pending.get("name", "?")) + chr(10) + "💰 <b>مبلغ:</b> " + f"{pending.get('price_toman', 0):,}" + " تومان" + chr(10) + chr(10) + "📝 <b>پیام خود را بفرستید:</b>" + chr(10) + chr(10) + "✅ بعد از تایید رسید توسط پشتیبانی، سفارش شما آماده می‌شه." + chr(10) + "🔖 کد رهگیری بعد از ثبت بهت داده می‌شه." + chr(10) + chr(10) + "✍️ <i>عکس فیش یا متن رسید رو همینجا بفرست:</i>"
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu", style="danger")]]))
        else:
            text = "💬 <b>پشتیبانی</b>" + chr(10) + "━━━━━━━━━━━━━━━━" + chr(10) + chr(10) + "برای ارتباط با پشتیبانی، روی دکمه زیر کلیک کنید:"
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 پشتیبانی", url="https://t.me/BOnlineStars?direct", style="success")], [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu", style="danger")]]))
        return

    if data == "check_join":
        from shop import check_user_joined
        if await check_user_joined(context.bot, user.id):
            text = f"سلام {user.first_name} 👋\n\n🛒 <b>خرید استارز، گیفت و تلگرام پریمیوم به ساده‌ترین و سریع‌ترین روش ممکن!</b>\n\n👇 یکی از دکمه‌های زیر را انتخاب کنید"
            await query.edit_message_text(text, reply_markup=main_menu(user.id, is_admin), parse_mode="HTML")
        else: await query.answer("❌ هنوز عضو کانال نشدی!", show_alert=True)
        return

    if data.startswith("send_receipt_"):
        try: tid = int(data.replace("send_receipt_", ""))
        except: await query.answer("❌ خطا", show_alert=True); return
        t = get_ticket(tid)
        if not t: await query.answer("❌ تیکت پیدا نشد", show_alert=True); return
        from config import get_user_purchases, RECEIPT_CHANNEL, build_receipt_text
        uid = t.get("user_id"); ticket_track = t.get("track_code"); purchases = get_user_purchases(uid)
        target_purchase = next((p for p in purchases if p.get("track_code") == ticket_track), purchases[-1] if purchases else None)
        if not target_purchase: await query.answer("❌ خرید مرتبط با این تیکت پیدا نشد!", show_alert=True); return
        receipt_text = build_receipt_text(uid, target_purchase.get("name", "?"), target_purchase.get("price_toman", 0), target_purchase.get("track_code", "?"), target_purchase.get("created_at", ""), target_purchase.get("created_at", ""))
        try:
            await context.bot.send_message(chat_id=RECEIPT_CHANNEL, text=receipt_text, parse_mode="HTML")
            await query.answer("✅ رسید دقیق در کانال ارسال شد!", show_alert=False)
        except Exception as e:
            print(f"[send_receipt] err: {e}"); await query.answer("❌ خطا در ارسال. ربات باید ادمین کانال باشه!", show_alert=True)
        return

    if data == "buy_wallet":
        from config import get_wallet_config
        cfg = get_wallet_config(); min_amt = cfg.get("min_amount", 100000); first_amt = cfg.get("first_amount", min_amt)
        text = "💳 <b>شارژ ولت تلگرام</b>" + chr(10) + "━━━━━━━━━━━━━━━━" + chr(10) + chr(10) + "👋 سلام! به بخش شارژ ولت خوش آمدید." + chr(10) + chr(10) + "⚠️ <b>توجه مهم:</b>" + chr(10) + "اگر برای بار اول است که ولت خود را شارژ می‌کنید، ولت شما باید فعال‌سازی شود." + chr(10) + "💰 <b>مبلغ مورد نیاز برای اولین واریز:</b> <b>" + f"{first_amt:,}" + " تومان</b>" + chr(10) + "📌 <i>حداقل مبلغ مجاز برای شارژ‌های بعدی: " + f"{min_amt:,}" + " تومان</i>" + chr(10) + chr(10) + "📝 <b>چه مبلغی می‌خواهید شارژ کنید؟</b>" + chr(10) + "👇 برای ادامه روی دکمه زیر بزنید:"
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💳 ثبت درخواست شارژ", callback_data="wallet_request", style="success")], [InlineKeyboardButton("🔙 بازگشت", callback_data="shop", style="danger")]]))
        return

    if data == "wallet_request":
        context.user_data["wallet_step"] = "waiting_amount"
        await query.edit_message_text("💰 <b>مبلغ شارژ</b>" + chr(10) + chr(10) + "✏️ مبلغ مورد نظر خود را به تومان بفرستید:" + chr(10) + chr(10) + "📌 <i>لطفاً مبلغ را دقیق وارد کنید.</i>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="buy_wallet", style="danger")]]))
        return

    if data == "gift_set_caption":
        context.user_data["waiting_gift_caption"] = True
        caption_photo_id = "AgACAgQAAyEFAAMBCbfqpQADHGrsTcGbZK3uJMfxqWvyV5csRa9pAAK-DWsbg_NhU4EXXLKrC7OLAQADAgADeQADPQQ"
        caption_text = "📝 <b>کپشنِ گیفت چیه؟</b>" + chr(10) + "━━━━━━━━━━━━━━━━" + chr(10) + chr(10) + "📌 <b>کپشن</b> یعنی متنی که همراه گیفت برای گیرنده فرستاده می‌شه." + chr(10) + chr(10) + "💡 <b>مثال:</b>" + chr(10) + "• تولدت مبارک عزیزم 🎂" + chr(10) + "• به یاد لحظه‌های خوبمون 💝" + chr(10) + chr(10) + "✏️ <b>حالا متن دلخواه خودت رو بنویس:</b>" + chr(10) + chr(10) + "📌 برای حذف کپشن، کلمه <code>skip</code> یا <code>رد</code> رو بفرست."
        try: await query.message.delete()
        except: pass
        try:
            guide_msg = await query.message.chat.send_photo(photo=caption_photo_id, caption=caption_text, parse_mode="HTML")
            context.user_data["caption_guide_msg_id"] = guide_msg.message_id
        except Exception as e:
            print(f"[caption_photo] err: {e}")
            guide_msg = await query.message.chat.send_message(caption_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="buy_gifts", style="danger")]]))
            context.user_data["caption_guide_msg_id"] = guide_msg.message_id
        return

    if await handle_shop(query, data, user, context): return
    if await handle_admin(query, data, user, context): return
    logger.warning(f"[BTN] unhandled: {data}")
