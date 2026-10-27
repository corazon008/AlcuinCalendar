"""Development entrypoint.

Production runs `gunicorn API:app` (see Dockerfile), which imports API.py and
therefore starts both the refresh queue and the APScheduler job.
"""

import logging

import API

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.info(
        "Starting development server (scheduler already started by API import)"
    )
    API.app.run(host="0.0.0.0", port=5000)
