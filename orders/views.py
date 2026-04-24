from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError, PermissionDenied

from .models import Order, OrderNotification
from .serializers import (
    OrderCreateSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    OrderUpdateSerializer,
    OrderStatusUpdateSerializer,
    OrderNotificationSerializer,
)
from .services import OrderCreateService, OrderStatusService, CancelExpiredOrdersService
from .constants import OrderStatus


class IsConsumer(permissions.BasePermission):
    """Permission class to allow only users with a consumer profile."""

    def has_permission(self, request, view):
        return hasattr(request.user, 'consumer')


class IsChef(permissions.BasePermission):
    """Permission class to allow only users with a chef profile."""

    def has_permission(self, request, view):
        return hasattr(request.user, 'chef')


class OrderCreateView(generics.CreateAPIView):
    """Place a new order (consumer only)."""

    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsConsumer]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        items = validated_data.pop('items', [])

        try:
            service = OrderCreateService(
                customer=request.user,
                chef_id=validated_data['chef_id'],
                items=items,
                delivery_address=validated_data['delivery_address'],
                delivery_longitude=validated_data.get('delivery_longitude'),
                delivery_latitude=validated_data.get('delivery_latitude'),
                special_instructions=validated_data.get('special_instructions'),
            )
            order = service.execute()
        except DjangoValidationError as e:
            raise ValidationError(str(e))

        output_serializer = OrderDetailSerializer(order)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class OrderListView(generics.ListAPIView):
    """List orders filtered by user role."""

    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if hasattr(user, 'consumer'):
            return Order.objects.filter(customer=user)
        elif hasattr(user, 'chef'):
            return Order.objects.filter(chef=user)

        return Order.objects.none()


class OrderDetailView(generics.RetrieveAPIView):
    """Get order details (consumer or chef)."""

    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'order_id'
    lookup_url_kwarg = 'order_id'

    def get_queryset(self):
        user = self.request.user

        if hasattr(user, 'consumer'):
            return Order.objects.filter(customer=user)
        elif hasattr(user, 'chef'):
            return Order.objects.filter(chef=user)

        return Order.objects.none()


class OrderStatusUpdateView(generics.GenericAPIView):
    """Update order status (chef or consumer for cancellation)."""

    serializer_class = OrderStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'order_id'
    lookup_url_kwarg = 'order_id'

    def get_queryset(self):
        user = self.request.user

        if hasattr(user, 'consumer'):
            return Order.objects.filter(customer=user)
        elif hasattr(user, 'chef'):
            return Order.objects.filter(chef=user)

        return Order.objects.none()

    def patch(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        cancellation_reason = serializer.validated_data.get('cancellation_reason')

        try:
            service = OrderStatusService(
                order=order,
                new_status=new_status,
                user=request.user,
                cancellation_reason=cancellation_reason,
            )
            updated_order = service.execute()
        except DjangoValidationError as e:
            raise ValidationError(str(e))
        except PermissionDenied as e:
            raise PermissionDenied(str(e))

        output_serializer = OrderDetailSerializer(updated_order)
        return Response(output_serializer.data)


class OrderNotificationListView(generics.ListAPIView):
    """List notifications for the current user."""

    serializer_class = OrderNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OrderNotification.objects.filter(recipient=self.request.user)


class NotificationMarkReadView(generics.UpdateAPIView):
    """Mark a notification as read."""

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        return OrderNotification.objects.filter(recipient=self.request.user)

    def patch(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        serializer = OrderNotificationSerializer(notification)
        return Response(serializer.data)


class CancelExpiredOrdersView(generics.GenericAPIView):
    """Manually trigger auto-cancel for expired pending orders (admin only)."""

    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        count = CancelExpiredOrdersService.execute()
        return Response({'cancelled_count': count})
