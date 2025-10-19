from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import smtplib
from email.mime.text import MIMEText
import os

app = FastAPI()

# ✅ Allow CORS from your GitHub Pages site
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

# ✅ Route 1: Test endpoint
@app.get("/api/test")
async def test_api():
    return {"status": "ok", "message": "API is reachable!"}

# ✅ Route 2: Contact form email (Brevo)
@app.post("/api/contact")
async def send_email(form: ContactForm):
    try:
        # 🧠 Load Brevo SMTP credentials from environment
        sender = os.getenv("BREVO_EMAIL")       # e.g., "yourname@domain.com"
        password = os.getenv("BREVO_SMTP_KEY")  # your Brevo SMTP key
        recipient = os.getenv("CONTACT_RECEIVER", sender)  # default to sender if not set

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
        msg["From"] = sender
        msg["To"] = recipient

        # ✅ Brevo SMTP settings
        with smtplib.SMTP("smtp-relay.brevo.com", 587) as smtp:
            smtp.starttls()
            smtp.login(sender, password)
            smtp.send_message(msg)

        return {"status": "success", "message": "Email sent successfully"}

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)},
        )
