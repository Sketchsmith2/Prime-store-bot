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
    # Create backup before saving
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

def save_json_file(filename, data):
    filepath = os.path.join(JSON_FILES_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    return filepath

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
            bot.send_message(
                call.message.chat.id,
                product['custom_message']
            )
        
        user_selection[call.from_user.id] = {
            "category": category,
            "category_key": category_key,
            "index": index,
            "product": product,
            "stock": stock
        }
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=5)
        max_qty = min(50, stock)
        
        # Row 1: 1-10
        row1 = []
        for q in range(1, 11):
            if q <= max_qty:
                row1.append(telebot.types.InlineKeyboardButton(f"{q}", callback_data=f"qty_{q}"))
        if row1:
            markup.row(*row1)
        
        # Row 2: 11-20
        row2 = []
        for q in range(11, 21):
            if q <= max_qty:
                row2.append(telebot.types.InlineKeyboardButton(f"{q}", callback_data=f"qty_{q}"))
        if row2:
            markup.row(*row2)
        
        # Row 3: 21-30
        row3 = []
        for q in range(21, 31):
            if q <= max_qty:
                row3.append(telebot.types.InlineKeyboardButton(f"{q}", callback_data=f"qty_{q}"))
        if row3:
            markup.row(*row3)
        
        # Row 4: 31-40
        row4 = []
        for q in range(31, 41):
            if q <= max_qty:
                row4.append(telebot.types.InlineKeyboardButton(f"{q}", callback_data=f"qty_{q}"))
        if row4:
            markup.row(*row4)
        
        # Row 5: 41-50
        row5 = []
        for q in range(41, 51):
            if q <= max_qty:
                row5.append(telebot.types.InlineKeyboardButton(f"{q}", callback_data=f"qty_{q}"))
        if row5:
            markup.row(*row5)
        
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
        
        bot.send_message(
            call.message.chat.id,
            payment_msg,
            reply_markup=markup)
        
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
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("❌ Cancel", callback_data="shop"))
        
        bot.edit_m
