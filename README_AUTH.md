# Authentication app (quick start)

Endpoints (base path: `/api/auth/`):

- `POST signup/` — create a new user. Required JSON: `first_name`, `last_name`, `email`, `phone_number`, `password`, `address_longitude`, `address_latitude`. Optional: `is_chef`.
- `POST login/` — login with `email` and `password`. Returns auth token.
- `POST logout/` — (auth required) deletes token.
- `POST password-reset/` — provide `email`, returns a reset `uid` and `token` (development behavior).
- `POST password-reset-confirm/` — provide `uid`, `token`, and `new_password` to reset.
- `POST cards/` — (auth required) add payment card: `card_number`, `cardholder_name`, `exp_month`, `exp_year`. When a card is added the user becomes `is_active=True`.

Notes:
- This app provides a custom `User` model. After adding the app, run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

- To test password reset flow in development, `EMAIL_BACKEND` is set to console; the reset endpoint returns uid/token for convenience.
