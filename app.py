from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
import json

app = Flask(__name__)

# ------------------------------
#  AI REPLY FUNCTION (Oil Bot)
# ------------------------------
def get_ai_reply(user_input):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/llama-4-maverick:free",  # ✅ Valid free model
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are OilBusinessBot, an AI ordering assistant for an edible oil business. "
                    "Your goal is to help customers browse oil types, check prices, and place polite orders. "
                    "Keep your responses short, friendly, and professional. "
                    "Do not mention food, restaurants, or dishes. "
                    "Available products are: Sunflower Oil, Groundnut Oil, Palm Oil, and Coconut Oil. "
                    "Each product is sold in 1L, 5L, and 15L packs. "
                    "Use ₹ symbol for prices."
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

# ------------------------------
#  HOME ROUTE
# ------------------------------
@app.route("/", methods=["GET"])
def home():
    return "✅ OilBusinessBot is live!"

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
