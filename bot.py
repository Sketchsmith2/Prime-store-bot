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
# ===== CREATE ITEM (JSON or COUPON) =====
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

    # ===== JSON ACCOUNT (FULL JSON) =====
    product_lower = product_name.lower()
    if 'flipkart' in product_lower: prefix = 'flipkart'
    elif 'bigbasket' in product_lower: prefix = 'bigbasket'
    elif 'meesho 120' in product_lower: prefix = 'meesho_120'
    elif 'meesho 170' in product_lower: prefix = 'meesho_170'
    elif 'meesho 175' in product_lower: prefix = 'meesho_175'
    elif 'meesho 195' in product_lower: prefix = 'meesho_195'
    elif 'meesho' in product_lower: prefix = 'meesho'
    else: prefix = 'account'

    if item.get('mobile'): identifier = str(item['mobile']).replace('+', '').replace(' ', '')
    elif item.get('phone'): identifier = str(item['phone']).replace('+', '').replace(' ', '')
    elif item.get('mId'): identifier = str(item['mId']).replace('=', '').replace('/', '')
    elif item.get('accountId'): identifier = str(item['accountId']).replace('=', '').replace('/', '')
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
# ===== SUPPORT & CATEGORIES =====
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
# ===== USER SELECTION (NEW UI WITH CUSTOM) =====
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
        bot.send_message(
            call.message.chat.id,
            f"📌 *Description:*\n{product['sub_category']}",
            parse_mode='Markdown'
        )

    user_selection[call.from_user.id] = {
        "category": category,
        "category_key": category_key,
        "index": index,
        "product": product,
        "stock": stock
    }

    # ✅ NEW UI: 1-5 + Custom
    markup = telebot.types.InlineKeyboardMarkup(row_width=5)
    
    row = []
    max_qty = min(5, stock)
    for q in range(1, max_qty + 1):
        row.append(telebot.types.InlineKeyboardButton(f"{q}", callback_data=f"qty_{q}"))
    if row:
        markup.row(*row)
    
    if stock > 5:
        markup.add(telebot.types.InlineKeyboardButton("✍️ Custom Quantity", callback_data=f"custom_qty_{index}"))
        
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="shop"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )

    bot.edit_message_text(
        f"📝 SELECT QUANTITY\n━━━━━━━━━━━━━━\n\n"
        f"📦 {product['name']}\n"
        f"💰 ₹{product['price']} each\n"
        f"📦 Available: {stock}\n\n"
        f"Select quantity from below or click Custom:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

# ============================================================
# ===== QUANTITY PROCESSING =====
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('qty_'))
def quantity_selected(call):
    qty = int(call.data.split('_')[1])

    if call.from_user.id not in user_selection:
        bot.answer_callback_query(call.id, "❌ Session expired!", show_alert=True)
        return

    process_order(call.message.chat.id, call.from_user.id, qty, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('custom_qty_'))
def custom_quantity_prompt(call):
    if call.from_user.id not in user_selection:
        bot.answer_callback_query(call.id, "❌ Session expired! Try again.", show_alert=True)
        return
        
    selection = user_selection[call.from_user.id]
    product = selection['product']
    stock = selection['stock']
    
    msg = bot.send_message(
        call.message.chat.id,
        f"✍️ *Custom Quantity*\n\n"
        f"📦 {product['name']}\n"
        f"📦 Available: {stock}\n\n"
        f"Reply with a number (1 to {stock}):",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, process_custom_quantity)

def process_custom_quantity(message):
    try:
        qty = int(message.text.strip())
    except ValueError:
        bot.reply_to(message, "❌ Invalid number. Please start again from shop.")
        return

    if message.from_user.id not in user_selection:
        bot.send_message(message.chat.id, "❌ Session expired. Please start again.")
        return

    selection = user_selection[message.from_user.id]
    stock = selection['stock']

    if qty < 1 or qty > stock:
        bot.reply_to(message, f"❌ Invalid! Quantity must be between 1 and {stock}.")
        return

    process_order(message.chat.id, message.from_user.id, qty, None)

def process_order(chat_id, user_id, qty, message_id_to_delete):
    selection = user_selection[user_id]
    product = selection['product']
    stock = selection['stock']
    
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

    if message_id_to_delete:
        try:
            bot.delete_message(chat_id, message_id_to_delete)
        except:
            pass

    try:
        qr_bytes = generate_upi_qr(OWNER_UPI, total_price)
        if qr_bytes:
            bot.send_photo(chat_id, qr_bytes,
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

    bot.send_message(chat_id, payment_msg, reply_markup=markup)

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

    bot.send_message(call.message.chat.id, f"❌ Order {order_id} cancelled.")
    bot.answer_callback_query(call.id, "❌ Cancelled!")

# ============================================================
# ===== PAYMENT & ADMIN NOTIFY =====
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

        bot.send_message(message.chat.id,
            f"✅ PAYMENT SUBMITTED!\n━━━━━━━━━━━━━━\n\n"
            f"🆔 Order: {order_id}\n"
            f"📦 Product: {order_found['product']}\n"
            f"💰 Amount: ₹{order_found['total']}\n"
            f"📝 Reference: {reference}\n\n"
            f"⏳ Waiting for admin approval...\n"
            f"📞 Contact: @Prime_Blogs if delayed.")

        admin_msg = (
            f"🟢 PAYMENT RECEIVED\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"🆔 Order: {order_id}\n"
            f"👤 User: {order_found.get('username', 'N/A')}\n"
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
        except Exception as e:
            print(f"❌ Admin notify FAILED: {e}")

    except Exception as e:
        print(f"❌ Error in process_reference: {e}")

# ============================================================
# ===== ADMIN APPROVE & REJECT =====
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
    category_key = order_found.get('category_key', 'json_files')

    files_created = []
    items_delivered = []
    for i in range(1, qty + 1):
        filename, filepath, item_id = create_single_order_file(order_found, i)
        if item_id is None:
            bot.answer_callback_query(call.id, "❌ Out of stock!", show_alert=True)
            return
        if filename is not None:
            files_created.append((filename, filepath))
        items_delivered.append(item_id)

    if category_key == 'coupons':
        code_list = "\n".join([f"🔑 {c}" for c in items_delivered])

        bot.send_message(
            order_found['user_id'],
            f"🎉 Payment Successful!\n\n"
            f"🧾 Order: {order_id}\n\n"
            f"{code_list}"
        )

        admin_msg = (
            f"✅ COUPON DELIVERED\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"🆔 Order: {order_id}\n"
            f"👤 User: {order_found.get('username', 'N/A')}\n"
            f"📦 Product: {order_found['product']}\n"
            f"🔢 Qty: {qty}\n\n"
            f"🔑 Codes Delivered:\n{code_list}\n\n"
            f"🕐 Time: {get_indian_time()}"
        )
        try:
            bot.send_message(ADMIN_ID, admin_msg)
        except Exception as e:
            print(f"❌ Admin notify FAILED: {e}")

    else:
        item_list = "\n".join([f"   • {m}" for m in items_delivered])

        bot.send_message(
            order_found['user_id'],
            f"✅ ORDER DELIVERED!\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"🆔 Order: {order_id}\n"
            f"📦 Product: {order_found['product']}\n"
            f"🔢 Quantity: {qty}\n\n"
            f"📱 Accounts Delivered:\n{item_list}\n\n"
            f"Thank you for shopping at Prime Store! 🎉"
        )

        for filename, filepath in files_created:
            try:
                with open(filepath, 'rb') as f:
                    bot.send_document(
                        order_found['user_id'],
                        f,
                        caption=(
                            f"🎁 Your Order File\n"
                            f"━━━━━━━━━━━━━━\n\n"
                            f"🆔 Order: {order_id}\n"
                            f"📦 {order_found['product']}\n"
                            f"📄 File: {filename}\n"
                            f"🕐 Time: {get_indian_time()}\n\n"
                            f"Thank you! 🎉"
                        )
                    )
            except Exception as e:
                print(f"File send error: {e}")

        admin_msg = (
            f"✅ ORDER DELIVERED\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"🆔 Order: {order_id}\n"
            f"👤 User: {order_found.get('username', 'N/A')}\n"
            f"📦 Product: {order_found['product']}\n"
            f"🔢 Qty: {qty}\n\n"
            f"📱 Accounts Delivered:\n{item_list}\n\n"
            f"🕐 Time: {get_indian_time()}"
        )
        try:
            bot.send_message(ADMIN_ID, admin_msg)
        except Exception as e:
            print(f"❌ Admin notify FAILED: {e}")

        for filename, filepath in files_created:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'rb') as f:
                        bot.send_document(
                            ADMIN_ID,
                            f,
                            caption=f"📄 Delivered to {order_found.get('username', 'N/A')}"
                        )
                except:
                    pass

    order_found['status'] = "delivered"
    order_found['delivered_at'] = get_indian_time()
    save_orders(orders)

    for filename, filepath in files_created:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass

    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass

    bot.answer_callback_query(call.id, "✅ Delivered!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def admin_reject(call):
    if not is_admin(call.from_user.id, call.from_user.username):
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
# ===== MENUS (MY ORDERS, HELP, HOME) =====
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
    keep_alive()

    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        print(f"❌ Crash: {e}")