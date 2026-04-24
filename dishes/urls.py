from django.urls import path
from . import views

urlpatterns = [
    # Homepage endpoint
    path('home/', views.HomePageView.as_view(), name='home-page'),

    # Category endpoints
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),

    # Dish endpoints
    path('', views.DishListView.as_view(), name='dish-list'),
    path('<int:pk>/', views.DishDetailView.as_view(), name='dish-detail'),

    # Chef-specific dish endpoints
    path('chef/', views.ChefDishListView.as_view(), name='chef-dish-list'),
    path('chef/<int:pk>/', views.ChefDishDetailView.as_view(), name='chef-dish-detail'),

    # Review endpoints
    path('<int:dish_id>/reviews/', views.ReviewListCreateView.as_view(), name='dish-reviews'),

    # Variety endpoints
    path('<int:dish_id>/varieties/', views.DishVarietySectionListCreateView.as_view(), name='dish-varieties-list-create'),
    path('<int:dish_id>/varieties/<int:section_id>/', views.DishVarietySectionRetrieveUpdateDestroyView.as_view(), name='dish-variety-section-detail'),
    path('<int:dish_id>/varieties/<int:section_id>/options/', views.DishVarietyOptionListCreateView.as_view(), name='dish-variety-options-list-create'),
    path('<int:dish_id>/varieties/<int:section_id>/options/<int:option_id>/', views.DishVarietyOptionRetrieveUpdateDestroyView.as_view(), name='dish-variety-option-detail'),

    # Dish Image endpoints (Chef only)
    path('<int:dish_id>/images/create/', views.DishImageCreateView.as_view(), name='dish-image-create'),
    path('<int:dish_id>/images/<int:image_id>/', views.DishImageUpdateDeleteView.as_view(), name='dish-image-detail'),
]