from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import os

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client (Render automatically loads environment variables)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg:
        # Generate AI reply
        ai_response = client.responses.create(
            model="gpt-4.1-mini",  # or "gpt-4.1" if available
            input=f"User said: {incoming_msg}. Reply helpfully as a friendly chatbot."
        )
        reply = ai_response.output[0].content[0].text
        msg.body(reply)
    else:
        msg.body("Hi 👋! Send me a message to start chatting 😊")

    return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
