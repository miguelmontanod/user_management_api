# Known bugs

Defects in the User Management API where its behavior diverges from the specs. Each bug is exposed by a test marked `@pytest.mark.xfail(strict=True)` in [tests/test_users.py](tests/test_users.py).

`strict=True` means the suite *fails* if any of these tests starts passing. That's a reminder to come back here and remove the marker once the API is fixed.

This is the set surfaced by the current test coverage. It is not an exhaustive audit of the API, more probing (response schema strictness, length limits, concurrency, etc.) would likely turn up additional issues.

## Summary

| ID | Severity | Endpoint | Defect |
|---|---|---|---|
| [CRT-001](#crt-001--post-users-returns-500-on-duplicate-email) | Medium | `POST /users` | 500 instead of 409 on duplicate email |
| [CRT-002](#crt-002--post-users-does-not-validate-email-format) | Low | `POST /users` | `format: email` not enforced |
| [CRT-003](#crt-003--post-users-accepts-non-string-name) | Medium | `POST /users` | `name` accepts non-string types |
| [CRT-004](#crt-004--post-users-accepts-non-string-email) | Medium | `POST /users` | `email` accepts non-string types |
| [GET-001](#get-001--get-usersemail-does-not-return-404-for-missing-user) | Medium | `GET /users/{email}` | 404 not returned for missing user |
| [PATH-001](#path-001--get-usersemail-does-not-validate-the-path-email-format) | Low | `GET /users/{email}` | Path `email` format not validated |
| [UPD-001](#upd-001--put-usersemail-does-not-validate-email-format) | Low | `PUT /users/{email}` | `format: email` not enforced |
| [UPD-002](#upd-002--put-usersemail-accepts-non-string-name) | Medium | `PUT /users/{email}` | `name` accepts non-string types |
| [UPD-003](#upd-003--put-usersemail-accepts-non-string-email) | Medium | `PUT /users/{email}` | `email` accepts non-string types |

To re-run only the bug-exposing tests:

```bash
python -m pytest -rx tests/test_users.py
```

The `-rx` flag prints a one-line reason for each `XFAIL` in the summary.

---

## CRT-001 — `POST /users` returns 500 on duplicate email

**Endpoint:** `POST /users`
**Severity:** Medium

**Spec:** Should return `409 Duplicate email` with an `ErrorResponse` body when a user with the same email already exists.

**Actual:** Returns `500 Internal Server Error`. The duplicate-email path isn't handled, looks like the constraint violation just bubbles up.

**Reproduction:** Create any user, then `POST /users` again with the same email.

**Test:** `tests/test_users.py::TestUsersCreate::test_returns_409_if_email_already_exists`

Clients can't tell whether the email is taken or the server crashed. 500s also tend to leak stack traces in the body.

---

## CRT-002 — `POST /users` does not validate email format

**Endpoint:** `POST /users`
**Severity:** Low

**Spec:** `email` is `type: string, format: email`. Malformed values should be rejected with `400`.

**Actual:** Strings that aren't valid emails (e.g. `"not-an-email"`) are accepted, the server returns `201` and stores the user.

**Reproduction:** `POST /users` with body `{"email": "not-an-email", "name": "Test User", "age": 30}`.

**Test:** `tests/test_users.py::TestUsersCreate::test_returns_400_if_email_is_invalid_format`

Anything that needs a deliverable email later (notifications, password resets, etc.) will silently break or send to garbage addresses.

---

## CRT-003 — `POST /users` accepts non-string `name`

**Endpoint:** `POST /users`
**Severity:** Medium

**Spec:** `name` is `type: string, required: true`.

**Actual:** A numeric `name` (e.g. `123`) is accepted and the user is created.

**Reproduction:** `POST /users` with body `{"email": "<unique>", "name": 123, "age": 30}`.

**Test:** `tests/test_users.py::TestUsersCreate::test_returns_400_if_name_is_wrong_type`

Anything that treats `name` as a string later (sorting, formatting, calling `.upper()`) will break or behave inconsistently depending on what got stored.

---

## CRT-004 — `POST /users` accepts non-string `email`

**Endpoint:** `POST /users`
**Severity:** Medium

**Spec:** `email` is `type: string, format: email`.

**Actual:** A numeric `email` (e.g. `42`) is accepted, the user is created.

**Reproduction:** `POST /users` with body `{"email": 42, "name": "Test User", "age": 30}`.

**Test:** `tests/test_users.py::TestUsersCreate::test_returns_400_if_email_is_wrong_type`

Email is the resource's primary key. A non-string PK breaks path lookups (is `/users/42` the same as `/users/"42"`?) and confuses any client expecting a string.

---

## GET-001 — `GET /users/{email}` does not return 404 for missing user

**Endpoint:** `GET /users/{email}`
**Severity:** Medium

**Spec:** Should return `404 User not found` with an `ErrorResponse` body when the email does not exist.

**Actual:** A different status / body is returned, not `404`.

**Reproduction:** `GET /users/<email-that-was-never-created>`.

**Test:** `tests/test_users.py::TestUserGet::test_returns_404_if_user_not_found`

Clients can't tell "no such user" apart from any other failure mode, which breaks the standard REST contract.

---

## PATH-001 — `GET /users/{email}` does not validate the path email format

**Endpoint:** `GET /users/{email}`
**Severity:** Low

**Spec:** The path parameter `email` is `type: string, format: email`. A malformed value should be rejected with `400`.

**Actual:** A clearly malformed value like `not-an-email` is accepted by the routing layer, the request reaches the handler and gets treated as a "missing user" lookup.

**Reproduction:** `GET /users/not-an-email`.

**Test:** `tests/test_users.py::TestUserGet::test_returns_400_if_path_email_invalid_format`

Same theme as CRT-002 / UPD-001, format validation is missing on the path too. Low severity on its own, but it confirms the pattern: nothing in this API validates email format anywhere.

---

## UPD-001 — `PUT /users/{email}` does not validate email format

**Endpoint:** `PUT /users/{email}`
**Severity:** Low

**Spec:** Same `email` constraint as POST, `type: string, format: email`.

**Actual:** Malformed emails in the request body are accepted on update.

**Reproduction:** Create a user, then `PUT /users/<email>` with body `{"email": "not-an-email", "name": "Test User", "age": 30}`.

**Test:** `tests/test_users.py::TestUserUpdate::test_returns_400_if_email_is_invalid_format`

Same downstream impact as CRT-002, plus an existing user can now be silently mutated to have an unreachable address.

---

## UPD-002 — `PUT /users/{email}` accepts non-string `name`

**Endpoint:** `PUT /users/{email}`
**Severity:** Medium

**Spec:** `name` is `type: string, required: true`.

**Actual:** A numeric `name` is accepted on update, the record is mutated.

**Reproduction:** Create a user, then `PUT /users/<email>` with body `{"email": "<email>", "name": 123, "age": 30}`.

**Test:** `tests/test_users.py::TestUserUpdate::test_returns_400_if_name_is_wrong_type`

Same type-confusion concern as CRT-003. Worse here because an existing valid user gets corrupted in place.

---

## UPD-003 — `PUT /users/{email}` accepts non-string `email`

**Endpoint:** `PUT /users/{email}`
**Severity:** Medium

**Spec:** `email` is `type: string, format: email`.

**Actual:** A numeric `email` is stored as the new email after a PUT. The original email no longer maps to the record.

**Reproduction:** Create a user, then `PUT /users/<email>` with body `{"email": 42, "name": "Test User", "age": 30}`.

**Test:** `tests/test_users.py::TestUserUpdate::test_returns_400_if_email_is_wrong_type`

Same primary-key concern as CRT-004. Mutating a user this way leaves it in a state where the old email no longer maps to it, and the new value may not be reachable as a path param either.

---

## Intentional environment differences (not bugs)

`DELETE /users/{email}` returns `204` in `/dev` regardless of the `Authentication` header (invalid or missing). This was initially flagged as a bug but is an intentional development convenience, the auth contract is enforced as the spec requires in `/prod`. The two corresponding tests are marked with `pytest.mark.skipif(API_ENV=='dev', ...)` so they skip in dev and run normally against prod:

- `tests/test_users.py::TestUserDelete::test_returns_401_if_authentication_is_invalid`
- `tests/test_users.py::TestUserDelete::test_returns_401_when_authentication_is_missing`
