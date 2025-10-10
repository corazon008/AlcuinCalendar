import sys
import time
import queue
import logging
import threading
import traceback
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

        self._initialized = True
        self.logger.info("RefreshQueue initialized")

    def start(self):
        """Start the worker thread (only once)."""
        if not self._is_running:
            self.logger.info("Starting RefreshQueue worker thread")
            self._is_running = True
            self._worker_thread.start()

    def add_task(self, token: str, username: str, password: str):
        """Add a new task to the queue."""
        try:
            self.queue.put_nowait((token, username, password))
            self.logger.info(f"Task queued for user '{username}' (queue size={self.queue.qsize()})")
        except queue.Full:
            self.logger.warning(f"Queue is full, could not add task for '{username}'")

    def _worker_loop(self):
        """Main worker loop: process tasks sequentially."""
        while True:
            token, username, password = self.queue.get()
            try:
                self.logger.info(f"[→] Starting refresh for {username}")

                # Run the Selenium job in a separate process
                p = Process(target=self._run_task, args=(token, username, password))
                p.start()
                p.join()  # Sequential: only one Selenium session at a time

                self.logger.info(f"[✓] Calendar for {username} updated successfully")
            except Exception:
                self.logger.error(f"Error while refreshing calendar for {username}:\n{traceback.format_exc()}")
            finally:
                self.queue.task_done()
                time.sleep(self.sleep_interval)

    def _run_task(self, token: str, username: str, password: str):
        """Run the actual Selenium task in a separate process."""
        try:
            refresh_calendars(token, username, password)
        except Exception as e:
            self.logger.error(f"[Process Error] {username}: {e}")

    def status(self) -> dict:
        """Return current queue status."""
        return {
            "pending_tasks": self.queue.qsize(),
            "is_running": self._is_running
        }
