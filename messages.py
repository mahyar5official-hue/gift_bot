import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import log_event, OWNER_ID, STAR_PACKS, GIFTS, PREMIUM_PLANS, get_username, get_display_name, is_owner, is_admin, add_admin, remove_admin, create_ticket, get_ticket, send_ticket_to_admins, add_ticket_message, get_user_purchases, get_user_stars, get_user_ref_count, add_purchase, get_star_price, get_star_pack_price, get_gift_price, get_premium_price, set_star_pack_price, clear_star_pack_price, set_gift_price, clear_gift_price, set_premium_price, clear_premium_price, calc_toman, calc_dollar, load_admins, format_ticket_header, format_ticket_body, load_purchases, set_custom_star_price, clear_custom_star_price, save_ticket_messages
from shop import gifts_menu, stars_menu, premium_menu, stars_text
logger = logging.getLogger(__name__); NL = chr(10)

async def do_broadcast(update, context):
    from config import load_logs, OWNER_ID
    import asyncio
    user = update.effective_user
    if user.id != OWNER_ID: return
    msg = update.message; users = list(load_logs().get("users", {}).keys())
    if not users: await msg.reply_text("❌ هیچ کاربری ثبت نشده!"); return
    status = await msg.reply_text(f"📢 شروع ارسال به <b>{len(users)}</b> کاربر...", parse_mode="HTML")
    success = failed = 0
    for uid in users:
        try: await context.bot.copy_message(chat_id=int(uid), from_chat_id=msg.chat_id, message_id=msg.message_id); success += 1
        except Exception as e: failed += 1; print(f"[broadcast] err {uid}: {e}")
        await asyncio.sleep(0.05)
        if (success + failed) % 25 == 0:
            try: await status.edit_text(f"📢 در حال ارسال..." + chr(10) + f"✅ موفق: {success}" + chr(10) + f"❌ خطا: {failed}" + chr(10) + f"📊 پیشرفت: {success + failed}/{len(users)}", parse_mode="HTML")
            except: pass
    try: await status.edit_text("✅ <b>ارسال همگانی تموم شد!</b>" + chr(10) + "━━━━━━━━━━━━━━━━" + chr(10) + f"✅ موفق: <b>{success}</b>" + chr(10) + f"❌ خطا: <b>{failed}</b>" + chr(10) + f"📊 کل: <b>{len(users)}</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پنل مالک", callback_data="adm_panel", style="primary")]]))
    except: pass
    context.user_data["waiting_broadcast"] = False

async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user; text = update.message.text.strip() if update.message.text else ""
    logger.info(f"[MSG] {user.id}: {text[:50]}")
    waiting_keys = ["waiting_wallet_amount", "waiting_ticket", "waiting_recipient", "waiting_custom_stars", "waiting_gift_count", "waiting_admin_id", "waiting_remove_id", "waiting_gift_price_for", "waiting_premium_price_for", "waiting_stars_pack_price_for", "waiting_broadcast", "waiting_wallet_receipt", "wallet_step", "replying_ticket", "waiting_gift_caption"]
    if not any(context.user_data.get(k) for k in waiting_keys):
        from shop import check_expiry_and_send_menu
        if await check_expiry_and_send_menu(update.message, user, context, context.bot): return

    if context.user_data.get("waiting_gift_caption"):
        context.user_data["waiting_gift_caption"] = False
        if text.lower() in ("skip", "رد", "حذف"): context.user_data.pop("gift_caption", None)
        else: context.user_data["gift_caption"] = text
        try: await update.message.delete()
        except: pass
        guide_msg_id = context.user_data.get("caption_guide_msg_id")
        if guide_msg_id:
            try: await context.bot.delete_message(chat_id=user.id, message_id=guide_msg_id)
            except: pass
            context.user_data.pop("caption_guide_msg_id", None)
        from shop import gifts_menu
        from config import GIFTS, get_username, get_gift_price
        selected = context.user_data.get("gift_selected") or list(GIFTS.keys())[0]
        count = context.user_data.get("gift_count", 1)
        recipient_clean = context.user_data.get("recipient", get_username(user)).lstrip("@")
        name, price = GIFTS[selected]; gift_toman = get_gift_price(selected) * count
        caption_val = context.user_data.get("gift_caption", "")
        msg_text = "🎁 <b>خرید گیفت تلگرام</b>" + NL + NL + "👤 نام کاربری: " + get_username(user) + NL + "🎁 گیرنده: " + str(recipient_clean) + NL + "🎁 تعداد: " + str(count) + "x " + name.split(" ", 1)[0] + NL + "💵 مبلغ: <b>" + f"{gift_toman:,}" + "</b> تومان 💸" + NL + "📝 کپشن: " + (caption_val or "-") + NL + NL + "🔽 گیرنده و تعداد را انتخاب کرده، سپس روی دکمه ادامه کلیک کنید."
        await update.message.chat.send_message(msg_text, parse_mode="HTML", reply_markup=gifts_menu(selected, count, recipient_clean))
        return

    if context.user_data.get("replying_ticket"):
        tid = context.user_data.get("replying_ticket"); context.user_data["replying_ticket"] = None
        if not is_admin(user.id): await update.message.reply_text("❌ فقط ادمین"); return
        add_ticket_message(tid, "admin", text); t = get_ticket(tid)
        if t:
            last_user_msg = next((m.get("text", "") for m in reversed(t.get("messages", [])) if m.get("from") == "user"), "")
            user_msg = "📨 <b>پاسخ پشتیبانی</b>" + NL + "🎫 تیکت #" + str(tid) + NL + "{" + last_user_msg + "}" + NL + "━━━━━━━━━━━━━━━━" + NL + NL + text + NL + NL + "👇 برای ادامه گفتگو:"
            try: await context.bot.send_message(chat_id=t["user_id"], text=user_msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 پاسخ", callback_data="support", style="primary")]]))
            except: pass
        admin_notif = "📩 <b>پاسخ جدید ادمین</b>" + NL + "👤 " + get_display_name(user) + NL + NL
        await send_ticket_to_admins(context.bot, t, extra_text=admin_notif, exclude_id=user.id)
        await update.message.reply_text("✅ <b>پاسخ ارسال شد</b>" + NL + NL + "🎫 تیکت #" + str(tid), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به تیکت", callback_data="adm_tv_" + str(tid))]]))
        return

    if context.user_data.get("waiting_admin_id"):
        context.user_data["waiting_admin_id"] = False
        if not is_owner(user.id): await update.message.reply_text("❌ فقط مالک"); return
        try: target_id = int(text.strip().replace("@", ""))
        except: await update.message.reply_text("❌ آیدی نامعتبر!\n\nمثال: <code>123456789</code>", parse_mode="HTML"); return
        if target_id == OWNER_ID: await update.message.reply_text("⚠️ این خود مالکه!"); return
        if add_admin(target_id) == "already": await update.message.reply_text(f"⚠️ کاربر <code>{target_id}</code> قبلاً ادمین بوده!", parse_mode="HTML"); return
        await update.message.reply_text(f"✅ <b>ادمین اضافه شد!</b>\n\n🆔 <code>{target_id}</code>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_manage")]]))
        try: await context.bot.send_message(chat_id=target_id, text="🎉 <b>تبریک!</b>\n\nشما به عنوان <b>ادمین</b> این ربات انتخاب شدید.\n\n👇 برای دیدن پنل، /start بزنید.", parse_mode="HTML")
        except: pass
        return

    if context.user_data.get("waiting_remove_id"):
        context.user_data["waiting_remove_id"] = False
        if not is_owner(user.id): await update.message.reply_text("❌ فقط مالک"); return
        try: target_id = int(text.strip().replace("@", ""))
        except: await update.message.reply_text("❌ آیدی نامعتبر!"); return
        if remove_admin(target_id) == "notfound": await update.message.reply_text(f"⚠️ کاربر <code>{target_id}</code> توی لیست ادمین‌ها نیست!", parse_mode="HTML"); return
        await update.message.reply_text(f"✅ <b>ادمین حذف شد!</b>\n\n🆔 <code>{target_id}</code>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_manage")]]))
        return

    if context.user_data.get("waiting_wallet_min"):
        context.user_data["waiting_wallet_min"] = False
        if not is_owner(user.id): return
        clean = text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).replace(",", "").strip()
        if clean.isdigit():
            from config import set_wallet_config
            set_wallet_config("min_amount", int(clean))
            try: await update.message.delete()
            except: pass
            await update.message.chat.send_message("✅ حداقل مبلغ واریز تنظیم شد: <b>" + f"{int(clean):,}" + " تومان</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_wallet_config", style="primary")]]))
        else: await update.message.reply_text("❌ فقط عدد بفرست!")
        return

    if context.user_data.get("waiting_wallet_first_amt"):
        context.user_data["waiting_wallet_first_amt"] = False
        if not is_owner(user.id): return
        clean = text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).replace(",", "").strip()
        if clean.isdigit():
            from config import set_wallet_config
            set_wallet_config("first_amount", int(clean))
            try: await update.message.delete()
            except: pass
            await update.message.chat.send_message("✅ مبلغ اولین بار تنظیم شد: <b>" + f"{int(clean):,}" + " تومان</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="adm_wallet_config", style="primary")]]))
        else: await update.message.reply_text("❌ فقط عدد بفرست!")
        return

    if context.user_data.get("waiting_broadcast"):
        await do_broadcast(update, context); return
    try: log_event(user, "/msg")
    except: pass

    if context.user_data.get("wallet_step") == "waiting_amount":
        clean = text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).replace(",", "").strip()
        if not clean.isdigit(): await update.message.reply_text("❌ فقط عدد بفرستید!"); return
        amount = int(clean)
        from config import get_wallet_config
        cfg = get_wallet_config(); min_amt = cfg.get("min_amount", 100000); first_amt = cfg.get("first_amount", min_amt)
        if amount < min_amt:
            await update.message.reply_text("⚠️ <b>مبلغ وارد شده کمتر از حد مجاز است!</b>" + chr(10) + chr(10) + "💰 <b>حداقل مبلغ مجاز:</b> <code>" + f"{min_amt:,}" + "</code> <b>تومان</b>" + chr(10) + "📌 <b>مبلغ مخصوص اولین واریز:</b> <code>" + f"{first_amt:,}" + "</code> <b>تومان</b>" + chr(10) + chr(10) + "🔢 لطفاً مبلغ بالاتری وارد کنید:", parse_mode="HTML")
            return
        context.user_data["wallet_step"] = "waiting_receipt"; context.user_data["wallet_amount_for_receipt"] = amount
        from datetime import datetime, timezone
        context.user_data["wallet_created_at"] = datetime.now(timezone.utc).isoformat()
        payment_text = "💳 <b>درخواست شارژ ولت</b>" + chr(10) + "━━━━━━━━━━━━━━━━" + chr(10) + chr(10) + "💰 <b>مبلغ قابل پرداخت:</b>" + chr(10) + "<code>" + f"{amount * 10:,}" + "</code> <b>ریال</b>" + chr(10) + chr(10) + "📌 <b>حداقل مبلغ مجاز:</b> " + f"{min_amt:,}" + " تومان" + chr(10) + chr(10) + "💳 <b>شماره کارت:</b>" + chr(10) + "<code>6219861482441127</code>" + chr(10) + chr(10) + "━━━━━━━━━━━━━━━━" + chr(10) + "✅ بعد از واریز، عکس فیش پرداخت رو همینجا بفرست."
        await update.message.reply_text(payment_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="buy_wallet", style="danger")]]))
        return

    if context.user_data.get("wallet_step") == "waiting_receipt":
        await update.message.reply_text("⚠️ لطفاً <b>عکس فیش</b> رو بفرستید، نه متن!", parse_mode="HTML"); return

    if context.user_data.get("waiting_ticket"):
        context.user_data["waiting_ticket"] = False
        pending = context.user_data.get("pending_purchase")
        track_code = product_name = None; price_toman = 0
        if pending:
            track_code = add_purchase(uid=user.id, product_type=pending.get("type", "unknown"), product_name=pending.get("name", "?"), count=pending.get("count", 1), price_toman=pending.get("price_toman", 0), recipient=pending.get("recipient", "—"))
            product_name = pending.get("name", "?"); price_toman = pending.get("price_toman", 0)
            context.user_data.pop("pending_purchase", None)
        tid = create_ticket(user_id=user.id, user_name=get_display_name(user), user_username=user.username or "", message=text)
        if track_code:
            from config import load_tickets, save_tickets
            td = load_tickets()
            if str(tid) in td["tickets"]: td["tickets"][str(tid)]["track_code"] = track_code; save_tickets(td)
            success_msg = "🛍 <b>سفارش شما با موفقیت ثبت شد.</b>" + chr(10) + chr(10) + "📦 <b>محصول:</b> " + str(product_name) + chr(10) + "💰 <b>مبلغ:</b> " + f"{price_toman:,}" + " تومان" + chr(10) + chr(10) + "🔖 <b>شماره سفارش:</b> <code>" + track_code + "</code>" + chr(10) + chr(10) + "✅ <b>وضعیت سفارش:</b> ثبت شده!" + chr(10) + chr(10) + "🛠 سفارش شما در حال بررسیه. به زودی تحویل داده می‌شه." + chr(10) + chr(10) + "📌 <i>شماره سفارش رو نگه دار تا بتونی پیگیری کنی.</i>"
        else:
            success_msg = "✅ <b>پیام شما دریافت شد</b>" + chr(10) + chr(10) + "🎫 شماره تیکت: <code>#" + str(tid) + "</code>" + chr(10) + chr(10) + "🛠 به زودی پاسخ می‌گیرید."
        await update.message.reply_text(success_msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📜 سابقه خرید", callback_data="my_purchases", style="primary")], [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu", style="danger")]]))
        rows = [[InlineKeyboardButton("✅ تایید رسید", callback_data="approve_" + str(tid), style="success"), InlineKeyboardButton("❌ رد رسید", callback_data="reject_" + str(tid), style="danger")], [InlineKeyboardButton("✉️ پاسخ به تیکت #" + str(tid), callback_data="adm_tv_" + str(tid), style="primary")]]
        kb = InlineKeyboardMarkup(rows); targets = [OWNER_ID] + [a.get("uid") for a in load_admins() if a.get("uid") and a.get("uid") != OWNER_ID]
        t = get_ticket(tid); admin_caption = "🔔 <b>تیکت / رسید جدید</b>" + chr(10) + chr(10)
        if track_code: admin_caption += "🛍 <b>سفارش:</b> " + str(product_name) + chr(10) + "💰 <b>مبلغ:</b> " + f"{price_toman:,}" + " تومان" + chr(10) + "🔖 <b>شماره سفارش:</b> <code>" + track_code + "</code>" + chr(10) + chr(10)
        if pending and pending.get("caption"):
            admin_caption += "📝 <b>کپشن کاربر:</b> " + pending.get("caption") + chr(10) + chr(10)
        admin_caption += format_ticket_header(t) + format_ticket_body(t)
        file_id = update.message.photo[-1].file_id if update.message.photo else (update.message.document.file_id if update.message.document else None)
        sent_messages = {}
        for target in targets:
            try:
                msg = await context.bot.send_photo(chat_id=target, photo=file_id, caption=admin_caption, parse_mode="HTML", reply_markup=kb) if file_id else await context.bot.send_message(chat_id=target, text=admin_caption, parse_mode="HTML", reply_markup=kb)
                sent_messages[str(target)] = msg.message_id
            except Exception as e: print(f"[photo] err {target}: {e}")
        save_ticket_messages(tid, sent_messages)
        return
    await update.message.reply_text("برای استفاده از ربات، /start را بزنید.")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"[PHOTO] {user.id}")
    try:
        from telegram import ReactionTypeEmoji
        await context.bot.set_message_reaction(chat_id=user.id, message_id=update.message.message_id, reaction=[ReactionTypeEmoji(emoji="⚡")])
    except: pass

    if context.user_data.get("wallet_step") == "waiting_receipt":
        context.user_data["wallet_step"] = None
        amount = context.user_data.get("wallet_amount_for_receipt", 0); context.user_data.pop("wallet_amount_for_receipt", None)
        tid = create_ticket(user_id=user.id, user_name=get_display_name(user), user_username=user.username or "", message="مبلغ واریزی: " + f"{amount:,}" + " تومان")
        try:
            from config import load_tickets, save_tickets
            td = load_tickets()
            if str(tid) in td["tickets"]: td["tickets"][str(tid)]["track_code"] = "WALLET-" + str(tid); td["tickets"][str(tid)]["wallet_amount"] = amount; save_tickets(td)
        except: pass
        await update.message.reply_text("✅ <b>فیش شما دریافت شد!</b>" + chr(10) + chr(10) + "🎫 شماره پیگیری: <code>#" + str(tid) + "</code>" + chr(10) + chr(10) + "🛠 به زودی ادمین بررسی می‌کنه.", parse_mode="HTML")
        rows = [[InlineKeyboardButton("✅ تایید رسید", callback_data="approve_" + str(tid), style="success"), InlineKeyboardButton("❌ رد رسید", callback_data="reject_" + str(tid), style="danger")], [InlineKeyboardButton("✉️ پاسخ به تیکت #" + str(tid), callback_data="adm_tv_" + str(tid), style="primary")]]
        kb = InlineKeyboardMarkup(rows); targets = [OWNER_ID] + [a.get("uid") for a in load_admins() if a.get("uid") and a.get("uid") != OWNER_ID]
        t = get_ticket(tid); admin_caption = "🔔 <b>درخواست شارژ جدید</b>" + chr(10) + chr(10) + "💳 <b>نوع درخواست: شارژ ولت تلگرام</b>" + chr(10) + "💰 <b>مبلغ واریزی:</b> " + f"{amount:,}" + " تومان" + chr(10) + chr(10) + format_ticket_header(t)
        file_id = update.message.photo[-1].file_id if update.message.photo else (update.message.document.file_id if update.message.document else None)
        sent_messages = {}
        for target in targets:
            try:
                msg = await context.bot.send_photo(chat_id=target, photo=file_id, caption=admin_caption, parse_mode="HTML", reply_markup=kb) if file_id else await context.bot.send_message(chat_id=target, text=admin_caption, parse_mode="HTML", reply_markup=kb)
                sent_messages[str(target)] = msg.message_id
            except Exception as e: print(f"[wallet_receipt] err {target}: {e}")
        save_ticket_messages(tid, sent_messages); return

    if context.user_data.get("waiting_ticket"):
        context.user_data["waiting_ticket"] = False
        pending = context.user_data.get("pending_purchase")
        track_code = product_name = None; price_toman = 0
        if pending:
            track_code = add_purchase(uid=user.id, product_type=pending.get("type", "unknown"), product_name=pending.get("name", "?"), count=pending.get("count", 1), price_toman=pending.get("price_toman", 0), recipient=pending.get("recipient", "—"))
            product_name = pending.get("name", "?"); price_toman = pending.get("price_toman", 0)
            context.user_data.pop("pending_purchase", None)
        ticket_text = update.message.caption or "📷 فیش پرداخت"
        tid = create_ticket(user_id=user.id, user_name=get_display_name(user), user_username=user.username or "", message=ticket_text)
        if track_code:
            from config import load_tickets, save_tickets
            td = load_tickets()
            if str(tid) in td["tickets"]: td["tickets"][str(tid)]["track_code"] = track_code; save_tickets(td)
            success_msg = "🛍 <b>سفارش شما با موفقیت ثبت شد.</b>" + chr(10) + chr(10) + "📦 <b>محصول:</b> " + str(product_name) + chr(10) + "💰 <b>مبلغ:</b> " + f"{price_toman:,}" + " تومان" + chr(10) + chr(10) + "🔖 <b>شماره سفارش:</b> <code>" + track_code + "</code>" + chr(10) + chr(10) + "✅ <b>وضعیت سفارش:</b> ثبت شده!"
        else: success_msg = "✅ <b>پیام شما دریافت شد</b>"
        await update.message.reply_text(success_msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📜 سابقه خرید", callback_data="my_purchases", style="primary")], [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu", style="danger")]]))
        rows = [[InlineKeyboardButton("✅ تایید رسید", callback_data="approve_" + str(tid), style="success"), InlineKeyboardButton("❌ رد رسید", callback_data="reject_" + str(tid), style="danger")], [InlineKeyboardButton("✉️ پاسخ به تیکت #" + str(tid), callback_data="adm_tv_" + str(tid), style="primary")]]
        kb = InlineKeyboardMarkup(rows); targets = [OWNER_ID] + [a.get("uid") for a in load_admins() if a.get("uid") and a.get("uid") != OWNER_ID]
        t = get_ticket(tid); admin_caption = "🔔 <b>تیکت / رسید جدید</b>" + chr(10) + chr(10)
        if track_code: admin_caption += "🛍 <b>سفارش:</b> " + str(product_name) + chr(10) + "💰 <b>مبلغ:</b> " + f"{price_toman:,}" + " تومان" + chr(10) + "🔖 <b>شماره سفارش:</b> <code>" + track_code + "</code>" + chr(10) + chr(10)
        if pending and pending.get("caption"):
            admin_caption += "📝 <b>کپشن کاربر:</b> " + pending.get("caption") + chr(10) + chr(10)
        admin_caption += format_ticket_header(t) + format_ticket_body(t)
        file_id = update.message.photo[-1].file_id if update.message.photo else (update.message.document.file_id if update.message.document else None)
        sent_messages = {}
        for target in targets:
            try:
                msg = await context.bot.send_photo(chat_id=target, photo=file_id, caption=admin_caption, parse_mode="HTML", reply_markup=kb) if file_id else await context.bot.send_message(chat_id=target, text=admin_caption, parse_mode="HTML", reply_markup=kb)
                sent_messages[str(target)] = msg.message_id
            except Exception as e: print(f"[photo] err {target}: {e}")
        save_ticket_messages(tid, sent_messages); return
    await update.message.reply_text("برای استفاده از ربات، /start را بزنید.")
