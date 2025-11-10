from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask
app = Flask(__name__)

# Load credentials from environment
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize Twilio client
client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    print("⚠ Warning: Twilio credentials not found in environment variables.")

# Function to get AI reply from OpenRouter (LLaMA)
def get_ai_reply(user_input):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/Llama-3-8b-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant for a WhatsApp ordering bot. Help users order products easily."},
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        result = response.json()
        print("AI response:", result)
        # Safely extract the AI reply
        return result.get("choices", [{}])[0].get("message", {}).get("content", "Sorry, I didn’t understand that.")
    except Exception as e:
        print(f"AI Error: {e}")
        return "There was a problem connecting to the AI server."

# WhatsApp route
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body", "").strip()
    from_number = request.form.get("From", "")
    print(f"📩 Incoming message: {incoming_msg} from {from_number}")

    # Create Twilio MessagingResponse
    resp = MessagingResponse()

    if not incoming_msg:
        resp.message("Please send a valid message.")
        return str(resp)

    # Get AI response
    ai_reply = get_ai_reply(incoming_msg)
    print(f"🤖 AI Reply: {ai_reply}")

    # Send back reply
    msg = resp.message(ai_reply)
    return str(resp)

@app.route("/", methods=["GET"])
def home():
    return "✅ Flask WhatsApp Ordering Bot with LLaMA is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
