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

# ===== DATA FUNCTIONS =====
def create_initial_files():
    if not os.path.exists(DATA_FILE):
        data = {"products": {"coupons": [], "json_files": []}}
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'w') as f:
            json.dump({"orders": []}, f, indent=2)

create_initial_files()

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
# ===== CORE LOGIC: AUTO REMOVE & FILE GENERATION =====
# ============================================================
def process_delivery(order, index=1):
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

    # ✅ COUPON LOGIC (No File, Only Code)
    if category_key == 'coupons':
        code = item.get('code', 'UNKNOWN')
        product['data'].pop(0) # Remove from stock
        product['stock'] = len(product['data'])
        save_data(data)
        return None, None, code

    # ✅ JSON LOGIC (File Generate & Remove)
    product_lower = product_name.lower()
    prefix = 'account'
    if 'flipkart' in product_lower: prefix = 'flipkart'
    elif 'bigbasket' in product_lower: prefix = 'bigbasket'
    elif 'meesho 120' in product_lower: prefix = 'meesho_120'
    elif 'meesho 170' in product_lower: prefix = 'meesho_170'
    elif 'meesho 175' in product_lower: prefix = 'meesho_175'
    elif 'meesho 195' in product_lower: prefix = 'meesho_195'
    elif 'meesho' in product_lower: prefix = 'meesho'

    # Get Identifier
    identifier = f"idx{index}"
    if item.get('mobile'): identifier = str(item['mobile']).replace('+', '').replace(' ', '')
    elif item.get('phone'): identifier = str(item['phone']).replace('+', '').replace(' ', '')
    elif item.get('mId'): identifier = str(item['mId']).replace('=', '').replace('/', '')
    elif item.get('accountId'): identifier = str(item['accountId']).replace('=', '').replace('/', '')

    filename = f"{prefix}_{identifier}.json"
    filepath = os.path.join(JSON_FILES_DIR, filename)

    # Save Full JSON to file
    with open(filepath, 'w') as f:
        json.dump(item, f, indent=2)

    # 🚀 AUTO REMOVE FROM DATABASE (No manual work needed)
    product['data'].pop(0)
    product['stock'] = len(product['data'])
    save_data(data)

    return filename, filepath, identifier

# ============================================================
# ===== USER MENUS =====
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
    bot.send_message(message.chat.id,
        f"✨ Welcome {message.from_user.first_name}!\n\n"
        "🏪 PRIME STORE\n"
        "━━━━━━━━━━━━━━\n"
        "🛍️ Premium Digital Products\n\n"
        "💳 Secure Payments\n"
        "📞 Support: @Prime_Blogs",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "shop")
def shop(call):
    data = load_data()
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    json_stock = sum(p.get('stock', 0) for p in data['products']['json_files'])
    coupon_stock = sum(p.get('stock', 0) for p in data['products']['coupons'])
    
    markup.add(
        telebot.types.InlineKeyboardButton(f"🎫 Coupons ({coupon_stock})", callback_data="cat_coupons"),
        telebot.types.InlineKeyboardButton(f"📁 JSON Files ({json_stock})", callback_data="cat_json"),
        telebot.types.InlineKeyboardButton("📞 Support", callback_data="support"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    try:
        bot.edit_message_text(
            "🛍️ CATEGORIES\n━━━━━━━━━━━━━━\n\nSelect a category:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "cat_json")
def cat_json(call):
    data = load_data()
    products = data['products']['json_files']
    if not products:
        bot.answer_callback_query(call.id, "❌ No JSON files available!", show_alert=True)
        return
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for i, p in enumerate(products):
        stock = p.get('stock', 0)
        emoji = "🟢" if stock > 0 else "🔴"
        markup.add(telebot.types.InlineKeyboardButton(f"{emoji} {p['name']} - ₹{p['price']} ({stock})", callback_data=f"buy_json_{i}"))
    
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="shop"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    bot.edit_message_text(
        "📁 JSON FILES\n━━━━━━━━━━━━━━\n\nSelect a file:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "cat_coupons")
def cat_coupons(call):
    data = load_data()
    products = data['products']['coupons']
    if not products:
        bot.answer_callback_query(call.id, "❌ No coupons available!", show_alert=True)
        return
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for i, p in enumerate(products):
        stock = p.get('stock', 0)
        emoji = "🟢" if stock > 0 else "🔴"
        markup.add(telebot.types.InlineKeyboardButton(
            f"{emoji} {p['name']} - ₹{p['price']} ({stock})",
            callback_data=f"buy_coupon_{i}"
        ))
    
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="shop"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    bot.edit_message_text(
        "🎫 COUPONS\n━━━━━━━━━━━━━━\n\nSelect a coupon:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

# ============================================================
# ===== BUY & QUANTITY (PRO UI) =====
# ============================================================
user_selection = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def buy_product(call):
    data = load_data()
    parts = call.data.split('_')
    category = parts[1]
    index = int(parts[2])
    category_map = {"coupon": "coupons", "json": "json_files"}
    category_key = category_map.get(category)
    products = data['products'][category_key]

    if index >= len(products):
        bot.answer_callback_query(call.id, "❌ Not available!", show_alert=True)
        return

    product = products[index]
    stock = product.get('stock', 0)

    if stock <= 0:
        bot.answer_callback_query(call.id, "❌ Out of stock!", show_alert=True)
        return

    if category_key == 'coupons' and product.get('sub_category'):
        bot.send_message(call.message.chat.id, f"📌 *Info:*\n{product['sub_category']}", parse_mode='Markdown')

    user_selection[call.from_user.id] = {
        "category": category,
        "category_key": category_key,
        "index": index,
        "product": product,
        "stock": stock
    }

    markup = telebot.types.InlineKeyboardMarkup(row_width=5)
    row = []
    for q in range(1, min(5, stock) + 1):
        row.append(telebot.types.InlineKeyboardButton(f"{q}", callback_data=f"qty_{q}"))
    if row: markup.row(*row)
    
    if stock > 5:
        markup.add(telebot.types.InlineKeyboardButton("✍️ Custom Qty", callback_data="custom_qty"))
        
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="shop"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )

    bot.edit_message_text(
        f"📝 SELECT QUANTITY\n━━━━━━━━━━━━━━\n\n"
        f"📦 {product['name']}\n"
        f"💰 ₹{product['price']} each\n"
        f"📦 Stock: {stock}\n\n"
        f"Select quantity:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('qty_'))
def quantity_selected(call):
    qty = int(call.data.split('_')[1])
    if call.from_user.id not in user_selection:
        bot.answer_callback_query(call.id, "❌ Session expired!", show_alert=True)
        return
    
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    process_order(call.message.chat.id, call.from_user.id, qty)

@bot.callback_query_handler(func=lambda call: call.data == "custom_qty")
def custom_quantity_prompt(call):
    if call.from_user.id not in user_selection:
        bot.answer_callback_query(call.id, "❌ Session expired!", show_alert=True)
        return
        
    stock = user_selection[call.from_user.id]['stock']
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    
    msg = bot.send_message(call.message.chat.id, f"✍️ *Custom Quantity*\n\nReply with a number (1 to {stock}):", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_custom_quantity)

def process_custom_quantity(message):
    try: qty = int(message.text.strip())
    except: 
        bot.reply_to(message, "❌ Invalid number. Start again.")
        return

    if message.from_user.id not in user_selection:
        bot.send_message(message.chat.id, "❌ Session expired.")
        return

    stock = user_selection[message.from_user.id]['stock']
    if qty < 1 or qty > stock:
        bot.reply_to(message, f"❌ Quantity must be between 1 and {stock}.")
        return

    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    process_order(message.chat.id, message.from_user.id, qty)

def process_order(chat_id, user_id, qty):
    selection = user_selection[user_id]
    product = selection['product']
    order_id = generate_order_id()
    total_price = product['price'] * qty

    orders = load_orders()
    orders['orders'].append({
        "order_id": order_id,
        "user_id": user_id,
        "username": bot.get_chat(user_id).username or bot.get_chat(user_id).first_name,
        "product": product['name'],
        "category_key": selection['category_key'],
        "product_index": selection['index'],
        "price": product['price'],
        "quantity": qty,
        "total": total_price,
        "status": "pending",
        "payment": "unpaid",
        "reference": None,
        "created_at": get_indian_time()
    })
    save_orders(orders)
    del user_selection[user_id]

    try:
        qr_bytes = generate_upi_qr(OWNER_UPI, total_price)
        if qr_bytes:
            bot.send_photo(chat_id, qr_bytes, caption=f"📱 Scan to Pay ₹{total_price}\nUPI: {OWNER_UPI}")
    except: pass

    payment_msg = (
        f"💳 PAYMENT REQUIRED\n━━━━━━━━━━━━━━\n\n"
        f"🆔 Order: {order_id}\n"
        f"📦 Product: {product['name']}\n"
        f"📦 Quantity: {qty}\n"
        f"💵 Total: ₹{total_price}\n\n"
        f"📤 UPI: {OWNER_UPI}\n"
        f"✅ Click 'I Have Paid' after payment"
    )

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("✅ I Have Paid", callback_data=f"paid_{order_id}"),
        telebot.types.InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{order_id}"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    bot.send_message(chat_id, payment_msg, reply_markup=markup)

# ============================================================
# ===== PAYMENT FLOW (VANISH FEATURE) =====
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_'))
def cancel_order(call):
    order_id = call.data.split('_')[1]
    orders = load_orders()
    for order in orders['orders']:
        if order['order_id'] == order_id and order['user_id'] == call.from_user.id:
            order['status'] = "cancelled"
            break
    save_orders(orders)
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    bot.send_message(call.message.chat.id, f"❌ Order cancelled.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('paid_'))
def payment_done(call):
    order_id = call.data.split('_')[1]
    orders = load_orders()
    order_found = next((o for o in orders['orders'] if o['order_id'] == order_id and o['user_id'] == call.from_user.id), None)

    if not order_found or order_found['status'] == "delivered":
        bot.answer_callback_query(call.id, "❌ Invalid or delivered!", show_alert=True)
        return

    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

    bot.answer_callback_query(call.id, "📝 Send reference now!")
    msg = bot.send_message(call.message.chat.id, f"📝 Send payment reference/UTR for Order {order_id}")
    bot.register_next_step_handler(msg, process_reference, order_id)

def process_reference(message, order_id):
    reference = message.text.strip() if message.text else ""
    if len(reference) < 3:
        msg = bot.send_message(message.chat.id, "❌ Invalid! Send again:")
        bot.register_next_step_handler(msg, process_reference, order_id)
        return

    orders = load_orders()
    order_found = next((o for o in orders['orders'] if o['order_id'] == order_id), None)
    if not order_found: return

    order_found['payment'] = "submitted"
    order_found['reference'] = reference
    order_found['paid_at'] = get_indian_time()
    save_orders(orders)

    bot.send_message(message.chat.id, f"✅ PAYMENT SUBMITTED!\n\n⏳ Waiting for admin approval...")

    admin_msg = (
        f"🟢 PAYMENT RECEIVED\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"🆔 Order: {order_id}\n"
        f"👤 User: @{order_found.get('username', 'N/A')}\n"
        f"📦 Product: {order_found['product']}\n"
        f"🔢 Qty: {order_found['quantity']}\n"
        f"💰 Total: ₹{order_found['total']}\n"
        f"📝 Ref: {reference}"
    )
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{order_id}"),
        telebot.types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{order_id}")
    )
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)

# ============================================================
# ===== ADMIN APPROVAL (AUTO REMOVE FROM DB) =====
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_'))
def admin_approve(call):
    if not is_admin(call.from_user.id, call.from_user.username):
        return

    order_id = call.data.replace('approve_', '')
    orders = load_orders()
    order_found = next((o for o in orders['orders'] if o['order_id'] == order_id), None)

    if not order_found or order_found['status'] == "delivered":
        bot.answer_callback_query(call.id, "❌ Invalid or already delivered!", show_alert=True)
        return

    qty = order_found['quantity']
    category_key = order_found.get('category_key', 'json_files')

    files_created = []
    items_delivered = []
    
    for i in range(1, qty + 1):
        filename, filepath, item_id = process_delivery(order_found, i)
        if item_id is None:
            bot.answer_callback_query(call.id, "❌ Out of stock!", show_alert=True)
            return
        if filename is not None:
            files_created.append((filename, filepath))
        items_delivered.append(item_id)

    if category_key == 'coupons':
        code_list = "\n".join([f"🔑 `{c}`" for c in items_delivered])
        bot.send_message(order_found['user_id'], f"🎉 *Order Delivered!*\n\n🧾 Order: `{order_id}`\n\n{code_list}", parse_mode='Markdown')
        bot.send_message(ADMIN_ID, f"✅ Coupon Delivered: {order_id}\n{code_list}")

    else:
        item_list = "\n".join([f"   • `{m}`" for m in items_delivered])
        bot.send_message(order_found['user_id'], f"✅ *Order Delivered!*\n\n📦 Product: {order_found['product']}\n🔢 Qty: {qty}\n\n📱 Accounts:\n{item_list}", parse_mode='Markdown')

        for filename, filepath in files_created:
            try:
                with open(filepath, 'rb') as f:
                    bot.send_document(order_found['user_id'], f, caption=f"🎁 File: `{filename}`", parse_mode='Markdown')
            except: pass

        bot.send_message(ADMIN_ID, f"✅ JSON Delivered: {order_id}\n{item_list}")

    order_found['status'] = "delivered"
    order_found['delivered_at'] = get_indian_time()
    save_orders(orders)

    for filename, filepath in files_created:
        try:
            if os.path.exists(filepath): os.remove(filepath)
        except: pass

    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except: pass
    bot.answer_callback_query(call.id, "✅ Delivered & Removed from DB!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def admin_reject(call):
    if not is_admin(call.from_user.id, call.from_user.username): return
    order_id = call.data.replace('reject_', '')
    orders = load_orders()
    for order in orders['orders']:
        if order['order_id'] == order_id:
            order['status'] = "cancelled"
            try: bot.send_message(order['user_id'], f"❌ ORDER REJECTED\n🆔 {order_id}\n\nContact: @Prime_Blogs")
            except: pass
            break
    save_orders(orders)
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except: pass

# ============================================================
# ===== HELP, SUPPORT & UTILS =====
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data == "my_orders")
def my_orders(call):
    orders = load_orders()
    user_orders = [o for o in orders['orders'] if o['user_id'] == call.from_user.id]
    if not user_orders:
        bot.answer_callback_query(call.id, "📭 No orders!", show_alert=True)
        return
    text = "📦 MY ORDERS\n━━━━━━━━━━━━━━\n\n"
    for o in user_orders[-10:]:
        emoji = {"pending": "⏳", "delivered": "✅", "cancelled": "❌"}.get(o['status'], "❓")
        text += f"{emoji} {o['order_id']}\n   📦 {o['product']} x{o['quantity']}\n   💰 ₹{o['total']}\n\n"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main"))
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "help")
def help_menu(call):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main"))
    bot.edit_message_text("❓ HELP\n\n1. Select Product\n2. Select Qty\n3. Pay via UPI\n4. Send Ref\n5. Get Delivery", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📩 Contact", url="https://t.me/Prime_Blogs"))
    bot.edit_message_text("📞 Support: @Prime_Blogs", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    start(call.message)

# ============================================================
# ===== FLASK KEEP-ALIVE & START =====
# ============================================================
app = Flask(__name__)
@app.route('/')
def home(): return "Prime Store Bot running ✅"

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

if __name__ == "__main__":
    print("🚀 Prime Store Bot Starting...")
    keep_alive()
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        print(f"❌ Crash: {e}")