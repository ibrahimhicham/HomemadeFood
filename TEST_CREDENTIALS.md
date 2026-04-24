# Test Credentials for Homemade Food Application

This file contains the test credentials for the sample accounts created by the `initial_data_fixture.json` fixture.

## Setup

Load all test data into your database:

```bash
python3 manage.py loaddata initial_data_fixture.json
```

This will create 9 users (7 chefs, 2 consumers), 20+ dishes, categories, reviews, and more.

## User Accounts


### Chefs
| Email | Password | Specialties |
|-------|----------|-------------|
| chef.john@example.com | chef123 | Italian, Mediterranean |
| chef.maria@example.com | chef456 | Mexican, Tex-Mex |
| chef.antonio@example.com | chef123 | French, Mediterranean, Fusion |
| chef.yuki@example.com | chef123 | Japanese, Sushi, Asian |
| chef.priya@example.com | chef123 | Indian, Curry, Vegetarian |
| chef.ahmed@example.com | chef123 | Middle Eastern, Lebanese, Turkish |
| chef.elena@example.com | chef123 | Eastern European, Romanian, Pastries |

### Consumers
| Email | Password |
|-------|----------|
| consumer.sarah@example.com | consumer123 |
| consumer.mike@example.com | consumer456 |

## Important Notes
- These are test accounts for development and testing purposes only
- Passwords are hashed using Django's PBKDF2 algorithm
- All accounts have working passwords and can be used for testing authentication
- After loading the fixture, access the admin panel at `http://127.0.0.1:8000/admin/`
- For a simpler dataset (4 users only), use: `python3 manage.py load_initial_data`