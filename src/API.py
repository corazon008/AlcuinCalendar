import os
import hashlib
import logging
import sys
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, request, jsonify, Response

from scraper.RefreshQueue import RefreshQueue
from utils.UserManager import UserManager
from utils.VARS import SECRETS_FOLDER, BASE_DIR, CALENDAR_FOLDER
from utils.utils import get_agenda_ics

app = Flask(__name__)

CACHE_DURATION = int(os.getenv("CALENDAR_CACHE_SECONDS", "3600"))  # 1 heure
REFRESH_JOB_ID = "refresh_all_calendars"


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")


# Global logging config (Docker-friendly)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

users = UserManager()
refresh_queue = RefreshQueue()
refresh_queue.start()  # start background worker


# ---------------------------------------------------------------------
# Scheduled refresh
# ---------------------------------------------------------------------
def refresh_all_calendars():
    """Queue a scrape for every registered user."""
    logger.info("Scheduled refresh: queueing calendars...")
    queued = 0
    for token, username, password in users:
        try:
            if refresh_queue.add_task(token, username, password):
                queued += 1
        except Exception:
            logger.error(
                f"Failed to queue refresh for {username}", exc_info=True
            )
    logger.info(f"Scheduled refresh done: {queued} task(s) queued.")


REFRESH_ENABLED = _env_flag("REFRESH_ENABLED", True)
REFRESH_TIMEZONE = os.getenv("REFRESH_TIMEZONE", "Europe/Paris")
REFRESH_CRON = os.getenv("REFRESH_CRON")  # e.g. "0 2 * * *"

scheduler = BackgroundScheduler(timezone=REFRESH_TIMEZONE)
if REFRESH_ENABLED:
    try:
        if REFRESH_CRON:
            trigger = CronTrigger.from_crontab(
                REFRESH_CRON, timezone=REFRESH_TIMEZONE
            )
        else:
            trigger = CronTrigger(
                hour=int(os.getenv("REFRESH_HOUR", "2")),
                minute=int(os.getenv("REFRESH_MINUTE", "0")),
                timezone=REFRESH_TIMEZONE,
            )
        scheduler.add_job(
            refresh_all_calendars,
            trigger,
            id=REFRESH_JOB_ID,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()
        next_run = scheduler.get_job(REFRESH_JOB_ID).next_run_time
        logger.info(
            f"APScheduler started (next refresh: {next_run.isoformat()})"
        )
    except Exception:
        logger.error(
            "Could not start scheduler; periodic refresh disabled",
            exc_info=True,
        )
else:
    logger.info("Periodic refresh disabled (REFRESH_ENABLED=false)")


# default route
@app.route("/")
def index():
    html_path = os.path.join(BASE_DIR, "src", "pages", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    return Response(html, mimetype="text/html")


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok", "queue": refresh_queue.status()})


@app.route("/register")
def register():
    username = request.args.get("username")
    password = request.args.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    if username.endswith("@esaip.org"):
        username = username.replace("@esaip.org", "")

    token_source = f"{username}:{password}:{os.urandom(8)}"
    token = hashlib.sha256(token_source.encode()).hexdigest()[:16]

    if users.user_exists_username(username):
        return jsonify({"error": "Username already exists"}), 400

    users.add_user(username, password, token)
    refresh_queue.add_task(token, username, password)

    return jsonify(
        {
            "token": token,
            "message": "User registered successfully; calendar refresh queued.",
        }
    )


def _calendar_response(ical: bytes, token: str) -> Response:
    """Return the ICS with validators so clients (Nextcloud) can refresh cheaply."""
    etag = f'"{hashlib.sha256(ical).hexdigest()}"'
    ics_path = CALENDAR_FOLDER / f"{token}.ics"
    last_modified = datetime.fromtimestamp(
        ics_path.stat().st_mtime, timezone.utc
    ).replace(microsecond=0)

    headers = {
        "ETag": etag,
        "Last-Modified": format_datetime(last_modified, usegmt=True),
        "Cache-Control": f"public, max-age={CACHE_DURATION}",
    }

    # Conditional request handling (304 = unchanged, client keeps its copy).
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match and etag in [
        value.strip() for value in if_none_match.split(",")
    ]:
        return Response(status=304, headers=headers)

    if_modified_since = request.headers.get("If-Modified-Since")
    if if_modified_since:
        try:
            since = parsedate_to_datetime(if_modified_since)
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)
            if last_modified <= since.astimezone(timezone.utc):
                return Response(status=304, headers=headers)
        except (TypeError, ValueError):
            pass

    return Response(
        ical,
        mimetype="text/calendar",
        headers=headers,
    )


@app.route("/agenda.ics")
def agenda():
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "Missing token"}), 401

    if not users.user_exists_token(token):
        return jsonify({"error": "Invalid token"}), 401

    # Open ics file
    if (ical := get_agenda_ics(token)) is False:
        return "ICS file not found", 404

    return _calendar_response(ical, token)


@app.route("/agenda/<token>.ics")
def agenda_token(token):
    if not token:
        return jsonify({"error": "Missing token"}), 401

    if not users.user_exists_token(token):
        return jsonify({"error": "Invalid token"}), 401

    # Open ics file
    if (ical := get_agenda_ics(token)) is False:
        return "ICS file not found", 404

    return _calendar_response(ical, token)


@app.route("/refresh")
def refresh():
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "Missing token"}), 401

    if not users.user_exists_token(token):
        return jsonify({"error": "Invalid token"}), 401

    user = users.get_user(token)
    username = user["username"]
    password = user["password"]

    if refresh_queue.add_task(token, username, password):
        return jsonify({"message": "Calendar refresh queued."}), 200
    return jsonify({"message": "Calendar refresh already queued/running."}), 202


@app.route("/queue_status")
def queue_status():
    """Expose queue and scheduler state."""
    job = scheduler.get_job(REFRESH_JOB_ID) if REFRESH_ENABLED else None
    status = refresh_queue.status()
    status.update(
        {
            "scheduler_enabled": REFRESH_ENABLED,
            "scheduler_timezone": REFRESH_TIMEZONE,
            "next_refresh": (
                job.next_run_time.isoformat()
                if job and job.next_run_time
                else None
            ),
        }
    )
    return jsonify(status)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
