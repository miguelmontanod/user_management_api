import requests


class UserApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def get_user(self, user_id: int):
        return requests.get(f"{self.base_url}/users/{user_id}")

    def get_users(self):
        return requests.get(f"{self.base_url}/users")

    def create_user(self, payload: dict):
        return requests.post(f"{self.base_url}/users", json=payload)

    def update_user(self, email: str, payload: dict):
        return requests.put(f"{self.base_url}/users/{email}", json=payload)

    def delete_user(self, email, token="mysecrettoken"):
        headers = {"Authentication": token} if token is not None else {}
        return requests.delete(
            f"{self.base_url}/users/{email}",
            headers=headers,
        )