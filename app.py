import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
# CORS को पूरी तरह खोलें ताकि आपका फ्रंटएंड बिना किसी रुकावट के कनेक्ट हो सके
CORS(app, resources={r"/*": {"origins": "*"}})

# Render के लिए डेटाबेस का सही रास्ता (Absolute Path)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "products.db")

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "The Mobile Hub Server is running!"}), 200

# 1. डेटाबेस इनिशियलाइज़ करने का रूट
@app.route("/init-db", methods=["GET"])
def init_db():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            
            # प्रोडक्ट्स टेबल बनाना
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    name TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    img TEXT,
                    ram TEXT,
                    processor TEXT,
                    battery TEXT
                )
                """
            )
            
            # ऑर्डर्स टेबल बनाना (यह आपके पुराने कोड में मिसिंग था)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    price TEXT NOT NULL,
                    customer_name TEXT NOT NULL,
                    customer_phone TEXT NOT NULL,
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            
            cursor.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    """
                    INSERT INTO products (category, brand, name, price, img, ram, processor, battery)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    # कैटेगरी को "phone" किया ताकि आपके फ्रंटएंड के डिफ़ॉल्ट currentCategory = 'phone' से मैच हो सके
                    ("phone", "Apple", "iPhone 15 Pro", 129900, "https://unsplash.com", "8GB", "A17 Pro", "3274mAh"),
                )
                conn.commit()
                message = "Database initialized, products and orders tables created with sample data!"
            else:
                message = "Database already exists and has data."
        return jsonify({"success": True, "message": message}), 200
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to initialize DB", "details": str(e)}), 500

# 2. प्रोडक्ट्स गेट करने का रूट
@app.route("/api/products", methods=["GET"])
def get_products():
    if not os.path.exists(DB_FILE):
        return jsonify({"error": "Database file not found", "hint": "Please visit /init-db first to create the database."}), 404
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, category, brand, name, price, img, ram, processor, battery FROM products")
            rows = cursor.fetchall()
        
        products_list = []
        for row in rows:
            products_list.append({
                "id": str(row["id"]),
                "category": str(row["category"]),
                "brand": str(row["brand"]),
                "name": str(row["name"]),
                "price": f"₹{row['price'] or 0:,}",
                "img": str(row["img"]),
                "specs": {
                    "RAM": str(row["ram"]), 
                    "Storage": "Included", 
                    "Processor": str(row["processor"]), 
                    "Battery": str(row["battery"])
                }
            })
        return jsonify(products_list), 200
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

# 3. ऑर्डर सेव करने का नया रूट (जो फ्रंटएंड के 'makeSale' फंक्शन के लिए ज़रूरी है)
@app.route("/add-order", methods=["POST"])
def add_order():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        product_name = data.get("product_name")
        price = data.get("price")
        customer_name = data.get("customer_name")
        customer_phone = data.get("customer_phone")
        
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO orders (product_name, price, customer_name, customer_phone)
                VALUES (?, ?, ?, ?)
                """,
                (product_name, price, customer_name, customer_phone)
            )
            conn.commit()
            
        return jsonify({"success": True, "message": "Order saved successfully!"}), 200
    except Exception as e:
        return jsonify({"error": "Failed to save order", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
