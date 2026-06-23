import sqlite3

# Connect to database
conn = sqlite3.connect("database.db")

cursor = conn.cursor()

# Create Users Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    fullname TEXT NOT NULL,

    email TEXT UNIQUE NOT NULL,

    username TEXT UNIQUE NOT NULL,

    password TEXT NOT NULL

)
""")

# Create Predictions Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS predictions(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT NOT NULL,

    gender TEXT,

    married TEXT,

    applicant_income REAL,

    coapplicant_income REAL,

    loan_amount REAL,

    credit_history INTEGER,

    prediction TEXT

)
""")

conn.commit()

conn.close()

print("Database Created Successfully!")