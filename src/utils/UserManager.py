import json
import threading
from pathlib import Path
from typing import Iterable, Dict

from utils.VARS import USERS_FILE


class UserManager:
    """
    Singleton class to manage user credentials stored in a JSON file.
    Provides thread-safe read/write operations for concurrent access.
    """

    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(UserManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, file_path: str | Path = USERS_FILE):
        if self._initialized:
            return  # prevent re-init (singleton)
        self.file_path: Path = Path(file_path)
        self.users: Dict[str, Dict[str, str]] = {}

        if self.file_path.exists():
            self.load()
        else:
            self.file_path.write_text(json.dumps({}, indent=2))

        self._initialized = True

    # ----------------------------------------------------------------------
    # File operations
    # ----------------------------------------------------------------------

    def load(self) -> None:
        """Load all users from the JSON file."""
        with self._lock:
            with open(self.file_path, "r") as f:
                try:
                    self.users = json.load(f)
                except json.JSONDecodeError:
                    self.users = {}  # recover from corrupted file

    def save(self) -> None:
        """Write current users to the JSON file."""
        with self._lock:
            with open(self.file_path, "w") as f:
                json.dump(self.users, f, indent=2)

    # ----------------------------------------------------------------------
    # User operations
    # ----------------------------------------------------------------------

    def add_user(self, username: str, password: str, token: str) -> None:
        """Add a new user entry."""
        self.users[token] = {"username": username, "password": password}
        self.save()

    def remove_user(self, token: str) -> None:
        """Remove a user entry by token."""
        if token not in self.users:
            raise KeyError(f"Token '{token}' not found.")
        del self.users[token]
        self.save()

    def get_user(self, token: str) -> Dict[str, str] | None:
        """Get user info by token."""
        return self.users.get(token)

    def list_tokens(self) -> list[str]:
        """Return a list of all user tokens."""
        return list(self.users.keys())

    def user_exists_username(self, username: str) -> bool:
        """Check if a user exists by username."""
        return any(u["username"] == username for u in self.users.values())

    def user_exists_token(self, token: str) -> bool:
        """Check if a user exists by token."""
        return token in self.users

    def __iter__(self) -> Iterable[tuple[str, str, str]]:
        """Iterate over all users as (token, username, password) tuples."""
        for token, user in self.users.items():
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
