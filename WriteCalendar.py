from datetime import datetime

def convertir_en_datetime(date, heure):
    date_obj = datetime.strptime(date, '%d/%m/%Y')
    heure_obj = datetime.strptime(heure, '%Hh%M')
    return date_obj.strftime('%Y%m%d') + 'T' + heure_obj.strftime('%H%M%S')

class WriteCalendar:

    def beginWriting(self, filename):
        print("Writing calendar")
        self.file_stream = open(f"Secrets/{filename}.ics", "w", encoding="utf-8")
        self.file_stream.write("BEGIN:VCALENDAR\n")
        self.file_stream.write("VERSION:2.0\n")
        self.file_stream.write("PRODID:-//My Calendar//EN\n")

    def endWriting(self):
        # Pied du fichier .ics
        self.file_stream.write("END:VCALENDAR\n")
        self.file_stream.close()

    def writeEvent(self, nom_cours, dtstart, dtend, salle):
        self.file_stream.write("BEGIN:VEVENT\n")
        self.file_stream.write(f"SUMMARY:{nom_cours}\n")
        self.file_stream.write(f"DTSTART:{dtstart}\n")
        self.file_stream.write(f"DTEND:{dtend}\n")
        self.file_stream.write(f"LOCATION:{salle}\n")
        self.file_stream.write("END:VEVENT\n")

    def writeEventWithTD(self, cells):
        # Extraire les informations pertinentes
        nom_cours = cells[1].get_text(strip=True)  # Nom du cours
        date_cours = cells[4].get_text(strip=True)  # Date du cours
        heure_debut = cells[5].get_text(strip=True)  # Heure de début
        heure_fin = cells[6].get_text(strip=True)  # Heure de fin
        salle = cells[8].get_text(strip=True)  # Salle

        # Convertir les heures en format iCalendar
        dtstart = convertir_en_datetime(date_cours, heure_debut)
        dtend = convertir_en_datetime(date_cours, heure_fin)

        self.writeEvent(nom_cours, dtstart, dtend, salle)