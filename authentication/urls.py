from django.urls import path
from .views import (
    SignupView, LoginView, LogoutView,
    PasswordResetRequestView, PasswordResetConfirmView,
    PaymentCardCreateView, UserProfileView, ProfilePictureUploadView,
    ChefToggleOnlineView, ChefListView,
)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('cards/', PaymentCardCreateView.as_view(), name='payment_card_create'),
    path('profile/<int:user_id>/', UserProfileView.as_view(), name='user_profile'),
    path('profile-picture/', ProfilePictureUploadView.as_view(), name='profile_picture_upload'),
    path('chef/toggle-online/', ChefToggleOnlineView.as_view(), name='chef_toggle_online'),
    path('chefs/', ChefListView.as_view(), name='chef_list'),
]
