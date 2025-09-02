import os
import hashlib
import json

import icalendar
from flask import Flask, Response, request, jsonify
from icalendar import Calendar, Event
from bs4 import BeautifulSoup
import datetime

import VARS

app = Flask(__name__)

CACHE_DURATION = 3600  # 1 heure

#default route
@app.route('/')
def index():
    return "Welcome to the Calendar Feed Service!"

@app.route('/register')
def register():
    username = request.args.get('username')
    password = request.args.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    # Generate token (hash, max 16 chars)
    token_source = f'{username}:{password}:{os.urandom(8)}'
    token = hashlib.sha256(token_source.encode()).hexdigest()[:16]

    # Store in logins.json
    logins_path = os.path.join(VARS.SECRETS_FOLDER, VARS.LOGINS_FILE)
    if os.path.exists(logins_path):
        with open(logins_path, 'r') as f:
            try:
                logins = json.load(f)
            except Exception:
                logins = {}
    else:
        logins = {}
    # Check if username already exists
    if username in logins:
        return jsonify({'error': 'Username already exists'}), 400
    # Save new login
    logins[username] = {'password': password, 'token': token}
    with open(logins_path, 'w') as f:
        json.dump(logins, f)

    return jsonify({'token': token})

@app.route('/agenda.ics')
def agenda():
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Missing token'}), 401

    # Load logins.json and check token validity
    logins_path = os.path.join(VARS.SECRETS_FOLDER, VARS.LOGINS_FILE)
    if not os.path.exists(logins_path):
        return jsonify({'error': 'No registered users'}), 401
    with open(logins_path, 'r') as f:
        try:
            logins = json.load(f)
        except Exception:
            return jsonify({'error': 'Invalid logins file'}), 500
    # Check if token exists for any user
    if not any(user.get('token') == token for user in logins.values()):
        return jsonify({'error': 'Invalid token'}), 401

    # Open ics file
    ics_path = os.path.join(VARS.SECRETS_FOLDER, f"{token}.ics")
    if not os.path.exists(ics_path):
        return "ICS file not found", 404
    with open(ics_path, 'rb') as f:
        ical = f.read()

    return Response(
        ical,
        mimetype='text/calendar',
        headers={
            'Cache-Control': f'public, max-age={CACHE_DURATION}'
        }
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)