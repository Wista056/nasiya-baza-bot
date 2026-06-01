import sqlite3

DB_PATH = "nasiya_bot.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Пользователи
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            company TEXT,
            status TEXT DEFAULT 'pending',
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Чёрный список (расширенный)
    c.execute("""
        CREATE TABLE IF NOT EXISTS blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            birth_date TEXT,
            passport_number TEXT,
            pinfl TEXT,
            address TEXT,
            phone TEXT,
            reason TEXT,
            added_by_telegram_id INTEGER NOT NULL,
            added_by_name TEXT,
            added_by_company TEXT,
            added_by_phone TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # База товаров в рассрочку (расширенная)
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number TEXT NOT NULL UNIQUE,
            product_name TEXT NOT NULL,
            buyer_name TEXT NOT NULL,
            buyer_phone TEXT NOT NULL,
            buyer_passport TEXT,
            buyer_pinfl TEXT,
            buyer_birth_date TEXT,
            buyer_address TEXT,
            total_amount REAL DEFAULT 0,
            paid_amount REAL DEFAULT 0,
            notes TEXT,
            added_by_telegram_id INTEGER NOT NULL,
            added_by_name TEXT,
            added_by_company TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ───────── USERS ─────────

def add_user(telegram_id, full_name, phone, company=""):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO users (telegram_id, full_name, phone, company) VALUES (?,?,?,?)",
            (telegram_id, full_name, phone, company)
        )
        conn.commit()
    finally:
        conn.close()


def get_user(telegram_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
    conn.close()
    return row


def get_pending_users():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM users WHERE status='pending'").fetchall()
    conn.close()
    return rows


def update_user_status(telegram_id, status):
    conn = get_conn()
    conn.execute("UPDATE users SET status=? WHERE telegram_id=?", (status, telegram_id))
    conn.commit()
    conn.close()


# ───────── BLACKLIST ─────────

def add_to_blacklist(full_name, phone, reason, added_by_telegram_id,
                     birth_date="", passport_number="", pinfl="", address="",
                     added_by_name="", added_by_company="", added_by_phone=""):
    conn = get_conn()
    conn.execute("""
        INSERT INTO blacklist
        (full_name, birth_date, passport_number, pinfl, address, phone, reason,
         added_by_telegram_id, added_by_name, added_by_company, added_by_phone)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (full_name, birth_date, passport_number, pinfl, address, phone, reason,
          added_by_telegram_id, added_by_name, added_by_company, added_by_phone))
    conn.commit()
    conn.close()


def search_blacklist(query):
    conn = get_conn()
    q = f"%{query}%"
    rows = conn.execute("""
        SELECT * FROM blacklist
        WHERE full_name LIKE ? OR phone LIKE ? OR passport_number LIKE ? OR pinfl LIKE ?
    """, (q, q, q, q)).fetchall()
    conn.close()
    return rows


# ───────── PRODUCTS ─────────

def add_product(serial_number, product_name, buyer_name, buyer_phone,
                total_amount, paid_amount, notes, added_by_telegram_id,
                buyer_passport="", buyer_pinfl="", buyer_birth_date="", buyer_address="",
                added_by_name="", added_by_company=""):
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO products
            (serial_number, product_name, buyer_name, buyer_phone,
             buyer_passport, buyer_pinfl, buyer_birth_date, buyer_address,
             total_amount, paid_amount, notes,
             added_by_telegram_id, added_by_name, added_by_company)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (serial_number, product_name, buyer_name, buyer_phone,
              buyer_passport, buyer_pinfl, buyer_birth_date, buyer_address,
              total_amount, paid_amount, notes,
              added_by_telegram_id, added_by_name, added_by_company))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def search_product(serial_number):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM products WHERE serial_number=?", (serial_number,)
    ).fetchone()
    conn.close()
    return row
