from pathlib import Path

BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

# Folders
SECRETS_FOLDER: Path = BASE_DIR / "Secrets"
LOG_FOLDER: Path = BASE_DIR / "Logs"
CALENDAR_FOLDER: Path = BASE_DIR / "Calendars"

## Create folders if they don't exist
SECRETS_FOLDER.mkdir(parents=True, exist_ok=True)
LOG_FOLDER.mkdir(parents=True, exist_ok=True)
CALENDAR_FOLDER.mkdir(parents=True, exist_ok=True)

# Files
ACCESS_LOG_FILE : Path = LOG_FOLDER / "access.log"
LOG_FILEs : Path = LOG_FOLDER / "app.log"
USERS_FILE : Path = SECRETS_FOLDER / "users.json"
