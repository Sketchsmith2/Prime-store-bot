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
        data = {
            "products": {
                "coupons": [],
                "json_files": []
            }
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print("✅ Created store_data.json")

    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'w') as f:
            json.dump({"orders": []}, f, indent=2)
        print("✅ Created orders.json")

create_initial_files()

# ===== DATA FUNCTIONS =====
def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    try:
        backup_file = f"{BACKUP_DIR}store_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Backup failed: {e}")

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
# ===== FIXED: SINGLE ACCOUNT PER ORDER =====
# ============================================================

def create_single_order_file(order, index=1):
    """
    Ek order ke liye EK account nikaalo aur uski alag JSON file banao.
    Delivery ke baad us account ko store_data.json se remove kar do.
    """
    order_id = order['order_id']
    product_name = order['product']

    # store_data.json load karo
    data = load_data()

    # Product dhundo
    product = None
    for p in data['products']['json_files']:
        if p['name'] == product_name:
            product = p
            break

    if not product:
        print(f"❌ Product not found: {product_name}")
        return None, None

    # Data array check karo
    if 'data' not in product or len(product['data']) == 0:
        print(f"❌ No stock data left for: {product_name}")
        return None, None

    # Pehla account uthao
    account = product['data'][0]

    # File banao
    safe_name = product_name.replace(' ', '_').replace('/', '_')
    filename = f"{order_id}_{safe_name}_{index}.json"
    filepath = os.path.join(JSON_FILES_DIR, filename)

    with open(filepath, 'w') as f:
        json.dump(account, f, indent=2)

    # ✅ Account ko data array se REMOVE karo
    product['data'].pop(0)

    # ✅ Stock bhi kam karo
    product['stock'] = len(product['data'])

    # ✅ Save karo store_data.json
    save_data(data)

    print(f"✅ Delivered account #{index} | Remaining: {product['stock']}")

    return filename, filepath

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
    bot.send_message(message.chat.id,
        f"✨ Welcome {message.from_user.first_name}!\n\n"
        "🏪 PRIME STORE\n"
        "━━━━━━━━━━━━━━\n"
        "🛍️ Products:\n"
        "🎫 Coupon Codes\n"
        "📁 JSON Files\n\n"
        "💳 Secure Payments\n"
        "📞 Support: @Prime_Blogs",
        reply_markup=markup)

# ============================================================
# ===== SUPPORT =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("📩 Contact", url="https://t.me/Prime_Blogs"),
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="shop"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    bot.edit_message_text(
        "📞 SUPPORT\n━━━━━━━━━━━━━━\n\n"
        "For any queries or issues:\n"
        "📱 Contact: @Prime_Blogs\n\n"
        "⏰ Response: Within 1 hour",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

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
        telebot.types.InlineKeyboardButton("📞 Support", callback_data="support"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    bot.edit_message_text(
        "🛍️ CATEGORIES\n━━━━━━━━━━━━━━\n\nSelect a category:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "cat_coupons")
def cat_coupons(call):
    data = load_data()
    products = data['products']['coupons']
    if not products:
        bot.answer_callback_query(call.id, "❌ No coupons!", show_alert=True)
        return
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for i, p in enumerate(products):
        stock = p.get('stock', 0)
        emoji = "🟢" if stock > 0 else "🔴"
        markup.add(telebot.types.InlineKeyboardButton(f"{emoji} {p['name']} - ₹{p['price']} ({stock})", callback_data=f"buy_coupon_{i}"))
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="shop"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    bot.edit_message_text(
        "🎫 COUPONS\n━━━━━━━━━━━━━━\n\nSelect a coupon:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "cat_json")
def cat_json(call):
    data = load_data()
    products = data['products']['json_files']
    if not products:
        bot.answer_callback_query(call.id, "❌ No JSON files!", show_alert=True)
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

# ============================================================
# ===== USER SELECTION =====
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

    user_selection[call.from_user.id] = {
        "category": category,
        "category_key": category_key,
        "index": index,
        "product": product,
        "stock": stock
    }

    markup = telebot.types.InlineKeyboardMarkup(row_width=5)
    max_qty = min(50, stock)
    for start in range(1, 51, 10):
        row = []
        for q in range(start, start + 10):
            if q <= max_qty:
                row.append(telebot.types.InlineKeyboardButton(f"{q}", callback_data=f"qty_{q}"))
        if row:
            markup.row(*row)
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="shop"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )

    bot.edit_message_text(
        f"📝 SELECT QUANTITY\n━━━━━━━━━━━━━━\n\n"
        f"📦 {product['name']}\n"
        f"💰 ₹{product['price']} each\n"
        f"📦 Available: {stock}\n\n"
        f"Select quantity:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

# ============================================================
# ===== QUANTITY SELECTED =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('qty_'))
def quantity_selected(call):
    qty = int(call.data.split('_')[1])

    if call.from_user.id not in user_selection:
        bot.answer_callback_query(call.id, "❌ Session expired!", show_alert=True)
        return

    selection = user_selection[call.from_user.id]
    product = selection['product']
    stock = selection['stock']

    if qty > stock:
        bot.answer_callback_query(call.id, f"❌ Only {stock} available!", show_alert=True)
        return

    order_id = generate_order_id()
    total_price = product['price'] * qty

    orders = load_orders()
    orders['orders'].append({
        "order_id": order_id,
        "user_id": call.from_user.id,
        "username": call.from_user.username or call.from_user.first_name,
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

    del user_selection[call.from_user.id]

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    try:
        qr_bytes = generate_upi_qr(OWNER_UPI, total_price)
        if qr_bytes:
            bot.send_photo(call.message.chat.id, qr_bytes,
                caption=f"📱 Scan to Pay ₹{total_price}\nUPI: {OWNER_UPI}")
    except Exception as e:
        print(f"QR Error: {e}")

    payment_msg = (
        f"💳 PAYMENT REQUIRED\n━━━━━━━━━━━━━━\n\n"
        f"🆔 Order: {order_id}\n"
        f"📦 Product: {product['name']}\n"
        f"📦 Quantity: {qty}\n"
        f"💰 Price: ₹{product['price']} each\n"
        f"💵 Total: ₹{total_price}\n\n"
        f"📤 UPI: {OWNER_UPI}\n"
        f"📱 Phone: {OWNER_PHONE}\n\n"
        f"✅ Click 'I Have Paid' after payment"
    )

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("✅ I Have Paid", callback_data=f"paid_{order_id}"),
        telebot.types.InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{order_id}"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )

    bot.send_message(call.message.chat.id, payment_msg, reply_markup=markup)

# ============================================================
# ===== CANCEL =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_'))
def cancel_order(call):
    order_id = call.data.split('_')[1]
    orders = load_orders()

    for order in orders['orders']:
        if order['order_id'] == order_id and order['user_id'] == call.from_user.id:
            if order['status'] == "delivered":
                bot.answer_callback_query(call.id, "✅ Already delivered!", show_alert=True)
                return
            order['status'] = "cancelled"
            break
    save_orders(orders)

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    bot.send_message(call.message.chat.id,
        f"❌ Order {order_id} cancelled.")
    bot.answer_callback_query(call.id, "❌ Cancelled!")

# ============================================================
# ===== PAYMENT - "I HAVE PAID" =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('paid_'))
def payment_done(call):
    order_id = call.data.split('_')[1]

    orders = load_orders()
    order_found = None
    for order in orders['orders']:
        if order['order_id'] == order_id and order['user_id'] == call.from_user.id:
            order_found = order
            break

    if not order_found:
        bot.answer_callback_query(call.id, "❌ Order not found!", show_alert=True)
        return

    if order_found['status'] == "delivered":
        bot.answer_callback_query(call.id, "✅ Already delivered!", show_alert=True)
        return

    bot.answer_callback_query(call.id, "📝 Send reference now!")

    msg = bot.send_message(call.message.chat.id,
        f"📝 Send payment reference/UTR for Order {order_id}\n\n"
        f"Example: 123456789012")
    bot.register_next_step_handler(msg, process_reference, order_id)

# ============================================================
# ===== PROCESS REFERENCE - ADMIN NOTIFY =====
# ============================================================

def process_reference(message, order_id):
    try:
        reference = message.text.strip() if message.text else ""

        if len(reference) < 3:
            msg = bot.send_message(message.chat.id, "❌ Invalid! Send again:")
            bot.register_next_step_handler(msg, process_reference, order_id)
            return

        orders = load_orders()
        order_found = None
        for order in orders['orders']:
            if order['order_id'] == order_id:
                order_found = order
                break

        if not order_found:
            bot.send_message(message.chat.id, "❌ Order not found!")
            return

        order_found['payment'] = "submitted"
        order_found['reference'] = reference
        order_found['paid_at'] = get_indian_time()
        save_orders(orders)

        print(f"\n{'='*50}")
        print(f"✅ Reference saved: {order_id} = {reference}")
        print(f"{'='*50}\n")

        # User confirmation
        bot.send_message(message.chat.id,
            f"✅ PAYMENT SUBMITTED!\n━━━━━━━━━━━━━━\n\n"
            f"🆔 Order: {order_id}\n"
            f"📦 Product: {order_found['product']}\n"
            f"💰 Amount: ₹{order_found['total']}\n"
            f"📝 Reference: {reference}\n\n"
            f"⏳ Waiting for admin approval...\n"
            f"📞 Contact: @Prime_Blogs if delayed.")

        # ===== ADMIN NOTIFICATION =====
        admin_msg = (
            f"🟢 PAYMENT RECEIVED\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"🆔 Order: {order_id}\n"
            f"👤 User: @{order_found.get('username', 'N/A')}\n"
            f"📦 Product: {order_found['product']}\n"
            f"🔢 Qty: {order_found['quantity']}\n"
            f"💰 Total: ₹{order_found['total']}\n"
            f"📝 Ref: {reference}\n"
            f"🕐 Time: {get_indian_time()}"
        )

        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            telebot.types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{order_id}"),
            telebot.types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{order_id}")
        )

        try:
            bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)
            print(f"✅ Admin ({ADMIN_ID}) notified for {order_id}")
        except Exception as e:
            print(f"❌ Admin notify FAILED: {e}")

    except Exception as e:
        print(f"❌ Error in process_reference: {e}")
        traceback.print_exc()

# ============================================================
# ===== ADMIN APPROVE BUTTON =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_'))
def admin_approve(call):
    if not is_admin(call.from_user.id, call.from_user.username):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return

    order_id = call.data.replace('approve_', '')

    orders = load_orders()
    order_found = None
    for order in orders['orders']:
        if order['order_id'] == order_id:
            order_found = order
            break

    if not order_found:
        bot.answer_callback_query(call.id, "❌ Order not found!", show_alert=True)
        return

    if order_found['status'] == "delivered":
        bot.answer_callback_query(call.id, "✅ Already delivered!", show_alert=True)
        return

    qty = order_found['quantity']

    # ✅ Create files — EK account per order
    files_created = []
    for i in range(1, qty + 1):
        filename, filepath = create_single_order_file(order_found, i)
        if filename is None:
            bot.answer_callback_query(call.id, "❌ Out of stock!", show_alert=True)
            return
        files_created.append((filename, filepath))

    # Send delivery message
    bot.send_message(order_found['user_id'],
        f"✅ ORDER DELIVERED!\n━━━━━━━━━━━━━━\n\n"
        f"🆔 {order_id}\n"
        f"📦 {order_found['product']}\n"
        f"🔢 Quantity: {qty}\n\n"
        f"Thank you for shopping at Prime Store! 🎉")

    # Send files
    for filename, filepath in files_created:
        try:
            with open(filepath, 'rb') as f:
                bot.send_document(order_found['user_id'], f,
                    caption=f"🎁 Your Order File\n🆔 {order_id}\n📄 {filename}")
        except Exception as e:
            print(f"File send error: {e}")

        # Auto-delete after sending
        try:
            os.remove(filepath)
        except:
            pass

    # Update status (stock already updated in create_single_order_file)
    order_found['status'] = "delivered"
    order_found['delivered_at'] = get_indian_time()
    save_orders(orders)

    # Admin confirmation
    bot.send_message(ADMIN_ID,
        f"✅ DELIVERED!\n"
        f"🆔 {order_id}\n"
        f"📦 {order_found['product']}\n"
        f"🔢 Qty: {qty}")

    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass

    bot.answer_callback_query(call.id, "✅ Delivered!")

# ============================================================
# ===== ADMIN REJECT BUTTON =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def admin_reject(call):
    if not is_admin(call.from_user.id, call.from_user.username):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return

    order_id = call.data.replace('reject_', '')

    orders = load_orders()
    for order in orders['orders']:
        if order['order_id'] == order_id:
            order['status'] = "cancelled"
            try:
                bot.send_message(order['user_id'],
                    f"❌ ORDER REJECTED\n🆔 {order_id}\n\nPayment could not be verified.\nContact: @Prime_Blogs")
            except:
                pass
            break
    save_orders(orders)

    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass

    bot.answer_callback_query(call.id, "❌ Rejected!")

# ============================================================
# ===== MY ORDERS =====
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
    markup.add(
        telebot.types.InlineKeyboardButton("🛒 Shop", callback_data="shop"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    bot.edit_message_text(text, chat_id=call.message.chat.id,
        message_id=call.message.message_id, reply_markup=markup)

# ============================================================
# ===== HELP =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "help")
def help_menu(call):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="shop"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    bot.edit_message_text(
        "❓ HELP\n━━━━━━━━━━━━━━\n\n"
        "🛒 How to buy:\n"
        "1. Click Shop Now\n"
        "2. Select category\n"
        "3. Choose product\n"
        "4. Select quantity\n"
        "5. Pay via UPI\n"
        "6. Click 'I Have Paid'\n"
        "7. Send reference\n"
        "8. Get delivery\n\n"
        "📞 Support: @Prime_Blogs",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

# ============================================================
# ===== HOME =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("🛒 Shop Now", callback_data="shop"),
        telebot.types.InlineKeyboardButton("📦 My Orders", callback_data="my_orders"),
        telebot.types.InlineKeyboardButton("❓ Help", callback_data="help"),
        telebot.types.InlineKeyboardButton("📞 Support", callback_data="support")
    )
    bot.edit_message_text(
        "🏪 PRIME STORE\n━━━━━━━━━━━━━━\n\n🛍️ Welcome back!\n\n📞 Support: @Prime_Blogs",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

# ============================================================
# ===== ADMIN COMMANDS =====
# ============================================================

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id, message.from_user.username):
        bot.reply_to(message, "❌ Unauthorized!")
        return

    orders = load_orders()
    pending = sum(1 for o in orders['orders'] if o['status'] == 'pending')
    delivered = sum(1 for o in orders['orders'] if o['status'] == 'delivered')

    bot.reply_to(message,
        f"👑 ADMIN PANEL\n━━━━━━━━━━━━━━\n\n"
        f"⏳ Pending: {pending}\n"
        f"✅ Delivered: {delivered}\n\n"
        f"Admin ID: {ADMIN_ID}")

@bot.message_handler(commands=['pending'])
def pending_orders(message):
    if not is_admin(message.from_user.id, message.from_user.username):
        return

    orders = load_orders()
    pending = [o for o in orders['orders'] if o['status'] == 'pending']

    if not pending:
        bot.reply_to(message, "✅ No pending!")
        return

    text = "⏳ PENDING\n━━━━━━━━━━━━━━\n\n"
    for o in pending[-10:]:
        text += f"🆔 {o['order_id']}\n📦 {o['product']} x{o['quantity']}\n💰 ₹{o['total']}\n\n"
    bot.reply_to(message, text)

@bot.message_handler(commands=['myid'])
def my_id(message):
    bot.reply_to(message,
        f"🆔 Your Telegram ID: `{message.from_user.id}`\n"
        f"👤 Username: @{message.from_user.username}\n\n"
        f"⚙️ Bot ADMIN_ID: `{ADMIN_ID}`\n"
        f"✅ Match: {message.from_user.id == ADMIN_ID}",
        parse_mode='Markdown')

@bot.message_handler(commands=['stock'])
def stock_check(message):
    if not is_admin(message.from_user.id, message.from_user.username):
        return

    data = load_data()
    text = "📦 STOCK STATUS\n━━━━━━━━━━━━━━\n\n"
    for p in data['products']['json_files']:
        stock = p.get('stock', 0)
        data_len = len(p.get('data', []))
        text += f"📁 {p['name']}\n   Stock: {stock} | Data: {data_len}\n\n"
    bot.reply_to(message, text)

# ============================================================
# ===== FLASK KEEP-ALIVE =====
# ============================================================

app = Flask(__name__)

@app.route('/')
def home():
    return "Prime Store Bot running ✅"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

# ============================================================
# ===== START BOT =====
# ============================================================

if __name__ == "__main__":
    print("🚀 Prime Store Bot Starting...")
    print(f"👑 Admin ID: {ADMIN_ID}")
    keep_alive()

    try:
        print("✅ Bot polling started...")
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except KeyboardInterrupt:
        print("🛑 Bot stopped")
    except Exception as e:
        print(f"❌ Crash: {e}")
        traceback.print_exc()
