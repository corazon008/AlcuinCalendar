import fastapi.responses
from fastapi import FastAPI
import uvicorn

from AlcuinSelenium import AlcuinSelenium
app = FastAPI()

@app.get("/",
         response_class=fastapi.responses.PlainTextResponse)
async def root(apiKey: str =""):
    if apiKey == "":
        return {"message": "No API key provided"}
    with open(f"Secrets/{apiKey}.ics", "r", encoding="utf-8") as file:
        return file.read()

@app.get("/calendar.ics",
             response_class=fastapi.responses.PlainTextResponse)
async def calendar(apiKey: str =""):
    if apiKey == "":
        return {"message": "No API key provided"}
    with open(f"Secrets/{apiKey}.ics", "r", encoding="utf-8") as file:
        return file.read()

@app.get("/refresh_calendar")
async def refresh_calendar(apiKey: str =""):
    if apiKey == "":
        return {"message": "No API key provided"}
    with open("Secrets/login.txt", "r") as file:
        apiKeys = {key : [username, password] for key, username, password in [line.split(" ") for line in file.readlines()]}
    if apiKey not in apiKeys.keys():
        return {"message": "Invalid API key " + apiKey}
    user = apiKeys[apiKey]
    
    alcuin = AlcuinSelenium(apiKey, *user, headless=True)
    alcuin.GetCalendar()
    return {"message": "Calendar refreshed"}

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=5000, workers=2)
