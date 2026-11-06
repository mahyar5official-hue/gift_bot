import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import STAR_PACKS, get_username, get_star_pack_price, get_star_pack_dollar
from shop import stars_menu, stars_text
logger = logging.getLogger(__name__)
NL = chr(10)

async def handle_stars(query, data, user, context):
    if data == "buy_stars":
        amount = 100; recipient = get_username(user)
        context.user_data["stars_selected"] = amount; context.user_data["recipient"] = recipient
        await query.edit_message_text(stars_text(user, amount, get_star_pack_price(amount), get_star_pack_dollar(amount), recipient), parse_mode="HTML", reply_markup=stars_menu(user, amount, recipient))
        return True
    if data.startswith("stars_") and data[6:].isdigit():
        amount = int(data[6:])
        if amount in STAR_PACKS:
            context.user_data["stars_selected"] = amount
            recipient = context.user_data.get("recipient", get_username(user))
            await query.edit_message_text(stars_text(user, amount, get_star_pack_price(amount), get_star_pack_dollar(amount), recipient), parse_mode="HTML", reply_markup=stars_menu(user, amount, recipient))
        return True
    if data == "stars_set_count":
        await query.answer("از دکمه‌های بالا تعداد رو انتخاب کن", show_alert=True); return True
    if data == "stars_custom":
        context.user_data["waiting_custom_stars"] = True
        await query.edit_message_text("✏️ <b>تعداد دلخواه استارز</b>" + NL + NL + "🔢 عدد مورد نظر رو بفرست:" + NL + NL + "⚠️ حداقل: <b>50</b> استارز" + NL + "💡 مثال: <code>150</code>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="buy_stars", style="danger")]]))
        return True
    if data == "stars_confirm":
        amount = context.user_data.get("stars_selected", 100)
        recipient = context.user_data.get("recipient", get_username(user))
        from config import get_star_price
        toman = get_star_pack_price(amount) if amount in STAR_PACKS else amount * get_star_price()
        context.user_data["pending_purchase"] = {"type": "stars", "name": str(amount) + " استارز", "count": amount, "price_toman": toman, "recipient": recipient}
        from shop_handlers import payment_text, payment_keyboard
        await query.edit_message_text(payment_text(title="⭐ " + str(amount) + " استارز", amount_toman=toman, recipient=recipient), parse_mode="HTML", reply_markup=payment_keyboard(toman))
        return True
    return False
