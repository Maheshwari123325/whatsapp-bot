
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os

app = Flask(__name__)

# AI function (connects to OpenRouter)
def get_ai_reply(user_input):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/Llama-3-8b-chat",
        "messages": [
            {"role": "system", "content": "You are an AI ordering assistant."},
            {"role": "user", "content": user_input}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=25)
        print("🔹 Status Code:", response.status_code)
        print("🔹 Raw Response:", response.text[:500])
        result = response.json()
        ai_reply = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        return ai_reply.strip() or "⚠ AI returned no reply."
    except Exception as e:
        print("AI Error:", e)
        return "⚠ Problem connecting to AI server."

# ✅ HOME route (for testing)
@app.route("/", methods=["GET"])
def home():
    return "✅ WhatsApp AI Ordering Bot is running successfully!"

# ✅ TWILIO BOT ROUTE
@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")
    print(f"📩 Message from {sender}: {incoming_msg}")

    ai_response = get_ai_reply(incoming_msg)

    reply = MessagingResponse()
    reply.message(ai_response)

    return str(reply)

# ✅ Run locally or via Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
