from flask import Flask, request
from twilio.rest import Client as TwilioClient
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# API keys (loaded from Render environment variables)
openai.api_key = os.getenv("OPENAI_API_KEY")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_from = os.getenv("TWILIO_FROM")

# Initialize Twilio client
twilio_client = TwilioClient(twilio_sid, twilio_token)

@app.route("/bot", methods=["POST"])
def bot():
    """Main WhatsApp bot endpoint."""
    incoming_msg = request.values.get("Body", "").strip()
    from_number = request.values.get("From", "")

    if not incoming_msg:
        return "No message received", 400

    try:
        # Generate AI response using OpenAI (old API syntax for 0.28.0)
        ai_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": (
                    "You are OilWhatsAppBot, a polite and professional assistant for an edible oil business. "
                    "Answer customer questions, share prices, and help them place orders clearly and formally."
                )},
                {"role": "user", "content": incoming_msg}
            ]
        )
        reply_text = ai_response.choices[0].message["content"].strip()

        # Send reply back via WhatsApp using Twilio
        twilio_client.messages.create(
            body=reply_text,
            from_=f"whatsapp:{twilio_from}",
            to=from_number
        )

        return "Message sent successfully", 200

    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}", 500


@app.route("/")
def home():
    return "OilWhatsAppBot is running successfully!"


if _name_ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
