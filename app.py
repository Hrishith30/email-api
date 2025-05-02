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
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

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
app.logger.info('Application startup')

# Setup CORS properly for GitHub Pages
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://hrishith30.github.io/portfolio"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept"]
    }
})

# Initialize mail
mail = Mail(app)

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

@app.route('/api/contact', methods=['POST'])
def contact():
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['name', 'email', 'phone', 'message']):
            return jsonify({'message': 'Missing required fields'}), 400

        # Log the incoming request
        app.logger.info(f'Received contact form submission from {data["email"]}')

        # Create email body
        email_body = f"""
        New Contact Form Submission
        
        Name: {data['name']}
        Email: {data['email']}
        Phone: {data['phone']}
        Message: {data['message']}
        
        Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        msg = Message(
            subject='New Contact Form Submission',
            recipients=[os.getenv('RECIPIENT_EMAIL')],
            body=email_body
        )

        mail.send(msg)
        app.logger.info(f'Successfully sent email for {data["email"]}')
        
        return jsonify({'message': 'Message sent successfully'}), 200

    except Exception as e:
        app.logger.error(f'Error processing request: {str(e)}')
        return jsonify({'message': 'Internal server error'}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    global server_healthy
    return jsonify({
        'status': 'healthy' if server_healthy else 'unhealthy',
        'timestamp': time.time()
    }), 200 if server_healthy else 500

def run_server():
    try:
        # Start health monitoring in background
        monitor_thread = Thread(target=monitor_server_health, daemon=True)
        monitor_thread.start()

        # Use waitress for production
        app.logger.info(f'Starting server on port {int(os.environ.get("PORT", 5000))}')
        serve(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    except Exception as e:
        app.logger.error(f'Server error: {str(e)}')
        time.sleep(5)  # Wait before restart attempt
        restart_server()

if __name__ == '__main__':
    # Use waitress for production
    serve(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
