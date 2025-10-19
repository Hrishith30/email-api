from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load .env locally
load_dotenv()

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://hrishith30.github.io"],  # your portfolio site
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Contact form model
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
        sender = "999f85001@smtp-brevo.com"  # Verified Brevo SMTP email
        smtp_pass = os.getenv("SMTP_PASSWORD")  # Your SMTP key
        recipient = os.getenv("RECIPIENT_EMAIL")  # rishi6211130@gmail.com

        if not smtp_pass or not recipient:
            raise ValueError("Missing SMTP_PASSWORD or RECIPIENT_EMAIL in environment variables.")

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

        # Connect to Brevo SMTP relay
        with smtplib.SMTP("smtp-relay.brevo.com", 587) as smtp:
            smtp.starttls()
            smtp.login(sender, smtp_pass)
            smtp.send_message(msg)

        return {"status": "success", "message": "Email sent successfully!"}

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)}
        )
