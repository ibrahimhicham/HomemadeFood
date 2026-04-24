# Dishes Module: Menu Management System

## Overview
The dishes module handles all aspects of menu management for the Homemade Food platform. It allows chefs to create and manage their dishes, organize them into categories, and enables consumers to browse, review, and rate dishes.

### Architecture

```
Category (name, description)
├── Dish (name, description, price, availability, prep_time)
│   ├── DishReview (rating, review_text from customer)
│   └── DishImage (image_url, is_primary)
```

## Database Changes

Run migrations to create the dishes-related tables:

```bash
python manage.py makemigrations dishes
python manage.py migrate
```

## Core Models

### Category Model
- `name`: Unique name for the category (e.g., "Italian", "Desserts", "Vegan")
- `description`: Optional description of the category
- `created_at`/`updated_at`: Timestamps for tracking

### Dish Model
- `chef`: Foreign key to the User (chef) who created the dish
- `name`: Name of the dish
- `description`: Detailed description of the dish
- `category`: Foreign key to the Category the dish belongs to
- `price`: Price of the dish (DecimalField)
- `is_available`: Boolean indicating if the dish is currently available
- `preparation_time`: Time in minutes to prepare the dish
- `created_at`/`updated_at`: Timestamps for tracking

### DishReview Model
- `dish`: Foreign key to the Dish being reviewed
- `customer`: Foreign key to the User (customer) who wrote the review
- `rating`: Integer rating from 1 to 5 stars
- `review_text`: Optional text review
- `created_at`/`updated_at`: Timestamps for tracking

### DishImage Model
- `dish`: Foreign key to the Dish the image belongs to
- `image_url`: URL to the dish image
- `is_primary`: Boolean indicating if this is the primary image
- `created_at`/`updated_at`: Timestamps for tracking

## API Endpoints

All dishes endpoints are accessible under the `/api/dishes/` base path:

- `GET /api/dishes/` - List all available dishes
  - Optional query parameters: `category`, `chef`, `min_price`, `max_price`, `search`
  - Returns paginated list of dishes

- `POST /api/dishes/` - Create a new dish (chef only)
  - Required: `name`, `description`, `category`, `price`, `preparation_time`
  - Optional: `is_available` (defaults to True)
  - Requires authentication as a chef

- `GET /api/dishes/<id>/` - Get details of a specific dish
  - Returns dish details including chef info, reviews, and images

- `PUT/PATCH /api/dishes/<id>/` - Update a dish (owner only)
  - Requires authentication as the dish owner (chef)

- `DELETE /api/dishes/<id>/` - Delete a dish (owner only)
  - Requires authentication as the dish owner (chef)

- `GET /api/dishes/categories/` - List all dish categories
  - Returns all available categories

- `POST /api/dishes/categories/` - Create a new category (admin only)
  - Requires authentication as admin

- `POST /api/dishes/reviews/` - Add a review for a dish
  - Required: `dish_id`, `rating`
  - Optional: `review_text`
  - Requires authentication as a consumer

- `GET /api/dishes/<dish_id>/reviews/` - Get all reviews for a dish
  - Returns paginated list of reviews for the dish

## Admin Interface

- **Categories**: Manage dish categories (create, update, delete)
- **Dishes**: View all dishes, filter by chef, category, availability
- **Dish Reviews**: View all dish reviews, filter by dish or customer
- **Dish Images**: Manage dish images, set primary images

## Best Practices

### Creating Dishes
- Ensure dish names are unique per chef (enforced by model)
- Include accurate preparation times for better customer experience
- Add multiple images with one designated as primary
- Regularly update availability status

### Managing Categories
- Use descriptive category names that help consumers find dishes easily
- Consider seasonal or special dietary categories
- Avoid creating too many overlapping categories

### Handling Reviews
- Monitor reviews to improve dish quality
- Respond to reviews professionally when appropriate
- Address low ratings by improving the dish or contacting the customer

### Querying Dishes

**Get dishes by chef:**
```python
dishes = Dish.objects.filter(chef=user)
```

**Get available dishes in a category:**
```python
available_dishes = Dish.objects.filter(
    category=category_instance, 
    is_available=True
)
```

**Get average rating for a dish:**
```python
from django.db.models import Avg
dish_rating = DishReview.objects.filter(dish=dish_instance).aggregate(Avg('rating'))
```

## Advantages of This Approach

1. **Structured Organization**: Categories allow for easy browsing and filtering
2. **Quality Assurance**: Reviews help maintain dish quality and inform consumer decisions
3. **Rich Media Support**: Multiple images per dish enhance consumer experience
4. **Scalability**: Easy to add new dish features like nutritional information or ingredients
5. **Data Integrity**: Proper foreign key relationships ensure data consistency

## Testing

```bash
# Run dishes-specific tests
python manage.py test dishes

# Shell testing
python manage.py shell
>>> from dishes.models import Category, Dish, DishReview, DishImage
>>> from authentication.models import User
>>> 
>>> # Create a category
>>> category = Category.objects.create(name="Italian", description="Italian cuisine")
>>> 
>>> # Get a chef user
>>> chef = User.objects.get(chef__isnull=False).first()
>>> 
>>> # Create a dish
>>> dish = Dish.objects.create(
...     chef=chef,
...     name="Spaghetti Carbonara",
...     description="Classic Italian pasta with eggs and pancetta",
...     category=category,
...     price=15.99,
...     preparation_time=20
... )
>>> 
>>> # Add a review from a customer
>>> customer = User.objects.get(consumer__isnull=False).first()
>>> review = DishReview.objects.create(
...     dish=dish,
...     customer=customer,
...     rating=5,
...     review_text="Amazing flavor, just like in Rome!"
... )
```