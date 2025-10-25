from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import csv
from datetime import datetime
import os

app = Flask(__name__)

# Product catalog with codes and prices
PRODUCTS = {
    "SFO-1L": {"name": "Sunflower Oil 1L", "price": 150},
    "SFO-5L": {"name": "Sunflower Oil 5L", "price": 700},
    "GNO-1L": {"name": "Groundnut Oil 1L", "price": 180},
    "GNO-5L": {"name": "Groundnut Oil 5L", "price": 850}
}

ORDER_FILE = "orders.csv"

# Create the CSV file with headers if not exist
if not os.path.exists(ORDER_FILE):
    with open(ORDER_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Customer_Number", "Product", "Quantity", "Total_Amount"])

@app.route('/')
def home():
    return "WhatsApp Bot is running!"

@app.route('/bot', methods=['POST'])
def bot():
    msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    resp = MessagingResponse()
    reply = resp.message()

    msg_lower = msg.lower()

    # Greeting
    if msg_lower in ['hi', 'hello']:
        reply.body("Hello 👋! I'm your WhatsApp ordering bot.\n"
                   "You can type:\n"
                   "👉 'price' to see product prices\n"
                   "👉 'menu' to view product codes\n"
                   "👉 'order <code> <quantity>' or simply '<code> <quantity>' to place an order")
        return str(resp)

    # Show prices
    elif 'price' in msg_lower:
        reply.body("🛍 Product Prices:\n"
                   "Sunflower Oil 1L - ₹150\n"
                   "Sunflower Oil 5L - ₹700\n"
                   "Groundnut Oil 1L - ₹180\n"
                   "Groundnut Oil 5L - ₹850")
        return str(resp)

    # Show menu
    elif 'menu' in msg_lower:
        menu_text = "📦 Menu Options:\n"
        for code, details in PRODUCTS.items():
            menu_text += f"{code} - {details['name']} (₹{details['price']})\n"
        menu_text += "\nExample: order SFO-1L 2 or SFO-1L 2"
        reply.body(menu_text)
        return str(resp)

    # Order (either "order code qty" or "code qty")
    elif msg_lower.startswith("order") or any(code.lower() in msg_lower for code in PRODUCTS):
        parts = msg.replace("order", "").strip().split()
        if len(parts) < 2:
            reply.body("⚠ Invalid format.\nUse: order <code> <quantity>\nExample: order SFO-1L 2")
            return str(resp)

        code = parts[0].upper()
        try:
            qty = int(parts[1])
        except ValueError:
            reply.body("⚠ Quantity must be a number.\nExample: order SFO-1L 2")
            return str(resp)

        if code not in PRODUCTS:
            reply.body("❌ Invalid product code. Type 'menu' to see available products.")
            return str(resp)

        product = PRODUCTS[code]
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
                   f"Product: {product['name']}\n"
                   f"Quantity: {qty}\n"
                   f"Total Amount: ₹{total}\n\n"
                   f"Thank you for your order! 🙏")
        return str(resp)

    # Fallback for unknown messages
    else:
        reply.body("🤖 Sorry, I didn’t understand that.\nType 'menu' for help.")
        return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
