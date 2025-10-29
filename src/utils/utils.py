from scraper.AlcuinSelenium import AlcuinSelenium  # Import here to avoid circular import issues
import time, os

from utils.VARS import CALENDAR_FOLDER


def refresh_calendars(token: str, username: str, password: str)-> bool:
    alcuin = AlcuinSelenium(token, username, password, headless=False)
    try:
        alcuin.get_calendar()
    except Exception as e:
        print(f"Error refreshing calendar for user {username}: {e}")
        return False
    finally:
        alcuin.close()
    return True

def retry(func, retries=3, delay=2, *args, **kwargs):
    """Retry a function a number of times with a delay"""
    for i in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e}. Retrying {i+1}/{retries}...")
            time.sleep(delay)
    raise Exception(f"Failed after {retries} retries")

def get_agenda_ics(token: str) -> bool|bytes:
    # Open ics file
    ics_path = CALENDAR_FOLDER / f"{token}.ics"
    if not os.path.exists(ics_path):
        return False
    with open(ics_path, 'rb') as f:
        ical = f.read()
    return ical