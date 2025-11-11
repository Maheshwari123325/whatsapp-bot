from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os

app = Flask(__name__)

# --- AI FUNCTION (OpenRouter / Meta LLaMA-3-8B-Chat) ---
def get_ai_reply(user_input):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/Llama-3-8b-chat",
        "messages": [
            {"role": "system", "content": "You are an AI ordering assistant that helps users order products, check prices, and get details politely."},
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=25)
        print("🔹 Status Code:", response.status_code)
        print("🔹 Raw Response:", response.text[:600])  # Log only the first 600 chars

        # Convert to JSON
        result = response.json()

        # --- Safe parsing (handles both 'message' and 'text' formats) ---
        ai_reply = ""
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                ai_reply = choice["message"]["content"]
            elif "text" in choice:
                ai_reply = choice["text"]

        if not ai_reply:
            return "⚠ The AI did not return a valid response."

        return ai_reply.strip()

    except Exception as e:
        print("AI Error:", e)
        return "⚠ Error connecting to AI server."

# --- HOME ROUTE (for testing on browser) ---
@app.route("/", methods=["GET"])
def home():
    return "✅ WhatsApp AI Ordering Bot is running successfully!"

# --- TWILIO WEBHOOK ROUTE ---
@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")
    print(f"📩 Message from {sender}: {incoming_msg}")

    ai_response = get_ai_reply(incoming_msg)

    reply = MessagingResponse()
    reply.message(ai_response)
    return str(reply)

# --- RUN APP (for Render deployment) ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
