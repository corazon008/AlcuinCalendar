import fastapi.responses
from fastapi import FastAPI
import uvicorn, os, random

from AlcuinSelenium import AlcuinSelenium
from VARS import *
app = FastAPI()

@app.get("/",
         response_class=fastapi.responses.PlainTextResponse)
async def root(apiKey: str =""):
    if apiKey == "":
        return {"message": "No API key provided"}
    with open(f"{SECRETS_FOLDER}/{apiKey}.ics", "r", encoding="utf-8") as file:
        return file.read()

@app.get("/calendar.ics",
             response_class=fastapi.responses.FileResponse)
async def calendar(apiKey: str =""):
    return f"{SECRETS_FOLDER}/{apiKey}.ics"

@app.get("/refresh_calendar")
async def refresh_calendar(apiKey: str =""):
    if apiKey == "":
        return {"message": "No API key provided"}
    with open(f"{SECRETS_FOLDER}/login.txt", "r") as file:
        apiKeys = {key : [username, password] for key, username, password in [line.split(" ") for line in file.readlines()]}
    if apiKey not in apiKeys.keys():
        return {"message": "Invalid API key " + apiKey}
    user = apiKeys[apiKey]
    
    alcuin = AlcuinSelenium(apiKey, *user, headless=True)
    alcuin.GetCalendar()
    return {"message": "Calendar refreshed"}

@app.get("/create_user")
async def create_user(username: str="", password: str=""):
    #verifier si le dossier existe
    if not os.path.exists(f"{SECRETS_FOLDER}"):
        os.mkdir(f"{SECRETS_FOLDER}")
    if not os.path.exists(f"{SECRETS_FOLDER}/login.txt"):
        with open(f"{SECRETS_FOLDER}/login.txt", "w") as file:
            pass
    #genere une cle api de 12 lettre
    api = ''.join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=12))
    with open(f"{SECRETS_FOLDER}/login.txt", "a") as file:
        file.write(f"{api} {username} {password}\n")
    return {"message": "User created", "apikey": api}

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=5000, workers=2)
