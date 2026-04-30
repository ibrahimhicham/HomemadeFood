from rest_framework import generics, permissions, exceptions
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count
from .models import Category, Dish, DishReview, DishImage, DishVarietySection, DishVarietyOption
from .serializers import (
    CategorySerializer, DishSerializer, DishListSerializer,
    DishReviewSerializer, DishImageSerializer,
    DishVarietySectionSerializer, DishVarietyOptionSerializer,
    HomePageSerializer)
from django.db.models import Avg, Count
import cloudinary.uploader
from rest_framework.parsers import MultiPartParser, FormParser
from .pagination import StandardResultsSetPagination
from authentication.models import User, Chef

from django.http import JsonResponse

def refresh_view(request):
    return JsonResponse({"message": "Refreshed!"})

class CategoryListView(generics.ListAPIView):
    """List all active categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CategoryDetailView(generics.RetrieveAPIView):
    """Get detailed information about a specific category"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]




class DishListView(generics.ListAPIView):
    """
    List all available dishes with optional filtering:
    - ?search={query}: Search by dish name or chef name
    - ?category_name={category_name}: Filter by category name
    - ?chef-id={chef_id}: Filter by chef ID
    - ?is_available=true/false: Filter by availability
    - ?min_price={price}&max_price={price}: Filter by price range
    """
    serializer_class = DishListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Dish.objects.filter(is_available=True).select_related('chef', 'category').prefetch_related('reviews')

        # Search functionality - search by dish name or chef name
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(chef__first_name__icontains=search_query) |
                Q(chef__last_name__icontains=search_query)
            )

        # Apply category filter by name if specified
        category_name = self.request.query_params.get('category_name', None)
        if category_name is not None:
            queryset = queryset.filter(category__name__icontains=category_name)

        # Apply chef-id filter if specified
        chef_id = self.request.query_params.get('chef-id', None)
        if chef_id is not None:
            queryset = queryset.filter(chef_id=chef_id)

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


class DishDetailView(generics.RetrieveAPIView):
    """Get detailed information about a specific dish"""
    serializer_class = DishSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Optimized queryset with annotations for rating and review count.
        Prefetches only the latest 3 reviews for preview and chef profile.
        """
        from django.db.models import Prefetch
        from authentication.models import Chef
        
        return Dish.objects.select_related('chef', 'category').prefetch_related(
            'images',
            Prefetch(
                'chef__chef',
                queryset=Chef.objects.all()
            ),
            Prefetch(
                'reviews',
                queryset=DishReview.objects.select_related('customer')
                    .order_by('-created_at')[:3],
                to_attr='latest_reviews'
            )
        ).annotate(
            rating_avg=Avg('reviews__rating'),
            reviews_count=Count('reviews')
        )


class ChefCategoryListView(generics.ListCreateAPIView):
    """List and create categories for the authenticated chef"""
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return categories created by the authenticated chef
        if hasattr(self.request.user, 'dishes'):
            # Get categories that have dishes created by this chef
            dish_categories = Dish.objects.filter(
                chef=self.request.user
            ).values_list('category_id', flat=True).distinct()
            return Category.objects.filter(id__in=dish_categories)
        return Category.objects.none()


class DishVarietySectionCreateView(generics.CreateAPIView):
    """Create a new variety section for a dish (only dish creator can access)"""
    serializer_class = DishVarietySectionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        dish_id = self.kwargs['dish_id']
        dish = get_object_or_404(Dish, id=dish_id)

        # Check if the authenticated user is the dish creator
        if dish.chef != self.request.user:
            raise permissions.PermissionDenied("Only the dish creator can add variety sections.")

        serializer.save(dish=dish)


class DishVarietySectionUpdateView(generics.UpdateAPIView):
    """Update a variety section (only dish creator can access)"""
    serializer_class = DishVarietySectionSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'section_id'

    def get_queryset(self):
        # Only allow updating sections of dishes created by the authenticated user
        return DishVarietySection.objects.filter(dish__chef=self.request.user)


class DishVarietySectionDeleteView(generics.DestroyAPIView):
    """Delete a variety section (only dish creator can access)"""
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'section_id'

    def get_queryset(self):
        # Only allow deleting sections of dishes created by the authenticated user
        return DishVarietySection.objects.filter(dish__chef=self.request.user)


class DishVarietyOptionCreateView(generics.CreateAPIView):
    """Create a new variety option within a section (only dish creator can access)"""
    serializer_class = DishVarietyOptionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        section_id = self.kwargs['section_id']
        section = get_object_or_404(DishVarietySection, id=section_id)

        # Check if the authenticated user is the dish creator
        if section.dish.chef != self.request.user:
            raise permissions.PermissionDenied("Only the dish creator can add variety options.")

        serializer.save(section=section)


class DishVarietyOptionUpdateView(generics.UpdateAPIView):
    """Update a variety option (only dish creator can access)"""
    serializer_class = DishVarietyOptionSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'option_id'

    def get_queryset(self):
        # Only allow updating options of sections from dishes created by the authenticated user
        return DishVarietyOption.objects.filter(section__dish__chef=self.request.user)


class DishVarietyOptionDeleteView(generics.DestroyAPIView):
    """Delete a variety option (only dish creator can access)"""
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'option_id'

    def get_queryset(self):
        # Only allow deleting options of sections from dishes created by the authenticated user
        return DishVarietyOption.objects.filter(section__dish__chef=self.request.user)


class ChefDishListView(generics.ListCreateAPIView):
    """List and create dishes for the authenticated chef"""
    serializer_class = DishListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Since this is accessed via /chef/ endpoint, we return dishes for the authenticated user
        user_type = self.request.user.get_user_type()
        if user_type != 'chef':
            return Dish.objects.none()
        return Dish.objects.filter(chef=self.request.user).select_related('category')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DishSerializer
        return DishListSerializer

    def perform_create(self, serializer):
        # Check if the user is a chef before allowing dish creation
        user_type = self.request.user.get_user_type()
        if user_type != 'chef':
            raise exceptions.PermissionDenied("Only chefs can create dishes")
        serializer.save(chef=self.request.user)


class ChefDishDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a specific dish for the authenticated chef"""
    serializer_class = DishSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only allow access to dishes created by this chef
        # The pk parameter comes from the URL pattern
        return Dish.objects.filter(chef=self.request.user)




class ReviewListCreateView(generics.ListCreateAPIView):
    """
    List all reviews for a dish with pagination or create a new review.
    
    Pagination:
    - GET /api/dishes/{id}/reviews/?page=1&page_size=10
    """
    serializer_class = DishReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        dish_id = self.kwargs['dish_id']
        return DishReview.objects.filter(dish_id=dish_id).select_related('customer').order_by('-created_at')


    def perform_create(self, serializer):
        dish_id = self.kwargs['dish_id']
        dish = get_object_or_404(Dish, id=dish_id)

        user_type = self.request.user.get_user_type()
        if user_type != 'consumer':
            raise permissions.PermissionDenied("Only customers can submit reviews")

        existing_review = DishReview.objects.filter(
            dish=dish,
            customer=self.request.user
        ).first()

        if existing_review:
            raise permissions.PermissionDenied("You have already reviewed this dish")

        # ✅ Save review first
        review = serializer.save(dish=dish, customer=self.request.user)

        # ✅ Get the chef
        chef = dish.chef

        # ✅ Aggregate ALL reviews for this chef's dishes
        stats = DishReview.objects.filter(
            dish__chef=chef
        ).aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id')
        )

        # ✅ Update chef
        chef.rating = stats['avg_rating'] or 0
        chef.total_reviews = stats['total_reviews']
        chef.save(update_fields=['rating', 'total_reviews'])

        # Check if the user has already reviewed this dish
        existing_review = DishReview.objects.filter(
            dish=dish,
            customer=self.request.user
        ).first()

        if existing_review:
            raise permissions.PermissionDenied("You have already reviewed this dish")

        serializer.save(dish=dish, customer=self.request.user)


class DishVarietySectionListCreateView(generics.ListCreateAPIView):
    """List all variety sections for a dish or create a new section"""
    serializer_class = DishVarietySectionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        dish_id = self.kwargs['dish_id']  # Matches the URL parameter name
        return DishVarietySection.objects.filter(dish_id=dish_id)

    def perform_create(self, serializer):
        dish_id = self.kwargs['dish_id']  # Matches the URL parameter name
        dish = get_object_or_404(Dish, id=dish_id)

        # Check if the authenticated user is the dish creator
        if dish.chef != self.request.user:
            raise permissions.PermissionDenied("Only the dish creator can add variety sections.")

        serializer.save(dish=dish)


class DishVarietySectionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a specific variety section"""
    serializer_class = DishVarietySectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        dish_id = self.kwargs['dish_id']  # Matches the URL parameter name
        section_id = self.kwargs['section_id']
        # Only allow access to sections of dishes created by the authenticated user
        return DishVarietySection.objects.filter(
            dish_id=dish_id,
            id=section_id,
            dish__chef=self.request.user
        )


class DishVarietyOptionListCreateView(generics.ListCreateAPIView):
    """List all options in a section or create a new option"""
    serializer_class = DishVarietyOptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        dish_id = self.kwargs['dish_id']  # Matches the URL parameter name
        section_id = self.kwargs['section_id']
        return DishVarietyOption.objects.filter(
            section_id=section_id,
            section__dish_id=dish_id
        )

    def perform_create(self, serializer):
        dish_id = self.kwargs['dish_id']  # Matches the URL parameter name
        section_id = self.kwargs['section_id']
        section = get_object_or_404(DishVarietySection, id=section_id)

        # Verify that the section belongs to the specified dish
        if section.dish_id != dish_id:
            raise permissions.PermissionDenied("Invalid section for this dish")

        # Check if the authenticated user is the dish creator
        if section.dish.chef != self.request.user:
            raise permissions.PermissionDenied("Only the dish creator can add variety options.")

        serializer.save(section=section)


class DishVarietyOptionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a specific variety option"""
    serializer_class = DishVarietyOptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        dish_id = self.kwargs['dish_id']  # Matches the URL parameter name
        section_id = self.kwargs['section_id']
        option_id = self.kwargs['option_id']
        # Only allow access to options of sections from dishes created by the authenticated user
        return DishVarietyOption.objects.filter(
            section__dish_id=dish_id,
            section_id=section_id,
            id=option_id,
            section__dish__chef=self.request.user
        )



class DishImageCreateView(generics.CreateAPIView):
    serializer_class = DishImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        dish_id = self.kwargs['dish_id']
        dish = get_object_or_404(Dish, id=dish_id)

        # ✅ Correct ownership check
        if dish.chef.user != self.request.user:
            raise permissions.PermissionDenied("Only the dish creator can add images.")

        serializer.save(dish=dish)

class DishImageUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DishImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        dish_id = self.kwargs['dish_id']
        image_id = self.kwargs['image_id']

        queryset = DishImage.objects.filter(dish_id=dish_id, id=image_id)

        # ✅ Restrict write operations to dish owner
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            queryset = queryset.filter(dish__chef__user=self.request.user)

        return queryset

    # ✅ Delete image from Cloudinary when deleting record
    def perform_destroy(self, instance):
        if instance.image:
            cloudinary.uploader.destroy(instance.image.public_id)  # Delete image from Cloudinary

    # ✅ Replace image safely (delete old one)
    def perform_update(self, serializer):
        instance = self.get_object()

        if 'image' in self.request.FILES:
            if instance.image:
                instance.image.delete(save=False)

        serializer.save()


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