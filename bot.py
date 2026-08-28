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
OWNER_UPI = os.environ.get('OWNER_UPI', "8218957984@mbk")
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

# ===== CREATE DIRECTORIES =====
os.makedirs(JSON_FILES_DIR, exist_ok=True)

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

def generate_file_id():
    return "FILE" + ''.join(random.choices(string.digits, k=6))

def save_json_file(filename, data):
    filepath = os.path.join(JSON_FILES_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    return filepath

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
        "━━━━━━━━━━━━━━━━\n"
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
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=3)
        max_qty = min(5, stock)
        for q in range(1, max_qty + 1):
            markup.add(telebot.types.InlineKeyboardButton(f"{q}", callback_data=f"qty_{q}"))
        markup.add(
            telebot.types.InlineKeyboardButton("🔙 Back", callback_data="shop"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
        )
        
        bot.edit_message_text(
            f"📝 SELECT QUANTITY\n━━━━━━━━━━━━━━\n\n"
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
            f"📝 ENTER REFERENCE\n━━━━━━━━━━━━━━\n\n"
            f"Order: {order_id}\n"
            f"Total: ₹{order_found['total']}\n\n"
            f"Send your:\n"
            f"• UPI Transaction ID\n"
            f"• UTR Number\n"
            f"• Bank Reference\n\n"
            f"Type /cancel to cancel",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup)
        
        bot.register_next_step_handler(call.message, process_reference, order_id)
    except Exception as e:
        print(f"Error in payment_done: {e}")
        traceback.print_exc()
        bot.answer_callback_query(call.id, "❌ Error!", show_alert=True)

def process_reference(message, order_id):
    if message.text == "/cancel":
        bot.reply_to(message, "❌ Cancelled!")
        return
    
    reference = message.text.strip()
    
    orders = load_orders()
    order_found = None
    for order in orders['orders']:
        if order['order_id'] == order_id and order['user_id'] == message.from_user.id:
            order_found = order
            break
    
    if not order_found:
        bot.reply_to(message, "❌ Order not found!")
        return
    
    for order in orders['orders']:
        if order['order_id'] == order_id:
            order['payment'] = "paid"
            order['status'] = "pending_approval"
            order['reference'] = reference
            break
    save_orders(orders)
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Approve & Deliver", callback_data=f"approve_{order_id}"),
        telebot.types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{order_id}")
    )
    
    admin_msg = (
        f"🆕 PAYMENT RECEIVED\n\n"
        f"Order: {order_id}\n"
        f"User: @{order_found['username']}\n"
        f"Product: {order_found['product']}\n"
        f"Qty: {order_found.get('quantity', 1)}\n"
        f"Total: ₹{order_found['total']}\n"
        f"Ref: {reference}\n"
        f"Time: {get_indian_time()}"
    )
    
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)
    bot.send_message(ADMIN_ID, f"🔔 NEW PAYMENT!\nRef: {reference}")
    
    try:
        bot.send_message(CO_ADMIN_CHAT_ID, admin_msg, reply_markup=markup)
        bot.send_message(CO_ADMIN_CHAT_ID, f"🔔 NEW PAYMENT!\nRef: {reference}")
    except:
        try:
            bot.send_message("@Prime_Blogs", admin_msg, reply_markup=markup)
            bot.send_message("@Prime_Blogs", f"🔔 NEW PAYMENT!\nRef: {reference}")
        except:
            pass
    
    markup_user = telebot.types.InlineKeyboardMarkup()
    markup_user.add(
        telebot.types.InlineKeyboardButton("📦 Track Order", callback_data=f"track_{order_id}"),
        telebot.types.InlineKeyboardButton("🛒 Shop More", callback_data="shop"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main"),
        telebot.types.InlineKeyboardButton("📞 Support", callback_data="support")
    )
    
    bot.reply_to(message,
        f"✅ PAYMENT SENT!\n━━━━━━━━━━━━━━\n\n"
        f"Order: {order_id}\n"
        f"Ref: {reference}\n"
        f"Waiting for admin approval...",
        reply_markup=markup_user)

# ============================================================
# ===== APPROVE / REJECT - FIXED =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_'))
def approve_order(call):
    if not is_admin(call.from_user.id, call.from_user.username):
        bot.answer_callback_query(call.id, "⛔ Admin only!", show_alert=True)
        return
    
    try:
        order_id = call.data.split('_')[1]
        orders = load_orders()
        data = load_data()
        
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
        
        if order_found['status'] == "processing":
            bot.answer_callback_query(call.id, "🔄 Order is already being processed!", show_alert=True)
            return
        
        category = order_found['category']
        category_map = {"coupon": "coupons", "json": "json_files"}
        category_key = category_map.get(category)
        if not category_key:
            bot.answer_callback_query(call.id, "❌ Invalid category!", show_alert=True)
            return
        
        products = data['products'][category_key]
        
        product_to_deliver = None
        product_index = -1
        for i, p in enumerate(products):
            if p['name'] == order_found['product']:
                product_to_deliver = p
                product_index = i
                break
        
        if not product_to_deliver:
            bot.answer_callback_query(call.id, "❌ Product not found!", show_alert=True)
            return
        
        quantity = order_found.get('quantity', 1)
        stock = product_to_deliver.get('stock', 1)
        
        if stock < quantity:
            bot.answer_callback_query(call.id, f"❌ Only {stock} available!", show_alert=True)
            return
        
        # ===== MARK AS PROCESSING =====
        for order in orders['orders']:
            if order['order_id'] == order_id:
                order['status'] = "processing"
                break
        save_orders(orders)
        
        # ===== REDUCE STOCK =====
        products[product_index]['stock'] = stock - quantity
        
        data['settings']['total_earned'] += order_found['total']
        data['settings']['total_orders'] += 1
        save_data(data)
        
        # ===== SEND PRODUCTS =====
        product_msg = f"🎉 Order Delivered!\n━━━━━━━━━━━━━━\n\n"
        product_msg += f"Order: {order_id}\n"
        product_msg += f"Product: {product_to_deliver['name']}\n"
        product_msg += f"Quantity: {quantity}\n\n"
        
        file_sent_count = 0
        delivered_file_names = []
        
        if category == "coupon":
            product_msg += f"Coupon Code:\n{product_to_deliver['code']}\n"
            if product_to_deliver.get('expiry'):
                product_msg += f"Expires: {product_to_deliver['expiry']}\n"
            file_sent_count = 1
            delivered_file_names = ["Coupon Code"]
        
        elif category == "json":
            if isinstance(product_to_deliver['data'], list):
                # ===== FILES TO SEND =====
                files_to_send = []
                for i in range(quantity):
                    if i < len(product_to_deliver['data']):
                        files_to_send.append(product_to_deliver['data'][i])
                
                # ===== SEND FILES =====
                for i, file_data in enumerate(files_to_send):
                    file_id = generate_file_id()
                    filename = f"{file_id}_{file_data.get('name', 'file').replace(' ', '_')}.json"
                    filepath = save_json_file(filename, file_data['data'])
                    try:
                        with open(filepath, 'rb') as f:
                            bot.send_document(order_found['user_id'], f, caption=f"📄 {file_data.get('name', f'File {i+1}')}")
                        product_msg += f"✅ File #{i+1} - Sent!\n"
                        file_sent_count += 1
                        delivered_file_names.append(file_data.get('name', f'File {i+1}'))
                    except Exception as e:
                        product_msg += f"⚠️ File #{i+1} - Error: {str(e)}\n"
                
                # ===== 🔥 REMOVE SOLD FILES FROM DATA =====
                for i in range(quantity):
                    if product_to_deliver['data']:
                        product_to_deliver['data'].pop(0)
                
                product_msg += f"\n📂 Saved in: json_files/"
            else:
                for i in range(quantity):
                    file_id = generate_file_id()
                    filename = f"{file_id}_{product_to_deliver['name'].replace(' ', '_')}_{i+1}.json"
                    filepath = save_json_file(filename, product_to_deliver['data'])
                    try:
                        with open(filepath, 'rb') as f:
                            bot.send_document(order_found['user_id'], f, caption=f"📄 {product_to_deliver['name']} #{i+1}")
                        product_msg += f"✅ File #{i+1} - Sent!\n"
                        file_sent_count += 1
                        delivered_file_names.append(f"{product_to_deliver['name']} #{i+1}")
                    except Exception as e:
                        product_msg += f"⚠️ File #{i+1} - Error: {str(e)}\n"
                product_msg += f"\n📂 Saved in: json_files/"
        
        product_msg += f"\n✅ {file_sent_count} file(s) delivered successfully!"
        
        # ===== UPDATE ORDER STATUS TO DELIVERED =====
        for order in orders['orders']:
            if order['order_id'] == order_id:
                order['status'] = "delivered"
                order['delivered_at'] = get_indian_time()
                break
        save_orders(orders)
        
        markup_delivery = telebot.types.InlineKeyboardMarkup()
        markup_delivery.add(
            telebot.types.InlineKeyboardButton("🛒 Shop More", callback_data="shop"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main"),
            telebot.types.InlineKeyboardButton("📞 Support", callback_data="support")
        )
        
        bot.send_message(order_found['user_id'], product_msg, reply_markup=markup_delivery)
        
        # ===== SEND DELIVERY LOG TO ADMIN =====
        delivery_log = f"📦 DELIVERY DETAILS\n━━━━━━━━━━━━━━\n\n"
        delivery_log += f"Order: {order_id}\n"
        delivery_log += f"User: @{order_found['username']}\n"
        delivery_log += f"Product: {product_to_deliver['name']}\n"
        delivery_log += f"Quantity: {quantity}\n"
        delivery_log += f"Time: {get_indian_time()}\n\n"
        
        if delivered_file_names:
            delivery_log += f"Files Delivered:\n"
            for i, name in enumerate(delivered_file_names, 1):
                delivery_log += f"  {i}. {name}\n"
        
        delivery_log += f"\nStatus: Delivered Successfully!"
        
        bot.send_message(ADMIN_ID, delivery_log)
        try:
            bot.send_message(CO_ADMIN_CHAT_ID, delivery_log)
        except:
            try:
                bot.send_message("@Prime_Blogs", delivery_log)
            except:
                pass
        
        ref_text = f"\nRef: {order_found.get('reference', 'N/A')}" if order_found.get('reference') else ""
        markup_admin = telebot.types.InlineKeyboardMarkup()
        markup_admin.add(
            telebot.types.InlineKeyboardButton("🔙 Admin", callback_data="admin_back"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
        )
        
        bot.edit_message_text(
            f"✅ Order Delivered!\n\n"
            f"Order: {order_id}\n"
            f"Product: {order_found['product']}\n"
            f"Qty: {quantity}\n"
            f"Files Sent: {file_sent_count}\n"
            f"User: @{order_found['username']}{ref_text}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup_admin)
        bot.answer_callback_query(call.id, f"✅ Delivered! {file_sent_count} file(s) sent!", show_alert=True)
    except Exception as e:
        print(f"Error in approve: {e}")
        traceback.print_exc()
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def reject_order(call):
    if not is_admin(call.from_user.id, call.from_user.username):
        bot.answer_callback_query(call.id, "⛔ Admin only!", show_alert=True)
        return
    
    try:
        order_id = call.data.split('_')[1]
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
        
        for order in orders['orders']:
            if order['order_id'] == order_id:
                order['status'] = "rejected"
                order['rejected_at'] = get_indian_time()
                break
        save_orders(orders)
        
        markup_user = telebot.types.InlineKeyboardMarkup()
        markup_user.add(
            telebot.types.InlineKeyboardButton("🛒 Shop More", callback_data="shop"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
        )
        
        bot.send_message(order_found['user_id'],
            f"❌ Order Rejected\n\n"
            f"Order: {order_id}\n"
            f"Ref: {order_found.get('reference', 'N/A')}\n"
            f"Reason: Payment verification failed.\n\n"
            f"Contact: @Prime_Blogs",
            reply_markup=markup_user)
        
        markup_admin = telebot.types.InlineKeyboardMarkup()
        markup_admin.add(
            telebot.types.InlineKeyboardButton("🔙 Admin", callback_data="admin_back"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
        )
        
        bot.edit_message_text(
            f"❌ Order Rejected\n\n"
            f"Order: {order_id}\n"
            f"User: @{order_found['username']}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup_admin)
        bot.answer_callback_query(call.id, "❌ Rejected!", show_alert=True)
    except Exception as e:
        print(f"Error in reject: {e}")
        bot.answer_callback_query(call.id, f"❌ Error!", show_alert=True)

# ============================================================
# ===== TRACK & MY ORDERS =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('track_'))
def track_order(call):
    try:
        order_id = call.data.split('_')[1]
        orders = load_orders()
        for order in orders['orders']:
            if order['order_id'] == order_id:
                status_emoji = {"pending": "⏳", "pending_approval": "🔄", "delivered": "✅", "rejected": "❌", "cancelled": "🚫", "processing": "⚙️"}
                msg = f"📦 ORDER STATUS\n━━━━━━━━━━━━━━\n\n"
                msg += f"Order: {order_id}\n"
                msg += f"Product: {order['product']}\n"
                msg += f"Qty: {order.get('quantity', 1)}\n"
                msg += f"Price: ₹{order['price']} each\n"
                msg += f"Total: ₹{order['total']}\n"
                msg += f"Status: {status_emoji.get(order['status'], '❓')} {order['status'].upper()}\n"
                if order.get('reference'):
                    msg += f"Ref: {order['reference']}\n"
                msg += f"Date: {order.get('created_at', 'N/A')}\n"
                if order.get('delivered_at'):
                    msg += f"Delivered: {order['delivered_at']}\n"
                markup = telebot.types.InlineKeyboardMarkup()
                markup.add(
                    telebot.types.InlineKeyboardButton("🛒 Shop", callback_data="shop"),
                    telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main"),
                    telebot.types.InlineKeyboardButton("📞 Support", callback_data="support")
                )
                bot.answer_callback_query(call.id, f"Status: {order['status'].upper()}", show_alert=True)
                bot.edit_message_text(msg, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
                return
        bot.answer_callback_query(call.id, "❌ Order not found!", show_alert=True)
    except Exception as e:
        print(f"Error: {e}")

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
            bot.edit_message_text("📦 No Orders\n\nStart shopping now!", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
            return
        msg = "📦 MY ORDERS\n━━━━━━━━━━━━━━\n\n"
        for i, order in enumerate(user_orders[:5], 1):
            status_emoji = {"pending": "⏳", "pending_approval": "🔄", "delivered": "✅", "rejected": "❌", "cancelled": "🚫", "processing": "⚙️"}
            msg += f"{i}. {order['order_id']}\n"
            msg += f"   Product: {order['product']}\n"
            msg += f"   Qty: {order.get('quantity', 1)}\n"
            msg += f"   ₹{order['price']} each | ₹{order['total']}\n"
            msg += f"   {status_emoji.get(order['status'], '❓')}\n"
            if order.get('reference'):
                msg += f"   Ref: {order['reference']}\n"
            msg += f"   {order['created_at']}\n\n"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🛒 Shop", callback_data="shop"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
        )
        bot.edit_message_text(msg, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "help")
def help_callback(call):
    try:
        msg = f"❓ HELP CENTER\n━━━━━━━━━━━━━━\n\n"
        msg += "How to Buy:\n"
        msg += "1. Browse categories\n"
        msg += "2. Select product\n"
        msg += "3. Choose quantity\n"
        msg += "4. Pay via UPI (Scan QR)\n"
        msg += "5. Click 'I Have Paid'\n"
        msg += "6. Enter Transaction ID/UTR\n"
        msg += "7. Wait for admin approval\n"
        msg += "8. Get delivery\n\n"
        msg += f"UPI: {OWNER_UPI}\n"
        msg += f"Phone: {OWNER_PHONE}\n\n"
        msg += "Commands:\n"
        msg += "/start - Main menu\n\n"
        msg += "Support: @Prime_Blogs"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🛒 Shop", callback_data="shop"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main"),
            telebot.types.InlineKeyboardButton("📞 Support", callback_data="support")
        )
        bot.edit_message_text(msg, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

# ============================================================
# ===== ADMIN PANEL =====
# ============================================================

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id, message.from_user.username):
        bot.reply_to(message, "⛔ Admin only!")
        return
    
    orders = load_orders()
    pending = len([o for o in orders['orders'] if o['status'] == 'pending_approval'])
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton(f"⏳ Pending ({pending})", callback_data="admin_pending"),
        telebot.types.InlineKeyboardButton("➕ Add Product", callback_data="admin_add"),
        telebot.types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        telebot.types.InlineKeyboardButton("📦 Orders", callback_data="admin_orders"),
        telebot.types.InlineKeyboardButton("🗑️ Remove", callback_data="admin_remove"),
        telebot.types.InlineKeyboardButton("📋 List", callback_data="admin_list"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    
    bot.reply_to(message,
        "⚙️ ADMIN PANEL\n━━━━━━━━━━━━━━\n\n"
        f"Pending: {pending}\n"
        f"Total: {len(orders['orders'])}\n\n"
        "Select:",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_pending")
def admin_pending(call):
    if not is_admin(call.from_user.id, call.from_user.username):
        bot.answer_callback_query(call.id, "⛔ Admin only!", show_alert=True)
        return
    
    orders = load_orders()
    pending_orders = [o for o in orders['orders'] if o['status'] == 'pending_approval']
    
    if not pending_orders:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
        )
        bot.edit_message_text("✅ No pending approvals!", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        return
    
    msg = "⏳ PENDING\n━━━━━━━━━━━━━━\n\n"
    for order in pending_orders:
        msg += f"Order: {order['order_id']}\n"
        msg += f"User: @{order['username']}\n"
        msg += f"Product: {order['product']}\n"
        msg += f"Qty: {order.get('quantity', 1)}\n"
        msg += f"₹{order['price']} each | Total: ₹{order['total']}\n"
        if order.get('reference'):
            msg += f"Ref: {order['reference']}\n"
        msg += f"Date: {order['created_at']}\n\n"
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    bot.edit_message_text(msg, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def admin_back(call):
    if not is_admin(call.from_user.id, call.from_user.username):
        return
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    orders = load_orders()
    pending = len([o for o in orders['orders'] if o['status'] == 'pending_approval'])
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton(f"⏳ Pending ({pending})", callback_data="admin_pending"),
        telebot.types.InlineKeyboardButton("➕ Add Product", callback_data="admin_add"),
        telebot.types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        telebot.types.InlineKeyboardButton("📦 Orders", callback_data="admin_orders"),
        telebot.types.InlineKeyboardButton("🗑️ Remove", callback_data="admin_remove"),
        telebot.types.InlineKeyboardButton("📋 List", callback_data="admin_list"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    
    bot.send_message(call.message.chat.id,
        "⚙️ ADMIN PANEL\n━━━━━━━━━━━━━━\n\n"
        f"Pending: {pending}\n"
        f"Total: {len(orders['orders'])}\n\n"
        "Select:",
        reply_markup=markup)

# ============================================================
# ===== ADMIN: ADD PRODUCT =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "admin_add")
def admin_add(call):
    if not is_admin(call.from_user.id, call.from_user.username):
        return
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("🎫 Coupon", callback_data="add_coupon"),
        telebot.types.InlineKeyboardButton("📁 JSON", callback_data="add_json"),
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back")
    )
    bot.edit_message_text("➕ ADD PRODUCT\n━━━━━━━━━━━━━━\n\nSelect type:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_coupon")
def add_coupon_form(call):
    if not is_admin(call.from_user.id, call.from_user.username):
        return
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    bot.edit_message_text("🎫 ADD COUPON\n━━━━━━━━━━━━━━\n\nSend:\nNAME|CODE|PRICE|EXPIRY|STOCK\nExample:\nZomato Gold|ZOMATO50|499|2026-12-31|10\n\nType /cancel", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    bot.register_next_step_handler(call.message, process_add_coupon)

def process_add_coupon(message):
    if message.text == "/cancel":
        bot.reply_to(message, "❌ Cancelled!")
        return
    try:
        parts = message.text.split('|')
        if len(parts) < 4:
            bot.reply_to(message, "❌ Use: NAME|CODE|PRICE|EXPIRY|STOCK")
            return
        name = parts[0].strip()
        code = parts[1].strip()
        price = int(parts[2].strip())
        expiry = parts[3].strip()
        stock = int(parts[4].strip()) if len(parts) > 4 else 1
        data = load_data()
        data['products']['coupons'].append({"name": name, "code": code, "price": price, "expiry": expiry, "stock": stock})
        save_data(data)
        bot.reply_to(message, f"✅ Coupon added: {name} - ₹{price} (Stock: {stock})")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == "add_json")
def add_json_form(call):
    if not is_admin(call.from_user.id, call.from_user.username):
        return
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    bot.edit_message_text("📁 ADD JSON\n━━━━━━━━━━━━━━\n\nSend:\nNAME|PRICE|STOCK|JSON_DATA\nExample:\nBigbasket JSON|15|10|{\"key\":\"value\"}\n\nJSON must be in ONE LINE!\nType /cancel", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    bot.register_next_step_handler(call.message, process_add_json)

def process_add_json(message):
    if message.text == "/cancel":
        bot.reply_to(message, "❌ Cancelled!")
        return
    try:
        parts = message.text.split('|')
        if len(parts) != 4:
            bot.reply_to(message, "❌ Use: NAME|PRICE|STOCK|JSON_DATA")
            return
        name = parts[0].strip()
        price = int(parts[1].strip())
        stock = int(parts[2].strip())
        json_data = parts[3].strip()
        data_dict = json.loads(json_data)
        data = load_data()
        data['products']['json_files'].append({"name": name, "price": price, "stock": stock, "data": data_dict})
        save_data(data)
        bot.reply_to(message, f"✅ JSON added: {name} - ₹{price} (Stock: {stock})")
    except json.JSONDecodeError as e:
        bot.reply_to(message, f"❌ Invalid JSON! {str(e)}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# ============================================================
# ===== ADMIN: STATS, ORDERS, LIST, REMOVE =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id, call.from_user.username):
        return
    data = load_data()
    orders = load_orders()
    
    json_stock = sum(p.get('stock', 1) for p in data['products']['json_files'])
    coupon_stock = sum(p.get('stock', 1) for p in data['products']['coupons'])
    
    msg = f"📊 STORE STATS\n━━━━━━━━━━━━━━\n\n"
    msg += f"💰 Total Earned: ₹{data['settings']['total_earned']}\n"
    msg += f"📦 Total Orders: {len(orders['orders'])}\n"
    msg += f"✅ Delivered: {len([o for o in orders['orders'] if o['status'] == 'delivered'])}\n"
    msg += f"🔄 Pending: {len([o for o in orders['orders'] if o['status'] == 'pending_approval'])}\n"
    msg += f"⏳ New: {len([o for o in orders['orders'] if o['status'] == 'pending'])}\n"
    msg += f"❌ Rejected: {len([o for o in orders['orders'] if o['status'] == 'rejected'])}\n"
    msg += f"🚫 Cancelled: {len([o for o in orders['orders'] if o['status'] == 'cancelled'])}\n"
    msg += f"⚙️ Processing: {len([o for o in orders['orders'] if o['status'] == 'processing'])}\n\n"
    msg += f"📋 Products (Stock):\n"
    msg += f"🎫 Coupons: {len(data['products']['coupons'])} ({coupon_stock} units)\n"
    msg += f"📁 JSON: {len(data['products']['json_files'])} ({json_stock} units)"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    bot.edit_message_text(msg, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_orders")
def admin_orders(call):
    if not is_admin(call.from_user.id, call.from_user.username):
        return
    orders = load_orders()
    if not orders['orders']:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"),
            telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
        )
        bot.edit_message_text("📦 No orders yet!", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        return
    
    msg = "📦 ALL ORDERS\n━━━━━━━━━━━━━━\n\n"
    for order in orders['orders'][-10:]:
        status_emoji = {"pending": "⏳", "pending_approval": "🔄", "delivered": "✅", "rejected": "❌", "cancelled": "🚫", "processing": "⚙️"}
        msg += f"Order: {order['order_id']}\n"
        msg += f"User: {order['username']}\n"
        msg += f"Product: {order['product']}\n"
        msg += f"Qty: {order.get('quantity', 1)}\n"
        msg += f"₹{order['price']} each | Total: ₹{order['total']}\n"
        msg += f"{status_emoji.get(order['status'], '❓')}\n"
        if order.get('reference'):
            msg += f"Ref: {order['reference']}\n"
        msg += f"Date: {order['created_at']}\n\n"
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    bot.edit_message_text(msg, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_list")
def admin_list(call):
    if not is_admin(call.from_user.id, call.from_user.username):
        return
    data = load_data()
    msg = "📋 ALL PRODUCTS\n━━━━━━━━━━━━━━\n\n"
    msg += "🎫 Coupons:\n"
    for p in data['products']['coupons']:
        stock = p.get('stock', 1)
        msg += f"  • {p['name']} - ₹{p['price']} (Stock: {stock})\n"
    msg += "\n📁 JSON Files:\n"
    for p in data['products']['json_files']:
        stock = p.get('stock', 1)
        msg += f"  • {p['name']} - ₹{p['price']} (Stock: {stock})\n"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"),
        telebot.types.InlineKeyboardButton("🏠 Home", callback_data="back_main")
    )
    bot.edit_message_text(msg, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_remove")
def admin_remove(call):
    if not is_admin(call.from_user.id, call.from_user.username):
        return
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    bot.edit_message_text("🗑️ REMOVE PRODUCT\n━━━━━━━━━━━━━━\n\nSend product name to remove:\nType /cancel", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    bot.register_next_step_handler(call.message, process_remove_product)

def process_remove_product(message):
    if message.text == "/cancel":
        bot.reply_to(message, "❌ Cancelled!")
        return
    name = message.text.strip()
    data = load_data()
    removed = False
    for category in data['products']:
        for i, p in enumerate(data['products'][category]):
            if p['name'].lower() == name.lower():
                data['products'][category].pop(i)
                removed = True
                break
        if removed:
            break
    if removed:
        save_data(data)
        bot.reply_to(message, f"✅ Removed: {name}")
    else:
        bot.reply_to(message, f"❌ Not found: {name}")

# ============================================================
# ===== BACK TO MAIN =====
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    start(call.message)

# ============================================================
# ===== FLASK SERVER FOR RENDER =====
# ============================================================

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 PRIME STORE BOT IS RUNNING!"

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            print(f"Bot polling error: {e}")
            time.sleep(5)

# ============================================================
# ===== RUN =====
# ============================================================

print("=" * 50)
print("PRIME STORE BOT")
print("=" * 50)
print("Bot is running...")
print(f"Admin ID: {ADMIN_ID}")
print(f"Co-Admin Chat ID: {CO_ADMIN_CHAT_ID}")
print(f"UPI: {OWNER_UPI}")
print("=" * 50)

bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
