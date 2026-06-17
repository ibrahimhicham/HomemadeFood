# AGENTS.md — Homemade Food Platform

## Project Structure

- `HomemadeFood/` — Django project config (`settings.py`, `asgi.py`, `urls.py`).
- `authentication/` — Custom User model, login/signup, cards, profile, permissions.
- `dishes/` — Dishes, categories, images, reviews, variety sections/options, pagination, APScheduler.
  - Uses `dishes.apps.DishesConfig` in `INSTALLED_APPS`.
- `orders/` — Orders, items, variety selections, notifications, WebSocket consumer/routing, services, middleware, management commands, constants, utils.

## Setup & Developer Commands

```bash
python -m venv .venv && source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata initial_data_fixture.json   # test data (see TEST_CREDENTIALS.md)
python manage.py load_initial_data                    # lighter 4-user fixture
python manage.py runserver
```

## Testing

```bash
python manage.py test                                  # full suite
python manage.py test authentication                   # only auth app
python manage.py test dishes                           # only dishes app
python manage.py test orders                           # only orders app
python manage.py test_order_websockets                 # WebSocket routing smoke test
```

- WebSocket tests need `TransactionTestCase` (not `TestCase`) for `WebsocketCommunicator`.
- Channel layer uses `InMemoryChannelLayer` in dev — no Redis needed.
- Auth tests extend `APITestCase`; dishes tests use `TestCase`.

## Key Architecture

- **Auth**: DRF Token auth. WebSocket auth via `?token=` query param (`orders/middleware.py`).
- **Orders**: Service classes (`OrderCreateService`, `OrderStatusService`, `CancelExpiredOrdersService`) in `orders/services.py`. Views call service `execute()`, not ORM directly.
- **WebSocket**: Single endpoint `/ws/orders/`. Groups: `user_{user_id}` (personal), `order_{order_id}` (per-order). Broadcast via `orders/utils.py` (`send_to_user_group`, `send_to_order_group`).
- **Order lookup** uses `order_id` (UUID), not PK `id`.
- **APScheduler** in `dishes/scheduler.py` periodically pings refresh and cancel-expired endpoints (1-min interval).
- **Media**: Cloudinary storage via `django-cloudinary-storage`. Cloudinary env vars loaded from `.env`.
- **Email**: Console backend in dev (`django.core.mail.backends.console.EmailBackend`).

## Style & Conventions

- PEP 8, 4-space indent, `snake_case` functions/vars, `PascalCase` classes.
- Business logic in service classes, not views.
- No formatter/linter configured — keep consistent with surrounding code.
- Commits: short imperative messages, e.g. `add order status websocket test`.
