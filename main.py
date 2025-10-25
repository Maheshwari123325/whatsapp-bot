from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()
    msg = resp.message()

    if 'hi' in incoming_msg:
        msg.body("Hello! 👋 Welcome to Oil Store. Type 'menu' to see products.")
    elif 'menu' in incoming_msg:
        msg.body("🛍 Product Prices:\nSFO-1L - ₹150\nSFO-5L - ₹700\nGNO-1L - ₹180\nGNO-5L - ₹850")
    elif 'order' in incoming_msg:
        msg.body("✅ Your order has been received! Thank you.")
    else:
        msg.body("Sorry, I didn’t understand. Type 'menu' to see options.")

    # VERY IMPORTANT
    return str(resp)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
