import uuid
from datetime import datetime
from icalendar import Calendar, Event, vText, vDatetime, Timezone
import pytz
from dateutil.tz import gettz
from VARS import *

class ICalWriter:
    def __init__(self):
        self.calendar = Calendar()
        self.calendar.add('prodid', '-//My Calendar//EN')
        self.calendar.add('version', '2.0')

        # Ajout du composant VTIMEZONE pour Europe/Paris
        tz = gettz('Europe/Paris')
        tzc = Timezone('Europe/Paris')
        tzc.add('TZID', 'Europe/Paris')
        self.calendar.add_component(tzc)

    def add_event(self, nom_cours, date_cours, heure_debut, heure_fin, salle):
        event = Event()
        event.add('summary', vText(nom_cours))

        # Gestion des dates avec timezone
        tz = pytz.timezone('Europe/Paris')
        start_dt = self._parse_datetime(date_cours, heure_debut)
        end_dt = self._parse_datetime(date_cours, heure_fin)

        event.add('dtstart', tz.localize(start_dt))
        event.add('dtend', tz.localize(end_dt))
        event.add('location', vText(salle))

        # Ajout des propriétés obligatoires
        event.add('dtstamp', vDatetime(datetime.now(tz)))
        event.add('uid', str(uuid.uuid4()) + '@mon-agenda.fr')

        self.calendar.add_component(event)

    def _parse_datetime(self, date_str, heure_str):
        date = datetime.strptime(date_str, '%d/%m/%Y')
        heure = datetime.strptime(heure_str.replace('h', ':'), '%H:%M')
        return datetime.combine(date.date(), heure.time())

    def write_to_file(self, filename):
        with open(f"{SECRETS_FOLDER}/{filename}.ics", 'wb') as f:
            f.write(self.calendar.to_ical())

    def get_ical(self):
        return self.calendar.to_ical()

    def add_event_from_cells(self, cells):
        nom_cours = cells[1].get_text(strip=True)
        date_cours = cells[4].get_text(strip=True)
        heure_debut = cells[5].get_text(strip=True)
        heure_fin = cells[6].get_text(strip=True)
        salle = cells[8].get_text(strip=True)

        self.add_event(nom_cours, date_cours, heure_debut, heure_fin, salle)