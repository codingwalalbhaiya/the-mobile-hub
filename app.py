from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DB_FILE = "shop.db"


# Cryptographic SHA-256 password hashing helper
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# INITIALIZING SECURE PERSISTENT SCHEMAS WITH AUTH TABLE
# INITIALIZING SECURE PERSISTENT SCHEMAS WITH AUTH TABLE
@app.route("/init-db", methods=["GET"])
def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 1. Admin Authentication Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_auth (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)

        # 2. Products Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL, brand TEXT NOT NULL, name TEXT NOT NULL,
                price INTEGER NOT NULL, img TEXT NOT NULL, ram TEXT NOT NULL,
                processor TEXT NOT NULL, battery TEXT NOT NULL
            )
        """)

        # 3. Orders Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL, price TEXT NOT NULL,
                customer_name TEXT NOT NULL, customer_phone TEXT NOT NULL,
                order_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
   
        conn.commit()
        conn.close() 
        
        
        return jsonify({
            "success": True, 
            "message": "Database tables initialized successfully!"
        }), 200

  
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({
            "success": False, 
            "message": "Database initialization failed", 
            "details": str(e)
        }), 500

    # AUTOMATIC DEFAULT CREDENTIALS: Agar table khali hai toh default login daal do
    cursor.execute("SELECT COUNT(*) FROM admin_auth")
    if cursor.fetchone()[0] == 0:
        # Default Username: admin | Default Password: hub_owner_password
        default_hash = hash_password("123456")
        cursor.execute(
            "INSERT INTO admin_auth (username, password_hash) VALUES (?, ?)",
            ("admin", default_hash),
        )

    conn.commit()
    conn.close()


# 1. LIVE SQL-BASED ADMIN LOGIN CHECK
@app.route("/admin-login", methods=["POST"])
def admin_login():
    data = request.json or {}
    username_input = data.get("user", "").strip()
    password_input = data.get("pass", "").strip()

    hashed_input = hash_password(password_input)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # SQL Parameterization ke sath database se username aur password check karna
    cursor.execute(
        "SELECT password_hash FROM admin_auth WHERE username = ?", (username_input,)
    )
    row = cursor.fetchone()
    conn.close()

    if row and row[0] == hashed_input:
        return (
            jsonify(
                {"status": "authorized", "token": "bearer_session_auth_token_999777"}
            ),
            200,
        )
    else:
        return jsonify({"error": "Access Denied: Invalid Username or Password."}), 401


# 2. DYNAMIC PASSWORD UPDATE ROUTE (SQL UPDATE COMMAND)
@app.route("/change-password", methods=["POST"])
def change_password():
    data = request.json or {}
    token = data.get("token")
    username = data.get("username", "admin").strip()
    new_password = data.get("new_pass", "").strip()

    # Token check for security
    if token != "bearer_session_auth_token_999777":
        return jsonify({"error": "Unauthorized session!"}), 403

    if not new_password:
        return jsonify({"error": "Password cannot be empty!"}), 400

    new_hash = hash_password(new_password)

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Asli SQL UPDATE Query jo database mein store naya password badal degi
        cursor.execute(
            "UPDATE admin_auth SET password_hash = ? WHERE username = ?",
            (new_hash, username),
        )
        conn.commit()
        conn.close()
        return (
            jsonify({"!"}),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# BAAKI SARE ROUTES APKE PHLE SE FIXED HAIN
@app.route("/api/products", methods=["GET"])
def get_products():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, category, brand, name, price, img, ram, processor, battery FROM products"
    )
    rows = cursor.fetchall()
    conn.close()
    products_list = []
    for row in rows:
        products_list.append(
            {
                "id": int(row[0]),
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
            }
        )
    return jsonify(products_list)


@app.route("/api/product", methods=["POST"])
def add_product():
    data = request.json or {}
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (category, brand, name, price, img, ram, processor, battery) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(data.get("category")),
                str(data.get("brand")),
                str(data.get("name")),
                int(data.get("price", 0)),
                str(data.get("img")),
                str(data.get("ram")),
                str(data.get("processor")),
                str(data.get("battery")),
            ),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Product saved successfully."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/order", methods=["POST"])
def add_order():
    data = request.json or {}
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (product_name, price, customer_name, customer_phone) VALUES (?, ?, ?, ?)",
            (
                str(data.get("product_name")),
                str(data.get("price")),
                str(data.get("customer_name")),
                str(data.get("customer_phone")),
            ),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Order successfully recorded."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/sales", methods=["GET"])
def get_sales():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT order_date, product_name, customer_name, customer_phone, price FROM orders ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    sales_list = []
    for row in rows:
        sales_list.append(
            {
                "date": str(row[0]),
                "productName": str(row[1]),
                "customerName": str(row[2]),
                "customerPhone": str(row[3]),
                "price": str(row[4]),
            }
        )
    return jsonify(sales_list)


if __name__ == "__main__":
    init_db()
    # Live cloud server ka dynamic port check karne ke liye:
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
