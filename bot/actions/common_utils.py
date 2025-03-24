from langdetect import detect_langs
import smtplib
import random
import os
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from actions.calendar_utils import get_unix_minutes
from datetime import datetime
import logging
logger = logging.getLogger(__name__)
def detect_language(text):
    # Detect languages and their confidence scores

    # Initialize confidence for English and German
    try:
        languages = detect_langs(text)

        # Initialize the confidence for English
        english_confidence = 0.0
        slovak_confidence = 0.0
        # Loop through the detected languages and find the confidence for English
        for lang in languages:
            if lang.lang == "en":
                english_confidence = lang.prob
            elif lang.lang == "sk":
                slovak_confidence = lang.prob
            else:
                break
        if english_confidence > slovak_confidence:
            return "en"
        else:
            return "sk"
    except Exception as e:
        return "sk"

def send_email_verification(email, code, language="en"):
    sender_email = "mlukan@gmail.com"
    app_password = "dkmqmzxhtcaeheqz"
    subject = "Your 2FA Verification Code from the Blood Donation Bot" if language == "en" else "Váš overovací kód od Blood Donation Bota"
    
    # Email content
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = subject
    body = f"Your verification code is: \n {code}" if language == "en" else f"Váš overovací kód je: \n {code}"
    message.attach(MIMEText(body, "plain"))

    try:
        # Connect to Gmail SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, email, message.as_string())
        server.quit()
        logger.info("Verification email sent!")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False



def validate_access_code(email, access_code, session_id):
    if access_code: 
        conn = sqlite3.connect("../data/calendar.db")
        cursor = conn.cursor()
        now = get_unix_minutes(datetime.now())
        logger.info(f"Validation query: {email}, {access_code}, {session_id}, {now}")
        cursor.execute("SELECT email, session, expires FROM sessions WHERE email = ? AND code = ? AND session = ? AND expires > ?", (email, access_code, session_id, now))
        res = cursor.fetchone()
        logger.info(f"Validation result: {res}")
        conn.close()
        if not res:
            return False
        else: return True
    else: return False
