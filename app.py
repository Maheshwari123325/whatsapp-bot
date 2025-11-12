from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests, os, json, gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# ------------------------------
# GOOGLE SHEETS SETUP
# ------------------------------
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SHEET_URL = "https://docs.google.com/spreadsheets/d/1RFdApVA3T-u4rb50DUWycFS0uO-b5ARWVI51IaT7Mh8/edit?gid=0#gid=0"

# Load credentials from JSON file
creds = Credentials.from_service_account_file("credential.json.json",scopes=SCOPE)
client = gspread.authorize(creds)
sheet = client.open_by_url(SHEET_URL).worksheet("Products")

# ------------------------------
#  AI REPLY FUNCTION
# ------------------------------
def get_ai_reply(user_input):
    # Basic keyword detection
    products = sheet.get_all_records()
    user_input_lower = user_input.lower()

    for row in products:
        name = row["item_name"].lower()
        price = row["price"]
        if name in user_input_lower:
            return f"The price of {row['item_name']} is ₹{price}."

    # Default fallback to AI for general replies
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/llama-4-maverick:free",
        "messages": [
            {"role": "system", "content": "You are an AI oil ordering assistant. Help users find oil prices, and handle polite chat."},
            {"role": "user", "content": user_input}
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=25)
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"].strip()
        else:
            return "Sorry, I couldn’t get a valid reply from AI."
    except Exception as e:
        return f"⚠ Error contacting AI: {e}"

# ------------------------------
#  TWILIO WEBHOOK
# ------------------------------
@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")

    print(f"📩 Message from {sender}: {incoming_msg}")

    ai_response = get_ai_reply(incoming_msg)
    print("🤖 Reply:", ai_response)

    reply = MessagingResponse()
    reply.message(ai_response)
    return str(reply)

# ------------------------------
#  ROOT ROUTE
# ------------------------------
@app.route("/", methods=["GET"])
def home():
    return "✅ Oil Business WhatsApp Bot is Live!"

# ------------------------------
#  RUN APP
# ------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
