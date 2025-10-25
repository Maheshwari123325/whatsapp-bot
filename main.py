from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route('/')
def home():
    return "WhatsApp Bot is running!"

@app.route('/bot', methods=['POST'])
def bot():
    msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()
    reply = resp.message()

    if 'hi' in msg:
        reply.body("Hello 👋! I'm your WhatsApp ordering bot. How can I help you today?")
    elif 'price' in msg:
        reply.body("🛍 Product Prices:\n"
                   "Sunflower Oil 1L - ₹150\n"
                   "Sunflower Oil 5L - ₹700\n"
                   "Groundnut Oil 1L - ₹180\n"
                   "Groundnut Oil 5L - ₹850")
    else:
        reply.body("Please say 'hi' or 'price' to start chatting!")

    return str(resp)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)
