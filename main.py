import os
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Load your API key from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip()
    response = MessagingResponse()
    msg = response.message()

    # If user sends something
    if incoming_msg:
        ai_response = get_ai_response(incoming_msg)
        msg.body(ai_response)
    else:
        msg.body("Hi! How can I help you today?")
    
    return str(response)

def get_ai_response(prompt):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "meta-llama/llama-3-70b-instruct",  # hosted LLaMA model
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant for a WhatsApp ordering bot."},
                {"role": "user", "content": prompt}
            ]
        }

        res = requests.post(url, headers=headers, json=data)
        res_json = res.json()
        ai_text = res_json["choices"][0]["message"]["content"]
        return ai_text

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
