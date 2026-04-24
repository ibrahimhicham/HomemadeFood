from django.contrib import admin
from .models import Category, Dish, DishReview, DishImage, DishVarietySection, DishVarietyOption


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('name', 'chef', 'category', 'price', 'is_available', 'created_at')
    list_filter = ('category', 'is_available', 'created_at')
    search_fields = ('name', 'description', 'chef__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DishReview)
class DishReviewAdmin(admin.ModelAdmin):
    list_display = ('dish', 'customer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('dish__name', 'customer__email', 'review_text')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DishImage)
class DishImageAdmin(admin.ModelAdmin):
    list_display = ('dish', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('dish__name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DishVarietySection)
class DishVarietySectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'dish', 'is_required')
    list_filter = ('is_required',)
    search_fields = ('name', 'dish__name')


@admin.register(DishVarietyOption)
class DishVarietyOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'price_adjustment', 'is_available')
    list_filter = ('is_available', 'section')
    search_fields = ('name', 'section__name')