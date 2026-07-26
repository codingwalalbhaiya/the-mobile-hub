import os
from flask import Flask, jsonify, render_template
from flask_cors import CORS  # अगर आप React/Frontend से कनेक्ट कर रहे हैं
import sqlite3

app = Flask(__name__)
CORS(app)  # CORS एरर से बचने के लिए

# 1. Render के लिए डेटाबेस का सही पाथ (Absolute Path) सेट करें
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "products.db")


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "The Mobile Hub Server is running!"}), 200


@app.route("/get-products", methods=["GET"])
def get_products():
    # 2. चेक करें कि डेटाबेस फ़ाइल सर्वर पर मौजूद है या नहीं
    if not os.path.exists(DB_FILE):
        return (
            jsonify(
                {
                    "error": "Database file not found",
                    "details": f"Could not find database file at: {DB_FILE}. Make sure it is pushed to GitHub.",
                }
            ),
            500,
        )

    try:
        # 3. Context Manager ('with') का उपयोग करें ताकि कनेक्शन लीक न हो
        with sqlite3.connect(DB_FILE) as conn:
            # Row factory से डेटा कॉलम के नाम से एक्सेस होगा
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, category, brand, name, price, img, ram, processor, battery FROM products"
            )
            rows = cursor.fetchall()

        # 4. डेटा को JSON फॉर्मेट में बदलें
        products_list = []
        for row in rows:
            products_list.append(
                {
                    "id": str(row["id"]),
                    "category": str(row["category"]),
                    "brand": str(row["brand"]),
                    "name": str(row["name"]),
                    # अगर प्राइस NULL हो, तो क्रैश होने के बजाय 0 दिखेगा
                    "price": f"₹{row['price'] or 0:,}",
                    "img": str(row["img"]),
                    "specs": {
                        "RAM": str(row["ram"]),
                        "Storage": "Included",
                        "Processor": str(row["processor"]),
                        "Battery": str(row["battery"]),
                    },
                }
            )

        return jsonify(products_list), 200

    except sqlite3.OperationalError as db_err:
        # अगर टेबल का नाम गलत है या डेटाबेस लॉक है
        return (
            jsonify(
                {
                    "error": "Database Operational Error",
                    "details": str(db_err),
                    "hint": "Check if the table 'products' exists in your database.",
                }
            ),
            500,
        )

    except Exception as e:
        # बाकी किसी भी अन्य एरर के लिए
        return (
            jsonify({"error": "Internal Server Error", "details": str(e)}),
            500,
        )


if __name__ == "__main__":
    # Render पर पोर्ट डायनामिक होता है, इसलिए os.environ का इस्तेमाल ज़रूरी है
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
