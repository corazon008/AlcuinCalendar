import fastapi.responses
from fastapi import FastAPI
import uvicorn, os, random
import logging

from AlcuinSelenium import AlcuinSelenium
from VARS import *

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,  # Log file name
    level=logging.INFO,  # Log level
    format="%(asctime)s - %(levelname)s - %(message)s"  # Log message format
)

app = FastAPI()

@app.get("/", response_class=fastapi.responses.PlainTextResponse)
async def root(apiKey: str = ""):
    logging.info(f"Root endpoint called with apiKey: {apiKey}")
    if apiKey == "":
        logging.warning("No API key provided")
        return {"message": "No API key provided"}
    try:
        with open(f"{SECRETS_FOLDER}/{apiKey}.ics", "r", encoding="utf-8") as file:
            logging.info(f"Calendar file found for apiKey: {apiKey}")
            return fastapi.responses.Response(
                content=file.read(),
                media_type="text/calendar"
            )
    except FileNotFoundError:
        logging.error(f"No calendar found for apiKey: {apiKey}")
        return {"message": "No calendar found"}

@app.get("/calendar.ics", response_class=fastapi.responses.FileResponse)
async def calendar(apiKey: str = ""):
    file_path = f"{SECRETS_FOLDER}/{apiKey}.ics"
    logging.info(f"calendar.ics endpoint called with apiKey: {apiKey}")
    if os.path.exists(file_path):
        logging.info(f"Serving calendar file: {file_path}")
        return file_path
    else:
        logging.error(f"Calendar file not found: {file_path}")
        return ""

@app.get("/refresh_calendar")
async def refresh_calendar(apiKey: str = ""):
    logging.info(f"refresh_calendar endpoint called with apiKey: {apiKey}")
    if apiKey == "":
        logging.warning("No API key provided")
        return {"message": "No API key provided"}
    try:
        with open(f"{SECRETS_FOLDER}/login.txt", "r") as file:
            apiKeys = {key: [username, password] for key, username, password in [line.split(" ") for line in file.readlines()]}
        if apiKey not in apiKeys.keys():
            logging.error(f"Invalid API key: {apiKey}")
            return {"message": "Invalid API key " + apiKey}
        user = apiKeys[apiKey]

        alcuin = AlcuinSelenium(apiKey, *user, headless=True)
        alcuin.GetCalendar()
        logging.info(f"Calendar refreshed for apiKey: {apiKey}")
        return {"message": "Calendar refreshed"}
    except Exception as e:
        logging.error(f"Error refreshing calendar for apiKey: {apiKey}: {e}")
        return {"message": "Error refreshing calendar"}

@app.get("/create_user")
async def create_user(username: str = "", password: str = ""):
    logging.info(f"create_user endpoint called with username: {username}")
    if not os.path.exists(f"{SECRETS_FOLDER}"):
        os.mkdir(f"{SECRETS_FOLDER}")
        logging.info(f"Created directory: {SECRETS_FOLDER}")
    if not os.path.exists(f"{SECRETS_FOLDER}/login.txt"):
        with open(f"{SECRETS_FOLDER}/login.txt", "w") as file:
            logging.info("Created login.txt file")

    api = ''.join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=12))
    with open(f"{SECRETS_FOLDER}/login.txt", "a") as file:
        file.write(f"{api} {username} {password}\n")
        logging.info(f"New user created with apiKey: {api}")

    return {"message": "User created", "apikey": api}

if __name__ == '__main__':
    logging.info("Starting the FastAPI application")
    uvicorn.run("main:app", host="0.0.0.0", port=5000, workers=2)
