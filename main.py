from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get('Body', '').strip()
    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg:
        ai_response = client.responses.create(
            model="gpt-3.5-turbo",
            input=f"User said: {incoming_msg}. Reply as a friendly assistant."
        )
        msg.body(ai_response.output_text)
    else:
        msg.body("Hi! Send a message to chat with me 😊")

    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
