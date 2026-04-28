# User Management API — Test Suite

End-to-end test suite for the User Management API. Built with `pytest` and `requests`. Tests exercise both `/dev` and `/prod` environments via independent CI jobs.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- Python 3.12+

## Setup

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the API locally

The API ships as a public Docker image:

```bash
docker run -p 3000:3000 ghcr.io/danielsilva-loanpro/sdet-interview-challenge:latest
```

It serves both environments at `http://localhost:3000/dev/...` and `http://localhost:3000/prod/...`.

## Run the tests

With the API running:

```bash
# Default — targets the dev environment
python -m pytest

# Pick an environment explicitly (defaults to dev)
API_ENV=dev  python -m pytest
API_ENV=prod python -m pytest
```

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `API_HOST` | `http://localhost:3000` | Base URL of the API |
| `API_ENV` | `dev` | Environment prefix — `dev` or `prod` |

### Filtering

```bash
# One endpoint group
python -m pytest tests/test_users.py::TestUsersCreate

# By name
python -m pytest -k "401"

# Only the known-bug tests (xfail)
python -m pytest -rx
```

### Generating test reports locally

```bash
pip install pytest-html
python -m pytest --junitxml=reports/junit.xml --html=reports/report.html --self-contained-html
```

## Continuous integration

[.github/workflows/test.yml](.github/workflows/test.yml) defines two **independent, parallel** jobs:

- `test-dev` — runs the suite with `API_ENV=dev`
- `test-prod` — runs the suite with `API_ENV=prod`

Each job starts the API container via a GitHub Actions `services:` block, waits for readiness, and runs the suite. The contents of `reports/` are uploaded as a per-environment artifact (`reports-dev` / `reports-prod`).

The jobs have no `needs:` dependency, so failure in one does **not** block the other — required by the brief because some tests are expected to fail against known API bugs.

## Project structure

```
.
├── .github/workflows/test.yml   # CI pipeline (dev + prod parallel jobs)
├── clients/
│   └── user_api_client.py       # Thin HTTP client wrapper around requests
├── tests/
│   ├── conftest.py              # Fixtures: user_client, created_user
│   └── test_users.py            # 54 tests across 5 endpoint classes
├── utils/
│   └── data.py                  # build_user_payload, unique_email
├── sdet_challenge_api.yml       # OpenAPI spec — the source of truth
├── BUGS.md                      # Documented divergences from the spec
├── pytest.ini
├── requirements.txt
└── README.md
```

## Test layout

Tests are grouped into one class per HTTP method:

| Class | Endpoint |
|---|---|
| `TestUsersList` | `GET /users` |
| `TestUsersCreate` | `POST /users` |
| `TestUserGet` | `GET /users/{email}` |
| `TestUserUpdate` | `PUT /users/{email}` |
| `TestUserDelete` | `DELETE /users/{email}` |

## Known bugs

The API has 10 documented places where its behavior diverges from the spec — including two **high-severity** auth-bypass issues on `DELETE /users/{email}`. Full details, severity, and reproduction steps live in [BUGS.md](BUGS.md).

Each bug is covered by a test marked `@pytest.mark.xfail(strict=True)`, so the suite stays green while the failures remain visible as `XFAIL` in the report. If a bug is ever fixed, the test starts passing and the suite fails — a reminder to remove the marker and update [BUGS.md](BUGS.md).

To see only the bug-exposing tests:

```bash
python -m pytest -rx tests/test_users.py
```

## Troubleshooting

**`pytest: error: unrecognized arguments: --html=...`** — your shell's `pytest` is resolving outside the venv (often a pyenv shim takes precedence). Use `python -m pytest` instead, or invoke the venv's pytest directly with `.venv/bin/pytest`.
