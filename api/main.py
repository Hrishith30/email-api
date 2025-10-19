from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import smtplib
from email.mime.text import MIMEText
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://hrishith30.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ContactForm(BaseModel):
    name: str
    email: str
    country: str
    phone: str
    message: str

@app.get("/api/test")
async def test_api():
    return {"status": "ok", "message": "API is reachable!"}

@app.post("/api/contact")
async def send_email(form: ContactForm):
    try:
        SMTP_HOST = "smtp-relay.brevo.com"
        SMTP_PORT = 587
        SMTP_USER = "999f85001@smtp-brevo.com"
        SMTP_PASS = os.getenv("SMTP_PASS")  # Your SMTP password (store in Vercel env)
        RECIPIENT = os.getenv("RECIPIENT_EMAIL")  # rishi6211130@gmail.com

        if not SMTP_PASS:
            raise ValueError("SMTP_PASS not set in environment variables.")

        # Compose the email
        subject = f"New Contact from {form.name}"
        body = f"""
Name: {form.name}
Email: {form.email}
Country: {form.country}
Phone: {form.phone}
Message:
{form.message}
"""
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = RECIPIENT

        # Connect to Brevo SMTP relay
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()  # Secure connection
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)

        return {"status": "success", "message": "Email sent successfully via SMTP"}

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)},
        )
