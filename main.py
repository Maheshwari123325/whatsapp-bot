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

    # 👋 Greeting
    if msg_lower in ['hi', 'hello']:
        reply.body(
            "Hello 👋! I'm your WhatsApp ordering bot.\n\n"
            "You can type:\n"
            "👉 'price' — to see product prices\n"
            "👉 'menu' — to view product codes\n"
            "👉 'order <items>' — to place an order\n\n"
            "Example:\n"
            "order sunflower oil 1 liter 2 packets, groundnut oil 5 liter 3 packets"
        )
        return str(resp)

    # 💰 Show prices
    elif 'price' in msg_lower:
        reply.body(
            "🛍 Product Prices:\n"
            "Sunflower Oil 1L - ₹150\n"
            "Sunflower Oil 5L - ₹700\n"
            "Groundnut Oil 1L - ₹180\n"
            "Groundnut Oil 5L - ₹850"
        )
        return str(resp)

    # 📦 Show menu
    elif 'menu' in msg_lower:
        menu_text = "📦 Menu Options:\n"
        for code, details in PRODUCTS.items():
            menu_text += f"{code} - {details['name']} (₹{details['price']})\n"
        menu_text += "\nExample:\norder SFO-1L 2, GNO-1L 4, SFO-5L 3"
        reply.body(menu_text)
        return str(resp)

    # 🛒 Order handling
    elif msg_lower.startswith("order") or any(code.lower() in msg_lower for code in PRODUCTS):
        msg_clean = msg_lower.replace("order", "").strip()
        parts = re.split(r',| and ', msg_clean)

        orders = []
        total_bill = 0
        invalid_items = []

        for part in parts:
            part = part.strip()

            # Try to identify the product
            found_code = None
            for code, details in PRODUCTS.items():
                pattern = re.compile(
                    rf"{details['name'].split()[0].lower()}.*(1l|5l|1|5|liter|litre|liters|litres)",
                    re.IGNORECASE
                )
                if code.lower() in part or pattern.search(part):
                    found_code = code
                    break

            if not found_code:
                invalid_items.append(part)
                continue

            # Extract quantity
            qty_match = re.findall(r'\d+', part)
            if not qty_match:
                invalid_items.append(part)
                continue

            qty = int(qty_match[-1])  # Last number is treated as quantity
            product = PRODUCTS[found_code]
            total = product["price"] * qty
            total_bill += total

            orders.append((product["name"], qty, total))

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

        if not orders:
            reply.body("⚠ Could not understand your order.\nExample:\norder sunflower oil 1 liter 2 packets, groundnut oil 5 liter 3 packets")
            return str(resp)

        # Build confirmation message
        confirm_msg = "✅ Order confirmed!\n"
        for p, q, t in orders:
            confirm_msg += f"{p} x{q} = ₹{t}\n"
        confirm_msg += f"\n🧾 Total Bill: ₹{total_bill}\nThank you for your order! 🙏"

        if invalid_items:
            confirm_msg += "\n\n⚠ Could not recognize: " + ", ".join(invalid_items)

        reply.body(confirm_msg)
        return str(resp)

    # 🤖 Unknown message
    else:
        reply.body("🤖 Sorry, I didn’t understand that.\nType 'menu' for help.")
        return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
