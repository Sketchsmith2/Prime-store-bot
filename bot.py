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
        
        # ✅ FIX: Stock check using stock field
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
        
        bot.edit_message_text(
            f"✅ PAYMENT SUBMITTED!\n━━━━━━━━━━━━━━\n\n"
            f"Order: {order_id}\n\n"
            f"⏳ Waiting for admin approval...\n\n"
            f"📞 Contact: @Prime_Blogs if delayed.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
        
        # Notify admin
        admin_msg = (
            f"🟢 NEW PAYMENT CLAIM\n━━━━━━━━━━━━━━\n\n"
            f"🆔 Order: {order_id}\n"
            f"👤 User: {order_found['username']}\n"
            f"📦 Product: {order_found['product']}\n"
            f"💰 Amount: ₹{order_found['total']}\n"
            f"📦 Quantity: {order_found['quantity']}\n\n"
            f"📌 Verify payment and deliver."
        )
        try:
            bot.send_message(ADMIN_ID, admin_msg)
        except:
            pass
        
        bot.answer_callback_query(call.id, "✅ Payment submitted!", show_alert=True)
    except Exception as e:
        print(f"Error in payment: {e}")
        bot.answer_callback_query(call.id, f"❌ Error!", show_alert=True)

# ============================================================
# ===== MY ORDERS =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "my_orders")
def my_orders(call):
    try:
        orders = load_orders()
        user_orders = [o for o in orders['orders'] if o['user_id'] == call.from_user.id]
        
        if not user_orders:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(
                telebot.types.InlineKeyboardButton("🛒 Shop", callback_data="shop"),
                telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
            )
            bot.edit_message_text(
                "📦 MY ORDERS\n━━━━━━━━━━━━━━\n\n"
                "No orders found!\n"
                "Start shopping now.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup)
            return
        
        recent_orders = user_orders[-5:][::-1]
        msg = "📦 MY ORDERS\n━━━━━━━━━━━━━━\n\n"
        
        for o in recent_orders:
            status_emoji = "✅" if o['status'] == "delivered" else ("⏳" if o['status'] == "pending" else "❌")
            msg += f"{status_emoji} #{o['order_id']}\n"
            msg += f"📦 {o['product']} x{o['quantity']} = ₹{o['total']}\n"
            msg += f"📅 {o['created_at']}\n"
            msg += f"📌 {o['status'].upper()}\n━━━━━━━━━━━━━━\n"
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🛒 Shop", callback_data="shop"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
        )
        
        bot.edit_message_text(
            msg,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

# ============================================================
# ===== HELP =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "help")
def help_command(call):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🛒 Shop", callback_data="shop"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    
    bot.edit_message_text(
        "❓ HELP\n━━━━━━━━━━━━━━\n\n"
        "🛍️ Browse products from Shop\n"
        "✅ Pay via UPI (QR code provided)\n"
        "📦 After payment, click 'I Have Paid'\n"
        "⏳ Wait for admin to deliver\n"
        "📞 Contact @Prime_Blogs for support\n\n"
        "📦 Files are auto-delivered after admin approval.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

# ============================================================
# ===== BACK TO MAIN =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start(call.message)
    except Exception as e:
        print(f"Back error: {e}")
        start(call.message)

# ============================================================
# ===== ADMIN COMMANDS =====
# ============================================================

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id, message.from_user.username or ""):
        bot.reply_to(message, "❌ Unauthorized!")
        return
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        telebot.types.InlineKeyboardButton("📦 Pending Orders", callback_data="admin_orders"),
        telebot.types.InlineKeyboardButton("➕ Add Product", callback_data="admin_add"),
        telebot.types.InlineKeyboardButton("🗑️ Delete Product", callback_data="admin_delete"),
        telebot.types.InlineKeyboardButton("📦 Deliver Order", callback_data="admin_deliver"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    
    bot.send_message(message.chat.id,
        "🔐 ADMIN PANEL\n━━━━━━━━━━━━━━\n\n"
        "Select an option:",
        reply_markup=markup)

# ============================================================
# ===== ADMIN STATS =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id, call.from_user.username or ""):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return
    
    try:
        data = load_data()
        orders = load_orders()
        
        total_orders = len(orders['orders'])
        pending_orders = len([o for o in orders['orders'] if o['status'] == "pending"])
        delivered_orders = len([o for o in orders['orders'] if o['status'] == "delivered"])
        
        total_earned = sum(o.get('total', 0) for o in orders['orders'] if o['status'] == "delivered")
        
        json_products = len(data['products']['json_files'])
        coupon_products = len(data['products']['coupons'])
        
        msg = (
            f"📊 STATISTICS\n━━━━━━━━━━━━━━\n\n"
            f"📦 Total Orders: {total_orders}\n"
            f"⏳ Pending: {pending_orders}\n"
            f"✅ Delivered: {delivered_orders}\n"
            f"💰 Total Earned: ₹{total_earned}\n"
            f"🎫 Coupons: {coupon_products}\n"
            f"📁 JSON Files: {json_products}"
        )
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
        
        bot.edit_message_text(
            msg,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

# ============================================================
# ===== ADMIN PENDING ORDERS =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "admin_orders")
def admin_orders(call):
    if not is_admin(call.from_user.id, call.from_user.username or ""):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return
    
    try:
        orders = load_orders()
        pending = [o for o in orders['orders'] if o['status'] == "pending"]
        
        if not pending:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            bot.edit_message_text(
                "📦 PENDING ORDERS\n━━━━━━━━━━━━━━\n\n"
                "No pending orders! ✅",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup)
            return
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for o in pending:
            markup.add(telebot.types.InlineKeyboardButton(
                f"🆔 {o['order_id']} - {o['username']} - ₹{o['total']}",
                callback_data=f"view_order_{o['order_id']}"
            ))
        markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
        
        bot.edit_message_text(
            f"📦 PENDING ORDERS ({len(pending)})\n━━━━━━━━━━━━━━\n\n"
            "Click an order to deliver:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

# ============================================================
# ===== VIEW ORDER =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('view_order_'))
def view_order(call):
    if not is_admin(call.from_user.id, call.from_user.username or ""):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return
    
    try:
        order_id = call.data.split('_')[2]
        
        orders = load_orders()
        order_found = None
        for o in orders['orders']:
            if o['order_id'] == order_id:
                order_found = o
                break
        
        if not order_found:
            bot.answer_callback_query(call.id, "❌ Order not found!", show_alert=True)
            return
        
        msg = (
            f"🆔 ORDER {order_id}\n━━━━━━━━━━━━━━\n\n"
            f"👤 User: {order_found['username']}\n"
            f"📦 Product: {order_found['product']}\n"
            f"📦 Quantity: {order_found['quantity']}\n"
            f"💰 Total: ₹{order_found['total']}\n"
            f"📅 Created: {order_found['created_at']}\n"
            f"📌 Status: {order_found['status']}"
        )
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton("✅ Deliver", callback_data=f"deliver_{order_id}"),
            telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_orders")
        )
        
        bot.edit_message_text(
            msg,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

# ============================================================
# ===== DELIVER ORDER =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('deliver_'))
def deliver_order(call):
    if not is_admin(call.from_user.id, call.from_user.username or ""):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return
    
    try:
        order_id = call.data.split('_')[1]
        
        orders = load_orders()
        order_found = None
        for o in orders['orders']:
            if o['order_id'] == order_id:
                order_found = o
                break
        
        if not order_found:
            bot.answer_callback_query(call.id, "❌ Order not found!", show_alert=True)
            return
        
        if order_found['status'] == "delivered":
            bot.answer_callback_query(call.id, "✅ Already delivered!", show_alert=True)
            return
        
        # Update order status
        for o in orders['orders']:
            if o['order_id'] == order_id:
                o['status'] = "delivered"
                o['delivered_at'] = get_indian_time()
                break
        save_orders(orders)
        
        # ✅ REDUCE STOCK
        try:
            data = load_data()
            category_key = order_found.get('category', 'json')
            if category_key == 'json':
                products = data['products']['json_files']
            else:
                products = data['products']['coupons']
            
            for p in products:
                if p['name'] == order_found['product']:
                    p['stock'] = p.get('stock', 0) - order_found['quantity']
                    if p['stock'] < 0:
                        p['stock'] = 0
                    break
            save_data(data)
            print(f"✅ Stock reduced for {order_found['product']}")
        except Exception as e:
            print(f"⚠️ Stock reduction failed: {e}")
        
        # Send file to user
        try:
            filepath = os.path.join(JSON_FILES_DIR, f"{order_found['product']}.json")
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    bot.send_document(
                        order_found['user_id'],
                        f,
                        caption=f"✅ ORDER DELIVERED!\n━━━━━━━━━━━━━━\n\n"
                               f"🆔 {order_id}\n"
                               f"📦 {order_found['product']}\n"
                               f"📦 Quantity: {order_found['quantity']}\n\n"
                               f"Thank you for shopping at {STORE_NAME}! 🛍️"
                    )
            else:
                bot.send_message(
                    order_found['user_id'],
                    f"✅ ORDER DELIVERED!\n━━━━━━━━━━━━━━\n\n"
                    f"🆔 {order_id}\n"
                    f"📦 {order_found['product']}\n"
                    f"📦 Quantity: {order_found['quantity']}\n\n"
                    f"Thank you for shopping at {STORE_NAME}! 🛍️"
                )
        except Exception as e:
            print(f"Error sending file: {e}")
            try:
                bot.send_message(
                    order_found['user_id'],
                    f"✅ ORDER DELIVERED!\n━━━━━━━━━━━━━━\n\n"
                    f"🆔 {order_id}\n"
                    f"📦 {order_found['product']}\n"
                    f"📦 Quantity: {order_found['quantity']}\n\n"
                    f"Thank you for shopping at {STORE_NAME}! 🛍️"
                )
            except:
                pass
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_orders"))
        
        bot.edit_message_text(
            f"✅ ORDER DELIVERED!\n━━━━━━━━━━━━━━\n\n"
            f"Order: {order_id}\n"
            f"User: {order_found['username']}\n"
            f"Product: {order_found['product']}\n"
            f"Quantity: {order_found['quantity']}\n\n"
            f"✅ Delivered successfully!",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
        
        bot.answer_callback_query(call.id, "✅ Delivered!", show_alert=True)
    except Exception as e:
        print(f"Error in deliver: {e}")
        traceback.print_exc()
        bot.answer_callback_query(call.id, f"❌ Error!", show_alert=True)

# ============================================================
# ===== ADMIN BACK =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def admin_back(call):
    if not is_admin(call.from_user.id, call.from_user.username or ""):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        admin_panel(call.message)
    except Exception as e:
        print(f"Error: {e}")
        admin_panel(call.message)

# ============================================================
# ===== ADMIN ADD PRODUCT =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "admin_add")
def admin_add(call):
    if not is_admin(call.from_user.id, call.from_user.username or ""):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🎫 Add Coupon", callback_data="add_coupon"),
        telebot.types.InlineKeyboardButton("📁 Add JSON File", callback_data="add_json"),
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back")
    )
    
    bot.edit_message_text(
        "➕ ADD PRODUCT\n━━━━━━━━━━━━━━\n\n"
        "Select product type:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)

# ============================================================
# ===== ADMIN DELETE PRODUCT =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "admin_delete")
def admin_delete(call):
    if not is_admin(call.from_user.id, call.from_user.username or ""):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return
    
    try:
        data = load_data()
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        
        for i, p in enumerate(data['products']['json_files']):
            markup.add(telebot.types.InlineKeyboardButton(
                f"🗑️ {p['name']} - ₹{p['price']} ({p.get('stock', 0)} left)",
                callback_data=f"del_json_{i}"
            ))
        for i, p in enumerate(data['products']['coupons']):
            markup.add(telebot.types.InlineKeyboardButton(
                f"🗑️ {p['name']} - ₹{p['price']} ({p.get('stock', 0)} left)",
                callback_data=f"del_coupon_{i}"
            ))
        markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
        
        bot.edit_message_text(
            "🗑️ DELETE PRODUCT\n━━━━━━━━━━━━━━\n\n"
            "Click product to delete:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

# ============================================================
# ===== DELETE PRODUCT HANDLERS =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_json_'))
def delete_json(call):
    if not is_admin(call.from_user.id, call.from_user.username or ""):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return
    
    try:
        index = int(call.data.split('_')[2])
        data = load_data()
        
        if index < len(data['products']['json_files']):
            product = data['products']['json_files'][index]
            name = product['name']
            
            # Delete file
            filepath = os.path.join(JSON_FILES_DIR, f"{name}.json")
            delete_json_file(filepath)
            
            # Remove from data
            del data['products']['json_files'][index]
            save_data(data)
            
            bot.answer_callback_query(call.id, f"✅ Deleted: {name}", show_alert=True)
            admin_delete(call)
        else:
            bot.answer_callback_query(call.id, "❌ Not found!", show_alert=True)
    except Exception as e:
        print(f"Error: {e}")
        bot.answer_callback_query(call.id, "❌ Error!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_coupon_'))
def delete_coupon(call):
    if not is_admin(call.from_user.id, call.from_user.username or ""):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return
    
    try:
        index = int(call.data.split('_')[2])
        data = load_data()
        
        if index < len(data['products']['coupons']):
            product = data['products']['coupons'][index]
            name = product['name']
            
            del data['products']['coupons'][index]
            save_data(data)
            
            bot.answer_callback_query(call.id, f"✅ Deleted: {name}", show_alert=True)
            admin_delete(call)
        else:
            bot.answer_callback_query(call.id, "❌ Not found!", show_alert=True)
    except Exception as e:
        print(f"Error: {e}")
        bot.answer_callback_query(call.id, "❌ Error!", show_alert=True)

# ============================================================
# ===== ADMIN DELIVER ORDER =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "admin_deliver")
def admin_deliver_panel(call):
    if not is_admin(call.from_user.id, call.from_user.username or ""):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return
    
    try:
        orders = load_orders()
        pending = [o for o in orders['orders'] if o['status'] == "pending"]
        
        if not pending:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            bot.edit_message_text(
                "📦 DELIVER ORDER\n━━━━━━━━━━━━━━\n\n"
                "No pending orders! ✅",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup)
            return
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for o in pending:
            markup.add(telebot.types.InlineKeyboardButton(
                f"📦 {o['order_id']} - {o['username']} - ₹{o['total']}",
                callback_data=f"deliver_order_{o['order_id']}"
            ))
        markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
        
        bot.edit_message_text(
            f"📦 DELIVER ORDER ({len(pending)} pending)\n━━━━━━━━━━━━━━\n\n"
            "Select order to deliver:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('deliver_order_'))
def deliver_order_from_panel(call):
    if not is_admin(call.from_user.id, call.from_user.username or ""):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return
    
    try:
        order_id = call.data.split('_')[2]
        
        orders = load_orders()
        order_found = None
        for o in orders['orders']:
            if o['order_id'] == order_id:
                order_found = o
                break
        
        if not order_found:
            bot.answer_callback_query(call.id, "❌ Order not found!", show_alert=True)
            return
        
        if order_found['status'] == "delivered":
            bot.answer_callback_query(call.id, "✅ Already delivered!", show_alert=True)
            return
        
        # Update order status
        for o in orders['orders']:
            if o['order_id'] == order_id:
                o['status'] = "delivered"
                o['delivered_at'] = get_indian_time()
                break
        save_orders(orders)
        
        # ✅ REDUCE STOCK
        try:
            data = load_data()
            category_key = order_found.get('category', 'json')
            if category_key == 'json':
                products = data['products']['json_files']
            else:
                products = data['products']['coupons']
            
            for p in products:
                if p['name'] == order_found['product']:
                    p['stock'] = p.get('stock', 0) - order_found['quantity']
                    if p['stock'] < 0:
                        p['stock'] = 0
                    break
            save_data(data)
            print(f"✅ Stock reduced for {order_found['product']}")
        except Exception as e:
            print(f"⚠️ Stock reduction failed: {e}")
        
        # Send file to user
        try:
            filepath = os.path.join(JSON_FILES_DIR, f"{order_found['product']}.json")
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    bot.send_document(
                        order_found['user_id'],
                        f,
                        caption=f"✅ ORDER DELIVERED!\n━━━━━━━━━━━━━━\n\n"
                               f"🆔 {order_id}\n"
                               f"📦 {order_found['product']}\n"
                               f"📦 Quantity: {order_found['quantity']}\n\n"
                               f"Thank you for shopping at {STORE_NAME}! 🛍️"
                    )
            else:
                bot.send_message(
                    order_found['user_id'],
                    f"✅ ORDER DELIVERED!\n━━━━━━━━━━━━━━\n\n"
                    f"🆔 {order_id}\n"
                    f"📦 {order_found['product']}\n"
                    f"📦 Quantity: {order_found['quantity']}\n\n"
                    f"Thank you for shopping at {STORE_NAME}! 🛍️"
                )
        except Exception as e:
            print(f"Error sending file: {e}")
            try:
                bot.send_message(
                    order_found['user_id'],
                    f"✅ ORDER DELIVERED!\n━━━━━━━━━━━━━━\n\n"
                    f"🆔 {order_id}\n"
                    f"📦 {order_found['product']}\n"
                    f"📦 Quantity: {order_found['quantity']}\n\n"
                    f"Thank you for shopping at {STORE_NAME}! 🛍️"
                )
            except:
                pass
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_deliver"))
        
        bot.edit_message_text(
            f"✅ ORDER DELIVERED!\n━━━━━━━━━━━━━━\n\n"
            f"Order: {order_id}\n"
            f"User: {order_found['username']}\n"
            f"Product: {order_found['product']}\n"
            f"Quantity: {order_found['quantity']}\n\n"
            f"✅ Delivered successfully!",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
        
        bot.answer_callback_query(call.id, "✅ Delivered!", show_alert=True)
    except Exception as e:
        print(f"Error in deliver: {e}")
        traceback.print_exc()
        bot.answer_callback_query(call.id, f"❌ Error!", show_alert=True)

# ============================================================
# ===== ADD COUPON - STEP 1 =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "add_coupon")
def add_coupon_step1(call):
    if not is_admin(call.from_user.id, call.from_user.username or ""):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_add"))
    
    bot.edit_message_text(
        "➕ ADD COUPON\n━━━━━━━━━━━━━━\n\n"
        "Send coupon data in this format:\n\n"
        "Name: [coupon name]\n"
        "Price: [price]\n"
        "Stock: [quantity]\n"
        "Data: [comma separated codes]\n\n"
        "Example:\n"
        "Name: Flipkart 100 OFF\n"
        "Price: 50\n"
        "Stock: 10\n"
        "Data: CODE1, CODE2, CODE3",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)
    
    bot.register_next_step_handler(call.message, add_coupon_step2)

def add_coupon_step2(message):
    try:
        if not is_admin(message.from_user.id, message.from_user.username or ""):
            bot.reply_to(message, "❌ Unauthorized!")
            return
        
        lines = message.text.strip().split('\n')
        coupon_data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                if key == 'name':
                    coupon_data['name'] = value
                elif key == 'price':
                    coupon_data['price'] = int(value)
                elif key == 'stock':
                    coupon_data['stock'] = int(value)
                elif key == 'data':
                    coupon_data['data'] = [d.strip() for d in value.split(',') if d.strip()]
        
        if not all(k in coupon_data for k in ['name', 'price', 'stock', 'data']):
            bot.reply_to(message, "❌ Invalid format! Try again.")
            return
        
        data = load_data()
        data['products']['coupons'].append({
            "name": coupon_data['name'],
            "price": coupon_data['price'],
            "stock": coupon_data['stock'],
            "data": coupon_data['data']
        })
        save_data(data)
        
        bot.reply_to(message,
            f"✅ COUPON ADDED!\n━━━━━━━━━━━━━━\n\n"
            f"Name: {coupon_data['name']}\n"
            f"Price: ₹{coupon_data['price']}\n"
            f"Stock: {coupon_data['stock']}\n"
            f"Total Codes: {len(coupon_data['data'])}")
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, f"❌ Error: {e}")

# ============================================================
# ===== ADD JSON FILE - STEP 1 =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "add_json")
def add_json_step1(call):
    if not is_admin(call.from_user.id, call.from_user.username or ""):
        bot.answer_callback_query(call.id, "❌ Unauthorized!", show_alert=True)
        return
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_add"))
    
    bot.edit_message_text(
        "➕ ADD JSON FILE\n━━━━━━━━━━━━━━\n\n"
        "Send the file details:\n\n"
        "Name: [product name]\n"
        "Price: [price]\n"
        "Stock: [quantity]\n\n"
        "Then send the JSON file in next step.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup)
    
    bot.register_next_step_handler(call.message, add_json_step2)

def add_json_step2(message):
    try:
        if not is_admin(message.from_user.id, message.from_user.username or ""):
            bot.reply_to(message, "❌ Unauthorized!")
            return
        
        lines = message.text.strip().split('\n')
        json_data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                if key == 'name':
                    json_data['name'] = value
                elif key == 'price':
                    json_data['price'] = int(value)
                elif key == 'stock':
                    json_data['stock'] = int(value)
        
        if not all(k in json_data for k in ['name', 'price', 'stock']):
            bot.reply_to(message, "❌ Invalid format! Try again.")
            return
        
        bot.reply_to(message, 
            f"✅ Details received!\n\n"
            f"Name: {json_data['name']}\n"
            f"Price: ₹{json_data['price']}\n"
            f"Stock: {json_data['stock']}\n\n"
            f"📤 Now send the JSON file.")
        
        bot.register_next_step_handler(message, add_json_step3, json_data)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, f"❌ Error: {e}")

def add_json_step3(message, json_data):
    try:
        if not is_admin(message.from_user.id, message.from_user.username or ""):
            bot.reply_to(message, "❌ Unauthorized!")
            return
        
        if not message.document:
            bot.reply_to(message, "❌ Please send a file!")
            return
        
        if not message.document.file_name.endswith('.json'):
            bot.reply_to(message, "❌ Please send a JSON file!")
            return
        
        # Download file
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        try:
            file_data = json.loads(downloaded_file)
        except:
            bot.reply_to(message, "❌ Invalid JSON format!")
            return
        
        # Save file
        filename = f"{json_data['name']}.json"
        filepath = save_json_file(filename, file_data)
        
        # Add to store
        data = load_data()
        data['products']['json_files'].append({
            "name": json_data['name'],
            "price": json_data['price'],
            "stock": json_data['stock'],
            "data": file_data
        })
        save_data(data)
        
        bot.reply_to(message,
            f"✅ JSON FILE ADDED!\n━━━━━━━━━━━━━━\n\n"
            f"Name: {json_data['name']}\n"
            f"Price: ₹{json_data['price']}\n"
            f"Stock: {json_data['stock']}\n"
            f"File: {filename}\n"
            f"Data entries: {len(file_data)}")
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, f"❌ Error: {e}")

# ============================================================
# ===== RUN BOT =====
# ============================================================

def run_polling():
    print("🚀 Bot started in polling mode!")
    print(f"📅 Time: {get_indian_time()}")
    print("✅ Bot is running...")
    bot.infinity_polling()

if __name__ == "__main__":
    print("=" * 40)
    print(f"🏪 {STORE_NAME} BOT")
    print(f"📅 Started: {get_indian_time()}")
    print("=" * 40)
    
    # Flask server for Render Web Service
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return "Bot is running!"
    
    def run_flask():
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
    
    # Run bot in thread
    import threading
    threading.Thread(target=run_polling, daemon=True).start()
    
    # Run Flask server
    run_flask()
