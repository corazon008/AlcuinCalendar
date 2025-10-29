import os
import hashlib
import logging
import sys
from flask import Flask, request, jsonify, Response

from scraper.RefreshQueue import RefreshQueue
from utils.UserManager import UserManager
from utils.VARS import SECRETS_FOLDER, BASE_DIR, CALENDAR_FOLDER
from utils.utils import get_agenda_ics

app = Flask(__name__)

CACHE_DURATION = 3600  # 1 heure

# Global logging config (Docker-friendly)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)

users = UserManager()
refresh_queue = RefreshQueue()
refresh_queue.start()  # start background worker


# default route
@app.route('/')
def index():
    html_path = os.path.join(BASE_DIR, 'src', 'pages', 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    return Response(html, mimetype='text/html')

@app.route("/register")
def register():
    username = request.args.get("username")
    password = request.args.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    if username.endswith("@esaip.org"):
        username = username.replace("@esaip.org", "")

    token_source = f"{username}:{password}:{os.urandom(8)}"
    token = hashlib.sha256(token_source.encode()).hexdigest()[:16]

    if users.user_exists_username(username):
        return jsonify({"error": "Username already exists"}), 400

    users.add_user(username, password, token)
    refresh_queue.add_task(token, username, password)

    return jsonify({
        "token": token,
        "message": "User registered successfully; calendar refresh queued."
    })


@app.route('/agenda.ics')
def agenda():
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Missing token'}), 401

    if not users.user_exists_token(token):
        return jsonify({'error': 'Invalid token'}), 401

    # Open ics file
    if (ical := get_agenda_ics(token)) is False:
        return "ICS file not found", 404

    return Response(
        ical,
        mimetype='text/calendar',
        headers={
            'Cache-Control': f'public, max-age={CACHE_DURATION}'
        }
    )

@app.route('/agenda/{token}.ics')
def agenda_token(token):
    if not token:
        return jsonify({'error': 'Missing token'}), 401

    if not users.user_exists_token(token):
        return jsonify({'error': 'Invalid token'}), 401

    # Open ics file
    if (ical := get_agenda_ics(token)) is False:
        return "ICS file not found", 404

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

    refresh_queue.add_task(token, username, password)
    return jsonify({'message': 'Calendar refresh queued.'}), 200

@app.route("/queue_status")
def queue_status():
    """Expose the current queue state."""
    return jsonify(refresh_queue.status())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)