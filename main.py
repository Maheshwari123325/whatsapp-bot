from flask import Flask, request
import os
from dotenv import load_dotenv
import requests
from twilio.rest import Client

# --- Load .env file ---
load_dotenv()

# --- Get secrets from environment ---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# --- Flask setup ---
app = Flask(__name__)

# --- Initialize Twilio client ---
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    try:
        incoming_msg = request.form.get('Body')
        from_number = request.form.get('From')

        # --- Call AI reply ---
        ai_response = get_ai_reply(incoming_msg)

        # --- Send reply via Twilio ---
        client.messages.create(
            from_='whatsapp:' + TWILIO_PHONE_NUMBER,
            body=ai_response,
            to=from_number
        )

        return "OK", 200
    except Exception as e:
        print(f"Error: {e}")
        return "Error",500

def get_ai_reply(user_input):
    """Send the user's message to the OpenRouter LLaMA API"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/Llama-3-8b-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant for a WhatsApp ordering bot."},
            {"role": "user", "content": user_input}
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    # Extract AI text
    return result["choices"][0]["message"]["content"]

if __name__ == '__main__':
    app.run(port=5000,debug=True)
