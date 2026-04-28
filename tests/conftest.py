import os
import pytest
from dotenv import load_dotenv

from clients.user_api_client import UserApiClient


@pytest.fixture(scope="session")
def user_client():
    load_dotenv()

    api_host = os.getenv("API_HOST", "http://localhost:3000").rstrip("/")
    api_env = os.getenv("API_ENV", "dev").strip("/")
    base_url = f"{api_host}/{api_env}"

    return UserApiClient(base_url)


@pytest.fixture
def created_user(user_client):
    emails = []
    yield emails.append
    for email in emails:
        user_client.delete_user(email)
