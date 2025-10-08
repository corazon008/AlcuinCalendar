from scraper.AlcuinSelenium import AlcuinSelenium  # Import here to avoid circular import issues


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