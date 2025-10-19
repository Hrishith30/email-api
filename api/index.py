from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# ✅ Load environment variables from .env
load_dotenv()

app = FastAPI()

# ✅ Allow CORS for your frontend (GitHub Pages)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hrishith30.github.io",  # your portfolio site
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Model for contact form
class ContactForm(BaseModel):
    name: str
    email: str
    country: str
    phone: str
    message: str

# ✅ Test endpoint
@app.get("/api/test")
async def test_api():
    return {"status": "ok", "message": "API is reachable!"}

# ✅ Send email using Brevo SMTP
@app.post("/api/contact")
async def send_email(form: ContactForm):
    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp-relay.brevo.com")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        recipient = os.getenv("RECIPIENT_EMAIL")

        if not all([smtp_user, smtp_pass, recipient]):
            raise ValueError("Missing SMTP or recipient configuration")

        subject = f"New Contact from {form.name}"
        body = (
            f"Name: {form.name}\n"
            f"Email: {form.email}\n"
            f"Country: {form.country}\n"
            f"Phone: {form.phone}\n"
            f"Message:\n{form.message}"
        )

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = recipient

        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)

        return {"status": "success", "message": "Email sent successfully"}

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)},
        )
