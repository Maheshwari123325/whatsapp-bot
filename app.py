from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    msg = request.form.get('Body').strip().lower()
    resp = MessagingResponse()

    if msg == "hi":
        resp.message("Hello 👋! I am your WhatsApp bot.\nType 'price' to get the price list.")
    elif msg == "price":
        resp.message("🛍 Product Prices:\nSunflower Oil 1L - ₹150\nSunflower Oil 5L - ₹700\nGroundnut Oil 1L - ₹180\nGroundnut Oil 5L - ₹850")
    else:
        resp.message("Sorry, I didn’t understand that. Type 'hi' or 'price'.")
    return str(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
