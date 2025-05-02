from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail, Message
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import traceback
import multiprocessing
from waitress import serve
import time
import sys
from threading import Thread

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

# Initialize extensions
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://hrishith30.github.io",
            "https://hrishith30.github.io/portfolio",
            "http://localhost:3000",
            "http://localhost:5000"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept", "Authorization"],
        "expose_headers": ["Content-Type", "X-CSRFToken"],
        "supports_credentials": True
    }
})
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
    global server_healthy
    try:
        # Log the incoming request
        app.logger.info("Received contact form submission")
        
        # Get JSON data with error handling
        try:
            data = request.get_json()
            if not data:
                raise ValueError("No JSON data received")
        except Exception as e:
            app.logger.error(f"Error parsing JSON: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Invalid request format'
            }), 400

        # Debug logging
        app.logger.info(f"Received data: {data}")
        
        # Extract and validate form data
        required_fields = {
            'name': data.get('name'),
            'email': data.get('email'),
            'message': data.get('message')
        }
        
        # Check for missing fields
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            app.logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
            return jsonify({
                'success': False,
                'message': f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Extract optional fields
        country = data.get('country_name', 'Not specified')
        country_phone = str(data.get('country_code_display', '')).strip()
        phone = data.get('phone', 'Not specified')

        # Create email body
        email_body = f"""
        New Contact Form Submission

        Name: {required_fields['name']}
        Email: {required_fields['email']}
        Country: {country}
        Phone: +{country_phone} {phone}
        
        Message:
        {required_fields['message']}
        """

        # Send email with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                msg = Message(
                    subject='New Contact Form Submission',
                    recipients=[os.getenv('RECIPIENT_EMAIL')],
                    body=email_body
                )
                msg.reply_to = required_fields['email']
                mail.send(msg)
                app.logger.info(f"Email sent successfully on attempt {attempt + 1}")
                break
            except Exception as mail_error:
                app.logger.error(f"Attempt {attempt + 1} failed: {str(mail_error)}")
                if attempt == max_retries - 1:
                    return jsonify({
                        'success': False,
                        'message': 'Failed to send email. Please try again later.'
                    }), 500
                time.sleep(2)

        server_healthy = True
        return jsonify({
            'success': True,
            'message': 'Message sent successfully!'
        })

    except Exception as e:
        server_healthy = False
        app.logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500

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

        # Calculate optimal number of threads
        num_threads = multiprocessing.cpu_count() * 2
        
        # Use waitress as production server
        app.logger.info(f'Starting server with {num_threads} threads')
        serve(app, host='0.0.0.0', port=5000, threads=num_threads)
    except Exception as e:
        app.logger.error(f'Server error: {str(e)}')
        time.sleep(5)  # Wait before restart attempt
        restart_server()

if __name__ == '__main__':
    # Install additional requirements
    os.system('pip install waitress')
    
    # Run the production server
    while True:
        try:
            run_server()
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            app.logger.error(f"Fatal error: {str(e)}")
            time.sleep(5)  # Wait before restart
            continue 
