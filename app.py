from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DB_FILE = "shop.db"

@app.route("/")
def home():
    return "BACKEND IS LIVE"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_auth (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, brand TEXT NOT NULL, 
            name TEXT NOT NULL, price INTEGER NOT NULL, img TEXT NOT NULL, ram TEXT NOT NULL, 
            processor TEXT NOT NULL, battery TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT NOT NULL, price TEXT NOT NULL,
            customer_name TEXT NOT NULL, customer_phone TEXT NOT NULL, order_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM admin_auth")
    if cursor.fetchone()[0] == 0:
        default_hash = hash_password("123456")
        cursor.execute("INSERT INTO admin_auth (username, password_hash) VALUES (?, ?)", ("admin", default_hash))
    conn.commit()
    conn.close()

@app.route("/admin-login", methods=["POST"])
def admin_login():
    data = request.json or {}
    username_input = data.get("user", "").strip()
    password_input = data.get("pass", "").strip()
    hashed_input = hash_password(password_input)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM admin_auth WHERE username = ?", (username_input,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0] == hashed_input:
        return jsonify({"status": "authorized", "token": "bearer_session_auth_token_999777"}), 200
    else:
        return jsonify({"error": "Access Denied: Invalid Username or Password."}), 401

@app.route("/get-products", methods=["GET"])
def get_products():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, category, brand, name, price, img, ram, processor, battery FROM products")
        rows = cursor.fetchall()
        conn.close()
        
        products_list = []
        for row in rows:
            # FIXED: Added safe explicitly extracted indices row[0], row[1] etc.
            products_list.append({
                "id": str(row[0]),
                "category": str(row[1]),
                "brand": str(row[2]),
                "name": str(row[3]),
                "price": f"₹{row[4]:,}",
                "img": str(row[5]),
                "specs": {
                    "RAM": str(row[6]),
                    "Storage": "Included",
                    "Processor": str(row[7]),
                    "Battery": str(row[8]),
                },
            })
        return jsonify(products_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/add-product", methods=["POST"])
def add_product():
    data = request.json or {}
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (category, brand, name, price, img, ram, processor, battery) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(data.get("category", "phone")), str(data.get("brand", "")), str(data.get("name", "")),
                int(data.get("price", 0)), str(data.get("img", "")), str(data.get("ram", "")),
                str(data.get("processor", "")), str(data.get("battery", ""))
            ),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Product saved successfully."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/add-order", methods=["POST"])
def add_order():
    data = request.json or {}
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (product_name, price, customer_name, customer_phone) VALUES (?, ?, ?, ?)",
            (str(data.get("product_name")), str(data.get("price")), str(data.get("customer_name")), str(data.get("customer_phone"))),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Order successfully recorded."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/get-sales", methods=["GET"])
def get_sales():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT order_date, product_name, customer_name, customer_phone, price FROM orders ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        
        sales_list = []
        for row in rows:
            sales_list.append({
                "date": str(row[0]), "productName": str(row[1]), "customerName": str(row[2]),
                "customerPhone": str(row[3]), "price": str(row[4])
            })
        return jsonify(sales_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
def get_db_connection():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/init-db')
def init_db():
    db = get_db_connection()
    db.execute('''CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY,nametTEXT,price REAL,image TEXT)''')
    db.commit()
    db.close()
    return "Database Initializee"

#@app.route('/api/products',methods=['GET'])
#def get_products():
   # conn = get_db_connection()
    #products = conn.execute('SELECT * FROM products').fetchall()
    #conn.close()
    #return jsonify([dict(row) for row in products])


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
