import os

import pytest

from clients.user_api_client import UserApiClient
from utils.data import build_user_payload, unique_email


class TestUsersList:
    """GET /users"""

    def test_returns_all_created_users(self, user_client, created_user):
        created_emails = []
        for i in range(5):
            payload = build_user_payload()
            response = user_client.create_user(payload)
            created_user(payload["email"])
            created_emails.append(payload["email"])

            assert response.status_code == 201
            assert response.json()["email"] == payload["email"]
            assert response.json()["name"] == payload["name"]
            assert response.json()["age"] == payload["age"]

        response = user_client.get_users()
        assert response.status_code == 200
        returned_emails = {user["email"] for user in response.json()}
        for email in created_emails:
            assert email in returned_emails


class TestUsersCreate:
    """POST /users"""

    def test_returns_201_with_created_user(self, user_client, created_user):
        payload = build_user_payload()

        response = user_client.create_user(payload)
        created_user(payload["email"])

        assert response.status_code == 201
        body = response.json()
        assert body == payload

    def test_returns_400_if_user_data_is_missing(self, user_client):
        response = user_client.create_user({})
        assert response.status_code == 400
        assert response.json()["error"] == "name is required"

    def test_returns_400_if_name_is_missing(self, user_client):
        response = user_client.create_user({"email": unique_email(), "age": 30})
        assert response.status_code == 400
        assert response.json()["error"] == "name is required"

    def test_returns_400_if_email_is_missing(self, user_client):
        response = user_client.create_user({"name": "Test User", "age": 30})
        assert response.status_code == 400
        assert response.json()["error"] == "email is required"

    def test_returns_400_if_age_is_missing(self, user_client):
        response = user_client.create_user({"email": unique_email(), "name": "Test User"})
        assert response.status_code == 400
        assert response.json()["error"] == "age is required"

    def test_returns_201_if_age_is_exactly_1(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user({"email": payload["email"], "name": "Test User", "age": 1})
        created_user(payload["email"])
        assert response.status_code == 201
        assert response.json()["age"] == 1

    def test_returns_201_if_age_is_exactly_150(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user({"email": payload["email"], "name": "Test User", "age": 150})
        created_user(payload["email"])
        assert response.status_code == 201
        assert response.json()["age"] == 150

    def test_returns_400_if_age_is_negative(self, user_client):
        response = user_client.create_user({"email": unique_email(), "name": "Test User", "age": -1})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    def test_returns_400_if_age_is_float(self, user_client):
        response = user_client.create_user({"email": unique_email(), "name": "Test User", "age": 1.5})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    def test_returns_400_if_age_is_string(self, user_client):
        response = user_client.create_user({"email": unique_email(), "name": "Test User", "age": "30"})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    def test_returns_400_if_age_is_null(self, user_client):
        response = user_client.create_user({"email": unique_email(), "name": "Test User", "age": None})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    def test_returns_400_if_age_is_out_of_range(self, user_client):
        response = user_client.create_user({"email": unique_email(), "name": "Test User", "age": 0})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    def test_returns_400_if_age_is_out_of_limit(self, user_client):
        response = user_client.create_user({"email": unique_email(), "name": "Test User", "age": 151})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    def test_returns_400_if_name_is_null(self, user_client):
        response = user_client.create_user({"email": unique_email(), "name": None, "age": 30})
        assert response.status_code == 400
        assert response.json()["error"] == "name is required"

    def test_returns_400_if_name_is_empty(self, user_client):
        response = user_client.create_user({"email": unique_email(), "name": "", "age": 30})
        assert response.status_code == 400
        assert response.json()["error"] == "name is required"

    def test_returns_400_if_email_is_null(self, user_client):
        response = user_client.create_user({"email": None, "name": "Test User", "age": 30})
        assert response.status_code == 400
        assert response.json()["error"] == "email is required"

    def test_returns_400_if_email_is_empty(self, user_client):
        response = user_client.create_user({"email": "", "name": "Test User", "age": 30})
        assert response.status_code == 400
        assert response.json()["error"] == "email is required"

    def test_returns_400_if_age_is_empty(self, user_client):
        response = user_client.create_user({"email": unique_email(), "name": "Test User", "age": ""})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    @pytest.mark.xfail(
        reason="BUG CRT-002: email format isn't being validated, malformed addresses go through",
        strict=True,
    )
    def test_returns_400_if_email_is_invalid_format(self, user_client):
        response = user_client.create_user({"email": "not-an-email", "name": "Test User", "age": 30})
        assert response.status_code == 400
        assert response.json()["error"] == "Email must be a valid email address"

    @pytest.mark.xfail(
        reason="BUG CRT-003: name type isn't checked",
        strict=True,
    )
    def test_returns_400_if_name_is_wrong_type(self, user_client, created_user):
        email = unique_email()
        response = user_client.create_user({"email": email, "name": 123, "age": 30})
        created_user(email)
        assert response.status_code == 400
        assert "error" in response.json()

    @pytest.mark.xfail(
        reason="BUG CRT-004: email type isn't checked",
        strict=True,
    )
    def test_returns_400_if_email_is_wrong_type(self, user_client, created_user):
        response = user_client.create_user({"email": 42, "name": "Test User", "age": 30})
        created_user(42)
        assert response.status_code == 400
        assert "error" in response.json()

    @pytest.mark.xfail(
        reason="BUG CRT-001: posting a duplicate email crashes with a 500 instead of returning 409",
        strict=True,
    )
    def test_returns_409_if_email_already_exists(self, user_client, created_user):
        payload = build_user_payload()
        existing_user = user_client.create_user(payload)
        created_user(payload["email"])
        assert existing_user.status_code == 201
        assert existing_user.json()["email"] == payload["email"]

        new_user = user_client.create_user({"email": payload["email"], "name": "Test User", "age": 30})
        assert new_user.status_code == 409
        assert new_user.json()["error"] == "Email already exists"


class TestUserGet:
    """GET /users/{email}"""

    def test_returns_user_after_create(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.get_user(payload["email"])
        assert response.status_code == 200
        assert response.json()["email"] == payload["email"]
        assert response.json()["name"] == payload["name"]
        assert response.json()["age"] == payload["age"]

    @pytest.mark.xfail(
        reason="BUG GET-001: looking up an email that doesn't exist doesn't come back as a 404",
        strict=True,
    )
    def test_returns_404_if_user_not_found(self, user_client):
        response = user_client.get_user(unique_email())
        assert response.status_code == 404
        assert response.json()["error"] == "User not found"

    @pytest.mark.xfail(
        reason="BUG PATH-001: server doesn't validate that the path email is a real email",
        strict=True,
    )
    def test_returns_400_if_path_email_invalid_format(self, user_client):
        response = user_client.get_user("not-an-email")
        assert response.status_code == 400


class TestUserUpdate:
    """PUT /users/{email}"""

    def test_returns_200_with_valid_data(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        new_payload = {
            "email": unique_email(),
            "name": "New Name",
            "age": 31,
        }

        response = user_client.update_user(payload["email"], new_payload)

        assert response.status_code == 200
        assert response.json()["email"] == new_payload["email"]
        assert response.json()["name"] == new_payload["name"]
        assert response.json()["age"] == new_payload["age"]

    def test_returns_404_if_user_not_found(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user("nonexistent@example.com", {"email": unique_email(), "name": "Test User", "age": 30})
        assert response.status_code == 404
        assert response.json()["error"] == "User not found"

    def test_returns_400_if_payload_is_missing(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {})
        assert response.status_code == 400
        assert response.json()["error"] == "name is required"

    def test_returns_400_if_name_is_missing(self, user_client):
        response = user_client.update_user(unique_email(), {"email": unique_email(), "age": 30})
        assert response.status_code == 400
        assert response.json()["error"] == "name is required"

    def test_returns_400_if_age_is_missing(self, user_client):
        response = user_client.update_user(unique_email(), {"email": unique_email(), "name": "Test User"})
        assert response.status_code == 400
        assert response.json()["error"] == "age is required"

    def test_returns_400_if_email_is_missing(self, user_client):
        response = user_client.update_user(unique_email(), {"name": "Test User", "age": 30})
        assert response.status_code == 400
        assert response.json()["error"] == "email is required"

    def test_returns_400_if_age_is_out_of_range(self, user_client):
        response = user_client.update_user(unique_email(), {"email": unique_email(), "name": "Test User", "age": 0})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    def test_returns_400_if_age_is_greater_than_limit(self, user_client):
        response = user_client.update_user(unique_email(), {"email": unique_email(), "name": "Test User", "age": 151})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    def test_returns_409_if_email_is_duplicate(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        affected_user_payload = build_user_payload()
        affected_user = user_client.create_user(affected_user_payload)
        created_user(affected_user_payload["email"])

        response = user_client.update_user(payload["email"], {"email": affected_user_payload["email"], "name": "Test User", "age": 30})
        assert response.status_code == 409
        assert response.json()["error"] == "Email already exists"

    def test_returns_200_if_email_is_the_same_for_same_user(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": payload["email"], "name": "Test User", "age": 30})
        assert response.status_code == 200

    def test_returns_200_if_age_is_exactly_1(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": payload["email"], "name": "Test User", "age": 1})
        assert response.status_code == 200
        assert response.json()["age"] == 1

    def test_returns_200_if_age_is_exactly_150(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": payload["email"], "name": "Test User", "age": 150})
        assert response.status_code == 200
        assert response.json()["age"] == 150

    def test_returns_400_if_age_is_negative(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": payload["email"], "name": "Test User", "age": -1})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    def test_returns_400_if_age_is_float(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": payload["email"], "name": "Test User", "age": 1.5})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    def test_returns_400_if_age_is_string(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": payload["email"], "name": "Test User", "age": "30"})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    def test_returns_400_if_name_is_null(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": unique_email(), "name": None, "age": 30})
        assert response.status_code == 400
        assert response.json()["error"] == "name is required"

    def test_returns_400_if_email_is_null(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": None, "name": "Test User", "age": 30})
        assert response.status_code == 400
        assert response.json()["error"] == "email is required"

    def test_returns_400_if_age_is_null(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": payload["email"], "name": "Test User", "age": None})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    def test_returns_400_if_name_is_empty(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": payload["email"], "name": "", "age": 30})
        assert response.status_code == 400
        assert response.json()["error"] == "name is required"

    def test_returns_400_if_email_is_empty(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": "", "name": "Test User", "age": 30})
        assert response.status_code == 400
        assert response.json()["error"] == "email is required"

    def test_returns_400_if_age_is_empty(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": unique_email(), "name": "Test User", "age": ""})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    def test_returns_400_if_age_is_invalid(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": payload["email"], "name": "Test User", "age": "a"})
        assert response.status_code == 400
        assert response.json()["error"] == "Age must be between 1 and 150"

    @pytest.mark.xfail(
        reason="BUG UPD-001: email format validation is also missing on PUT",
        strict=True,
    )
    def test_returns_400_if_email_is_invalid_format(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": "not-an-email", "name": "Test User", "age": 30})
        assert response.status_code == 400
        assert response.json()["error"] == "Email must be a valid email address"

    @pytest.mark.xfail(
        reason="BUG UPD-002: PUT happily accepts a non-string name and updates the record",
        strict=True,
    )
    def test_returns_400_if_name_is_wrong_type(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.update_user(payload["email"], {"email": payload["email"], "name": 123, "age": 30})
        assert response.status_code == 400
        assert "error" in response.json()

    @pytest.mark.xfail(
        reason="BUG UPD-003: same problem for email on PUT — a number gets stored as the new email",
        strict=True,
    )
    def test_returns_400_if_email_is_wrong_type(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])
        created_user(42)

        response = user_client.update_user(payload["email"], {"email": 42, "name": "Test User", "age": 30})
        assert response.status_code == 400
        assert "error" in response.json()


class TestUserDelete:
    """DELETE /users/{email}"""

    def test_returns_204_with_deleted_user(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.delete_user(payload["email"])
        assert response.status_code == 204

    def test_returns_404_if_user_not_found(self, user_client):
        payload = build_user_payload()

        response = user_client.delete_user(payload["email"])
        assert response.status_code == 404

    @pytest.mark.xfail(
        reason="BUG DEL-001: an invalid auth token still gets accepted and the delete goes through",
        strict=True,
    )
    def test_returns_401_if_authentication_is_invalid(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.delete_user(payload["email"], token="invalid")
        assert response.status_code == 401

    @pytest.mark.xfail(
        reason="BUG DEL-002: delete works even when no auth header is sent at all",
        strict=True,
    )
    def test_returns_401_when_authentication_is_missing(self, user_client, created_user):
        payload = build_user_payload()
        response = user_client.create_user(payload)
        created_user(payload["email"])

        response = user_client.delete_user(payload["email"], token=None)
        assert response.status_code == 401


class TestEnvironmentIsolation:
    """Cross-environment isolation between /dev and /prod"""

    def test_user_created_in_dev_is_not_visible_in_prod(self):
        api_host = os.getenv("API_HOST", "http://localhost:3000").rstrip("/")
        dev = UserApiClient(f"{api_host}/dev")
        prod = UserApiClient(f"{api_host}/prod")

        payload = build_user_payload()
        try:
            create = dev.create_user(payload)
            assert create.status_code == 201

            prod_users = prod.get_users()
            assert prod_users.status_code == 200
            prod_emails = {u["email"] for u in prod_users.json()}
            assert payload["email"] not in prod_emails, (
                "Env isolation broken: user created in /dev appeared in /prod"
            )
        finally:
            dev.delete_user(payload["email"])
