from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import requests
from dotenv import load_dotenv

# ✅ Load local .env for development
load_dotenv()

app = FastAPI()

# ✅ CORS setup for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://hrishith30.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Contact form data model
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

# ✅ Contact form endpoint using Brevo API
@app.post("/api/contact")
async def send_email(form: ContactForm):
    try:
        api_key = os.getenv("BREVO_API_KEY")
        recipient = os.getenv("RECIPIENT_EMAIL")

        if not all([api_key, recipient]):
            raise ValueError("Missing BREVO_API_KEY or RECIPIENT_EMAIL in environment")

        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        data = {
            "sender": {"name": "Portfolio Contact", "email": recipient},
            "to": [{"email": recipient, "name": "Rishi"}],
            "subject": f"New Contact from {form.name}",
            "textContent": f"""
Name: {form.name}
Email: {form.email}
Country: {form.country}
Phone: {form.phone}
Message: {form.message}
"""
        }

        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code not in (200, 201, 202):
            raise ValueError(f"Brevo API error: {resp.text}")

        return {"status": "success", "message": "Email sent successfully"}

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)},
        )
