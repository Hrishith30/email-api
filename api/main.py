from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import requests

app = FastAPI()

# Allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://hrishith30.github.io"],  # your portfolio
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

def send_email_brevo(sender_name, sender_email, to_email, to_name, subject, text_content, reply_to=None):
    """Send email via Brevo HTTP API"""
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
        "textContent": text_content
    }

    # Add reply-to if provided
    if reply_to:
        data["replyTo"] = {"email": reply_to, "name": sender_name}

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 401:
        raise ValueError(
            "Brevo API Key Unauthorized. "
            "Make sure you are using the HTTP API key and the sender email is verified."
        )
    if response.status_code not in (200, 201, 202):
        raise ValueError(f"Brevo API error: {response.status_code} - {response.text}")

    return response

@app.post("/api/contact")
async def contact(form: ContactForm):
    try:
        # Recipient = your inbox
        owner_email = os.getenv("RECIPIENT_EMAIL")
        # Must be verified in Brevo
        sender_email = "999f85001@smtp-brevo.com"

        if not owner_email:
            raise ValueError("RECIPIENT_EMAIL is missing. Set it in environment variables.")

        # Compose email
        subject = f"New Contact from {form.name}"
        content = f"""
Name: {form.name}
Email: {form.email}
Country: {form.country}
Phone: {form.phone}
Message:
{form.message}
"""

        # Send email to owner with Reply-To set to the user email
        send_email_brevo(
            sender_name="Portfolio Contact",
            sender_email=sender_email,
            to_email=owner_email,
            to_name="Rishi",
            subject=subject,
            text_content=content,
            reply_to=form.email
        )

        return {"status": "success", "message": "Email sent successfully!"}

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)}
        )
