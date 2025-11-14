from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
import json
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# ---------------------------------
# GOOGLE SHEETS SETUP
# ---------------------------------
SCOPE = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SHEET_URL = os.getenv("SHEET_URL")

def load_google_sheet():
    """
    Load Google Credentials from Render secret file and return sheet object.
    """
    SECRET_FILE_PATH = "/etc/secrets/credential.json"

    try:
        print("🔍 Checking Google Credential file...")

        if not os.path.exists(SECRET_FILE_PATH):
            print(f"❌ Secret file NOT found at: {SECRET_FILE_PATH}")
            return None

        print("📄 Credential file found. Authorizing Google client...")
        creds = Credentials.from_service_account_file(SECRET_FILE_PATH, scopes=SCOPE)

        client = gspread.authorize(creds)
        sheet = client.open_by_url(SHEET_URL).worksheet("Products")

        print("✅ Google Sheet connected successfully!")
        return sheet

    except Exception as e:
        print("❌ Google Sheets error:", str(e))
        return None


sheet = load_google_sheet()


# ---------------------------------
# Fetch product price from Sheet
# ---------------------------------
def get_product_price(product_name):
    if sheet is None:
        return "⚠ Could not connect to Google Sheets. Please try later."

    try:
        records = sheet.get_all_records()

        for row in records:
            if row["Product"].lower() == product_name.lower():
                return f"✔ The price of {product_name} is ₹{row['Price']} per litre."

        return "❌ Product not found in Google Sheet."

    except Exception as e:
        print("❌ Error reading Google Sheet:", e)
        return "⚠ Could not fetch product prices right now."


# ---------------------------------
# AI Reply Function
# ---------------------------------
def get_ai_reply(user_input):
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
                    "You are an AI assistant for an oil business. "
                    "Help customers check oil prices from Google Sheet "
                    "and assist with orders politely."
                ),
            },
            {"role": "user", "content": user_input},
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        result = response.json()

        if "choices" in result:
            return result["choices"][0]["message"]["content"].strip()

        if "error" in result:
            return f"⚠ AI error: {result['error'].get('message')}"

        return "⚠ Unexpected AI response."

    except Exception:
        return "⚠ Error connecting to AI server."


# ---------------------------------
# Routes
# ---------------------------------
@app.route("/", methods=["GET"])
def home():
    return "✅ WhatsApp Oil Business Bot is Live!"


@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()

    # Check if asking for price
    if any(x in incoming_msg.lower() for x in ["price", "rate", "cost"]):
        product = incoming_msg.lower()
        product = product.replace("price", "").replace("rate", "").replace("cost", "").strip()
        reply_text = get_product_price(product)
    else:
        reply_text = get_ai_reply(incoming_msg)

    reply = MessagingResponse()
    reply.message(reply_text)
    return str(reply)


# ---------------------------------
# RUN SERVER
# ---------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
