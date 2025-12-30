from flask import Flask, request, jsonify, send_from_directory
import os
import threading
from Acc_Gen import InstagramAccountCreator

app = Flask(__name__, static_folder='static')

# In-memory storage for active sessions
sessions = {}

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/request-otp', methods=['POST'])
def request_otp():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    creator = InstagramAccountCreator(country='US', language='en')
    try:
        creator.generate_headers()
        if creator.send_verification_email(email):
            sessions[email] = creator
            return jsonify({'success': True, 'message': 'OTP sent to email'})
        else:
            return jsonify({'error': 'Failed to send OTP'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')
    
    if not email or not otp:
        return jsonify({'error': 'Email and OTP are required'}), 400
        
    creator = sessions.get(email)
    if not creator:
        return jsonify({'error': 'Session expired or not found'}), 404
        
    try:
        signup_code = creator.validate_verification_code(email, otp)
        if signup_code:
            credentials = creator.create_account(email, signup_code)
            if credentials:
                # Remove from sessions after successful creation
                del sessions[email]
                return jsonify({
                    'success': True, 
                    'credentials': {
                        'username': credentials.username,
                        'password': credentials.password,
                        'email': credentials.email
                    }
                })
            else:
                return jsonify({'error': 'Account creation failed'}), 500
        else:
            return jsonify({'error': 'Invalid OTP'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
