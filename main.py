from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os

# -----------------------------------
# ⿡ Initialize Flask App
# -----------------------------------
app = Flask(__name__)

# Load your OpenRouter API key from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# -----------------------------------
# ⿢ Function: Get AI reply from OpenRouter (Llama 3 8B Chat)
# -----------------------------------
def get_ai_reply(user_input):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/Llama-3-8b-chat",
        "messages": [
            {"role": "system", "content": "You are an AI ordering assistant that helps customers order products via WhatsApp."},
            {"role": "user", "content": user_input}
        ]
    }

    try:
        # Send request to OpenRouter
        response = requests.post(url, headers=headers, json=data, timeout=25)
        print("🔹 Status Code:", response.status_code)
        print("🔹 Raw Response:", response.text[:500])  # short preview

        # Handle missing/invalid key
        if response.status_code == 401:
            return "⚠ Invalid OpenRouter API key. Please check your Render environment variable."

        result = response.json()
        choices = result.get("choices")
        if not choices:
            return f"⚠ No choices field in AI response: {result}"

        ai_reply = choices[0].get("message", {}).get("content")
        if not ai_reply:
            return f"⚠ AI returned no text. Raw: {result}"
        return ai_reply.strip()

    except Exception as e:
        print("AI Error:", e)
        return "⚠ Connection problem with AI server."

# -----------------------------------
# ⿣ Flask route: Homepage (for testing)
# -----------------------------------
@app.route("/")
def home():
    return "✅ WhatsApp AI Ordering Bot is running successfully!"

# -----------------------------------
# ⿤ Flask route: WhatsApp Bot Webhook (Twilio → Flask)
# -----------------------------------
@app.route("/bot", methods=["POST"])
def bot():
    # Get message from WhatsApp
    incoming_msg = request.values.get("Body", "").strip()
    print("📩 User message:", incoming_msg)

    # Create Twilio reply object
    resp = MessagingResponse()

    if not incoming_msg:
        reply = "⚠ Please type something to start your order."
    else:
        # Get AI reply from OpenRouter
        reply = get_ai_reply(incoming_msg)

    # Send reply back to WhatsApp
    msg = resp.message(reply)
    return str(resp)

# -----------------------------------
# ⿥ Run Flask app (for local development)
# -----------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
