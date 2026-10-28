import logging
import os
import time

from utils.VARS import CALENDAR_FOLDER

logger = logging.getLogger(__name__)


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")


def refresh_calendars(token: str, username: str, password: str) -> bool:
    # Local import: AlcuinSelenium imports this module, a top-level import
    # would create a circular dependency.
    from scraper.AlcuinSelenium import AlcuinSelenium

    # Headless by default when running in a container/server.
    headless = _env_flag("SELENIUM_HEADLESS", True)
    try:
        alcuin = AlcuinSelenium(token, username, password, headless=headless)
    except Exception as e:
        logger.error(f"Could not start browser for user {username}: {e}")
        return False

    try:
        alcuin.get_calendar()
    except Exception as e:
        logger.error(f"Error refreshing calendar for user {username}: {e}")
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


def get_agenda_ics(token: str) -> bool | bytes:
    # Open ics file
    ics_path = CALENDAR_FOLDER / f"{token}.ics"
    if not os.path.exists(ics_path):
        return False
    with open(ics_path, "rb") as f:
        ical = f.read()
    return ical
