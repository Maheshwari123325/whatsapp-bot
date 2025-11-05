from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import os

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client (Render automatically loads env vars)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    resp = MessagingResponse()
    msg = resp.message()

    if not incoming_msg:
        msg.body("Hi 👋! Send me a message to start chatting 😊")
        return str(resp)

    try:
        # Generate AI reply with safe prompt and basic fallback
        ai_response = client.responses.create(
            model="gpt-4o-mini",  # faster & cheaper than gpt-4.1-mini
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a friendly, helpful WhatsApp assistant. "
                        "Keep replies short (under 100 words) and safe. "
                        "Never ask for personal details or payment info."
                    )
                },
                {"role": "user", "content": incoming_msg}
            ],
            max_output_tokens=200
        )

        # Extract model text output safely
        reply = ai_response.output[0].content[0].text.strip()
        msg.body(reply)

    except Exception as e:
        # Simple fallback for OpenAI/Twilio errors
        print("Error:", e)
        msg.body("Sorry 😔, something went wrong. Please try again later.")

    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
