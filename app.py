from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import joblib
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "loan_approval_secret_key"

# Load ML Model
model = joblib.load("models/model.pkl")


# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# HOME PAGE
# -----------------------------
@app.route("/")
def home():
    return redirect(url_for("login"))


# -----------------------------
# REGISTER
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:
            return render_template(
                "register.html",
                message="Passwords do not match!"
            )

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE username=? OR email=?",
            (username, email)
        ).fetchone()

        if user:

            conn.close()

            return render_template(
                "register.html",
                message="Username or Email already exists!"
            )

        hashed = generate_password_hash(password)

        conn.execute("""
        INSERT INTO users
        (fullname,email,username,password)
        VALUES(?,?,?,?)
        """,
        (
            fullname,
            email,
            username,
            hashed
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# -----------------------------
# LOGIN
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["username"] = username

            return redirect(url_for("dashboard"))

        else:

            return render_template(
                "login.html",
                error="Invalid Username or Password"
            )

    return render_template("login.html")
    # -----------------------------
# DASHBOARD
# -----------------------------
@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    total = conn.execute(
        "SELECT COUNT(*) FROM predictions WHERE username=?",
        (session["username"],)
    ).fetchone()[0]

    approved = conn.execute(
        """
        SELECT COUNT(*) FROM predictions
        WHERE username=? AND prediction=?
        """,
        (session["username"], "Loan Approved ✅")
    ).fetchone()[0]

    rejected = conn.execute(
        """
        SELECT COUNT(*) FROM predictions
        WHERE username=? AND prediction=?
        """,
        (session["username"], "Loan Rejected ❌")
    ).fetchone()[0]

    recent = conn.execute("""
        SELECT *
        FROM predictions
        WHERE username=?
        ORDER BY id DESC
        LIMIT 5
    """, (session["username"],)).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        total=total,
        approved=approved,
        rejected=rejected,
        recent=recent
    )


# -----------------------------
# LOAN PREDICTION
# -----------------------------
@app.route("/predict", methods=["GET", "POST"])
def predict():

    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        gender = int(request.form["gender"])
        married = int(request.form["married"])
        applicant_income = float(request.form["applicant_income"])
        coapplicant_income = float(request.form["coapplicant_income"])
        loan_amount = float(request.form["loan_amount"])
        credit_history = float(request.form["credit_history"])

        data = np.array([[
            gender,
            married,
            applicant_income,
            coapplicant_income,
            loan_amount,
            credit_history
        ]])

        prediction = model.predict(data)

        if prediction[0] == 1:
            result = "Loan Approved ✅"
        else:
            result = "Loan Rejected ❌"

        conn = get_db_connection()

        conn.execute("""
        INSERT INTO predictions
        (
            username,
            gender,
            married,
            applicant_income,
            coapplicant_income,
            loan_amount,
            credit_history,
            prediction
        )
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            session["username"],
            str(gender),
            str(married),
            applicant_income,
            coapplicant_income,
            loan_amount,
            int(credit_history),
            result
        ))

        conn.commit()
        conn.close()

        return render_template(
            "result.html",
            result=result
        )

    return render_template("predict.html")


# -----------------------------
# HISTORY
# -----------------------------
@app.route("/history")
def history():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    predictions = conn.execute(
        """
        SELECT *
        FROM predictions
        WHERE username=?
        ORDER BY id DESC
        """,
        (session["username"],)
    ).fetchall()

    conn.close()

    return render_template(
        "history.html",
        predictions=predictions
    )

# -----------------------------
# PROFILE
# -----------------------------
@app.route("/profile")
def profile():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE username=?",
        (session["username"],)
    ).fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )
# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)