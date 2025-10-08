from apscheduler.schedulers.background import BackgroundScheduler

import API
from utils.UserManager import UserManager
from utils import utils

def refresh_calendars():
    print("Refreshing calendars...")
    users = UserManager()
    for token, username, password in users:
        print(f"Refreshing calendar for user {username}")
        utils.refresh_calendars(token, username, password)
    print("Calendars refreshed.")

scheduler = BackgroundScheduler()
# everyday at 2
scheduler.add_job(refresh_calendars, 'cron', hour=2, minute=0)
scheduler.start()


if __name__ == '__main__':
    API.app.run(host='0.0.0.0', port=5000)
