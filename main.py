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

# Create the CSV file with headers if not exist
if not os.path.exists(ORDER_FILE):
    with open(ORDER_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Customer_Number", "Product", "Quantity", "Total_Amount"])


def normalize_text(s: str) -> str:
    """Lowercase and remove non-alphanumeric characters to make matching robust."""
    return re.sub(r'[^a-z0-9]', '', s.lower())


def extract_quantity(text: str):
    """
    Extract quantity from the text.
    - Prefer the last numeric token (so '1 liter 4 packets' -> 4)
    - If no digits, try small number words ('one', 'two', ...)
    Returns int quantity or None if not found.
    """
    digits = re.findall(r'\d+', text)
    if digits:
        try:
            return int(digits[-1])  # last number is the quantity
        except ValueError:
            return None

    # fallback: check small number words
    word_map = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }
    words = re.findall(r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\b', text)
    if words:
        return word_map[words[-1]]
    return None


def find_product_code(part: str):
    """
    Try to find the matching product code for the given text part.
    Uses normalized code match first (handles hyphen/space variations),
    then checks product name keywords (sunflower / groundnut + size).
    """
    part_norm = normalize_text(part)

    # 1) direct code match (normalized)
    for code in PRODUCTS.keys():
        if normalize_text(code) in part_norm:
            return code

    # 2) match by product name keywords (e.g., 'sunflower' and '1l')
    for code, details in PRODUCTS.items():
        name = details['name'].lower()  # ex: 'sunflower oil 1l'
        name_tokens = name.split()
        # check if the brand/type (first token) is present and size token (last) is also present
        if name_tokens[0] in part and name_tokens[-1] in part:
            return code
        # If only brand present but size not explicitly mentioned, still match brand if no ambiguity
        if name_tokens[0] in part:
            # only match by brand if there is no other brand keyword for safety
            return code

    return None


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

    print("Received message:", msg)  # useful for debugging in logs

    # Greeting
    if msg_lower in ['hi', 'hello']:
        reply.body("Hello 👋! I'm your WhatsApp ordering bot.\n"
                   "You can type:\n"
                   "👉 'price' to see product prices\n"
                   "👉 'menu' to view product codes\n"
                   "👉 'order <items>' to place an order (e.g., 'order SFO-1L 2, GNO-1L 4' or 'order groundnut oil 1 liter 4 packets')")
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
        menu_text += "\nExample: order SFO-1L 2, GNO-1L 4, SFO-5L 3"
        reply.body(menu_text)
        return str(resp)

    # Order handling (supports multiple items separated by commas or 'and')
    elif msg_lower.startswith("order") or any(code.lower() in msg_lower for code in PRODUCTS):
        msg_clean = msg_lower.replace("order", "").strip()

        # split by comma or the word 'and' as a separator
        parts = [p.strip() for p in re.split(r',|\band\b', msg_clean) if p.strip()]

        orders = []
        total_bill = 0
        invalid_items = []

        for part in parts:
            # find product code using robust matching
            found_code = find_product_code(part)
            if not found_code:
                invalid_items.append(part)
                continue

            qty = extract_quantity(part)
            if qty is None or qty <= 0:
                invalid_items.append(part)
                continue

            product = PRODUCTS[found_code]
            total = product["price"] * qty
            total_bill += total
            orders.append((product["name"], qty, total))

            # Save each item into CSV
            try:
                with open(ORDER_FILE, mode="a", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        sender,
                        product['name'],
                        qty,
                        total
                    ])
            except Exception as e:
                print("Error writing CSV:", e)

        if not orders:
            reply.body("⚠ Could not understand your order.\nUse: order SFO-1L 2, GNO-1L 4, SFO-5L 3\nOr try: order sunflower oil 1 liter 2 packets")
            return str(resp)

        # Build confirmation message
        confirm_lines = ["✅ Order confirmed!"]
        for p_name, p_qty, p_total in orders:
            confirm_lines.append(f"{p_name} x{p_qty} = ₹{p_total}")
        confirm_lines.append(f"\n🧾 Total Bill: ₹{total_bill}")
        confirm_lines.append("Thank you for your order! 🙏")

        if invalid_items:
            confirm_lines.append("\n⚠ Could not recognize: " + "; ".join(invalid_items))

        reply.body("\n".join(confirm_lines))
        return str(resp)

    # Fallback for unknown messages
    else:
        reply.body("🤖 Sorry, I didn’t understand that.\nType 'menu' for help.")
        return str(resp)
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
