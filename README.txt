# Tracker App (Instagram Style + Email Alerts + Analytics)

## Features
- Logs visitor IP, location, device info
- Captures optional name and email
- Sends email alerts with visitor details
- Animates and mimics Instagram login layout
- Responsive on desktop and mobile

## How to Use

### 1. Unzip and Install
```
pip install -r requirements.txt
```

### 2. Configure Email
Edit `app.py` and set:
- EMAIL_SENDER
- EMAIL_PASSWORD (use App Password for Gmail)
- EMAIL_RECEIVER

### 3. Run the App
```
python app.py
```

### 4. Public Access
Use [ngrok](https://ngrok.com):
```
ngrok http 5000
```

### 5. Logs
Check log.txt or your email for visitor info.

Use responsibly.
