import openai
print("OpenAI SDK version in Render:", openai.__version__)
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import csv
from datetime import datetime
import os
import re

# Initialize Flask
app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI()

# Product catalog with codes and prices
PRODUCTS = {
    "SFO-1L": {"name": "Sunflower Oil 1L", "price": 150},
    "SFO-5L": {"name": "Sunflower Oil 5L", "price": 700},
    "GNO-1L": {"name": "Groundnut Oil 1L", "price": 180},
    "GNO-5L": {"name": "Groundnut Oil 5L", "price": 850}
}

ORDER_FILE = "orders.csv"

# Create CSV file if not exists
if not os.path.exists(ORDER_FILE):
    with open(ORDER_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Customer_Number", "Product", "Quantity", "Total_Amount"])


@app.route('/')
def home():
    return "✅ OilWhatsAppBot (AI Version) is running!"


@app.route('/bot', methods=['POST'])
def bot():
    msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    resp = MessagingResponse()
    reply = resp.message()

    msg_lower = msg.lower()

    # --- RULE-BASED QUICK COMMANDS ---
    if msg_lower in ['hi', 'hello']:
        reply.body(
            "Hello 👋! I'm OilWhatsAppBot (AI), your smart ordering assistant.\n\n"
            "You can type:\n"
            "👉 'price' — to see product prices\n"
            "👉 'menu' — to view product codes\n"
            "👉 'order <items>' — to place an order\n"
            "👉 Or just talk naturally, like:\n"
            "‘I want 5L sunflower oil and 1L groundnut oil.’"
        )
        return str(resp)

    elif 'price' in msg_lower:
        prices = "\n".join([f"{v['name']} - ₹{v['price']}" for v in PRODUCTS.values()])
        reply.body(f"🛍 Product Prices:\n{prices}")
        return str(resp)

    elif 'menu' in msg_lower:
        menu_text = "📦 Menu Options:\n"
        for code, details in PRODUCTS.items():
            menu_text += f"{code} - {details['name']} (₹{details['price']})\n"
        menu_text += "\nExample:\norder SFO-1L 2, GNO-1L 4"
        reply.body(menu_text)
        return str(resp)

    # --- AI ORDER HANDLING ---
    try:
        ai_prompt = f"""
        You are an intelligent WhatsApp ordering assistant for an oil business.
        Understand the user's message and identify product names, quantities, and sizes.
        The available products are:
        {PRODUCTS}

        Message: "{msg}"

        Respond in this structured JSON format:
        {{
            "orders": [
                {{"product_code": "SFO-1L", "quantity": 2}},
                {{"product_code": "GNO-5L", "quantity": 1}}
            ],
            "clarification": "if needed"
        }}
        """

        # ✅ Updated syntax for OpenAI v1.x
        ai_response = client.responses.create(
            model="gpt-4.1-mini",
            input=ai_prompt
        )

        ai_text = ai_response.output[0].content[0].text.strip()

        # --- Extract product orders from AI response ---
        orders = []
        total_bill = 0

        # Try to parse AI JSON-like text
        matches = re.findall(r'"product_code":\s*"(\w+-\w+)"\s*,\s*"quantity":\s*(\d+)', ai_text)
        for code, qty in matches:
            qty = int(qty)
            if code in PRODUCTS:
                product = PRODUCTS[code]
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

        # --- AI-Driven Natural Reply ---
        if orders:
            confirm_msg = "✅ Order confirmed!\n"
            for p, q, t in orders:
                confirm_msg += f"{p} x{q} = ₹{t}\n"
            confirm_msg += f"\n🧾 Total Bill: ₹{total_bill}\nThank you for your order! 🙏"
            reply.body(confirm_msg)
        else:
            reply.body("🤖 I couldn’t identify your order. Please specify product and quantity clearly.\nExample: 'Order SFO-1L 2, GNO-1L 1'.")

    except Exception as e:
        reply.body(f"⚠ AI bot error: {str(e)}")

    return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
