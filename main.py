import os

import icalendar
from flask import Flask, Response
from icalendar import Calendar, Event
from bs4 import BeautifulSoup
import datetime

app = Flask(__name__)

CACHE_DURATION = 3600  # 1 heure

#default route
@app.route('/')
def index():
    return "Welcome to the Calendar Feed Service!"

@app.route('/agenda.ics')
def calendar_feed():
    # Vérification du token
    #if request.args.get("token") != API_TOKEN:
    #    return "Accès non autorisé", 401

    # Open ics file
    ics_path = os.path.join("Secrets", "12345.ics")
    if not os.path.exists(ics_path):
        return "Fichier ICS non trouvé", 404
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