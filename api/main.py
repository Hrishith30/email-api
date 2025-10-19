from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import requests
from dotenv import load_dotenv

load_dotenv()

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
        api_key = os.getenv("BREVO_API_KEY")
        recipient = os.getenv("RECIPIENT_EMAIL")

        if not all([api_key, recipient]):
            raise ValueError("Missing BREVO_API_KEY or RECIPIENT_EMAIL")

        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        data = {
            "sender": {"name": "Portfolio Contact", "email": "999f85001@smtp-brevo.com"},
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

        response = requests.post(url, headers=headers, json=data)
        if response.status_code not in (200, 201, 202):
            raise ValueError(f"Brevo API error: {response.text}")

        return {"status": "success", "message": "Email sent successfully"}

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)},
        )
