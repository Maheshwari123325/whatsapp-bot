from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import csv
from datetime import datetime
import os

app = Flask(__name__)

# Product catalog
PRODUCTS = {
    "SFO-1L": {"name": "Sunflower Oil 1L", "price": 150},
    "SFO-5L": {"name": "Sunflower Oil 5L", "price": 700},
    "GNO-1L": {"name": "Groundnut Oil 1L", "price": 180},
    "GNO-5L": {"name": "Groundnut Oil 5L", "price": 850}
}

ORDER_FILE = "orders.csv"

# Create the CSV file if not exists
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
    sender = request.values.get('From', '').replace("whatsapp:", "")
    resp = MessagingResponse()
    reply = resp.message()

    msg_lower = msg.lower()

    # Greeting
    if msg_lower in ['hi', 'hello']:
        reply.body("Hello 👋! I'm your WhatsApp ordering bot.\n\n"
                   "You can type:\n"
                   "🛍 'price' → View product prices\n"
                   "📦 'menu' → View product codes\n"
                   "🛒 'order <code> <quantity>' or '<code> <quantity>' → Place an order\n"
                   "📋 'my orders' → View your past orders")
        return str(resp)

    # Price list
    elif 'price' in msg_lower:
        reply.body("🛍 Product Prices:\n"
                   "SFO-1L - ₹150\n"
                   "SFO-5L - ₹700\n"
                   "GNO-1L - ₹180\n"
                   "GNO-5L - ₹850")
        return str(resp)

    # Menu with codes
    elif 'menu' in msg_lower:
        menu_text = "📦 Menu Options:\n"
        for code, details in PRODUCTS.items():
            menu_text += f"{code} - {details['name']} (₹{details['price']})\n"
        menu_text += "\nExample: order SFO-1L 2 or SFO-1L 2"
        reply.body(menu_text)
        return str(resp)

    # View order history
    elif 'my orders' in msg_lower:
        if not os.path.exists(ORDER_FILE):
            reply.body("📝 You have no orders yet.")
            return str(resp)

        with open(ORDER_FILE, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            orders = [row for row in reader if row["Customer_Number"] == sender]

        if not orders:
            reply.body("📝 You have no previous orders.")
            return str(resp)

        summary = "🧾 Your Order History:\n"
        for o in orders[-5:]:  # show last 5 orders
            summary += (f"📅 {o['Date']}\n"
                        f"🛒 {o['Product']}\n"
                        f"Qty: {o['Quantity']} | ₹{o['Total_Amount']}\n\n")

        reply.body(summary)
        return str(resp)

    # Order command (supports "order SFO-1L 2" or "SFO-1L 2")
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

        # Save order in CSV
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

    # Fallback
    else:
        reply.body("🤖 Sorry, I didn’t understand that.\nType 'menu' or 'hi' for help.")
        return str(resp)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0",port=port)
