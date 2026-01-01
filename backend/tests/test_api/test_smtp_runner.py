#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import smtplib, ssl
from email.message import EmailMessage

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'False') == 'True'
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False') == 'True'
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_TO = os.getenv('MAIL_TEST_TO', MAIL_USERNAME)

print("SMTP config:", MAIL_SERVER, MAIL_PORT, "USE_TLS=", MAIL_USE_TLS, "USE_SSL=", MAIL_USE_SSL)

msg = EmailMessage()
msg["Subject"] = "Mirage SMTP Test"
msg["From"] = MAIL_USERNAME
msg["To"] = MAIL_TO
msg.set_content("This is a test email from Mirage backend.")

try:
    if MAIL_USE_SSL:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT, context=ctx, timeout=15) as s:
            s.set_debuglevel(1)
            s.login(MAIL_USERNAME, MAIL_PASSWORD)
            s.send_message(msg)
    else:
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=15) as s:
            s.set_debuglevel(1)
            if MAIL_USE_TLS:
                s.starttls()
            s.login(MAIL_USERNAME, MAIL_PASSWORD)
            s.send_message(msg)
    print("SMTP send: OK")
except Exception as e:
    print("SMTP send: FAILED ->", type(e).__name__, e)


