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

try:
    print("🔍 Trying to connect to Google Sheet...")
    creds = Credentials.from_service_account_file("credential.json.json", scopes=SCOPE)
    print("✅ Loaded credential file successfully.")
    client = gspread.authorize(creds)
    print("✅ Authorized Google client successfully.")
    sheet = client.open_by_url(SHEET_URL).worksheet("Products")
    print("✅ Connected to 'Products' worksheet successfully.")
except Exception as e:
    print("❌ Google Sheet connection error:", str(e))
    sheet = None


# ---------------------------------
# FUNCTION TO FETCH PRICE FROM SHEET
# ---------------------------------
def get_product_price(product_name):
    if not sheet:
        return "⚠ Could not load product list from Google Sheet."

    try:
        records = sheet.get_all_records()
        for row in records:
            if row["Product"].lower() == product_name.lower():
                return f"The price of {product_name} is ₹{row['Price']} per litre."
        return "Sorry, I couldn’t find that product in the price list."
    except Exception as e:
        print("⚠ Error reading from Google Sheet:", e)
        return "⚠ Could not fetch product prices at the moment."


# ---------------------------------
# AI REPLY FUNCTION
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
                    "Help customers check oil prices, product details, and place polite orders. "
                    "If a user asks for a product price, reply by saying you will check the Google Sheet."
                ),
            },
            {"role": "user", "content": user_input},
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=25)
        print("🔹 Status Code:", response.status_code)
        print("🔹 Raw Response (first 800 chars):", response.text[:800])

        try:
            result = response.json()
        except json.JSONDecodeError:
            return "⚠ AI server returned unreadable response."

        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"].strip()
            elif "text" in choice:
                return choice["text"].strip()

        if "error" in result:
            msg = result["error"].get("message", "Unknown AI error")
            return f"⚠ AI error: {msg}"

        return f"⚠ Unexpected response format: {result}"

    except Exception as e:
        print("AI Error:", e)
        return "⚠ Error connecting to AI server."


# ---------------------------------
# HOME ROUTE
# ---------------------------------
@app.route("/", methods=["GET"])
def home():
    return "✅ WhatsApp Oil Business Bot is live!"


# ---------------------------------
# TWILIO WEBHOOK
# ---------------------------------
@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")
    print(f"📩 Message from {sender}: {incoming_msg}")

    # If user asks for price
    if any(word in incoming_msg.lower() for word in ["price", "cost", "rate"]):
        product_name = incoming_msg.replace("price", "").replace("cost", "").replace("rate", "").strip()
        ai_response = get_product_price(product_name)
    else:
        ai_response = get_ai_reply(incoming_msg)

    print("🤖 AI Reply:", ai_response)

    reply = MessagingResponse()
    reply.message(ai_response)
    return str(reply)


# ---------------------------------
# RUN APP (Render)
# ---------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
