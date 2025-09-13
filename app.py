from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_to_any_random_string"

DB_PATH = "users.db"

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    email TEXT UNIQUE
                )''')
    conn.commit()
    conn.close()

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()
        if user:
            session["email"] = email
            return redirect(url_for("request_time"))
        else:
            return "Email not registered! Please register first."
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip()
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO users (email) VALUES (?)", (email,))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Email already registered!"
    return render_template("register.html")

@app.route("/request_time", methods=["GET", "POST"])
def request_time():
    if "email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        date = request.form.get("date")
        time = request.form.get("time")
        extra = request.form.get("extra", "No")
        extra_text = request.form.get("extra_text", "")

        send_email_to_all(date, time, extra, extra_text)
        return f"Request sent! Emails dispatched to all registered users."
    return render_template("request_time.html")

@app.route("/logout")
def logout():
    session.pop("email", None)
    return redirect(url_for("login"))

# --- Email Sending (Gmail) ---
SENDER_EMAIL = "cheemaabdullah591@gmail.com"
SENDER_APP_PASSWORD = "duxz eeer rcji kddq"  # Gmail App Password

def send_email_to_all(date, time, extra="No", extra_text=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT email FROM users")
    emails = [row[0] for row in c.fetchall()]
    conn.close()

    subject = "Your VIP time slot has been booked ✨"

    # Convert time to AM/PM format
    try:
        formatted_time = datetime.strptime(time, "%H:%M").strftime("%I:%M %p")
    except ValueError:
        formatted_time = time  # fallback if time is weird

    # Cute/flirty email body
    body = f"""
Hey you 😏

Your VIP time slot has been booked! I promise to behave… maybe 😜

📅 Date: {date}
⏰ Time: {formatted_time}
"""

    if extra == "Yes" and extra_text:
        body += f"\nAnd yes, please bring what I asked for: {extra_text} 💌"

    body += """

Do you accept or accept this time? (You have no choice :)) 💖

______________________________
"""

    for recipient in emails:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
                server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
            print(f"✅ Email sent to {recipient}")
        except Exception as e:
            print(f"❌ Failed to send email to {recipient}: {e}")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
