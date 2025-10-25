from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# --- Product Catalog ---
PRODUCTS = {
    "SFO-1L": {"name": "Sunflower Oil 1L", "price": 150},
    "SFO-5L": {"name": "Sunflower Oil 5L", "price": 700},
    "GNO-1L": {"name": "Groundnut Oil 1L", "price": 180},
    "GNO-5L": {"name": "Groundnut Oil 5L", "price": 850}
}


@app.route('/')
def home():
    return "🌐 WhatsApp Bot is running!"


@app.route('/bot', methods=['POST'])
def bot():
    msg = request.values.get('Body', '').strip().lower()
    resp = MessagingResponse()
    reply = resp.message()

    # --- Greeting ---
    if msg in ['hi', 'hello', 'hey']:
        reply.body("Hello 👋! I'm your WhatsApp ordering bot.\n\n"
                   "Type:\n"
                   "- 'price' to view products\n"
                   "- 'order <item_id> <quantity>' to place an order\n"
                   "- 'menu' to see these options again.")
        return str(resp)

    # --- Menu ---
    elif msg == 'menu':
        reply.body("📋 Menu Options:\n"
                   "- 'price' → Show available products & prices\n"
                   "- 'order <item_id> <quantity>' → Place an order\n"
                   "- Example: order sfo-1l 2")
        return str(resp)

    # --- Price list ---
    elif msg == 'price':
        price_list = "🛍 Product Prices:\n"
        for pid, details in PRODUCTS.items():
            price_list += f"{pid} - {details['name']} - ₹{details['price']}\n"
        reply.body(price_list)
        return str(resp)

    # --- Order placing ---
    elif msg.startswith("order"):
        parts = msg.split()
        if len(parts) != 3:
            reply.body("⚠ Invalid format!\nPlease use: order <item_id> <quantity>\nExample: order sfo-1l 2")
            return str(resp)

        _, item_id, quantity = parts
        item_id = item_id.upper()

        if item_id not in PRODUCTS:
            reply.body("❌ Invalid item ID. Type 'price' to check available product IDs.")
            return str(resp)

        try:
            quantity = int(quantity)
        except ValueError:
            reply.body("⚠ Quantity should be a number.")
            return str(resp)

        item = PRODUCTS[item_id]
        total = item['price'] * quantity

        reply.body(f"✅ Order placed successfully!\n\n"
                   f"🧾 Item: {item['name']}\n"
                   f"📦 Quantity: {quantity}\n"
                   f"💰 Total: ₹{total}\n\n"
                   "Thank you for your order! 🙏")
        return str(resp)

    # --- Unknown message ---
    else:
        reply.body("🤖 Sorry, I didn’t understand that.\nType 'menu' for help.")
        return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
