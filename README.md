# Homemade Food Application

## Project Overview

The Homemade Food Authentication Service is a Django-based authentication microservice designed for a food delivery platform. The service manages user registration, login/logout, password reset functionality, and user profile management for both chefs and consumers.

### Key Features
- Custom User model with email-based authentication
- Support for two user types: Chefs and Consumers  
- JWT-style token authentication
- Password reset functionality
- Payment card management
- Geolocation support for user addresses
- Comprehensive profile information for both chef and consumer roles
- Dish management system with categories and reviews
- Planned orders module for food ordering functionality

## Project Architecture

### Main Components
1. **HomemadeFood** - Django project directory containing settings, URLs, and configuration
2. **authentication** - Primary app handling all authentication and user management logic
3. **dishes** - App for managing dishes, categories, and reviews
4. **orders** - Planned module for handling food orders (implementation planned)

### Core Models
- `User` - Custom user model using email as the username field
- `Chef` - Chef-specific profile with ratings, specialties, and experience
- `Consumer` - Consumer-specific profile
- `PaymentCard` - Payment card information storage
- `Category` - Categories for organizing dishes
- `Dish` - Menu items created by chefs
- `DishReview` - Reviews and ratings for dishes
- `DishImage` - Images for dishes
- `Order` - (Planned) Food orders placed by consumers
- `OrderItem` - (Planned) Individual items within an order

## Building and Running

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Setup Instructions
1. Clone or access the project directory
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations to set up the database:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
5. Seed the database with initial data (optional but recommended for testing):
   ```bash
   python manage.py loaddata initial_data_fixture.json
   ```
   This will create sample users (chefs and consumers), dishes, categories, and other data for testing purposes.

   Note: For test account credentials, see TEST_CREDENTIALS.md

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Modules

### Authentication Module
Handles all user authentication and management:
- User registration, login/logout
- Password reset functionality
- User profile management for chefs and consumers
- Payment card management
- Custom permissions and roles

### Dishes Module
Manages the food items available on the platform:
- Dish creation and management
- Category organization
- Dish reviews and ratings
- Dish images

### Orders Module (Planned)
Future module for handling food orders:
- Order creation and management
- Order status tracking
- Integration with dishes and users

## API Endpoints

### Authentication Endpoints
All authentication endpoints are accessible under the `/api/auth/` base path:

- `POST /api/auth/signup/` - Create a new user
  - Required: `first_name`, `last_name`, `email`, `phone_number`, `password`, `address_longitude`, `address_latitude`, `user_type`
  - Optional (for chefs): `bio`, `cuisine_specialties`, `years_of_experience`

- `POST /api/auth/login/` - Authenticate user with `email` and `password`
  - Returns authentication token and user profile data

- `POST /api/auth/logout/` - Log out current user (requires authentication)

- `POST /api/auth/password-reset/` - Request password reset for `email`
  - Returns UID and token for development; sends email in production

- `POST /api/auth/password-reset-confirm/` - Reset password using `uid`, `token`, and `new_password`

- `POST /api/auth/cards/` - Add payment card (requires authentication)
  - Fields: `card_number`, `cardholder_name`, `exp_month`, `exp_year`
  - Creating a card sets user `is_active=True`

- `GET /api/auth/profile/<user_id>/` - Retrieve user profile with access controls
  - Consumer can read chef profiles
  - Users can read their own profiles
  - Requires authentication

- `PUT /api/auth/profile/<user_id>/` - Update user's own profile (full update)
  - Both chefs and consumers can update their own profiles
  - Requires authentication as the user whose profile is being updated

- `PATCH /api/auth/profile/<user_id>/` - Update user's own profile (partial update)
  - Both chefs and consumers can update their own profiles
  - Requires authentication as the user whose profile is being updated

### Dishes Endpoints
Dishes endpoints are accessible under the `/api/dishes/` base path:
- `GET /api/dishes/` - List all available dishes
- `POST /api/dishes/` - Create a new dish (chef only)
- `GET /api/dishes/<id>/` - Get details of a specific dish
- `PUT/PATCH /api/dishes/<id>/` - Update a dish (owner only)
- `DELETE /api/dishes/<id>/` - Delete a dish (owner only)
- `GET /api/dishes/categories/` - List all dish categories
- `POST /api/dishes/reviews/` - Add a review for a dish

## Admin Interface
Access the Django admin interface at `/admin/` to manage users, chefs, consumers, dishes, categories, reviews, and payment cards.

## Development Conventions

### Coding Standards
- Follow PEP 8 Python style guidelines
- Use descriptive variable and function names
- Maintain consistent model field naming conventions
- Use docstrings for complex functions and classes

### Testing
Recommended approach for testing this service:
- Unit tests for serializers and model methods
- API tests for all endpoint functionality
- Authentication flow tests for both chef and consumer user types
- Data validation tests for form inputs

### Security Practices
- Password hashing using Django's built-in mechanisms
- Token-based authentication for API endpoints
- Input validation through Django REST Framework serializers
- CSRF protection enabled for session-based requests

## Key Configuration Notes

### Environment Settings
- Email backend defaults to console output for development (emails printed to console)
- SQLite database used by default (configurable in settings.py)
- Debug mode enabled by default (change in production)

### Custom User Model
- The project uses a custom User model (`authentication.User`)
- Email is used as the unique identifier for authentication
- Extended fields include geolocation data, profile picture URL, and user role indicators

### Project Extensibility
The authentication service is designed to integrate with a larger food delivery platform. Additional modules could be built to handle:
- Recipe management (for chefs)
- Order processing
- Rating and review systems
- Payment processing integration
- Location-based services
- Notification systems

## Common Operations

### Setting up a new environment:
1. Install dependencies from requirements.txt
2. Run migrations to create database tables
3. Configure settings as needed for your environment

### Managing user data:
1. Use Django admin for direct database access
2. Leverage API endpoints for programmatic access
3. Implement custom management commands for bulk operations if needed

## Database Structure
The database structure includes the following key relationships:
- Users can be either Chefs or Consumers
- Chefs can create multiple Dishes
- Dishes belong to Categories and can have multiple Reviews
- Consumers can place multiple Orders
- Each Order contains multiple OrderItems
- Orders are linked to specific Dishes

For a detailed UML diagram of the database structure, see `database_structure.puml`.

## Future Enhancements
- Complete implementation of the Orders module
- Notification system for order status updates
- Advanced analytics and reporting
- Mobile application integration
- Real-time order tracking
- Advanced search and filtering capabilities

## Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License
This project is licensed under the terms specified in the LICENSE file.
