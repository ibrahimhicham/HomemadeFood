from rest_framework import serializers
from .models import Order, OrderItem, OrderItemVarietySelection, OrderNotification
from authentication.models import User
from dishes.models import Dish


class OrderItemInputSerializer(serializers.Serializer):
    """Input serializer for order items (write-only, nested inside order creation)."""

    dish_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    variety_selections = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        required=False,
        default=list,
    )
    special_requests = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )


class OrderItemReadSerializer(serializers.ModelSerializer):
    """Read serializer for order items in order details."""

    dish_name = serializers.CharField(source='dish_name_snapshot')
    dish_base_price = serializers.CharField(source='dish_base_price_snapshot')
    variety_selections = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'dish_name',
            'dish_base_price',
            'quantity',
            'unit_price',
            'item_total',
            'special_requests',
            'variety_selections',
        ]

    def get_variety_selections(self, obj):
        return [
            {
                'section_name': vs.section_name,
                'option_name': vs.option_name,
                'price_adjustment': vs.option_price_adjustment,
            }
            for vs in obj.variety_selections.all()
        ]


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders."""

    chef_id = serializers.IntegerField()
    delivery_address = serializers.CharField()
    delivery_longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    delivery_latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    special_instructions = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    items = OrderItemInputSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for order list view."""

    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    chef_name = serializers.CharField(source='chef_name_snapshot')
    items_count = serializers.SerializerMethodField()
    estimated_ready_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'order_id',
            'customer_name',
            'chef_name',
            'status',
            'total_amount',
            'created_at',
            'items_count',
            'estimated_ready_time',
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for order detail view."""

    items = OrderItemReadSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    chef_name = serializers.CharField(source='chef_name_snapshot', read_only=True)

    class Meta:
        model = Order
        fields = [
            'order_id',
            'customer',
            'customer_name',
            'chef',
            'chef_name',
            'status',
            'subtotal',
            'delivery_fee',
            'total_amount',
            'estimated_preparation_minutes',
            'estimated_ready_time',
            'delivery_address',
            'delivery_longitude',
            'delivery_latitude',
            'estimated_delivery_time',
            'special_instructions',
            'created_at',
            'updated_at',
            'accepted_at',
            'out_for_delivery_at',
            'delivered_at',
            'cancelled_at',
            'cancelled_by',
            'cancellation_reason',
            'items',
        ]


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order status (legacy, kept for compatibility)."""

    class Meta:
        model = Order
        fields = ['status']


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Serializer for order status transitions."""

    status = serializers.ChoiceField(
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('out_for_delivery', 'Out for Delivery'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled'),
            ('rejected', 'Rejected'),
        ]
    )
    cancellation_reason = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )


class OrderNotificationSerializer(serializers.ModelSerializer):
    """Serializer for order notifications."""

    order_id = serializers.UUIDField(source='order.order_id', read_only=True)
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', read_only=True
    )

    class Meta:
        model = OrderNotification
        fields = [
            'id',
            'order_id',
            'notification_type',
            'notification_type_display',
            'message',
            'is_read',
            'created_at',
        ]
