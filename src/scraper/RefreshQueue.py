import sys
import time
import queue
import logging
import threading
import traceback
from datetime import datetime, timezone
from multiprocessing import Process

from utils.utils import refresh_calendars


class RefreshQueue:
    """
    Singleton task queue for Selenium-based calendar refresh jobs.
    Each task runs in a separate process for isolation.
    """

    _instance = None
    _initialized = False  # Prevent __init__ from running multiple times

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, sleep_interval: float = 1.0, max_queue_size: int = 0):
        """
        :param sleep_interval: time to sleep between tasks (default: 1s)
        :param max_queue_size: maximum number of queued tasks (0 = unlimited)
        """

        if self._initialized:
            return  # Avoid reinitializing the singleton

        self.queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self.sleep_interval = sleep_interval
        self._is_running = False
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)

        # Queue bookkeeping (used to dedupe tasks and expose status).
        self._lock = threading.Lock()
        self._pending_tokens: set[str] = set()
        self._running_token: str | None = None
        self._last_refresh: dict[str, str] = {}

        self.logger = logging.getLogger("RefreshQueue")
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        # Logging is already configured at application level; avoid duplicate lines.
        self.logger.propagate = False

        self._initialized = True
        self.logger.info("RefreshQueue initialized")

    def start(self):
        """Start the worker thread (only once)."""
        if not self._is_running:
            self.logger.info("Starting RefreshQueue worker thread")
            self._is_running = True
            self._worker_thread.start()

    def add_task(self, token: str, username: str, password: str) -> bool:
        """Add a new task to the queue. Returns False if it was already queued."""
        with self._lock:
            if token in self._pending_tokens or token == self._running_token:
                self.logger.info(f"Refresh already queued/running for '{username}', skipping")
                return False
            self._pending_tokens.add(token)

        try:
            self.queue.put_nowait((token, username, password))
            self.logger.info(f"Task queued for user '{username}' (queue size={self.queue.qsize()})")
            return True
        except queue.Full:
            with self._lock:
                self._pending_tokens.discard(token)
            self.logger.warning(f"Queue is full, could not add task for '{username}'")
            return False

    def _worker_loop(self):
        """Main worker loop: process tasks sequentially."""
        while True:
            token, username, password = self.queue.get()
            with self._lock:
                self._running_token = token
            try:
                self.logger.info(f"[→] Starting refresh for {username}")

                # Run the Selenium job in a separate process
                p = Process(target=self._run_task, args=(token, username, password))
                p.start()
                p.join()  # Sequential: only one Selenium session at a time

                if p.exitcode == 0:
                    with self._lock:
                        self._last_refresh[token] = datetime.now(timezone.utc).isoformat()
                    self.logger.info(f"[✓] Calendar for {username} updated successfully")
                else:
                    self.logger.error(
                        f"[✗] Calendar refresh failed for {username} (exit code {p.exitcode}); "
                        "previous calendar file kept"
                    )
            except Exception:
                self.logger.error(f"Error while refreshing calendar for {username}:\n{traceback.format_exc()}")
            finally:
                with self._lock:
                    self._running_token = None
                    self._pending_tokens.discard(token)
                self.queue.task_done()
                time.sleep(self.sleep_interval)

    def _run_task(self, token: str, username: str, password: str):
        """Run the actual Selenium task in a separate process."""
        try:
            if not refresh_calendars(token, username, password):
                raise SystemExit(1)
        except Exception as e:
            self.logger.error(f"[Process Error] {username}: {e}")
            raise SystemExit(1)

    def status(self) -> dict:
        """Return current queue status."""
        with self._lock:
            return {
                "pending_tasks": self.queue.qsize(),
                "pending_tokens": sorted(self._pending_tokens),
                "running_token": self._running_token,
                "is_running": self._is_running,
                "last_refresh": dict(self._last_refresh),
            }
