from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://hrishith30.github.io"],
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

def send_brevo_email(sender_name, sender_email, to_email, to_name, subject, content):
    """Helper function to send an email via Brevo HTTP API"""
    api_key = os.getenv("BREVO_API_KEY")
    if not api_key:
        raise ValueError("BREVO_API_KEY is missing. Set it in environment variables.")
    
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "textContent": content
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 401:
        raise ValueError("Brevo API Key Unauthorized. Check your API key and sender email verification.")
    if response.status_code not in (200, 201, 202):
        raise ValueError(f"Brevo API error: {response.status_code} - {response.text}")

    return response

@app.post("/api/contact")
async def send_email(form: ContactForm):
    try:
        # Recipient and sender
        recipient = os.getenv("RECIPIENT_EMAIL")  # Your inbox
        sender_email = "999f85001@smtp-brevo.com"  # Verified sender email in Brevo

        if not recipient:
            raise ValueError("RECIPIENT_EMAIL is missing. Set it in environment variables.")

        # 1️⃣ Send notification to site owner
        owner_subject = f"New Contact from {form.name}"
        owner_content = f"""
Name: {form.name}
Email: {form.email}
Country: {form.country}
Phone: {form.phone}
Message:
{form.message}
"""
        send_brevo_email(
            sender_name="Portfolio Contact",
            sender_email=sender_email,
            to_email=recipient,
            to_name="Rishi",
            subject=owner_subject,
            content=owner_content
        )

        # 2️⃣ Send confirmation to user
        user_subject = "Thank you for contacting me!"
        user_content = f"""
Hi {form.name},

Thank you for reaching out. I have received your message and will get back to you soon.

Here’s a copy of your message:

{form.message}

Best regards,
Rishi
"""
        send_brevo_email(
            sender_name="Rishi Portfolio",
            sender_email=sender_email,
            to_email=form.email,
            to_name=form.name,
            subject=user_subject,
            content=user_content
        )

        return {"status": "success", "message": "Emails sent successfully via Brevo API"}

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)}
        )
