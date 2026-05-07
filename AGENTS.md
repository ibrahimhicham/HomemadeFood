# Repository Guidelines

## Project Structure & Module Organization

`HomemadeFood/` contains the Django project configuration (`settings.py`, `asgi.py`, `urls.py`). Feature code lives in app directories:

- `authentication/`: custom user model, login/signup, cards, profile APIs
- `dishes/`: dishes, categories, images, reviews, variety sections/options
- `orders/`: order APIs, websocket consumer, routing, services, management commands

Tests currently live beside app code in `authentication/tests.py`, `dishes/tests.py`, and `orders/tests.py`. Project docs and API notes are stored at the repo root in files such as `README.md`, `ORDERS_GUIDE.md`, and `WEBSOCKETS.md`.

## Build, Test, and Development Commands

- `python -m venv .venv` then `.venv\Scripts\activate`: create and activate a local virtual environment on Windows
- `pip install -r requirements.txt`: install Django, DRF, Channels, and supporting packages
- `python manage.py migrate`: apply database migrations
- `python manage.py runserver`: start the local API server
- `python manage.py test`: run the full Django test suite
- `python manage.py test orders`: run only the orders tests
- `python manage.py test_order_websockets`: run the websocket routing smoke test

## Coding Style & Naming Conventions

Follow PEP 8 with 4-space indentation. Use `snake_case` for functions, variables, and module names; `PascalCase` for classes; and descriptive service names such as `OrderCreateService`. Keep business logic in service classes or serializers rather than views when possible. No formatter or linter is configured in this repository, so keep changes consistent with surrounding code.

## Testing Guidelines

Use Django’s test runner and `unittest`-style test cases. Add tests next to the app you change. Name test methods `test_<behavior>` and cover API permissions, serializer validation, and websocket routing where relevant. For realtime behavior, prefer `channels.testing.WebsocketCommunicator`.

## Commit & Pull Request Guidelines

Recent history uses short, informal messages like `editing on serializers and readme`. Keep commits concise, imperative, and scoped to one change, for example `add order status websocket test`. For pull requests, include a clear summary, affected endpoints or apps, migration notes if any, and example requests/responses when API behavior changes.

## Security & Configuration Tips

Do not commit secrets or real tokens. Authentication uses DRF token auth, and the websocket endpoint expects `?token=...`. Development uses SQLite and an in-memory channel layer; production should use environment-backed settings and Redis for Channels.
