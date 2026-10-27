import hashlib
from datetime import datetime, timezone
from icalendar import Calendar, Event, vText, vDatetime
import pytz
from utils.VARS import CALENDAR_FOLDER


class ICalWriter:
    def __init__(self):
        self.calendar = Calendar()
        self.calendar.add("prodid", "-//My Calendar//EN")
        self.calendar.add("version", "2.0")
        # UIDs must stay stable across refreshes, so identical events are
        # counted to keep duplicates distinct without using random values.
        self._uid_counters = {}

    def add_event(self, nom_cours, date_cours, heure_debut, heure_fin, salle):
        event = Event()
        event.add("summary", vText(nom_cours))

        # Gestion des dates avec timezone
        tz = pytz.timezone("Europe/Paris")
        start_dt = self._parse_datetime(date_cours, heure_debut)
        end_dt = self._parse_datetime(date_cours, heure_fin)

        event.add("dtstart", tz.localize(start_dt))
        event.add("dtend", tz.localize(end_dt))
        event.add("location", vText(salle))

        # DTSTAMP must be in UTC per RFC 5545
        event.add("dtstamp", vDatetime(datetime.now(timezone.utc)))
        event.add(
            "uid",
            self._make_uid(
                nom_cours, date_cours, heure_debut, heure_fin, salle
            ),
        )

        self.calendar.add_component(event)

    def _make_uid(self, *fields):
        """Deterministic UID: same event keeps the same UID on every refresh."""
        key = "|".join(fields)
        count = self._uid_counters.get(key, 0)
        self._uid_counters[key] = count + 1
        digest = hashlib.sha256(f"{key}|{count}".encode()).hexdigest()
        return f"{digest}@mon-agenda.fr"

    def _parse_datetime(self, date_str, heure_str):
        date = datetime.strptime(date_str, "%d/%m/%Y")
        heure = datetime.strptime(heure_str.replace("h", ":"), "%H:%M")
        return datetime.combine(date.date(), heure.time())

    def write_to_file(self, filename):
        with open(CALENDAR_FOLDER / f"{filename}.ics", "wb") as f:
            f.write(self.get_ical())

    def get_ical(self):
        # Let icalendar emit a valid VTIMEZONE (with STANDARD/DAYLIGHT).
        # An empty VTIMEZONE is rejected by strict parsers such as Nextcloud's.
        self.calendar.add_missing_timezones()
        return self.calendar.to_ical()

    def add_event_from_cells(self, cells):
        nom_cours = cells[1].get_text(strip=True)
        date_cours = cells[4].get_text(strip=True)
        heure_debut = cells[5].get_text(strip=True)
        heure_fin = cells[6].get_text(strip=True)
        salle = cells[8].get_text(strip=True)

        self.add_event(nom_cours, date_cours, heure_debut, heure_fin, salle)
