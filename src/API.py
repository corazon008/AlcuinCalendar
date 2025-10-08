import os
import hashlib

from flask import Flask, Response, request, jsonify
from utils.UserManager import UserManager
from utils.VARS import SECRETS_FOLDER, BASE_DIR
from utils.utils import refresh_calendars

app = Flask(__name__)

CACHE_DURATION = 3600  # 1 heure

users = UserManager()


# default route
@app.route('/')
def index():
    html_path = os.path.join(BASE_DIR, 'src', 'pages', 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    return Response(html, mimetype='text/html')


@app.route('/register')
def register():
    username = request.args.get('username')
    password = request.args.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    # Generate token (hash, max 16 chars)
    token_source = f'{username}:{password}:{os.urandom(8)}'
    token = hashlib.sha256(token_source.encode()).hexdigest()[:16]


    if users.user_exists_username(username):
        return jsonify({'error': 'Username already exists'}), 400

    users.add_user(username, password, token)

    return jsonify({'token': token})


@app.route('/agenda.ics')
def agenda():
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Missing token'}), 401

    if not users.user_exists_token(token):
        return jsonify({'error': 'Invalid token'}), 401

    # Open ics file
    ics_path = SECRETS_FOLDER / f"{token}.ics"
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


@app.route('/refresh')
def refresh():
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Missing token'}), 401

    if not users.user_exists_token(token):
        return jsonify({'error': 'Invalid token'}), 401

    user = users.get_user(token)
    username = user['username']
    password = user['password']

    if not refresh_calendars(token, username, password):
        return jsonify({'error': 'Failed to refresh calendar'}), 500

    return jsonify({'status': 'Calendar refreshed successfully'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)