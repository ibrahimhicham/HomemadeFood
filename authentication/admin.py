from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import PaymentCard, Chef, Consumer

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Chef)
class ChefAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'is_verified', 'years_of_experience', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_filter = ('is_verified', 'rating', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Consumer)
class ConsumerAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_orders', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PaymentCard)
class PaymentCardAdmin(admin.ModelAdmin):
    list_display = ('user', 'card_last4', 'cardholder_name', 'exp_month', 'exp_year', 'is_default')
    search_fields = ('user__email', 'card_last4')
    readonly_fields = ('created_at',)
