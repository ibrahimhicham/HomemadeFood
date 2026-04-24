from django.db import models
from django.utils import timezone
from authentication.models import User  # Using the existing User model


class Category(models.Model):
    """Category model to group dishes"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']


class Dish(models.Model):
    """Dish model representing a menu item created by a chef"""
    chef = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dishes')
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='dishes')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    preparation_time = models.PositiveIntegerField(help_text="Preparation time in minutes")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('chef', 'name')  # Dish name must be unique per chef
        ordering = ['name']


class DishReview(models.Model):
    """Review model for dishes"""
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dish_reviews')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # 1 to 5 stars
    review_text = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review for {self.dish.name} by {self.customer.email}"

    class Meta:
        unique_together = ('dish', 'customer')  # Each customer can review a dish only once
        ordering = ['-created_at']


class DishImage(models.Model):
    """Image model for dishes (optional enhancement)"""
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='dishes/%Y/%m/%d/', default='dishes/dish_zldtcj.jpg')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Image for {self.dish.name}"

    class Meta:
        ordering = ['-is_primary', 'created_at']


class DishVarietySection(models.Model):
    """Section of varieties for a dish (e.g., Size Options, Toppings)"""
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='variety_sections')
    name = models.CharField(max_length=100)  # e.g., "Size Options"
    description = models.TextField(blank=True, null=True)
    is_required = models.BooleanField(default=False)  # Whether customer must select an option

    def __str__(self):
        return f"{self.name} for {self.dish.name}"


class DishVarietyOption(models.Model):
    """Individual option within a variety section (e.g., Small, Medium, Large)"""
    section = models.ForeignKey(DishVarietySection, on_delete=models.CASCADE, related_name='options')
    name = models.CharField(max_length=100)  # e.g., "Small"
    price_adjustment = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # Additional cost
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.section.name})"