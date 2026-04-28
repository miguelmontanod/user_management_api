import uuid

def unique_email():
    return f"test.user.{uuid.uuid4()}@example.com"

def build_user_payload(**overrides):
    payload = {
        "name": "Test User",
        "email": unique_email(),
        "age": 30,
    }

    payload.update(overrides)
    return payload
