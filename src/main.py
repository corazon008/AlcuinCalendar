import logging
import signal
import sys
from apscheduler.schedulers.background import BackgroundScheduler

import API
from scraper.RefreshQueue import RefreshQueue
from utils.UserManager import UserManager
from utils import utils


# ---------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Background refresh queue
# ---------------------------------------------------------------------
refresh_queue = RefreshQueue()
refresh_queue.start()
logger.info("RefreshQueue started.")


# ---------------------------------------------------------------------
# Job: refresh calendars
# ---------------------------------------------------------------------
def refresh_calendars():
    """Refresh all users' calendars using the Alcuin scraper."""
    logger.info("Refreshing calendars...")

    users = UserManager()
    for token, username, password in users:
        try:
            logger.info(f"Refreshing calendar for user '{username}'...")
            refresh_queue.add_task(token, username, password)
        except Exception as e:
            logger.error(f"Failed to refresh calendar for {username}: {e}", exc_info=True)

    logger.info("All calendars refreshed.")


# ---------------------------------------------------------------------
# Scheduler setup
# ---------------------------------------------------------------------
scheduler = BackgroundScheduler()
# every day at 2
scheduler.add_job(refresh_calendars, 'cron', hour=2, minute=0)
scheduler.start()
logger.info("APScheduler started (daily at 02:00).")


# ---------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------
def shutdown_handler(signum, frame):
    logger.info("Received shutdown signal. Stopping services...")
    scheduler.shutdown(wait=False)
    refresh_queue.stop()  # assuming you have a stop() method
    logger.info("Shutdown complete.")
    sys.exit(0)


signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)


# ---------------------------------------------------------------------
# Flask API entrypoint
# ---------------------------------------------------------------------
if __name__ == '__main__':
    API.app.run(host='0.0.0.0', port=5000)
