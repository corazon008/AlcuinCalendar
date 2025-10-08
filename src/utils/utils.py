from scraper.AlcuinSelenium import AlcuinSelenium  # Import here to avoid circular import issues
import time

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