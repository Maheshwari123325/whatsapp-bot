from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import csv
from datetime import datetime
import os
import re

app = Flask(__name__)

# Product catalog with codes and prices
PRODUCTS = {
    "SFO-1L": {"name": "Sunflower Oil 1L", "price": 150},
    "SFO-5L": {"name": "Sunflower Oil 5L", "price": 700},
    "GNO-1L": {"name": "Groundnut Oil 1L", "price": 180},
    "GNO-5L": {"name": "Groundnut Oil 5L", "price": 850}
}

ORDER_FILE = "orders.csv"

# Create CSV file with headers if not exists
if not os.path.exists(ORDER_FILE):
    with open(ORDER_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Customer_Number", "Product", "Quantity", "Total_Amount"])

@app.route('/')
def home():
    return "✅ WhatsApp Bot is running!"

@app.route('/bot', methods=['POST'])
def bot():
    msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    resp = MessagingResponse()
    reply = resp.message()
    msg_lower = msg.lower()

    # Greeting
    if msg_lower in ['hi', 'hello']:
        reply.body("👋 Hello! Welcome to Oil Store.\nSend product code to order.\n\nExample: SFO-1L or GNO-5L")
        return str(resp)

    # Product info and order
    match = re.match(r'([A-Za-z0-9\-]+)\s*(\d+)?', msg)
    if match:
        code = match.group(1).upper()
        qty = int(match.group(2)) if match.group(2) else 1

        if code in PRODUCTS:
            product = PRODUCTS[code]
            total = product['price'] * qty

            # Save to CSV
            with open(ORDER_FILE, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    sender,
                    product['name'],
                    qty,
                    total
                ])

            reply.body(f"✅ Order placed:\n{product['name']} x {qty}\n💰 Total = ₹{total}")
            return str(resp)
        else:
            reply.body("❌ Invalid code! Please try again with valid product code.")
            return str(resp)

    reply.body("Please send a valid product code or type 'Hi' to start.")
    return str(resp)

# ✅ NEW ROUTE TO SEE YOUR ORDERS IN BROWSER
@app.route('/orders', methods=['GET'])
def show_orders():
    if os.path.exists(ORDER_FILE):
        with open(ORDER_FILE, 'r', encoding='utf-8') as file:
            return "<pre>" + file.read() + "</pre>"
    else:
        return "No orders.csv file found yet."

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
