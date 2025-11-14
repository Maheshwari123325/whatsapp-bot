from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
import json
import gspread
from google.oauth2.service_account import Credentials
import sys

# Force real-time log output
sys.stdout.reconfigure(line_buffering=True)

app = Flask(__name__)

# ------------------------------
#  GOOGLE SHEETS CONNECTION
# ------------------------------
def connect_to_gsheet():
    """Connect to Google Sheets using credentials stored in environment."""
    try:
        creds_env = os.getenv("GOOGLE_CREDENTIALS")
        if not creds_env:
            print("⚠ GOOGLE_CREDENTIALS variable not found!")
            return None

        print("🔹 Parsing GOOGLE_CREDENTIALS...")
        creds_json = json.loads(creds_env)

        print("🔹 Authorizing Google client...")
        creds = Credentials.from_service_account_info(creds_json)
        client = gspread.authorize(creds)

        print("🔹 Opening Google Sheet...")
        # ✅ Change sheet and tab names exactly as in your Google Sheet
        sheet = client.open("OIL BUSINESS BOT").worksheet("Products")

        print("✅ Google Sheet connected successfully.")
        return sheet

    except Exception as e:
        print("❌ Google Sheet connection error:", str(e))
        return None


# ------------------------------
#  FETCH PRODUCT DATA
# ------------------------------
def get_product_data():
    sheet = connect_to_gsheet()
    if not sheet:
        print("⚠ Could not connect to Google Sheet.")
        return None

    try:
        print("🔹 Fetching all records from sheet...")
        records = sheet.get_all_records()
        print(f"✅ Retrieved {len(records)} records from sheet.")
        if len(records) == 0:
            print("⚠ No records found — check header row in sheet.")
        return records
    except Exception as e:
        print("❌ Error reading sheet:", str(e))
        return None


# ------------------------------
#  AI REPLY FUNCTION
# ------------------------------
def get_ai_reply(user_input):
    """Send user input to OpenRouter AI model."""
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
                    "You are an AI ordering assistant for an oil business. "
                    "If the user asks about prices or menu, guide them politely."
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

    # --- Menu or Price Request ---
    if "menu" in msg_lower or "price" in msg_lower:
        data = get_product_data()
        if not data:
            reply.body("⚠ Could not fetch product prices at the moment. Please try again later.")
            return str(resp)

        text = "🛍 Available Products:\n"
        for row in data:
            name = row.get("item_name") or "Unnamed"
            price = row.get("price") or "N/A"
            text += f"• {name} — ₹{price}\n"
        reply.body(text)
        return str(resp)

    # --- Specific Product Query ---
    data = get_product_data()
    if data:
        for row in data:
            name = str(row.get("item_name", "")).lower()
            if name and name in msg_lower:
                price = row.get("price", "N/A")
                reply.body(f"{row['item_name']} costs ₹{price}.")
                return str(resp)

    # --- AI Fallback ---
    ai_reply = get_ai_reply(incoming_msg)
    print("🤖 AI Reply:", ai_reply)
    reply.body(ai_reply)
    return str(resp)


# ------------------------------
#  TEST GOOGLE SHEET ENDPOINT
# ------------------------------
@app.route("/test_gsheet", methods=["GET"])
def test_gsheet():
    """Debug endpoint to verify Google Sheet connectivity."""
    sheet = connect_to_gsheet()
    if not sheet:
        return "❌ Could not connect to Google Sheet"
    try:
        records = sheet.get_all_records()
        return f"✅ Connected! Found {len(records)} records."
    except Exception as e:
        return f"❌ Error reading sheet: {str(e)}"


# ------------------------------
#  RUN APP
# ------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",10000))  # Render often uses 10000
    app.run(host="0.0.0.0",port=port,debug=True)
