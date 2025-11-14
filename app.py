from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# ---------------------------------
# GOOGLE SHEET CONFIG
# ---------------------------------
SCOPE = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SHEET_URL = os.getenv("SHEET_URL")   # You MUST set this in Render

SECRET_FILE_PATH = "/etc/secrets/credential.json"


def load_google_sheet():
    """Loads Google Sheet fresh on every request (fixes sheet=None issue)."""
    try:
        if not os.path.exists(SECRET_FILE_PATH):
            print("❌ Credential file missing:", SECRET_FILE_PATH)
            return None

        creds = Credentials.from_service_account_file(
            SECRET_FILE_PATH, scopes=SCOPE
        )

        client = gspread.authorize(creds)
        sheet = client.open_by_url(SHEET_URL).worksheet("Products")

        return sheet

    except Exception as e:
        print("❌ Google Sheet error:", e)
        return None


# ---------------------------------
# Fetch price or menu
# ---------------------------------
def fetch_all_products():
    sheet = load_google_sheet()
    if sheet is None:
        return None

    try:
        return sheet.get_all_records()
    except Exception as e:
        print("❌ Sheet read error:", e)
        return None


def get_product_price(product_name):
    records = fetch_all_products()
    if records is None:
        return "⚠ Could not fetch product prices now. Please try again."

    for row in records:
        if row["Product"].lower() == product_name.lower():
            return f"✔ The price of {product_name} is ₹{row['Price']} per litre."

    return "❌ Product not found in Google Sheet."


def get_menu():
    records = fetch_all_products()
    if records is None:
        return "⚠ Could not fetch product menu now."

    text = "📦 Available Products:\n\n"
    for row in records:
        text += f"- {row['Product']} — ₹{row['Price']}\n"
    return text


def get_all_prices():
    records = fetch_all_products()
    if records is None:
        return "⚠ Could not fetch product prices now."

    text = "💰 Product Prices:\n\n"
    for row in records:
        text += f"- {row['Product']}: ₹{row['Price']}\n"
    return text


# ---------------------------------
# AI Reply
# ---------------------------------
def get_ai_reply(user_input):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "meta-llama/llama-4-maverick:free",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant for an oil business. "
                    "Answer politely and help customers with oil purchases."
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

        return "⚠ Unexpected AI response."

    except Exception:
        return "⚠ AI server error. Please try again."


# ---------------------------------
# Routes
# ---------------------------------
@app.route("/", methods=["GET"])
def home():
    return "✅ WhatsApp Oil Business Bot is Live!"


@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip().lower()

    # PRICE COMMAND
    if "price" in incoming_msg or "rate" in incoming_msg or "cost" in incoming_msg:
        product = incoming_msg.replace("price", "").replace("rate", "").replace("cost", "").strip()
        if product == "":
            return str(MessagingResponse().message(get_all_prices()))
        return str(MessagingResponse().message(get_product_price(product)))

    # MENU COMMAND
    if "menu" in incoming_msg:
        return str(MessagingResponse().message(get_menu()))

    # AI FALLBACK
    ai_reply = get_ai_reply(incoming_msg)
    return str(MessagingResponse().message(ai_reply))


# ---------------------------------
# RUN SERVER
# ---------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
