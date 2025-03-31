from langdetect import detect_langs
import smtplib
import random
import os
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import time
from actions.calendar_utils import get_unix_minutes
from datetime import datetime
import logging
from ftlangdetect import detect
import re
import qrcode
from io import BytesIO
from actions.orm import SessionLocal, User, Session as UserSession, Base
logger = logging.getLogger(__name__)
sender_email = os.getenv("SENDER_EMAIL")
app_password = os.getenv("APP_PASSWORD")
def detect_language(text):
    try:
        res = detect(text)
        if res["lang"] == "en":
            return "en"
        else:
            return "sk"
    except Exception as e:
        logger.error(f"Error detecting language: {e}")
        return "sk"
    


def send_email_verification(email, code, language="en"):
    subject = "Your 2FA Verification Code from Eryc" if language == "en" else "Váš overovací kód od Eryca"
    
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


def send_ics_email(email, ics_content, language="en"):
    subject = "Your booking for blood donation  from Eryc" if language == "en" else "Váš plánovaný termín darovania krvi od Eryca"
    # Email content
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = subject
    # Attach the .ics content
    ics_part = MIMEText(ics_content, "calendar;method=REQUEST")
    ics_part.add_header("Content-Disposition", "attachment", filename="appointment.ics")
    message.attach(ics_part)
    try:
        # Connect to Gmail SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, email, message.as_string())
        server.quit()
        logger.info("ICS email sent!")
        return True
    except Exception as e:
        logger.error(f"Error sending ICSemail: {e}")
        return False
    


def validate_access_code(email, access_code, session_id):
    if not access_code:
        return False

    session = SessionLocal()
    try:
        now = get_unix_minutes(datetime.now())
        logger.info(f"Validation query: {email}, {access_code}, {session_id}, {now}")

        result = (
            session.query(UserSession)
            .filter(
                UserSession.email == email,
                UserSession.code == access_code,
                UserSession.session == session_id,
                UserSession.expires > now
            )
            .first()
        )

        logger.info(f"Validation result: {result}")
        return result is not None

    except Exception as e:
        logger.error(f"Error during access code validation: {e}")
        return False
    finally:
        session.close()


def is_valid_email(email: str) -> bool:
    # Basic regex pattern for email validation
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


def generate_qr_code(data: dict):
    expires_str = data.get("expires",datetime.now().strftime("%d.%m.%Y %H:%M"))

    qr_data = f"UID:{data.get('UID')}\nexpires:{expires_str}"

    # Generate QR code
    qr = qrcode.make(qr_data)

    # Save QR code to memory (not disk)
    qr_buffer = BytesIO()
    qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    return qr_buffer

def send_qr_code(email, qr_buffer, language="en"):
    # Email subject
    subject = "Your blood donation questionnaire code from Eryc" if language == "en" else "Kód Vášho dotazník k darovaniu krvi od Eryca"
    # Email content
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = subject
    # Attach QR code image
    qr_image = MIMEImage(qr_buffer.read(), _subtype="png")
    qr_image.add_header("Content-ID", "<qrcode>")
    qr_image.add_header("Content-Disposition", "attachment", filename="qrcode.png")
    message.attach(qr_image)
    try:
        # Connect to Gmail SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, email, message.as_string())
        server.quit()
        logger.info("QR code email sent!")
        return True
    except Exception as e:
        logger.error(f"Error sending QR code: {e}")
        return False