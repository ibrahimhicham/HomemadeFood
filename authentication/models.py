from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils import timezone
from django.conf import settings

class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, phone_number, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, first_name, last_name, phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # common attributes
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, unique=True)
    profile_picture = models.ImageField(upload_to='profiles/', default=settings.DEFAULT_PROFILE_PICTURE)
    address_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']

    def __str__(self):
        return f"{self.email} ({self.first_name} {self.last_name})"

    def get_user_type(self):
        """Return 'chef' or 'consumer' based on related objects."""
        if hasattr(self, 'chef'):
            return 'chef'
        elif hasattr(self, 'consumer'):
            return 'consumer'
        return None


class Chef(models.Model):
    """Chef-specific profile extending User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chef')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True, null=True)
    cuisine_specialties = models.CharField(max_length=255, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False, help_text="Whether the chef is currently available to accept orders")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chef: {self.user.email}"


class Consumer(models.Model):
    """Consumer-specific profile extending User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='consumer')
    total_orders = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Consumer: {self.user.email}"


class PaymentCard(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='payment_cards')
    card_last4 = models.CharField(max_length=4)
    cardholder_name = models.CharField(max_length=128)
    exp_month = models.PositiveSmallIntegerField()
    exp_year = models.PositiveSmallIntegerField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"**** **** **** {self.card_last4} ({self.user.email})"


# Signals to toggle user active state based on presence of payment cards
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """Log user creation for debugging."""
    if created:
        pass  # User created; Chef/Consumer will be created separately or on demand

@receiver(post_save, sender=PaymentCard)
def activate_user_on_card_added(sender, instance, created, **kwargs):
    """Activate user when they add their first payment card."""
    if created and instance.user.payment_cards.count() == 1:
        instance.user.is_active = True
        instance.user.save()

@receiver(post_delete, sender=PaymentCard)
def deactivate_user_if_no_cards(sender, instance, **kwargs):
    """Deactivate user if they remove their last payment card."""
    if instance.user.payment_cards.count() == 0:
        instance.user.is_active = False
        instance.user.save()
