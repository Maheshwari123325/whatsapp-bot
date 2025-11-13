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
    """Connect to Google Sheets using service account credentials from Render env variable."""
    try:
        creds_env = os.getenv("GOOGLE_CREDENTIALS")
        if not creds_env:
            print("⚠ GOOGLE_CREDENTIALS variable not found!")
            return None

        print("🔹 Parsing GOOGLE_CREDENTIALS...")
        creds_json = json.loads(creds_env)

        print("🔹 Authorizing client...")
        creds = Credentials.from_service_account_info(creds_json)
        client = gspread.authorize(creds)

        print("🔹 Opening Google Sheet...")
        # ⚠ Change to your actual Google Sheet name and worksheet/tab name
        sheet = client.open("Your Google Sheet Name").worksheet("Products")

        print("✅ Google Sheet connected successfully.")
        return sheet

    except Exception as e:
        print("❌ Google Sheet connection error:", str(e))
        return None


# ------------------------------
#  FETCH PRODUCT DATA
# ------------------------------
def get_product_data():
    """Fetch all product rows from Google Sheet."""
    sheet = connect_to_gsheet()
    if not sheet:
        print("⚠ Could not connect to Google Sheet.")
        return None

    try:
        records = sheet.get_all_records()
        print(f"✅ Retrieved {len(records)} rows from Google Sheet.")
        return records
    except Exception as e:
        print("❌ Error reading sheet:", str(e))
        return None


# ------------------------------
#  AI REPLY FUNCTION
# ------------------------------
def get_ai_reply(user_input):
    """Send user input to OpenRouter AI model and return the reply text."""
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
                    "Help users browse products, check prices, and place polite orders. "
                    "If product data is unavailable, respond helpfully using your knowledge."
                ),
            },
            {"role": "user", "content": user_input},
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=25)
        result = response.json()
        print("🔹 AI Raw Response:", str(result)[:200])

        if "choices" in result and len(result["choices"]) > 0:
            msg = result["choices"][0].get("message", {}).get("content", "")
            return msg.strip() if msg else "⚠ AI returned empty reply."
        elif "error" in result:
            return f"⚠ AI error: {result['error'].get('message', 'Unknown')}"
        else:
            return "⚠ Unexpected AI response format."

    except Exception as e:
        print("❌ AI Error:", e)
        return "⚠ Error connecting to AI server."


# ------------------------------
#  FLASK ROUTES
# ------------------------------
@app.route("/", methods=["GET"])
def home():
    return "✅ WhatsApp AI Bot with Google Sheet integration is live!"


@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")
    msg_lower = incoming_msg.lower()

    print(f"\n📩 Message from {sender}: {incoming_msg}")

    resp = MessagingResponse()
    reply = resp.message()

    # --- ⿡ Menu or Price Request ---
    if "menu" in msg_lower or "price" in msg_lower:
        data = get_product_data()
        if not data:
            reply.body("⚠ Could not load product list from Google Sheet.")
            return str(resp)

        text = "🛍 Available Products:\n"
        for row in data:
            product_name = row.get("Product") or row.get("Name") or "Unnamed"
            product_price = row.get("Price") or "N/A"
            text += f"• {product_name} — ₹{product_price}\n"
        reply.body(text)
        return str(resp)

    # --- ⿢ Specific Product Price ---
    data = get_product_data()
    if data:
        for row in data:
            product_name = str(row.get("Product", "")).lower()
            if product_name and product_name in msg_lower:
                product_price = row.get("Price", "N/A")
                reply.body(f"{row['Product']} costs ₹{product_price}.")
                return str(resp)

    # --- ⿣ AI Response (fallback) ---
    ai_reply = get_ai_reply(incoming_msg)
    print("🤖 AI Reply:", ai_reply)
    reply.body(ai_reply)
    return str(resp)


# ------------------------------
#  RUN APP
# ------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
