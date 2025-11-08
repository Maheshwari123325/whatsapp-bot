from flask import Flask, request
from twilio.rest import Client as TwilioClient
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# API keys and credentials
openai_key = os.getenv("OPENAI_API_KEY")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_from = os.getenv("TWILIO_FROM")

# Initialize clients
client = OpenAI(api_key=openai_key)
twilio_client = TwilioClient(twilio_sid, twilio_token)

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    from_number = request.values.get("From", "")

    if not incoming_msg:
        return "No message received", 400

    try:
        # Generate AI response with a business tone
        ai_response = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                f"You are OilWhatsAppBot, a formal and professional assistant for an edible oil business. "
                f"Respond politely, concisely, and clearly.\n\n"
                f"Customer said: {incoming_msg}"
            )
        )

        reply_text = ai_response.output[0].content[0].text

        # Send WhatsApp reply via Twilio
        twilio_client.messages.create(
            body=reply_text,
            from_=f"whatsapp:{twilio_from}",
            to=from_number
        )

        return "Message sent successfully", 200

    except Exception as e:
        print("Error:", str(e))
        return f"Error: {str(e)}", 500

@app.route("/")
def home():
    return "✅ OilWhatsAppBot is running successfully!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0",port=port)
