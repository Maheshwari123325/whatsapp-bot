from flask import Flask, request
import requests
import os

app = Flask(__name__)

# 🧠 --- CONFIGURATION ---
# Twilio credentials
TWILIO_WHATSAPP_NUMBER = "whatsapp:‪+14155238886‬"  # Twilio Sandbox number (default)
# Replace with your real number if you’ve upgraded.

# OpenRouter (LLaMA) API key
OPENROUTER_API_KEY = "paste_your_openrouter_api_key_here"

# --- Optional: Your bot’s “personality” ---
SYSTEM_PROMPT = "You are a helpful AI assistant for a WhatsApp ordering bot that helps users view products, check prices, and place orders."

# --- WhatsApp Message Sender (via Twilio REST API) ---
def send_whatsapp_message(to, message):
    from twilio.rest import Client

    # Twilio credentials (set these in Render or local environment)
    ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "paste_your_sid_here")
    AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "paste_your_auth_token_here")
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        body=message,
        to=to
    )

# --- LLaMA AI Function (OpenRouter API) ---
def ask_llama(user_message):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "meta-llama/llama-3-8b-instruct",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        }

        response = requests.post(url, headers=headers, json=data)
        response_json = response.json()

        # ✅ Handle both success and error cases
        if "choices" in response_json:
            reply = response_json["choices"][0]["message"]["content"]
        else:
            print("Error from API:", response_json)
            reply = "Sorry, I couldn't process that right now. Please try again."

        return reply.strip()

    except Exception as e:
        print("Exception:", e)
        return "An error occurred while contacting the AI service."

# --- WhatsApp Webhook ---
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        incoming_msg = request.values.get("Body", "").strip()
        from_number = request.values.get("From", "")

        if not incoming_msg:
            return "No message received", 400

        print(f"Incoming message: {incoming_msg} from {from_number}")

        # Get AI-generated response
        ai_reply = ask_llama(incoming_msg)

        # Send back to user via WhatsApp
        send_whatsapp_message(from_number, ai_reply)

        return "OK", 200

    except Exception as e:
        print("Webhook error:", e)
        return "Internal Server Error", 500


# --- Run Flask App ---
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
