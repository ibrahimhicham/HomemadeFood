from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.OrderListView.as_view(), name='order-list'),
    path('create/', views.OrderCreateView.as_view(), name='order-create'),
    path('<uuid:order_id>/', views.OrderDetailView.as_view(), name='order-detail'),
    path(
        '<uuid:order_id>/status/',
        views.OrderStatusUpdateView.as_view(),
        name='order-status-update',
    ),
    path(
        'notifications/',
        views.OrderNotificationListView.as_view(),
        name='order-notifications',
    ),
    path(
        'notifications/<int:pk>/read/',
        views.NotificationMarkReadView.as_view(),
        name='notification-mark-read',
    ),
    path(
        'cancel-expired/',
        views.CancelExpiredOrdersView.as_view(),
        name='cancel-expired-orders',
    ),
]
