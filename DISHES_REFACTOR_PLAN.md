# Dishes Module Refactoring Plan

## Overview
This document outlines the comprehensive refactoring plan for the dishes module, focusing on code cleanup, removing unused endpoints, and API redesign for better usability and maintainability.

## Current Issues

### 1. Code Cleanup Issues
- **Unused imports**: `Q`, `Avg`, `status`, `api_view`, `User` in views.py
- **Duplicate code**: `average_rating` method duplicated in multiple serializers
- **Redundant classes**: Multiple similar views that can be consolidated
- **Inconsistent naming**: Mix of `pk`, `dish_id`, `chef_id` in URL patterns

### 2. Unused/Redundant Endpoints
- `ChefCategoryListView` and `ChefCategoryDetailView` - Categories should be global, not per-chef
- `CategoryDetailView` - Rarely used standalone
- Duplicate variety CRUD views with complex nesting

### 3. API Design Issues
- Inconsistent URL patterns (`/chef/` vs `/chef/<chef_id>/` vs `/chef/<pk>/`)
- Variety endpoints are overly complex and deeply nested
- No search functionality for dishes
- No clear separation between public (consumer) and chef-only endpoints
- Missing endpoint for chef's own dishes with full details

## Proposed New API Structure

### Public/Consumer Endpoints (Read-Only or Authenticated)
```
GET    /api/dishes/                          - List all available dishes
       Query params: category_name, min_price, max_price, search, chef_id

GET    /api/dishes/<id>/                     - Get dish details (with reviews, images, varieties)

GET    /api/dishes/chef/<chef_id>/           - List all dishes by a specific chef

GET    /api/dishes/categories/               - List all categories

GET    /api/dishes/<dish_id>/reviews/        - List all reviews for a dish
POST   /api/dishes/<dish_id>/reviews/        - Add a review (consumer only, authenticated)
```

### Chef-Only Endpoints (Require Authentication as Chef)
```
# My Dishes Management
GET    /api/dishes/my-dishes/                - List MY dishes (authenticated chef)
POST   /api/dishes/my-dishes/                - Create a new dish
GET    /api/dishes/my-dishes/<id>/           - Get details of MY dish
PUT    /api/dishes/my-dishes/<id>/           - Update MY dish
PATCH  /api/dishes/my-dishes/<id>/           - Partially update MY dish
DELETE /api/dishes/my-dishes/<id>/           - Delete MY dish

# Dish Images Management
POST   /api/dishes/my-dishes/<id>/images/         - Add image to dish
DELETE /api/dishes/my-dishes/<id>/images/<img_id>/ - Delete image

# Variety Management (nested under my-dishes for clarity)
GET    /api/dishes/my-dishes/<id>/varieties/      - List varieties for MY dish
POST   /api/dishes/my-dishes/<id>/varieties/      - Add variety section
PUT    /api/dishes/my-dishes/<id>/varieties/<section_id>/ - Update section
DELETE /api/dishes/my-dishes/<id>/varieties/<section_id>/ - Delete section

POST   /api/dishes/my-dishes/<id>/varieties/<section_id>/options/ - Add option
PUT    /api/dishes/my-dishes/<id>/varieties/<section_id>/options/<option_id>/ - Update
DELETE /api/dishes/my-dishes/<id>/varieties/<section_id>/options/<option_id>/ - Delete
```

## Implementation Steps

### Phase 1: Models (No Changes Required)
The current models are well-structured. No changes needed:
- `Category`
- `Dish`
- `DishReview`
- `DishImage`
- `DishVarietySection`
- `DishVarietyOption`

### Phase 2: Serializers Refactoring

#### 2.1 Create a Base Serializer Utility
Create a utility module to avoid code duplication:

```python
# dishes/utils.py
from django.db.models import Avg

def calculate_average_rating(dish):
    """Calculate average rating for a dish"""
    reviews = dish.reviews.all()
    if reviews:
        return sum(review.rating for review in reviews) / len(reviews)
    return 0
```

#### 2.2 Update Serializers
- Remove duplicate `average_rating` methods
- Use the utility function instead
- Simplify `DishSerializer` to avoid nested serialization overhead when not needed

### Phase 3: Views Refactoring

#### 3.1 Remove Unused Views
Delete:
- `ChefCategoryListView`
- `ChefCategoryDetailView`
- `CategoryDetailView` (optional, keep if needed)

#### 3.2 Create New Views

**Public Views:**
```python
class PublicDishListView(generics.ListAPIView)
    - Filter by: category_name, min_price, max_price, search, chef_id
    - Only shows available dishes

class PublicDishDetailView(generics.RetrieveAPIView)

class ChefDishesPublicView(generics.ListAPIView)
    - List all dishes for a specific chef (public)

class ReviewListCreateView(generics.ListCreateAPIView)
    - GET: List reviews (public)
    - POST: Create review (consumer only)
```

**Chef Views:**
```python
class ChefDishListCreateView(generics.ListCreateAPIView)
    - GET: List chef's own dishes
    - POST: Create new dish

class ChefDishDetailView(generics.RetrieveUpdateDestroyAPIView)
    - GET/PUT/PATCH/DELETE: Manage own dish

class ChefDishImageView(generics.CreateAPIView, generics.DestroyAPIView)
    - POST: Add image
    - DELETE: Remove image

class ChefVarietySectionView(generics.ListCreateAPIView, 
                              generics.RetrieveUpdateDestroyAPIView)
    - Consolidated view for variety sections

class ChefVarietyOptionView(generics.ListCreateAPIView,
                             generics.RetrieveUpdateDestroyAPIView)
    - Consolidated view for variety options
```

#### 3.3 Create Custom Permissions
```python
# dishes/permissions.py
from rest_framework import permissions

class IsChefOrReadOnly(permissions.BasePermission):
    """Allow read-only access to all, write access only to chefs"""
    
class IsDishOwner(permissions.BasePermission):
    """Only allow dish creator to modify"""
    
class IsConsumerOrReadOnly(permissions.BasePermission):
    """Allow read-only access to all, write access only to consumers"""
```

### Phase 4: URL Restructuring

```python
# dishes/urls.py
from django.urls import path, include
from . import views

urlpatterns = [
    # Public endpoints
    path('', views.PublicDishListView.as_view(), name='dish-list'),
    path('<int:pk>/', views.PublicDishDetailView.as_view(), name='dish-detail'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('chef/<int:chef_id>/', views.ChefDishesPublicView.as_view(), name='chef-dishes-public'),
    path('<int:dish_id>/reviews/', views.ReviewListCreateView.as_view(), name='dish-reviews'),
    
    # Chef-only endpoints
    path('my-dishes/', views.ChefDishListCreateView.as_view(), name='chef-dish-list'),
    path('my-dishes/<int:pk>/', views.ChefDishDetailView.as_view(), name='chef-dish-detail'),
    path('my-dishes/<int:dish_id>/images/', views.ChefDishImageView.as_view(), name='chef-dish-images'),
    path('my-dishes/<int:dish_id>/images/<int:img_id>/', views.ChefDishImageView.as_view(), name='chef-dish-image-detail'),
    path('my-dishes/<int:dish_id>/varieties/', views.ChefVarietySectionView.as_view(), name='chef-dish-varieties'),
    path('my-dishes/<int:dish_id>/varieties/<int:section_id>/', views.ChefVarietySectionView.as_view(), name='chef-dish-variety-section'),
    path('my-dishes/<int:dish_id>/varieties/<int:section_id>/options/', views.ChefVarietyOptionView.as_view(), name='chef-dish-variety-options'),
    path('my-dishes/<int:dish_id>/varieties/<int:section_id>/options/<int:option_id>/', views.ChefVarietyOptionView.as_view(), name='chef-dish-variety-option'),
]
```

### Phase 5: Update Documentation

#### 5.1 Update DISHES_GUIDE.md
- Document new endpoint structure
- Update API examples
- Add migration guide for existing users

#### 5.2 Update Postman Collection
- Remove deprecated endpoints
- Add new endpoints with examples
- Update authentication requirements

### Phase 6: Testing

#### 6.1 Update Existing Tests
- Update tests for renamed/modified endpoints
- Remove tests for deleted endpoints

#### 6.2 Add New Tests
- Test new permission classes
- Test search functionality
- Test filtering by chef_id
- Test variety management endpoints

## Migration Guide for Existing Users

### Breaking Changes
1. `/api/dishes/chef/` → `/api/dishes/my-dishes/` (chef's own dishes)
2. `/api/dishes/chef/<pk>/` → `/api/dishes/my-dishes/<id>/` (manage own dish)
3. `/api/dishes/chef/categories/` → Removed (categories are global)
4. Variety endpoints moved under `/api/dishes/my-dishes/<id>/varieties/`

### Non-Breaking Changes
- `/api/dishes/` - Still works, added new query params
- `/api/dishes/<id>/` - Still works
- `/api/dishes/categories/` - Still works
- `/api/dishes/<dish_id>/reviews/` - Still works

## Benefits of This Refactoring

### 1. Clearer API Structure
- Public vs Chef-only endpoints clearly separated
- Consistent URL patterns
- Intuitive endpoint names (`my-dishes` vs `chef`)

### 2. Better Code Maintainability
- Removed unused code and imports
- Consolidated similar views
- Custom permissions for reusable access control

### 3. Improved Functionality
- Search functionality for dishes
- Filter by chef_id for public access
- Better variety management structure

### 4. Enhanced Security
- Explicit permission classes
- Clear ownership validation
- Proper role-based access control

## Timeline Estimate

| Phase | Description | Estimated Time |
|-------|-------------|----------------|
| Phase 1 | Models review | 0.5 hours |
| Phase 2 | Serializers refactoring | 2 hours |
| Phase 3 | Views refactoring | 4 hours |
| Phase 4 | URL restructuring | 1 hour |
| Phase 5 | Documentation updates | 2 hours |
| Phase 6 | Testing | 3 hours |
| **Total** | | **~12.5 hours** |

## Rollback Plan

If issues arise during implementation:
1. Keep original files in a backup branch
2. Implement changes incrementally
3. Test each phase before proceeding
4. Use feature flag for new endpoints during transition

## Success Criteria

- [ ] All new endpoints functional and tested
- [ ] No code duplication in serializers
- [ ] All unused imports and views removed
- [ ] Documentation updated
- [ ] Postman collection updated
- [ ] All tests passing
- [ ] No breaking changes for public endpoints
- [ ] Clear migration path for chef endpoints
