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
import shutil

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

# ===== CREATE DIRECTORIES =====
os.makedirs(JSON_FILES_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# ===== BOT INITIALIZE =====
bot = telebot.TeleBot(TOKEN)

# ===== DELETE WEBHOOK =====
try:
    bot.delete_webhook()
    print("✅ Webhook deleted")
except:
    pass

# ===== CHECK ADMIN FUNCTION =====
def is_admin(user_id, username):
    return user_id == ADMIN_ID or username == CO_ADMIN_USERNAME

# ===== QR CODE FUNCTION =====
def generate_upi_qr(upi_id, amount, name=STORE_NAME):
    try:
        upi_url = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR"
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=2)
        qr.add_data(upi_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', quality=95)
        img_bytes.seek(0)
        return img_bytes
    except Exception as e:
        print(f"QR Error: {e}")
        return None

# ===== CREATE INITIAL FILES =====
def create_initial_files():
    if not os.path.exists(DATA_FILE):
        data = {
            "products": {
                "coupons": [],
                "json_files": []
            },
            "settings": {
                "total_earned": 0,
                "total_orders": 0
            }
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print("✅ Created store_data.json")

    if not os.path.exists(ORDERS_FILE):
        orders = {"orders": []}
        with open(ORDERS_FILE, 'w') as f:
            json.dump(orders, f, indent=2)
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
        print(f"✅ Backup created: {backup_file}")
    except Exception as e:
        print(f"⚠️ Backup failed: {e}")

    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print("✅ Data saved")

def load_orders():
    with open(ORDERS_FILE, 'r') as f:
        return json.load(f)

def save_orders(data):
    with open(ORDERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def generate_order_id():
    return "ORD" + ''.join(random.choices(string.digits, k=8))

def generate_file_id():
    return "FILE" + ''.join(random.choices(string.digits, k=6))

# ============================================================
# ===== FIXED: SINGLE JSON FILE PER ORDER =====
# ============================================================

def create_single_order_file(order, index=1):
    """
    Creates ONE JSON file for ONE order.
    Filename: order_<ORDER_ID>_<index>.json
    """
    order_id = order['order_id']
    safe_name = order['product'].replace(' ', '_').replace('/', '_')
    filename = f"order_{order_id}_{safe_name}_{index}.json"
    filepath = os.path.join(JSON_FILES_DIR, filename)

    with open(filepath, 'w') as f:
        json.dump({
            "order_id": order_id,
            "product": order['product'],
            "category": order.get('category', 'json'),
            "price": order['price'],
            "quantity": 1,
            "buyer": order.get('username', 'N/A'),
            "buyer_id": order.get('user_id'),
            "delivered_at": get_indian_time()
        }, f, indent=2)

    return filename, filepath


def delete_json_file(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"🗑️ Deleted: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error deleting: {e}")
        return False

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
        "⏰ Response: Within 1 hour\n\n"
        "💬 Feel free to reach out!",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

# ============================================================
# ===== SHOP & CATEGORIES =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "shop")
def shop(call):
    try:
        data = load_data()
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)

        json_stock = sum(p.get('stock', 1) for p in data['products']['json_files'])
        coupon_stock = sum(p.get('stock', 1) for p in data['products']['coupons'])

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
    except Exception as e:
        print(f"Error: {e}")

# ============================================================
# ===== CATEGORY VIEWS =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "cat_coupons")
def cat_coupons(call):
    try:
        data = load_data()
        products = data['products']['coupons']
        if not products:
            bot.answer_callback_query(call.id, "❌ No coupons!", show_alert=True)
            return
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for i, p in enumerate(products):
            stock = p.get('stock', 1)
            stock_emoji = "🟢" if stock > 0 else "🔴"
            markup.add(telebot.types.InlineKeyboardButton(f"{stock_emoji} {p['name']} - ₹{p['price']} ({stock} left)", callback_data=f"buy_coupon_{i}"))
        markup.add(
            telebot.types.InlineKeyboardButton("🔙 Back", callback_data="shop"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
        )
        bot.edit_message_text(
            "🎫 COUPONS\n━━━━━━━━━━━━━━\n\nSelect a coupon:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "cat_json")
def cat_json(call):
    try:
        data = load_data()
        products = data['products']['json_files']
        if not products:
            bot.answer_callback_query(call.id, "❌ No JSON files!", show_alert=True)
            return
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for i, p in enumerate(products):
            stock = p.get('stock', 1)
            stock_emoji = "🟢" if stock > 0 else "🔴"
            markup.add(telebot.types.InlineKeyboardButton(f"{stock_emoji} {p['name']} - ₹{p['price']} ({stock} left)", callback_data=f"buy_json_{i}"))
        markup.add(
            telebot.types.InlineKeyboardButton("🔙 Back", callback_data="shop"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
        )
        bot.edit_message_text(
            "📁 JSON FILES\n━━━━━━━━━━━━━━\n\nSelect a file:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

# ============================================================
# ===== USER SELECTION STORAGE =====
# ============================================================

user_selection = {}

# ============================================================
# ===== BUY PRODUCT - ASK QUANTITY =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def buy_product(call):
    try:
        data = load_data()
        parts = call.data.split('_')
        category = parts[1]
        index = int(parts[2])

        category_map = {"coupon": "coupons", "json": "json_files"}
        category_key = category_map.get(category)
        if not category_key:
            bot.answer_callback_query(call.id, "❌ Invalid category!", show_alert=True)
            return

        products = data['products'][category_key]
        if index >= len(products):
            bot.answer_callback_query(call.id, "❌ Not available!", show_alert=True)
            return

        product = products[index]
        stock = product.get('stock', 1)

        if stock <= 0:
            bot.answer_callback_query(call.id, "❌ Out of stock!", show_alert=True)
            return

        if product.get('custom_message'):
            bot.send_message(call.message.chat.id, product['custom_message'])

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
            f"📝 SELECT QUANTITY (1-50)\n━━━━━━━━━━━━━━\n\n"
            f"📦 Product: {product['name']}\n"
            f"💰 Price: ₹{product['price']} each\n"
            f"📦 Available: {stock} files\n\n"
            f"Select quantity:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
    except Exception as e:
        print(f"Error in buy_product: {e}")
        traceback.print_exc()
        bot.answer_callback_query(call.id, "❌ Error!", show_alert=True)

# ============================================================
# ===== QUANTITY SELECTED =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('qty_'))
def quantity_selected(call):
    try:
        qty = int(call.data.split('_')[1])

        if call.from_user.id not in user_selection:
            bot.answer_callback_query(call.id, "❌ Session expired! Try again.", show_alert=True)
            return

        selection = user_selection[call.from_user.id]
        product = selection['product']
        stock = selection['stock']

        if qty > stock:
            bot.answer_callback_query(call.id, f"❌ Only {stock} available!", show_alert=True)
            return

        category = selection['category']
        category_key = selection['category_key']
        index = selection['index']

        order_id = generate_order_id()
        total_price = product['price'] * qty

        orders = load_orders()
        orders['orders'].append({
            "order_id": order_id,
            "user_id": call.from_user.id,
            "username": call.from_user.username or call.from_user.first_name,
            "product": product['name'],
            "category": category,
            "category_key": category_key,
            "product_index": index,
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
                bot.send_photo(
                    call.message.chat.id,
                    qr_bytes,
                    caption=f"📱 Scan to Pay ₹{total_price}\nUPI: {OWNER_UPI}"
                )
        except Exception as e:
            print(f"QR Error: {e}")

        payment_msg = (
            f"💳 PAYMENT REQUIRED\n━━━━━━━━━━━━━━\n\n"
            f"🆔 Order: {order_id}\n"
            f"📦 Product: {product['name']}\n"
            f"📦 Quantity: {qty} files\n"
            f"💰 Price: ₹{product['price']} each\n"
            f"💵 Total: ₹{total_price}\n"
            f"📦 Stock Left: {stock - qty}\n\n"
            f"📤 UPI: {OWNER_UPI}\n"
            f"📱 Phone: {OWNER_PHONE}\n\n"
            f"⚠️ Send exact amount ₹{total_price}\n"
            f"📝 Use order ID as reference\n\n"
            f"✅ Click 'I Have Paid' after payment"
        )

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton("✅ I Have Paid", callback_data=f"paid_{order_id}"),
            telebot.types.InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{order_id}"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main"),
            telebot.types.InlineKeyboardButton("📞 Support", callback_data="support")
        )

        bot.send_message(call.message.chat.id, payment_msg, reply_markup=markup)

    except Exception as e:
        print(f"Error in quantity_selected: {e}")
        traceback.print_exc()
        bot.answer_callback_query(call.id, "❌ Error!", show_alert=True)

# ============================================================
# ===== CANCEL ORDER =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_'))
def cancel_order(call):
    try:
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

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        for order in orders['orders']:
            if order['order_id'] == order_id:
                order['status'] = "cancelled"
                order['cancelled_at'] = get_indian_time()
                break
        save_orders(orders)

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🛒 Shop", callback_data="shop"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
        )

        bot.send_message(
            call.message.chat.id,
            f"❌ Order Cancelled\n━━━━━━━━━━━━━━\n\n"
            f"Order: {order_id}\n"
            f"Product: {order_found['product']}\n\n"
            f"Order has been cancelled.",
            reply_markup=markup)

        bot.answer_callback_query(call.id, "❌ Order cancelled!", show_alert=True)
    except Exception as e:
        print(f"Error in cancel: {e}")
        bot.answer_callback_query(call.id, f"❌ Error!", show_alert=True)

# ============================================================
# ===== PAYMENT WITH REFERENCE =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('paid_'))
def payment_done(call):
    try:
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

        if order_found['payment'] == "submitted":
            bot.answer_callback_query(call.id, "⏳ Already submitted!", show_alert=True)
            return

        msg = bot.send_message(
            call.message.chat.id,
            f"📝 Send payment reference/UTR for Order {order_id}\n\n"
            f"Example: 123456789012"
        )
        bot.register_next_step_handler(msg, process_reference, order_id)

    except Exception as e:
        print(f"Error in payment_done: {e}")
        bot.answer_callback_query(call.id, "❌ Error!", show_alert=True)

def process_reference(message, order_id):
    try:
        reference = message.text.strip()
        if len(reference) < 3:
            msg = bot.send_message(message.chat.id, "❌ Invalid reference! Send again:")
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

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📦 My Orders", callback_data="my_orders"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
        )

        bot.send_message(
            message.chat.id,
            f"✅ PAYMENT SUBMITTED!\n━━━━━━━━━━━━━━\n\n"
            f"🆔 Order: {order_id}\n"
            f"📦 Product: {order_found['product']}\n"
            f"💰 Amount: ₹{order_found['total']}\n"
            f"📝 Reference: {reference}\n\n"
            f"⏳ Waiting for admin approval...\n"
            f"📞 Contact: @Prime_Blogs if delayed.",
            reply_markup=markup)

        # ===== NOTIFY ADMIN =====
        admin_msg = (
            f"🔔 NEW ORDER\n━━━━━━━━━━━━━━\n\n"
            f"🆔 Order: {order_id}\n"
            f"👤 User: {order_found.get('username', 'N/A')}\n"
            f"📦 Product: {order_found['product']}\n"
            f"📦 Quantity: {order_found['quantity']}\n"
            f"💰 Total: ₹{order_found['total']}\n"
            f"📝 Reference: {reference}\n\n"
            f"✅ Approve: /approve {order_id}"
        )

        try:
            bot.send_message(ADMIN_ID, admin_msg)
        except Exception as e:
            print(f"Admin notify error: {e}")

    except Exception as e:
        print(f"Error in process_reference: {e}")

# ============================================================
# ===== ADMIN - APPROVE ORDER (FIXED) =====
# ============================================================

@bot.message_handler(commands=['approve'])
def approve_order(message):
    if not is_admin(message.from_user.id, message.from_user.username):
        bot.reply_to(message, "❌ Unauthorized!")
        return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Usage: /approve ORDER_ID")
            return

        order_id = args[1]
        orders = load_orders()

        order_found = None
        for order in orders['orders']:
            if order['order_id'] == order_id:
                order_found = order
                break

        if not order_found:
            bot.reply_to(message, "❌ Order not found!")
            return

        if order_found['status'] == "delivered":
            bot.reply_to(message, "✅ Already delivered!")
            return

        # ✅ FIX: Har unit ke liye ALAG JSON file banao
        files_created = []
        qty = order_found['quantity']
        for i in range(1, qty + 1):
            filename, filepath = create_single_order_file(order_found, i)
            files_created.append((filename, filepath))

        # ✅ Deliver all files
        bot.send_message(
            order_found['user_id'],
            f"✅ ORDER DELIVERED!\n━━━━━━━━━━━━━━\n\n"
            f"🆔 {order_id}\n"
            f"📦 {order_found['product']}\n"
            f"📦 Quantity: {qty}\n\n"
            f"Thank you for shopping at Prime Store!"
        )

        for filename, filepath in files_created:
            try:
                with open(filepath, 'rb') as f:
                    bot.send_document(order_found['user_id'], f)
            except Exception as e:
                print(f"File send error: {e}")

            # Auto-delete after sending
            try:
                delete_json_file(filepath)
            except:
                pass

        # Update order status
        order_found['status'] = "delivered"
        order_found['delivered_at'] = get_indian_time()

        # ✅ Stock kam karo
        try:
            data = load_data()
            cat_key = order_found.get('category_key', 'json_files')
            idx = order_found.get('product_index', None)
            if idx is not None and idx < len(data['products'][cat_key]):
                data['products'][cat_key][idx]['stock'] = max(
                    0, data['products'][cat_key][idx]['stock'] - qty
                )
                save_data(data)
        except Exception as e:
            print(f"Stock update error: {e}")

        save_orders(orders)

        bot.reply_to(
            message,
            f"✅ Order {order_id} delivered!\n"
            f"📁 {qty} JSON file(s) sent & auto-deleted."
        )

    except Exception as e:
        print(f"Error in approve: {e}")
        traceback.print_exc()
        bot.reply_to(message, f"❌ Error: {e}")

# ============================================================
# ===== MY ORDERS =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "my_orders")
def my_orders(call):
    try:
        orders = load_orders()
        user_orders = [o for o in orders['orders'] if o['user_id'] == call.from_user.id]

        if not user_orders:
            bot.answer_callback_query(call.id, "📭 No orders yet!", show_alert=True)
            return

        text = "📦 MY ORDERS\n━━━━━━━━━━━━━━\n\n"
        for o in user_orders[-10:]:
            status_emoji = {
                "pending": "⏳",
                "delivered": "✅",
                "cancelled": "❌"
            }.get(o['status'], "❓")
            text += (
                f"{status_emoji} {o['order_id']}\n"
                f"   📦 {o['product']} x{o['quantity']}\n"
                f"   💰 ₹{o['total']} | {o['status'].upper()}\n\n"
            )

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🛒 Shop", callback_data="shop"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
        )

        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
    except Exception as e:
        print(f"Error in my_orders: {e}")

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
        "4. Select quantity (1-50)\n"
        "5. Pay via UPI\n"
        "6. Submit reference\n"
        "7. Get delivery\n\n"
        "💳 Payment: UPI only\n"
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
        "🏪 PRIME STORE\n━━━━━━━━━━━━━━\n\n"
        "🛍️ Welcome back!\n\n"
        "💳 Secure Payments\n"
        "📞 Support: @Prime_Blogs",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

# ============================================================
# ===== ADMIN PANEL =====
# ============================================================

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id, message.from_user.username):
        bot.reply_to(message, "❌ Unauthorized!")
        return

    data = load_data()
    orders = load_orders()

    pending = sum(1 for o in orders['orders'] if o['status'] == 'pending')
    delivered = sum(1 for o in orders['orders'] if o['status'] == 'delivered')

    json_stock = sum(p.get('stock', 1) for p in data['products']['json_files'])
    coupon_stock = sum(p.get('stock', 1) for p in data['products']['coupons'])

    bot.reply_to(
        message,
        f"👑 ADMIN PANEL\n━━━━━━━━━━━━━━\n\n"
        f"📊 Stats:\n"
        f"⏳ Pending: {pending}\n"
        f"✅ Delivered: {delivered}\n\n"
        f"📦 Stock:\n"
        f"📁 JSON: {json_stock}\n"
        f"🎫 Coupons: {coupon_stock}\n\n"
        f"⚙️ Commands:\n"
        f"/pending - View pending orders\n"
        f"/approve ORDER_ID - Deliver order\n"
        f"/addstock - Add stock\n"
        f"/stats - View stats"
    )

@bot.message_handler(commands=['pending'])
def pending_orders(message):
    if not is_admin(message.from_user.id, message.from_user.username):
        return

    orders = load_orders()
    pending = [o for o in orders['orders'] if o['status'] == 'pending']

    if not pending:
        bot.reply_to(message, "✅ No pending orders!")
        return

    text = "⏳ PENDING ORDERS\n━━━━━━━━━━━━━━\n\n"
    for o in pending[-15:]:
        text += (
            f"🆔 {o['order_id']}\n"
            f"👤 {o.get('username', 'N/A')}\n"
            f"📦 {o['product']} x{o['quantity']}\n"
            f"💰 ₹{o['total']}\n"
            f"📝 Ref: {o.get('reference', 'N/A')}\n"
            f"✅ /approve {o['order_id']}\n\n"
        )

    bot.reply_to(message, text)

@bot.message_handler(commands=['stats'])
def stats(message):
    if not is_admin(message.from_user.id, message.from_user.username):
        return

    orders = load_orders()
    total_orders = len(orders['orders'])
    delivered = sum(1 for o in orders['orders'] if o['status'] == 'delivered')
    revenue = sum(o['total'] for o in orders['orders'] if o['status'] == 'delivered')

    bot.reply_to(
        message,
        f"📊 STATS\n━━━━━━━━━━━━━━\n\n"
        f"📦 Total Orders: {total_orders}\n"
        f"✅ Delivered: {delivered}\n"
        f"💰 Revenue: ₹{revenue}"
    )

# ============================================================
# ===== FLASK KEEP-ALIVE (for Render/Replit) =====
# ============================================================

app = Flask(__name__)

@app.route('/')
def home():
    return "Prime Store Bot is running ✅"

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

    while True:
        try:
            print("✅ Bot polling started...")
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            print(f"❌ Bot crashed: {e}")
            traceback.print_exc()
            time.sleep(5)
