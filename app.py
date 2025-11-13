from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
import json
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# ------------------------------
#  GOOGLE SHEETS CONNECTION
# ------------------------------
def connect_to_gsheet():
    """Connect to Google Sheets using credentials stored in Render environment."""
    try:
        creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        creds = Credentials.from_service_account_info(creds_json)
        client = gspread.authorize(creds)
        # 👇 Change these to your own Google Sheet + worksheet names
        sheet = client.open("Your Google Sheet Name").worksheet("Products")
        return sheet
    except Exception as e:
        print("❌ Google Sheet connection error:", e)
        return None

# ------------------------------
#  AI REPLY FUNCTION
# ------------------------------
def get_ai_reply(user_input):
    """Send user message to OpenRouter and return AI-generated text."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/llama-4-maverick:free",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI ordering assistant. "
                    "If the user asks for prices or menu, first check the Google Sheet data. "
                    "If not found, respond politely using your AI reasoning."
                ),
            },
            {"role": "user", "content": user_input},
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=25)
        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()
        elif "error" in result:
            return f"⚠ AI error: {result['error'].get('message', 'Unknown')}"
        else:
            return "⚠ Unexpected AI response format."

    except Exception as e:
        print("AI Error:", e)
        return "⚠ Error connecting to AI server."

# ------------------------------
#  FETCH PRODUCT DATA FROM GOOGLE SHEET
# ------------------------------
def get_product_data():
    """Fetch all product names and prices from the Google Sheet."""
    sheet = connect_to_gsheet()
    if not sheet:
        return None

    try:
        records = sheet.get_all_records()
        return records  # list of dicts like [{'Product': 'Sunflower Oil 1L', 'Price': 150}, ...]
    except Exception as e:
        print("❌ Error reading sheet:", e)
        return None

# ------------------------------
#  MAIN ROUTES
# ------------------------------
@app.route("/", methods=["GET"])
def home():
    return "✅ WhatsApp AI Bot with Google Sheet integration is live!"

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")
    msg_lower = incoming_msg.lower()
    print(f"📩 Message from {sender}: {incoming_msg}")

    reply = MessagingResponse().message()

    # ⿡ Check for 'price' or 'menu' keywords
    if "price" in msg_lower or "menu" in msg_lower:
        data = get_product_data()
        if not data:
            reply.body("⚠ Could not load product list from Google Sheet.")
            return str(reply)

        # Build price/menu message
        text = "🛍 Available Products:\n"
        for row in data:
            name = row.get("Product") or row.get("Name") or "Unnamed"
            price = row.get("Price") or "N/A"
            text += f"• {name} — ₹{price}\n"
        reply.body(text)
        return str(reply)

    # ⿢ Try to match a specific product name in the message
    data = get_product_data()
    if data:
        for row in data:
            name = row.get("Product", "").lower()
            if name and name in msg_lower:
                price = row.get("Price", "N/A")
                reply.body(f"{row['Product']} costs ₹{price}.")
                return str(reply)

    # ⿣ Otherwise, ask AI
    ai_response = get_ai_reply(incoming_msg)
    print("🤖 AI Reply:", ai_response)
    reply.body(ai_response)
    return str(reply)

# ------------------------------
#  RUN APP
# ------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
