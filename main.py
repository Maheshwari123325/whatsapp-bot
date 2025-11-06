from flask import Flask, request
from twilio.rest import Client as TwilioClient
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# API keys
openai_key = os.getenv("OPENAI_API_KEY")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_from = os.getenv("TWILIO_FROM")

# Initialize clients
openai_client = OpenAI(api_key=openai_key)
twilio_client = TwilioClient(twilio_sid, twilio_token)

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    
    if not incoming_msg:
        return "No message received", 400

    # Generate AI response
    ai_response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful WhatsApp assistant."},
            {"role": "user", "content": incoming_msg}
        ]
    )
    reply_text = ai_response.choices[0].message.content.strip()

    # Send WhatsApp message via Twilio
    twilio_client.messages.create(
        body=reply_text,
        from_=f"whatsapp:{twilio_from}",
        to=from_number
    )

    return "Message sent successfully", 200

@app.route("/")
def home():
    return "WhatsApp bot is running successfully!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0",port=port)
