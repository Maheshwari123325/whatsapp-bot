from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Connect Google Sheet
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

sheet = client.open("OIL BUSINESS BOT")
products_sheet = sheet.worksheet("Products")
orders_sheet = sheet.worksheet("Orders")

@app.route("/message", methods=["POST"])
def reply_whatsapp():
    msg = request.form.get("Body").strip().lower()
    resp = MessagingResponse()
    reply = resp.message()

    if msg == "hi":
        reply.body("Hello 👋! I'm your WhatsApp ordering bot. How can I help you today?\n\nType:\n- 'price' to see items\n- 'order <item_id> <quantity>' to place order\n- 'menu' to see this menu again.")
        return str(resp)

    elif msg == "menu":
        reply.body("📋 Menu:\n- 'price' to view prices\n- 'order <item_id> <quantity>' to place order")
        return str(resp)

    elif msg == "price":
        data = products_sheet.get_all_records()
        price_list = "🛍 Product Prices:\n"
        for row in data:
            price_list += f"{row['item_name']} - ₹{row['price']}\n"
        reply.body(price_list)
        return str(resp)

    elif msg.startswith("order"):
        parts = msg.split()
        if len(parts) != 3:
            reply.body("⚠ Please use correct format:\norder <item_id> <quantity>")
            return str(resp)

        _, item_id, quantity = parts
        data = products_sheet.get_all_records()

        item = next((row for row in data if row["item_id"].lower() == item_id.lower()), None)
        if not item:
            reply.body("❌ Invalid item_id. Type 'price' to check available IDs.")
            return str(resp)

        total = int(quantity) * int(item["price"])
        orders_sheet.append_row([item_id, item["item_name"], quantity, item["price"], total])

        reply.body(f"✅ Order placed!\n\nItem: {item['item_name']}\nQuantity: {quantity}\nTotal: ₹{total}")
        return str(resp)

    else:
        reply.body("🤖 Sorry, I didn’t understand that.\nType 'menu' for help.")
        return str(resp)

if __name__ == "_main_":
    app.run()
