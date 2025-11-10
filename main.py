# --- Import required libraries ---
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
import requests
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# --- Flask app setup ---
app = Flask(__name__)

# --- Check if keys loaded ---
print("✅ Checking environment variables...")
print("Twilio SID found:", bool(TWILIO_ACCOUNT_SID))
print("OpenRouter key found:", bool(OPENROUTER_API_KEY))

# --- AI function using OpenRouter (LLaMA model) ---
def get_ai_reply(user_input):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/Llama-3-8b-chat",
        "messages": [
            {"role": "system", "content": "You are an AI assistant for a WhatsApp ordering bot. Respond naturally and helpfully."},
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        print("🔹 Status:", response.status_code)
        print("🔹 Raw response:", response.text[:500])  # show first 500 chars

        if response.status_code == 401:
            return "⚠ Invalid or missing OpenRouter API key. Please check your Render environment variables."

        result = response.json()
        ai_reply = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not ai_reply:
            return "⚠ AI returned no reply. Try again."
        return ai_reply.strip()

    except Exception as e:
        print("AI Error:", e)
        return "There was an issue contacting the AI server."

# --- WhatsApp route ---
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")
    print(f"📩 New message from {sender}: {incoming_msg}")

    resp = MessagingResponse()
    msg = resp.message()

    if not incoming_msg:
        msg.body("Please send a message to start chatting 😊")
    else:
        reply = get_ai_reply(incoming_msg)
        msg.body(reply)

    return str(resp)

# --- Health check route ---
@app.route("/", methods=["GET"])
def index():
    return "✅ WhatsApp AI Bot is running!"

# --- Run the app locally or on Render ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
