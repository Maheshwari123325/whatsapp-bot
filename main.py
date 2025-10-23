from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(_name_)

@app.route('/')
def home():
    return "WhatsApp Bot is running!"

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()
    msg = resp.message()

    if 'hi' in incoming_msg:
        msg.body("Hello! 👋 I'm your WhatsApp ordering bot. How can I help you today?")
    else:
        msg.body("Please say 'hi' to start chatting!")

    return str(resp)

if __name__ == '__main__':
    app.run()
