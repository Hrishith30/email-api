from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail, Message
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import traceback
from waitress import serve
import time
import sys
from threading import Thread
import requests

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App configuration
app.config.update(
    DEBUG=False,
    TESTING=False,
    # Mail configuration
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('EMAIL_USER'),
    MAIL_PASSWORD=os.getenv('EMAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.getenv('EMAIL_USER')
)

# Setup logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# Add console handler for better visibility
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app.logger.addHandler(console_handler)

app.logger.info('Application startup - Initializing server...')

# Allow all origins for development and production
ALLOWED_ORIGINS = [
    "https://hrishith30.github.io",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://hrishith30.github.io/portfolio"
]

# CORS configuration
CORS(app, resources={
    r"/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept", "Origin"],
        "supports_credentials": False
    }
})

# Initialize mail
mail = Mail(app)
app.logger.info('Mail server configured')

# Server health monitoring
server_healthy = True

def monitor_server_health():
    """Background task to monitor server health"""
    while True:
        try:
            # Check if server is responding
            if not server_healthy:
                app.logger.error("Server health check failed, attempting restart")
                restart_server()
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            app.logger.error(f"Monitor error: {str(e)}")

def restart_server():
    """Restart the server process"""
    app.logger.info("Restarting server...")
    os.execv(sys.executable, ['python'] + sys.argv)

@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'false')
    return response

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"status": "API is working"}), 200

@app.route('/api/contact', methods=['POST', 'OPTIONS'])
def contact():
    logger.info(f"Received {request.method} request from {request.headers.get('Origin')}")
    
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json()
        logger.info(f"Received data: {data}")

        if not data:
            return jsonify({'message': 'No data received'}), 400

        # Create and send email
        email_body = f"""
        New Contact Form Submission

        Name: {data.get('name', 'Not provided')}
        Email: {data.get('email', 'Not provided')}
        Country: {data.get('country', 'Not provided')}
        Phone: {data.get('phone', 'Not provided')}
        Message: {data.get('message', 'Not provided')}
        """

        msg = Message(
            subject='New Contact Form Submission',
            recipients=[os.getenv('RECIPIENT_EMAIL')],
            body=email_body
        )

        mail.send(msg)
        logger.info("Email sent successfully")
        return jsonify({'message': 'Message sent successfully'}), 200

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'message': f'Server error: {str(e)}'}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    global server_healthy
    return jsonify({
        'status': 'healthy' if server_healthy else 'unhealthy',
        'timestamp': time.time()
    }), 200 if server_healthy else 500

def self_ping():
    """Background task to ping the server's own health endpoint every 10 seconds."""
    while True:
        try:
            url = f"http://localhost:{os.environ.get('PORT', 5000)}/health"
            public_url = os.environ.get("PUBLIC_URL")
            if public_url:
                url = f"{public_url}/health"
            requests.get(url, timeout=10)
            app.logger.info(f"Self-pinged {url}")
        except Exception as e:
            app.logger.warning(f"Self-ping failed: {e}")
        time.sleep(30)  # Ping every 10 seconds

def run_server():
    try:
        # Start health monitoring in background
        monitor_thread = Thread(target=monitor_server_health, daemon=True)
        monitor_thread.start()

        # Start self-ping in background
        ping_thread = Thread(target=self_ping, daemon=True)
        ping_thread.start()

        # Use waitress for production
        app.logger.info(f'Starting server on port {int(os.environ.get("PORT", 5000))}')
        app.logger.info('Server is ready to accept connections')
        serve(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    except Exception as e:
        app.logger.error(f'Server error: {str(e)}')
        time.sleep(5)  # Wait before restart attempt
        restart_server()

if __name__ == '__main__':
    # Start self-ping in background
    ping_thread = Thread(target=self_ping, daemon=True)
    ping_thread.start()

    # Use waitress for production
    port = int(os.environ.get('PORT', 5000))
    app.logger.info(f'Starting server on port {port}...')
    app.logger.info('Server is ready to accept connections')
    serve(app, host='0.0.0.0', port=port)
