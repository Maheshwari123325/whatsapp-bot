from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
import json

app = Flask(__name__)

# ------------------------------
#  AI REPLY FUNCTION
# ------------------------------
def get_ai_reply(user_input):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/Llama-3-8b-chat",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI ordering assistant. "
                    "Help users browse products, check prices, and place polite orders."
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

        # Handle normal OpenRouter JSON formats
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"].strip()
            elif "text" in choice:
                return choice["text"].strip()

        # Handle API errors
        if "error" in result:
            msg = result["error"].get("message", "Unknown AI error")
            return f"⚠ AI error: {msg}"

        # Otherwise, print raw for debugging
        return f"⚠ Unexpected response format: {result}"

    except Exception as e:
        print("AI Error:", e)
        return "⚠ Error connecting to AI server."

# ------------------------------
#  HOME ROUTE (for Render test)
# ------------------------------
@app.route("/", methods=["GET"])
def home():
    return "✅ WhatsApp AI Ordering Bot is live!"

# ------------------------------
#  TWILIO WEBHOOK
# ------------------------------
@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")
    print(f"📩 Message from {sender}: {incoming_msg}")

    ai_response = get_ai_reply(incoming_msg)
    print("🤖 AI Reply:", ai_response)

    reply = MessagingResponse()
    reply.message(ai_response)
    return str(reply)

# ------------------------------
#  RUN APP (for Render)
# ------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
