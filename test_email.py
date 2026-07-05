# test_email.py
import os, smtplib
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("FROM_EMAIL", "").strip()
pwd = os.getenv("APP_PASSWORD", "").replace(" ", "").strip()

print("FROM_EMAIL:", user)
print("APP_PASSWORD length:", len(pwd))

with smtplib.SMTP("smtp.mail.yahoo.com", 587) as smtp:
    smtp.set_debuglevel(1)
    smtp.starttls()
    smtp.login(user, pwd)
    print("LOGIN OK")
