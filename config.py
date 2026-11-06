#!/usr/bin/env python3
import os, json, random, string
from datetime import datetime, timezone, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8740237434:AAHNtVAM-pA9_du1gd9xGXtos7kxIcLj8Jc"
OWNER_ID = 7380622594
ADMIN_ID = OWNER_ID
SUPPORT_ID = "@YourSupport"
CHANNEL_URL = "https://t.me/BOnlineStars"
REQUIRED_CHANNEL = "@BOnlineStars"
RECEIPT_CHANNEL = "@BOnlineStars"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "user_logs.json")
ADMINS_FILE = os.path.join(BASE_DIR, "admins.json")
TICKETS_FILE = os.path.join(BASE_DIR, "tickets.json")
PRICE_FILE = os.path.join(BASE_DIR, "prices.json")
REFERRAL_FILE = os.path.join(BASE_DIR, "referrals.json")
PREMIUM_PRICE_FILE = os.path.join(BASE_DIR, "premium_prices.json")
GIFT_PRICE_FILE = os.path.join(BASE_DIR, "gift_prices.json")
PURCHASES_FILE = os.path.join(BASE_DIR, "purchases.json")
WALLET_FILE = os.path.join(BASE_DIR, "wallet_config.json")
TICKET_MSG_FILE = os.path.join(BASE_DIR, "ticket_messages.json")

GIFTS = {
    "teddy": ("🧸 تدی", 15), "heart": ("💝 قلب صورتی", 25), "champagne": ("🍾 شامپاین", 50),
    "rocket": ("🚀 موشک", 50), "flowers": ("💐 دسته گل", 50), "cake": ("🎂 کیک", 50),
    "giftbox": ("🎁 جعبه کادو", 50), "rose": ("🌹 گل رز", 50), "ring": ("💍 حلقه", 100),
    "diamond": ("💎 الماس", 100), "cup": ("🏆 کاپ قهرمانی", 200),
}
STAR_PACKS = {50: (50, 0.58), 75: (75, 0.86), 100: (100, 1.15), 200: (200, 2.30)}
PREMIUM_PLANS = {3: (750, 9.19), 6: (1500, 18.38), 12: (3000, 36.76)}

def get_username(user):
    return str(user.username).strip().lstrip("@") if user and user.username else "—"
def get_username_clean(user): return get_username(user)
def get_display_name(user): return user.full_name or user.first_name or "کاربر"

REFERRAL_REWARD = 1
REFERRAL_MIN_WITHDRAW = 50
REFERRAL_MILESTONE = 50

def load_referrals():
    if os.path.exists(REFERRAL_FILE):
        try:
            with open(REFERRAL_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict) and "users" in d: return d
        except: pass
    return {"users": {}, "pending": {}, "counter": 1000}

def save_referrals(d):
    try:
        with open(REFERRAL_FILE, "w", encoding="utf-8") as f: json.dump(d, f, indent=2, ensure_ascii=False)
    except: pass

def generate_ref_code():
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=6))
        used = [u.get("ref_code") for u in load_referrals()["users"].values() if u.get("ref_code")]
        if code not in used: return code

def get_or_create_ref_code(uid):
    d = load_referrals(); uid = str(uid)
    if uid not in d["users"]:
        d["users"][uid] = {"stars": 0, "refs": [], "joined": True, "ref_code": generate_ref_code()}
        save_referrals(d); return d["users"][uid]["ref_code"]
    if not d["users"][uid].get("ref_code"):
        d["users"][uid]["ref_code"] = generate_ref_code(); save_referrals(d)
    return d["users"][uid]["ref_code"]

def find_uid_by_ref_code(code):
    for uid, u in load_referrals()["users"].items():
        if u.get("ref_code") == code: return int(uid)
    return None
def get_user_stars(uid): return load_referrals()["users"].get(str(uid), {}).get("stars", 0)
def get_user_ref_count(uid): return load_referrals()["users"].get(str(uid), {}).get("refs", [])

def register_pending_referral(new_uid, inviter_uid):
    if new_uid == inviter_uid: return None
    d = load_referrals(); new_uid, inviter_uid = str(new_uid), str(inviter_uid)
    if new_uid in d.get("pending", {}): return None
    if inviter_uid not in d["users"]: d["users"][inviter_uid] = {"stars": 0, "refs": [], "joined": True, "ref_code": generate_ref_code()}
    counter = d.get("counter", 1000) + 1; d["counter"] = counter; track_code = "REF-" + str(counter)
    d.setdefault("pending", {})[new_uid] = {"inviter": inviter_uid, "track_code": track_code, "registered_at": datetime.now(timezone.utc).isoformat()}
    save_referrals(d); return track_code

def confirm_purchase_referral(new_uid):
    d = load_referrals(); new_uid = str(new_uid)
    if new_uid not in d.get("pending", {}): return None
    pending = d["pending"][new_uid]; inviter_uid = pending["inviter"]; track_code = pending["track_code"]
    if inviter_uid not in d["users"]: d["users"][inviter_uid] = {"stars": 0, "refs": [], "joined": True, "ref_code": generate_ref_code()}
    if new_uid not in d["users"][inviter_uid]["refs"]:
        d["users"][inviter_uid]["refs"].append(new_uid); d["users"][inviter_uid]["stars"] += REFERRAL_REWARD
    del d["pending"][new_uid]; save_referrals(d)
    return {"inviter": int(inviter_uid), "track_code": track_code, "total_refs": len(d["users"][inviter_uid]["refs"]), "stars": d["users"][inviter_uid]["stars"]}

def withdraw_stars(uid, amount):
    d = load_referrals(); uid = str(uid)
    if uid not in d["users"] or d["users"][uid].get("stars", 0) < amount: return False
    d["users"][uid]["stars"] -= amount; save_referrals(d); return True

def load_purchases():
    if os.path.exists(PURCHASES_FILE):
        try:
            with open(PURCHASES_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict): return d
        except: pass
    return {"counter": 1000, "purchases": {}}
def save_purchases(d):
    try:
        with open(PURCHASES_FILE, "w", encoding="utf-8") as f: json.dump(d, f, indent=2, ensure_ascii=False)
    except: pass

def add_purchase(uid, product_type, product_name, count, price_toman, recipient="—"):
    d = load_purchases(); chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    while True:
        track_code = ''.join(random.choices(chars, k=8))
        if track_code not in [p.get("track_code") for u_p in d.get("purchases", {}).values() for p in u_p]: break
    d.setdefault("purchases", {}).setdefault(str(uid), []).append({"id": track_code, "track_code": track_code, "type": product_type, "name": product_name, "count": count, "price_toman": price_toman, "recipient": recipient, "status": "registered", "created_at": datetime.now(timezone.utc).isoformat()})
    save_purchases(d); return track_code

def get_user_purchases(uid): return load_purchases()["purchases"].get(str(uid), [])
def get_user_purchases_count(uid): return len(get_user_purchases(uid))
def get_user_purchases_total(uid): return sum(p.get("price_toman", 0) for p in get_user_purchases(uid))

STARS_PRICES_FILE = os.path.join(BASE_DIR, "stars_prices.json")
CUSTOM_STAR_FILE = os.path.join(BASE_DIR, "custom_star_price.json")

def load_stars_prices():
    if os.path.exists(STARS_PRICES_FILE):
        try:
            with open(STARS_PRICES_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict): return d
        except: pass
    return {}
def save_stars_prices(d):
    try:
        with open(STARS_PRICES_FILE, "w", encoding="utf-8") as f: json.dump(d, f, indent=2, ensure_ascii=False)
    except: pass
def get_star_pack_price(stars): return int(load_stars_prices().get(str(stars), 0))
def set_star_pack_price(stars, toman):
    d = load_stars_prices(); d[str(stars)] = int(toman); save_stars_prices(d)
def clear_star_pack_price(stars):
    d = load_stars_prices(); d.pop(str(stars), None); save_stars_prices(d)
def get_star_pack_dollar(stars): return round(stars * 0.0115, 2)

def load_custom_star_price():
    if os.path.exists(CUSTOM_STAR_FILE):
        try:
            with open(CUSTOM_STAR_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict) and "price" in d: return int(d["price"])
        except: pass
    return 0
def save_custom_star_price(price):
    try:
        with open(CUSTOM_STAR_FILE, "w", encoding="utf-8") as f: json.dump({"price": int(price)}, f, ensure_ascii=False)
    except: pass
def get_custom_star_price(): return load_custom_star_price()
def set_custom_star_price(price): save_custom_star_price(price)
def clear_custom_star_price():
    if os.path.exists(CUSTOM_STAR_FILE): os.remove(CUSTOM_STAR_FILE)
def get_star_price(): return get_custom_star_price()

def load_wallet_config():
    if os.path.exists(WALLET_FILE):
        try:
            with open(WALLET_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict): return d
        except: pass
    return {"min_amount": 100000, "price_per_unit": 1000, "unit_name": "TET"}
def save_wallet_config(d):
    try:
        with open(WALLET_FILE, "w", encoding="utf-8") as f: json.dump(d, f, indent=2, ensure_ascii=False)
    except: pass
def get_wallet_config(): return load_wallet_config()
def set_wallet_config(key, value):
    d = load_wallet_config(); d[key] = value; save_wallet_config(d)

def load_gift_prices():
    if os.path.exists(GIFT_PRICE_FILE):
        try:
            with open(GIFT_PRICE_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict): return d
        except: pass
    return {}
def save_gift_prices(d):
    try:
        with open(GIFT_PRICE_FILE, "w", encoding="utf-8") as f: json.dump(d, f, indent=2, ensure_ascii=False)
    except: pass
DEFAULT_GIFT_PRICES = {"teddy": 75600, "heart": 126000, "champagne": 252000, "rocket": 252000, "flowers": 252000, "cake": 252000, "giftbox": 252000, "rose": 252000, "ring": 504000, "diamond": 504000, "cup": 1008000}
def get_gift_price(key):
    return int(load_gift_prices().get(key)) if key in load_gift_prices() else DEFAULT_GIFT_PRICES.get(key, GIFTS[key][1]*5040 if key in GIFTS else 0)
def set_gift_price(key, toman):
    d = load_gift_prices(); d[key] = int(toman); save_gift_prices(d)
def clear_gift_price(key):
    d = load_gift_prices(); d.pop(key, None); save_gift_prices(d)

def load_premium_prices():
    if os.path.exists(PREMIUM_PRICE_FILE):
        try:
            with open(PREMIUM_PRICE_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict): return d
        except: pass
    return {}
def save_premium_prices(d):
    try:
        with open(PREMIUM_PRICE_FILE, "w", encoding="utf-8") as f: json.dump(d, f, indent=2, ensure_ascii=False)
    except: pass
DEFAULT_PREMIUM_PRICES = {3: 3025500, 6: 6051000, 12: 12102000}
def get_premium_price(months):
    return int(load_premium_prices().get(str(months))) if str(months) in load_premium_prices() else DEFAULT_PREMIUM_PRICES.get(months, 0)
def set_premium_price(months, toman):
    d = load_premium_prices(); d[str(months)] = int(toman); save_premium_prices(d)
def clear_premium_price(months):
    d = load_premium_prices(); d.pop(str(months), None); save_premium_prices(d)
def get_premium_dollar(months): return PREMIUM_PLANS[months][1] if months in PREMIUM_PLANS else 0

def load_admins():
    if os.path.exists(ADMINS_FILE):
        try:
            with open(ADMINS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list): return data
        except: pass
    return []
def save_admins(admins):
    try:
        with open(ADMINS_FILE, "w", encoding="utf-8") as f: json.dump(admins, f, indent=2, ensure_ascii=False)
    except: pass
def is_owner(uid): return uid == OWNER_ID
def is_admin(uid):
    if uid == OWNER_ID: return True
    for a in load_admins():
        if a.get("uid") == uid: return True
    return False
def add_admin(uid):
    admins = load_admins()
    for a in admins:
        if a.get("uid") == uid: return "already"
    admins.append({"uid": uid, "added_at": datetime.now().isoformat()}); save_admins(admins); return "ok"
def remove_admin(uid):
    admins = load_admins(); new = [a for a in admins if a.get("uid") != uid]
    if len(new) == len(admins): return "notfound"
    save_admins(new); return "ok"

def load_logs():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {"users": {}, "events": []}
def save_logs(d):
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f: json.dump(d, f, indent=2, ensure_ascii=False)
    except: pass
def log_event(user, action):
    try:
        d = load_logs(); uid = str(user.id); now_utc = datetime.now(timezone.utc).isoformat()
        if uid not in d["users"]: d["users"][uid] = {"first_name": user.first_name or "", "username": user.username or "", "first_seen": now_utc, "last_seen": now_utc, "starts": 0}
        d["users"][uid]["first_name"] = user.first_name or ""; d["users"][uid]["username"] = user.username or ""; d["users"][uid]["last_seen"] = now_utc
        if action == "/start": d["users"][uid]["starts"] = d["users"][uid].get("starts", 0) + 1
        d["events"].append({"uid": user.id, "name": user.first_name or "", "username": user.username or "", "action": action, "time": now_utc})
        if len(d["events"]) > 200: d["events"] = d["events"][-200:]
        save_logs(d)
    except Exception as e: print(f"log_event err: {e}")

def load_tickets():
    if os.path.exists(TICKETS_FILE):
        try:
            with open(TICKETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict): return data
        except: pass
    return {"counter": 1000, "tickets": {}}
def save_tickets(d):
    try:
        with open(TICKETS_FILE, "w", encoding="utf-8") as f: json.dump(d, f, indent=2, ensure_ascii=False)
    except: pass
def create_ticket(user_id, user_name, user_username, message):
    d = load_tickets(); tid = d.get("counter", 1000) + 1; d["counter"] = tid
    d["tickets"][str(tid)] = {"id": tid, "user_id": user_id, "user_name": user_name, "user_username": user_username, "messages": [{"from": "user", "text": message, "time": datetime.now().isoformat()}], "status": "open", "created_at": datetime.now().isoformat()}
    save_tickets(d); return tid
def add_ticket_message(tid, from_type, text):
    d = load_tickets(); tid = str(tid)
    if tid not in d["tickets"]: return False
    d["tickets"][tid]["messages"].append({"from": from_type, "text": text, "time": datetime.now().isoformat()})
    if from_type == "admin": d["tickets"][tid]["status"] = "answered"
    save_tickets(d); return True
def get_ticket(tid): return load_tickets()["tickets"].get(str(tid))
def close_ticket(tid):
    d = load_tickets(); tid = str(tid)
    if tid in d["tickets"]: d["tickets"][tid]["status"] = "closed"; save_tickets(d); return True
    return False

def format_ticket_header(ticket):
    name, uname, uid, tid = ticket.get("user_name", "کاربر"), ticket.get("user_username", ""), ticket.get("user_id", 0), ticket.get("id", 0)
    user_line = '<a href="https://t.me/' + uname + '">' + name + '</a> | <code>@' + uname + '</code>' if uname else '<a href="tg://user?id=' + str(uid) + '">' + name + '</a>'
    return "🎫 <b>تیکت #" + str(tid) + "</b>\n━━━━━━━━━━━━━━━━\n👤 " + user_line + "\n🆔 <code>" + str(uid) + "</code>\n━━━━━━━━━━━━━━━━\n\n"
def format_ticket_body(ticket, max_msgs=10):
    msgs = ticket.get("messages", []); msgs = msgs[-max_msgs:] if len(msgs) > max_msgs else msgs
    text = ""
    for m in msgs:
        frm, msg_text, t = m.get("from", "user"), m.get("text", ""), m.get("time", "")[11:16] if len(m.get("time", "")) > 16 else "?"
        text += ("👤 <b>کاربر:</b>\n" if frm == "user" else "🛠 <b>پشتیبانی:</b>\n") + msg_text + "\n<i>" + t + "</i>\n\n"
    return text
def get_all_open_tickets():
    result = [t for t in load_tickets()["tickets"].values() if t.get("status") != "closed"]
    result.sort(key=lambda x: x.get("created_at", ""), reverse=True); return result

def build_receipt_text(user_id, product_name, price_toman, track_code, created_at, paid_at=None):
    iran_tz = timezone(timedelta(hours=3, minutes=30))
    try: created_ir = (datetime.fromisoformat(created_at).replace(tzinfo=timezone.utc) if datetime.fromisoformat(created_at).tzinfo is None else datetime.fromisoformat(created_at)).astimezone(iran_tz)
    except: created_ir = datetime.now(iran_tz)
    try: paid_ir = (datetime.fromisoformat(paid_at).replace(tzinfo=timezone.utc) if datetime.fromisoformat(paid_at).tzinfo is None else datetime.fromisoformat(paid_at)).astimezone(iran_tz) if paid_at else datetime.now(iran_tz)
    except: paid_ir = datetime.now(iran_tz)
    uid_str = str(user_id); masked_id = uid_str[:3] + "···" + uid_str[-2:] if len(uid_str) > 6 else uid_str
    return "🔥 <b>سفارش " + str(track_code) + " با موفقیت تحویل شد!</b>\n\n⚡️⚡️⚡️⚡️⚡️⚡️⚡️⚡️⚡️\n🎯 <b>" + str(product_name) + "</b>\n👤 خریدار: <code>" + masked_id + "</code>\n💸 مبلغ: <b>" + f"{price_toman:,}" + "</b> تومان\n🎫 کد پیگیری: <code>" + str(track_code) + "</code>\n📅 " + created_ir.strftime("%Y/%m/%d") + " | ثبت: " + created_ir.strftime("%H:%M:%S") + " | تحویل: " + paid_ir.strftime("%H:%M:%S") + "\n🚀 سرعت تحویل: <b>0.3 ثانیه</b>\n⚡️⚡️⚡️⚡️⚡️⚡️⚡️⚡️⚡️\n\n✅ <b>پرداخت انجام شد، سفارش تحویل داده شد.</b>\n\n🛒 خرید از: <b>@BOnlineStars</b>"

async def send_ticket_to_admins(bot, ticket, extra_text="", exclude_id=None):
    text = extra_text + format_ticket_header(ticket) + format_ticket_body(ticket); tid = ticket.get("id", 0)
    rows = [[InlineKeyboardButton("✅ تایید رسید", callback_data="approve_" + str(tid), style="success"), InlineKeyboardButton("❌ رد رسید", callback_data="reject_" + str(tid), style="danger")], [InlineKeyboardButton("✉️ پاسخ به تیکت #" + str(tid), callback_data="adm_tv_" + str(tid), style="primary")]]
    kb = InlineKeyboardMarkup(rows); targets = [OWNER_ID] if OWNER_ID != exclude_id else []
    targets += [a.get("uid") for a in load_admins() if a.get("uid") and a.get("uid") != OWNER_ID and a.get("uid") != exclude_id]
    targets = list(set(targets)); sent_messages = {}
    for t in targets:
        try:
            msg = await bot.send_message(chat_id=t, text=text, parse_mode="HTML", reply_markup=kb)
            sent_messages[str(t)] = msg.message_id
        except Exception as e: print(f"[ticket] err {t}: {e}")
    try: save_ticket_messages(tid, sent_messages)
    except: pass

def save_ticket_messages(tid, messages):
    try:
        d = json.load(open(TICKET_MSG_FILE, "r")) if os.path.exists(TICKET_MSG_FILE) else {}
        d[str(tid)] = messages; json.dump(d, open(TICKET_MSG_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    except Exception as e: print(f"[save_ticket_messages] err: {e}")
def load_ticket_messages(tid):
    if os.path.exists(TICKET_MSG_FILE):
        try:
            d = json.load(open(TICKET_MSG_FILE, "r")); return d.get(str(tid), {})
        except: pass
    return {}

def calc_toman(stars_count):
    return int(stars_count * get_star_price())

def calc_dollar(stars_count):
    return round(stars_count * 0.0115, 2)
