# Project Configuration Guide: HomemadeFood Settings

## Overview
The HomemadeFood project is the main Django project configuration that ties together all modules of the Homemade Food platform. It handles settings for authentication, database, middleware, and application integration.

## Project Structure
```
HomemadeFood/ (Project Root)
├── settings.py (Main configuration)
├── urls.py (Root URL configuration)
├── wsgi.py (Web Server Gateway Interface)
└── asgi.py (Asynchronous Server Gateway Interface)
```

## Key Settings

### Application Configuration
The project includes several core applications:
- `django.contrib.admin` - Django's admin interface
- `django.contrib.auth` - Django's authentication framework
- `rest_framework` - Django REST framework for API development
- `authentication` - Custom authentication module with Chef/Consumer models
- `dishes` - Menu management system
- `orders` - Food ordering system

### Custom User Model
The project uses a custom user model from the authentication app:
```python
AUTH_USER_MODEL = 'authentication.User'
```
This replaces Django's default User model with a custom implementation that supports both chef and consumer user types.

### Database Configuration
By default, the project uses SQLite for development:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```
For production, this can be changed to PostgreSQL or MySQL by modifying the ENGINE and adding appropriate connection parameters.

### REST Framework Settings
The project is configured to use both session and token authentication:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
}
```

### Email Backend
For development, emails are printed to the console:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
In production, this should be changed to a real email service like SMTP or a third-party provider.

## Environment Configuration

### Development Settings
The default settings are configured for development:
- `DEBUG = True` - Enables debug mode for detailed error pages
- `SECRET_KEY` - Insecure default key (should be changed in production)
- `ALLOWED_HOSTS = []` - Empty list for local development

### Production Settings
To configure for production, you should:
1. Set `DEBUG = False`
2. Add your domain(s) to `ALLOWED_HOSTS`
3. Use a strong, secret `SECRET_KEY`
4. Configure a production database
5. Set up a production email backend
6. Configure static files for production serving

## URL Configuration

The project's main `urls.py` file includes URL patterns from all modules:
- `/api/auth/` - Authentication endpoints from the authentication app
- `/api/dishes/` - Dish management endpoints from the dishes app
- `/api/orders/` - Order management endpoints from the orders app

## Middleware Configuration

The project uses essential Django middleware:
- `SecurityMiddleware` - Handles security-related tasks
- `SessionMiddleware` - Enables session support
- `CommonMiddleware` - Handles common HTTP tasks
- `CsrfViewMiddleware` - Prevents Cross-Site Request Forgery attacks
- `AuthenticationMiddleware` - Integrates authentication into request objects

## Static Files

Static files (CSS, JavaScript, Images) are served from the `/static/` URL path:
```python
STATIC_URL = 'static/'
```

## Custom Settings

### User Authentication
The project is configured to use email-based authentication rather than username-based:
- Custom User model with email as the unique identifier
- Email normalization and validation
- Password reset functionality via email

### Timezone Handling
The project uses UTC for time storage:
```python
TIME_ZONE = 'UTC'
USE_TZ = True
```
This ensures consistent time handling across different geographical locations.

## Deployment Considerations

### Security
- Change the `SECRET_KEY` in production
- Add your domain(s) to `ALLOWED_HOSTS`
- Consider using Django's security middleware
- Implement HTTPS in production

### Performance
- Configure a production database (PostgreSQL recommended)
- Set up static file serving through a web server
- Consider using a cache backend (Redis, Memcached)
- Use a production WSGI server (Gunicorn, uWSGI)

### Monitoring
- Set up logging for production environments
- Configure error reporting
- Monitor database performance
- Track API usage and performance metrics

## Testing Configuration

The project is configured to work with Django's testing framework:
- Test database is created automatically during testing
- All apps' tests are discoverable
- Authentication and authorization are tested in each module

## Best Practices

### Configuration Management
- Use environment variables for sensitive settings
- Keep development and production settings separate
- Use Django's `django-environ` or similar for environment-based configuration

### Security
- Regularly update dependencies
- Use Django's built-in security features
- Implement proper input validation
- Sanitize user inputs

### Performance
- Optimize database queries
- Use Django's caching framework appropriately
- Optimize static file serving
- Monitor and optimize API response times

## Common Operations

### Running Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Starting the Development Server
```bash
python manage.py runserver
```

### Creating a Superuser (optional)
```bash
python manage.py createsuperuser
```

### Running Tests (optional)
```bash
python manage.py test
```

### Collecting Static Files (for production)
```bash
python manage.py collectstatic
```

## Troubleshooting

### Common Issues
1. **Missing migrations**: Run `makemigrations` and `migrate` after code changes
2. **Authentication issues**: Check that `AUTH_USER_MODEL` is correctly set
3. **Database connection errors**: Verify database configuration settings
4. **Static files not loading**: Check `STATIC_URL` and run `collectstatic` in production

### Debugging Tips
- Enable Django debug mode in development to see detailed error messages
- Use Django's logging framework to track application behavior
- Check the Django admin interface for data validation
- Use Django shell (`python manage.py shell`) for debugging queries