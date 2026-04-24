# Consumer Homepage API Implementation Plan

## Overview

This document outlines the implementation plan for the Consumer Homepage API endpoint for the Homemade Food platform (Talabat-like). The homepage provides a single aggregated endpoint that returns all necessary data for the consumer home page.

**Implementation Approach:** Add homepage endpoint to the existing `dishes` app (no new app required).

---

## Homepage Requirements

The homepage should return the following sections:

### 1. Search
- Ability to search dishes by name
- Should use the existing dishes endpoint if possible

### 2. Categories
- List dish categories
- Use the existing `Category` model

### 3. Featured Dishes
- A list of highlighted dishes
- Can be based on highest rating or a simple selection of available dishes for now

### 4. Top Chefs
- Show chefs with the highest rating

### 5. New Dishes
- Recently added dishes ordered by creation date

---

## API Endpoints

### Main Homepage Endpoint

```
GET /api/dishes/home/
```

**Authentication:** Optional (recommended `IsAuthenticatedOrReadOnly`)

**Response Example:**

```json
{
  "categories": [
    {
      "id": 1,
      "name": "Italian",
      "description": "Italian cuisine",
      "dish_count": 5
    },
    {
      "id": 2,
      "name": "Desserts",
      "description": "Sweet treats",
      "dish_count": 3
    }
  ],
  "featured_dishes": [
    {
      "id": 1,
      "name": "Margherita Pizza",
      "description": "Classic Italian pizza",
      "price": "12.99",
      "chef": {
        "id": 2,
        "first_name": "Mario",
        "last_name": "Rossi"
      },
      "average_rating": 4.8,
      "image": "/media/dishes/2026/03/06/pizza.jpg"
    }
  ],
  "top_chefs": [
    {
      "id": 2,
      "user": {
        "id": 2,
        "first_name": "Mario",
        "last_name": "Rossi",
        "profile_picture": "/media/profiles/chef.jpg"
      },
      "rating": 4.9,
      "total_reviews": 45,
      "cuisine_specialties": "Italian, Pasta"
    }
  ],
  "new_dishes": [
    {
      "id": 5,
      "name": "Tiramisu",
      "description": "Classic Italian dessert",
      "price": "8.99",
      "chef": {
        "id": 2,
        "first_name": "Mario",
        "last_name": "Rossi"
      },
      "created_at": "2026-03-06T10:00:00Z"
    }
  ]
}
```

### Search Endpoint (Existing)

```
GET /api/dishes/?search={query}
```

---

## Current Project Status

### ✅ Already Implemented

| Feature | Model | Endpoint | Status |
|---------|-------|----------|--------|
| Categories | `Category` | `GET /api/dishes/categories/` | ✅ Complete |
| Dishes | `Dish` | `GET /api/dishes/` | ✅ Complete |
| Dish Reviews | `DishReview` | `GET /api/dishes/{id}/reviews/` | ✅ Complete |
| Chefs | `Chef` (via User) | `GET /api/auth/profile/{id}/` | ✅ Complete |
| Dish Images | `DishImage` | `GET /api/dishes/{id}/images/` | ✅ Complete |

### ❌ To Be Implemented

| Feature | Action Required |
|---------|-----------------|
| Homepage Endpoint | Add `GET /api/dishes/home/` to dishes app |
| Search Functionality | Add `search` query param to dishes endpoint |
| Top Chefs Endpoint | Create `GET /api/auth/chefs/top-rated/` (optional) |

---

## Implementation Plan

### Why Add to Dishes App?

- ✅ No new app structure needed
- ✅ Homepage is primarily dish-focused
- ✅ Reuses existing dish serializers
- ✅ Simpler and cleaner for this project scope
- ✅ All required models are already accessible

---

### 1. Homepage Serializer

Add to `dishes/serializers.py`:

```python
class CategoryHomeSerializer(serializers.ModelSerializer):
    """Lightweight category serializer for homepage"""
    dish_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'dish_count']

    def get_dish_count(self, obj):
        return obj.dishes.filter(is_available=True).count()


class FeaturedDishSerializer(DishListSerializer):
    """Extended dish serializer with image for homepage"""
    image = serializers.SerializerMethodField()

    class Meta(DishListSerializer.Meta):
        fields = DishListSerializer.Meta.fields + ['image']

    def get_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image.url
        return None


class TopChefSerializer(serializers.ModelSerializer):
    """Chef serializer for homepage"""
    user = serializers.SerializerMethodField()

    class Meta:
        model = Chef
        fields = ['id', 'user', 'rating', 'total_reviews', 'cuisine_specialties']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'profile_picture': obj.user.profile_picture.url if obj.user.profile_picture else None
        }


class NewDishSerializer(serializers.ModelSerializer):
    """Lightweight dish serializer for new dishes"""
    chef_name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = ['id', 'name', 'description', 'price', 'chef_name', 'image', 'created_at']

    def get_chef_name(self, obj):
        return f"{obj.chef.first_name} {obj.chef.last_name}"

    def get_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image.url
        return None


class HomePageSerializer(serializers.Serializer):
    """Aggregated homepage response"""
    categories = CategoryHomeSerializer(many=True)
    featured_dishes = FeaturedDishSerializer(many=True)
    top_chefs = TopChefSerializer(many=True)
    new_dishes = NewDishSerializer(many=True)
```

### 2. Homepage View

Add to `dishes/views.py`:

```python
from django.db.models import Avg
from authentication.models import Chef


class HomePageView(APIView):
    """
    Homepage endpoint returning aggregated data for consumer home page.
    Located in dishes app since homepage is primarily dish-focused.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        # Get categories with available dishes
        categories = Category.objects.all()[:6]  # Limit to 6 categories

        # Get featured dishes (highest rated, available)
        featured_dishes = Dish.objects.filter(
            is_available=True
        ).annotate(
            avg_rating=Avg('reviews__rating')
        ).order_by('-avg_rating')[:6]  # Top 6 rated dishes

        # Get top chefs (highest rating)
        top_chefs = Chef.objects.filter(
            is_verified=True
        ).order_by('-rating')[:5]  # Top 5 chefs

        # Get new dishes (recently added)
        new_dishes = Dish.objects.filter(
            is_available=True
        ).select_related('chef').order_by('-created_at')[:6]  # Latest 6 dishes

        serializer = HomePageSerializer({
            'categories': categories,
            'featured_dishes': featured_dishes,
            'top_chefs': top_chefs,
            'new_dishes': new_dishes
        })

        return Response(serializer.data)
```

### 3. URL Configuration

Update `dishes/urls.py`:

```python
urlpatterns = [
    # Homepage endpoint (add at the top)
    path('home/', views.HomePageView.as_view(), name='home-page'),
    
    # Category endpoints
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    ...
]
```

### 4. Add Search to Dishes Endpoint

Update `dishes/views.py` - `DishListView.get_queryset()`:

```python
from django.db.models import Q

class DishListView(generics.ListAPIView):
    """
    List all available dishes with optional filtering:
    - ?search={query}: Search by dish name or description
    - ?category_name={category_name}: Filter by category name
    - ?is_available=true/false: Filter by availability
    - ?min_price={price}&max_price={price}: Filter by price range
    """
    serializer_class = DishListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Dish.objects.filter(is_available=True).select_related('chef', 'category').prefetch_related('reviews')

        # Search functionality
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )

        # Apply category filter by name if specified
        category_name = self.request.query_params.get('category_name', None)
        if category_name is not None:
            queryset = queryset.filter(category__name__icontains=category_name)

        # Apply additional filters
        is_available = self.request.query_params.get('is_available', None)
        if is_available is not None:
            is_available = is_available.lower() == 'true'
            queryset = queryset.filter(is_available=is_available)

        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        return queryset
```

---

## Model Changes Required

**None!** All existing models support the homepage requirements.

---

## Implementation Steps

### Step 1: Add Serializers to `dishes/serializers.py`
Add the homepage serializers (CategoryHomeSerializer, FeaturedDishSerializer, TopChefSerializer, NewDishSerializer, HomePageSerializer).

### Step 2: Add View to `dishes/views.py`
Add `HomePageView` class.

### Step 3: Update `dishes/urls.py`
Add the homepage route:
```python
path('home/', views.HomePageView.as_view(), name='home-page'),
```

### Step 4: Add Search to `dishes/views.py`
Update `DishListView.get_queryset()` to support `?search=` query parameter.

### Step 5: Test
```bash
python manage.py runserver

# Test homepage
curl http://localhost:8000/api/dishes/home/

# Test search
curl "http://localhost:8000/api/dishes/?search=pizza"
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `dishes/serializers.py` | Add 5 new serializers |
| `dishes/views.py` | Add `HomePageView`, update `DishListView` |
| `dishes/urls.py` | Add homepage route |

**No new apps or files needed!**

---

## Future Enhancements

1. **Caching** - Cache homepage response for 5-10 minutes
2. **Personalization** - Filter based on user preferences/location
3. **Banners/Promotions** - Add promotional content section
4. **Popular Near Me** - Add geolocation-based filtering
5. **Recently Viewed** - Track and display user's viewed items

---

## Testing

### Test Homepage Endpoint

```bash
# Get homepage data
curl http://localhost:8000/api/dishes/home/

# With authentication
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/dishes/home/
```

### Test Search

```bash
# Search dishes
curl "http://localhost:8000/api/dishes/?search=pizza"
```

---

## Summary

| Component | Location | Status |
|-----------|----------|--------|
| Homepage Endpoint | `GET /api/dishes/home/` | To implement |
| Search | `GET /api/dishes/?search={}` | To implement |
| Categories | Existing | ✅ Ready |
| Featured Dishes | Aggregated in homepage | To implement |
| Top Chefs | Aggregated in homepage | To implement |
| New Dishes | Aggregated in homepage | To implement |

**Total Implementation Time:** ~1-2 hours

**Files to Modify:**
- `dishes/serializers.py` - Add homepage serializers
- `dishes/views.py` - Add HomePageView, update DishListView with search
- `dishes/urls.py` - Add homepage route
