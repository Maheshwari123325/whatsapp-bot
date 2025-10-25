from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import csv
from datetime import datetime
import os
import re

app = Flask(__name__)

# Product catalog with keywords for flexible matching
PRODUCTS = {
    "SFO-1L": {
        "name": "Sunflower Oil 1L",
        "price": 150,
        "keywords": ["sunflower 1l", "sunflower oil 1 litre", "sunflower oil 1 liter", "sfo-1l"]
    },
    "SFO-5L": {
        "name": "Sunflower Oil 5L",
        "price": 700,
        "keywords": ["sunflower 5l", "sunflower oil 5 litre", "sunflower oil 5 liter", "sfo-5l"]
    },
    "GNO-1L": {
        "name": "Groundnut Oil 1L",
        "price": 180,
        "keywords": ["groundnut 1l", "groundnut oil 1 litre", "groundnut oil 1 liter", "gno-1l"]
    },
    "GNO-5L": {
        "name": "Groundnut Oil 5L",
        "price": 850,
        "keywords": ["groundnut 5l", "groundnut oil 5 litre", "groundnut oil 5 liter", "gno-5l"]
    }
}

ORDER_FILE = "orders.csv"

# Create CSV file if not exist
if not os.path.exists(ORDER_FILE):
    with open(ORDER_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Customer_Number", "Product", "Quantity", "Total_Amount"])

@app.route('/')
def home():
    return "WhatsApp Bot is running!"

@app.route('/bot', methods=['POST'])
def bot():
    msg = request.values.get('Body', '').strip().lower()
    sender = request.values.get('From', '')
    resp = MessagingResponse()
    reply = resp.message()

    # Greeting
    if msg in ['hi', 'hello']:
        reply.body("Hello 👋! I'm your WhatsApp ordering bot.\n"
                   "You can type:\n"
                   "👉 'menu' to view product codes\n"
                   "👉 'price' to view current prices\n"
                   "👉 or directly type your order, e.g.:\n"
                   "   'sunflower oil 1 litre 2 packets'\n"
                   "   'groundnut oil 5 litres 4 packets'\n"
                   "   'order SFO-1L 2'")
        return str(resp)

    # Show price list
    elif 'price' in msg:
        price_text = "🛍 Product Prices:\n"
        for code, details in PRODUCTS.items():
            price_text += f"{details['name']} - ₹{details['price']}\n"
        reply.body(price_text)
        return str(resp)

    # Show menu
    elif 'menu' in msg:
        menu_text = "📦 Menu Options:\n"
        for code, details in PRODUCTS.items():
            menu_text += f"{code} - {details['name']} (₹{details['price']})\n"
        menu_text += "\nExample: 'sunflower oil 1 litre 2 packets' or 'order GNO-5L 3'"
        reply.body(menu_text)
        return str(resp)

    # Detect quantity (e.g., 2, 3 packets, etc.)
    qty_match = re.search(r'(\d+)\s*(packet|packets|nos|no|qty|quantity)?', msg)
    qty = int(qty_match.group(1)) if qty_match else 1  # Default to 1 if not found

    # Identify product
    selected_product = None
    for code, info in PRODUCTS.items():
        for kw in info['keywords']:
            if kw in msg:
                selected_product = code
                break
        if selected_product:
            break

    # Handle order
    if selected_product:
        product = PRODUCTS[selected_product]
        total = product["price"] * qty

        # Save order
        with open(ORDER_FILE, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                sender,
                product['name'],
                qty,
                total
            ])

        reply.body(f"✅ Order confirmed!\n"
                   f"🛒 {product['name']}\n"
                   f"Qty: {qty}\n"
                   f"💰 Total: ₹{total}\n\n"
                   f"Thank you for your order! 🙏")
        return str(resp)

    # If message not recognized
    reply.body("🤖 Sorry, I didn’t understand that.\n"
               "Try messages like:\n"
               "👉 Sunflower oil 1 litre 2 packets\n"
               "👉 Groundnut oil 5 litre 4 packets\n"
               "👉 order GNO-1L 3")
    return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
