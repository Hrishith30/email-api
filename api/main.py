from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Allow requests from your portfolio frontend
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
        sender = os.getenv("GMAIL_USER")
        smtp_pass = os.getenv("GMAIL_APP_PASSWORD")
        recipient = os.getenv("RECIPIENT_EMAIL")

        if not all([sender, smtp_pass, recipient]):
            raise ValueError("Missing GMAIL_USER, GMAIL_APP_PASSWORD, or RECIPIENT_EMAIL in environment variables.")

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
        msg["From"] = sender
        msg["To"] = recipient

        # Connect to Gmail SMTP
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(sender, smtp_pass)
            smtp.send_message(msg)

        return {"status": "success", "message": "Email sent successfully!"}

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)}
        )
