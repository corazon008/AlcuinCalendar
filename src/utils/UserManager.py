import json
from pathlib import Path
from utils.VARS import USERS_FILE


class UserManager:
    def __init__(self, file_path: str | Path = USERS_FILE):
        self.file_path: Path = Path(file_path)
        self.users: dict[str, dict[str, str]] = {}

        if self.file_path.exists():
            self.load()
        else:
            self.save()  # create an empty file if it doesn't exist

    def load(self):
        """Load users from the JSON file"""
        with open(self.file_path, "r") as f:
            self.users = json.load(f)

    def save(self):
        """Save users to the JSON file"""
        with open(self.file_path, "w") as f:
            json.dump(self.users, f, indent=2)

    def add_user(self, username: str, password: str, token: str):
        """Add a new user"""
        self.users[token] = {"username": username, "password": password}
        self.save()

    def remove_user(self, token: str):
        """Remove an existing user"""
        if token in self.users:
            del self.users[token]
            self.save()
        else:
            raise KeyError(f"Token '{token}' not found.")

    def get_user(self, token: str) -> dict[str, str]:
        """Get user info by username"""
        return self.users.get(token)

    def list_tokens(self) -> list[str]:
        """Return a list of all usernames"""
        return list(self.users.keys())

    def user_exists_username(self, username: str) -> bool:
        """Check if a user exists by token"""
        for user in self.users.values():
            if user["username"] == username:
                return True
        return False

    def user_exists_token(self, token: str) -> bool:
        """Check if a user exists by token"""
        return token in self.users


if __name__ == "__main__":
    users = UserManager()
    users.add_user("testuser", "testpass", "testtoken")
    print(users.list_tokens())
    print(users.get_user("testtoken"))
    users.remove_user("testtoken")
    print(users.list_tokens())
