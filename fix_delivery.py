import json
import time
import os

def deliver_order(order_id):
    # Load orders
    with open('orders.json', 'r') as f:
        orders = json.load(f)
    
    # Get specific order
    order = orders.get(order_id)
    if not order or order['status'] != 'pending':
        return False
    
    # Create unique JSON file for this order ONLY
    timestamp = int(time.time())
    filename = f"json_files/order_{order_id}_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump({order_id: order}, f, indent=2)
    
    # Update order status
    order['status'] = 'delivered'
    with open('orders.json', 'w') as f:
        json.dump(orders, f, indent=2)
    
    print(f"✅ Order {order_id} delivered: {filename}")
    return filename

# Test with your order
deliver_order("ORD47903454")
