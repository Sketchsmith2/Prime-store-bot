#!/usr/bin/env python3
import telebot
import json
import os
import random
import string
from datetime import datetime
import time
import traceback
import qrcode
import io
from PIL import Image
from flask import Flask
import threading
import pytz

# ===== CONFIGURATION =====
TOKEN = os.environ.get('BOT_TOKEN', "8931616308:AAHwwwjGhxxpM_6S00o1eBshSKT3aTC8iWM")
ADMIN_ID = int(os.environ.get('ADMIN_ID', 939433537))
CO_ADMIN_USERNAME = "Prime_Blogs"
CO_ADMIN_CHAT_ID = 939433537
OWNER_UPI = os.environ.get('OWNER_UPI', "8218957984@seyes")
OWNER_PHONE = os.environ.get('OWNER_PHONE', "8218957984")
STORE_NAME = "Prime Store"

# ===== TIME ZONE =====
IST = pytz.timezone('Asia/Kolkata')

def get_indian_time():
    return datetime.now(IST).strftime('%d-%m-%Y %I:%M:%S %p')

# ===== FILE PATHS =====
DATA_FILE = "store_data.json"
ORDERS_FILE = "orders.json"
JSON_FILES_DIR = "json_files/"
BACKUP_DIR = "backups/"

os.makedirs(JSON_FILES_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# ===== BOT INITIALIZE =====
bot = telebot.TeleBot(TOKEN)

try:
    bot.delete_webhook()
    print("✅ Webhook deleted")
except:
    pass

# ===== ADMIN CHECK =====
def is_admin(user_id, username):
    return user_id == ADMIN_ID or username == CO_ADMIN_USERNAME

# ===== QR CODE =====
def generate_upi_qr(upi_id, amount, name=STORE_NAME):
    try:
        upi_url = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR"
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=2)
        qr.add_data(upi_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    except Exception as e:
        print(f"QR Error: {e}")
        return None

# ===== INITIAL FILES =====
def create_initial_files():
    if not os.path.exists(DATA_FILE):
        data = {"products": {"coupons": [], "json_files": []}}
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'w') as f:
            json.dump({"orders": []}, f, indent=2)

create_initial_files()

# ===== DATA FUNCTIONS =====
def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_orders():
    with open(ORDERS_FILE, 'r') as f:
        return json.load(f)

def save_orders(data):
    with open(ORDERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def generate_order_id():
    return "ORD" + ''.join(random.choices(string.digits, k=8))

# ============================================================
# ===== CREATE ITEM (JSON FILE or COUPON CODE) =====
# ============================================================
def create_single_order_file(order, index=1):
    order_id = order['order_id']
    product_name = order['product']
    category_key = order.get('category_key', 'json_files')

    data = load_data()
    product = None
    for p in data['products'][category_key]:
        if p['name'] == product_name:
            product = p
            break

    if not product or 'data' not in product or len(product['data']) == 0:
        return None, None, None

    item = product['data'][0]

    # ===== COUPON =====
    if category_key == 'coupons':
        code = item.get('code', 'UNKNOWN')
        product['data'].pop(0)
        product['stock'] = len(product['data'])
        save_data(data)
        return None, None, code

    # ===== JSON FILES (Full JSON as it is) =====
    product_lower = product_name.lower()
    if 'flipkart' in product_lower: prefix = 'flipkart'
    elif 'bigbasket' in product_lower: prefix = 'bigbasket'
    elif 'meesho 120' in product_lower: prefix = 'meesho_120'
    elif 'meesho 170' in product_lower: prefix = 'meesho_170'
    elif 'meesho 175' in product_lower: prefix = 'meesho_175'
    else: prefix = 'account'

    if item.get('mobile'): identifier = str(item['mobile']).replace('+', '').replace(' ', '')
    elif item.get('phone'): identifier = str(item['phone']).replace('+', '').replace(' ', '')
    elif item.get('mId'): identifier = str(item['mId']).replace('=', '').replace('/', '')
    else: identifier = f"idx{index}"

    filename = f"{prefix}_{identifier}.json"
    filepath = os.path.join(JSON_FILES_DIR, filename)

    with open(filepath, 'w') as f:
        json.dump(item, f, indent=2)

    product['data'].pop(0)
    product['stock'] = len(product['data'])
    save_data(data)
    return filename, filepath, identifier

# ============================================================
# ===== MAIN MENU =====
# ============================================================
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("🛒 Shop Now", callback_data="shop"),
        telebot.types.InlineKeyboardButton("📦 My Orders", callback_data="my_orders"),
        telebot.types.InlineKeyboardButton("❓ Help", callback_data="help"),
        telebot.types.InlineKeyboardButton("📞 Support", callback_data="support")
    )
    bot.send_message(message.chat.id, "🏪 *PRIME STORE*\n\nWelcome! Use menu below.", reply_markup=markup, parse_mode='Markdown')

# ============================================================
# ===== SHOP =====
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data == "shop")
def shop(call):
    data = load_data()
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    json_stock = sum(p.get('stock', 0) for p in data['products']['json_files'])
    coupon_stock = sum(p.get('stock', 0) for p in data['products']['coupons'])
    markup.add(
        telebot.types.InlineKeyboardButton(f"🎫 Coupons ({coupon_stock})", callback_data="cat_coupons"),
        telebot.types.InlineKeyboardButton(f"📁 JSON Files ({json_stock})", callback_data="cat_json"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    bot.edit_message_text("🛍️ Select Category:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "cat_coupons")
def cat_coupons(call):
    data = load_data()
    products = data['products']['coupons']
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for i, p in enumerate(products):
        stock = p.get('stock', 0)
        emoji = "🟢" if stock > 0 else "🔴"
        markup.add(telebot.types.InlineKeyboardButton(f"{emoji} {p['name']} - ₹{p['price']} ({stock})", callback_data=f"buy_coupon_{i}"))
    markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="shop"))
    bot.edit_message_text("🎫 Coupons:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "cat_json")
def cat_json(call):
    data = load_data()
    products = data['products']['json_files']
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for i, p in enumerate(products):
        stock = p.get('stock', 0)
        emoji = "🟢" if stock > 0 else "🔴"
        markup.add(telebot.types.InlineKeyboardButton(f"{emoji} {p['name']} - ₹{p['price']} ({stock})", callback_data=f"buy_json_{i}"))
    markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="shop"))
    bot.edit_message_text("📁 JSON Files:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# ============================================================
# ===== BUY PRODUCT (Quantity Selection) =====
# ============================================================
user_selection = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def buy_product(call):
    data = load_data()
    parts = call.data.split('_')
    category = parts[1]
    index = int(parts[2])
    category_key = "coupons" if category == "coupon" else "json_files"
    products = data['products'][category_key]

    if index >= len(products):
        bot.answer_callback_query(call.id, "❌ Not available!")
        return

    product = products[index]
    stock = product.get('stock', 0)

    if stock <= 0:
        bot.answer_callback_query(call.id, "❌ Out of stock!")
        return

    user_selection[call.from_user.id] = {"category": category, "category_key": category_key, "index": index, "product": product, "stock": stock}

    markup = telebot.types.InlineKeyboardMarkup(row_width=5)
    max_qty = min(50, stock)
    for start in range(1, 51, 10):
        row = [telebot.types.InlineKeyboardButton(f"{q}", callback_data=f"qty_{q}") for q in range(start, start + 10) if q <= max_qty]
        if row: markup.row(*row)

    markup.add(telebot.types.InlineKeyboardButton("❌ Cancel", callback_data="shop"))
    
    bot.edit_message_text(
        f"📦 {product['name']}\n💰 ₹{product['price']}\n📦 Stock: {stock}\n\nSelect Quantity:",
        chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup
    )

# ============================================================
# ===== QUANTITY SELECTED (Payment & QR) =====
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('qty_'))
def quantity_selected(call):
    qty = int(call.data.split('_')[1])
    if call.from_user.id not in user_selection:
        bot.answer_callback_query(call.id, "❌ Session expired! /start")
        return

    sel = user_selection[call.from_user.id]
    product = sel['product']
    stock = sel['stock']

    if qty > stock:
        bot.answer_callback_query(call.id, f"❌ Only {stock} available!")
        return

    order_id = generate_order_id()
    total_price = product['price'] * qty

    orders = load_orders()
    orders['orders'].append({
        "order_id": order_id, "user_id": call.from_user.id,
        "username": call.from_user.username or call.from_user.first_name,
        "product": product['name'], "category_key": sel['category_key'],
        "product_index": sel['index'], "price": product['price'], "quantity": qty,
        "total": total_price, "status": "pending", "payment": "unpaid",
        "reference": None, "created_at": get_indian_time()
    })
    save_orders(orders)
    del user_selection[call.from_user.id]

    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

    # Send QR
    qr_bytes = generate_upi_qr(OWNER_UPI, total_price)
    if qr_bytes:
        qr_msg = bot.send_photo(call.message.chat.id, qr_bytes, caption=f"📱 Scan to Pay ₹{total_price}")
    
    payment_msg = (
        f"💳 PAYMENT REQUIRED\n━━━━━━━━━━━━━━\n\n"
        f"🆔 Order: {order_id}\n"
        f"📦 Product: {product['name']}\n"
        f"💵 Total: ₹{total_price}\n\n"
        f"📤 UPI: {OWNER_UPI}\n\n"
        f"✅ Pay & Click 'I Have Paid'"
    )

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("✅ I Have Paid", callback_data=f"paid_{order_id}"),
        telebot.types.InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{order_id}_{qr_msg.message_id if qr_bytes else 0}"),
    )
    bot.send_message(call.message.chat.id, payment_msg, reply_markup=markup)

# ============================================================
# ===== CANCEL ORDER (Delete QR + Msg) =====
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_'))
def cancel_order(call):
    parts = call.data.split('_')
    order_id = parts[1]
    qr_msg_id = int(parts[2]) if len(parts) > 2 else 0

    orders = load_orders()
    for order in orders['orders']:
        if order['order_id'] == order_id:
            order['status'] = "cancelled"
            break
    save_orders(orders)

    # Delete QR
    if qr_msg_id != 0:
        try: bot.delete_message(call.message.chat.id, qr_msg_id)
        except: pass
    
    # Delete Payment Message
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

    bot.send_message(call.message.chat.id, "❌ Order Cancelled.")
    bot.answer_callback_query(call.id, "❌ Cancelled")

# ============================================================
# ===== PAYMENT DONE (Reference Validate) =====
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('paid_'))
def payment_done(call):
    order_id = call.data.split('_')[1]
    msg = bot.send_message(call.message.chat.id, f"📝 Send UTR / Reference for `{order_id}`\n(Any number/letter is fine)", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_reference, order_id)

def process_reference(message, order_id):
    reference = message.text.strip() if message.text else ""
    
    if len(reference) < 1: # Changed from 3 to 1
        msg = bot.send_message(message.chat.id, "❌ Invalid! Send again:")
        bot.register_next_step_handler(msg, process_reference, order_id)
        return

    orders = load_orders()
    order_found = None
    for order in orders['orders']:
        if order['order_id'] == order_id:
            order_found = order
            break

    if not order_found: return

    order_found['payment'] = "submitted"
    order_found['reference'] = reference
    order_found['paid_at'] = get_indian_time()
    save_orders(orders)

    bot.send_message(message.chat.id, "✅ PAYMENT SUBMITTED!\nWaiting for admin approval...")

    # Admin msg
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{order_id}"),
        telebot.types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{order_id}")
    )
    bot.send_message(ADMIN_ID, f"🟢 PAYMENT RECEIVED\n🆔 {order_id}\n📦 {order_found['product']}\n💰 ₹{order_found['total']}\n📝 Ref: {reference}", reply_markup=markup)

# ============================================================
# ===== ADMIN APPROVE (Delivery) =====
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_'))
def admin_approve(call):
    if not is_admin(call.from_user.id, call.from_user.username): return

    order_id = call.data.replace('approve_', '')
    orders = load_orders()
    order_found = None
    for order in orders['orders']:
        if order['order_id'] == order_id:
            order_found = order
            break

    if not order_found or order_found['status'] == "delivered": return

    qty = order_found['quantity']
    category_key = order_found.get('category_key', 'json_files')

    files_created = []
    items_delivered = []
    for i in range(1, qty + 1):
        filename, filepath, item_id = create_single_order_file(order_found, i)
        if item_id is None: return # Out of stock
        if filename is not None: files_created.append((filename, filepath))
        items_delivered.append(item_id)

    if category_key == 'coupons':
        code_list = "\n".join([f"🔑 `{c}`" for c in items_delivered])
        bot.send_message(order_found['user_id'], f"🎉 *Payment Successful!*\n\n🧾 Order: `{order_id}`\n\n{code_list}", parse_mode='Markdown')
    else:
        bot.send_message(order_found['user_id'], f"✅ *ORDER DELIVERED!*\n\n🆔 Order: `{order_id}`", parse_mode='Markdown')
        for filename, filepath in files_created:
            with open(filepath, 'rb') as f:
                bot.send_document(order_found['user_id'], f, caption=f"🎁 `{filename}`", parse_mode='Markdown')
            os.remove(filepath)

    order_found['status'] = "delivered"
    order_found['delivered_at'] = get_indian_time()
    save_orders(orders)

    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.answer_callback_query(call.id, "✅ Delivered!")

# ============================================================
# ===== ADMIN REJECT =====
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def admin_reject(call):
    if not is_admin(call.from_user.id, call.from_user.username): return
    order_id = call.data.replace('reject_', '')
    orders = load_orders()
    for order in orders['orders']:
        if order['order_id'] == order_id:
            order['status'] = "cancelled"
            bot.send_message(order['user_id'], "❌ ORDER REJECTED\nContact: @Prime_Blogs")
            break
    save_orders(orders)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

# ============================================================
# ===== MY ORDERS & STOCK =====
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data == "my_orders")
def my_orders(call):
    orders = load_orders()
    user_orders = [o for o in orders['orders'] if o['user_id'] == call.from_user.id]
    if not user_orders:
        bot.answer_callback_query(call.id, "📭 No orders!")
        return
    text = "📦 YOUR ORDERS\n\n"
    for o in user_orders[-10:]:
        emoji = {"pending": "⏳", "delivered": "✅", "cancelled": "❌"}.get(o['status'], "❓")
        text += f"{emoji} {o['order_id']} - {o['product']} (x{o['quantity']})\n"
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main"))
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.message_handler(commands=['stock'])
def stock_check(message):
    if not is_admin(message.from_user.id, message.from_user.username): return
    data = load_data()
    text = "📦 *STOCK STATUS*\n\n"
    text += "🎫 *COUPONS:*\n"
    for p in data['products']['coupons']:
        text += f"   {p['name']}: {p.get('stock', 0)} (₹{p['price']})\n"
    text += "\n📁 *JSON FILES:*\n"
    for p in data['products']['json_files']:
        text += f"   {p['name']}: {p.get('stock', 0)} (₹{p['price']})\n"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    start(call.message)

# ============================================================
# ===== START BOT =====
# ============================================================
if __name__ == "__main__":
    print("🚀 Bot Starting...")
    
    app = Flask(__name__)
    @app.route('/')
    def home(): return "Bot Running"
    def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    threading.Thread(target=run_flask, daemon=True).start()

    bot.infinity_polling(timeout=60, long_polling_timeout=30)