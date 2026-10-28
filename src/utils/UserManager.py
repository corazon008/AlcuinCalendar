import json
import logging
import threading
from pathlib import Path
from typing import Iterable, Dict

from utils.VARS import USERS_FILE

logger = logging.getLogger(__name__)


class UserManager:
    """
    Singleton class to manage user credentials stored in a JSON file.
    Provides thread-safe read/write operations for concurrent access.

    The file is reloaded automatically when it changes on disk, so users added
    while the container is already running are picked up without a restart.
    """

    _instance = None
    _initialized = False
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(UserManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, file_path: str | Path = USERS_FILE):
        if self._initialized:
            return  # prevent re-init (singleton)
        self.file_path: Path = Path(file_path)
        self.users: Dict[str, Dict[str, str]] = {}
        self._last_mtime: int | None = None

        if self.file_path.exists():
            self.load()
        else:
            self.file_path.write_text(json.dumps({}, indent=2))
            self._last_mtime = self._get_mtime()

        self._initialized = True

    # ----------------------------------------------------------------------
    # File operations
    # ----------------------------------------------------------------------

    def _get_mtime(self) -> int | None:
        try:
            return self.file_path.stat().st_mtime_ns
        except FileNotFoundError:
            return None

    def load(self) -> None:
        """Load all users from the JSON file."""
        with self._lock:
            mtime = self._get_mtime()
            try:
                with open(self.file_path, "r") as f:
                    try:
                        self.users = json.load(f)
                    except json.JSONDecodeError as e:
                        # Keep the current in-memory state: the file may be
                        # half-written or edited by hand. Retry on next access.
                        logger.warning(
                            f"Invalid JSON in {self.file_path}: {e}. Keeping previous users."
                        )
                        return
                self._last_mtime = mtime
            except FileNotFoundError:
                self.users = {}
                self._last_mtime = None

    def reload_if_changed(self) -> bool:
        """Reload the file if it changed on disk. Returns True if reloaded."""
        with self._lock:
            mtime = self._get_mtime()
            if mtime is None or mtime == self._last_mtime:
                return False
            logger.info(f"Users file changed on disk, reloading {self.file_path}")
            self.load()
            return True

    def save(self) -> None:
        """Write current users to the JSON file."""
        with self._lock:
            with open(self.file_path, "w") as f:
                json.dump(self.users, f, indent=2)
            self._last_mtime = self._get_mtime()

    # ----------------------------------------------------------------------
    # User operations
    # ----------------------------------------------------------------------

    def add_user(self, username: str, password: str, token: str) -> None:
        """Add a new user entry."""
        self.reload_if_changed()
        with self._lock:
            self.users[token] = {"username": username, "password": password}
            self.save()

    def remove_user(self, token: str) -> None:
        """Remove a user entry by token."""
        self.reload_if_changed()
        with self._lock:
            if token not in self.users:
                raise KeyError(f"Token '{token}' not found.")
            del self.users[token]
            self.save()

    def get_user(self, token: str) -> Dict[str, str] | None:
        """Get user info by token."""
        self.reload_if_changed()
        with self._lock:
            return self.users.get(token)

    def list_tokens(self) -> list[str]:
        """Return a list of all user tokens."""
        self.reload_if_changed()
        with self._lock:
            return list(self.users.keys())

    def user_exists_username(self, username: str) -> bool:
        """Check if a user exists by username."""
        self.reload_if_changed()
        with self._lock:
            return any(u["username"] == username for u in self.users.values())

    def user_exists_token(self, token: str) -> bool:
        """Check if a user exists by token."""
        self.reload_if_changed()
        with self._lock:
            return token in self.users

    def count(self) -> int:
        """Return the number of registered users."""
        self.reload_if_changed()
        with self._lock:
            return len(self.users)

    def __iter__(self) -> Iterable[tuple[str, str, str]]:
        """Iterate over all users as (token, username, password) tuples."""
        self.reload_if_changed()
        with self._lock:
            snapshot = list(self.users.items())
        for token, user in snapshot:
            yield token, user["username"], user["password"]

    # ----------------------------------------------------------------------
    # CLI testing
    # ----------------------------------------------------------------------

if __name__ == "__main__":
    users = UserManager()
    users.add_user("testuser", "testpass", "testtoken")
    print(users.list_tokens())
    print(users.get_user("testtoken"))
    users.remove_user("testtoken")
    print(users.list_tokens())
