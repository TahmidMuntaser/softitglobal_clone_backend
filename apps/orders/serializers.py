import re
from decimal import Decimal

from rest_framework import serializers

from apps.catalog.serializers import ProductSerializer
from apps.orders.constants import OrderStatus
from apps.orders.models import Cart, CartItem, Order, OrderItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'quantity', 'subtotal')

    def get_subtotal(self, obj):
        return str(obj.product.price * obj.quantity)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('id', 'session_id', 'created_at', 'updated_at', 'items', 'subtotal', 'total')

    def _cart_total(self, obj):
        return sum((item.product.price * item.quantity for item in obj.items.select_related('product').all()), Decimal('0.00'))

    def get_subtotal(self, obj):
        return str(self._cart_total(obj))

    def get_total(self, obj):
        return str(self._cart_total(obj))


class CartAddSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=True, help_text='Cart session UUID stored by the frontend.')
    product_id = serializers.UUIDField(required=True, help_text='Product UUID to add to the cart.')
    quantity = serializers.IntegerField(required=True, min_value=1, help_text='Number of units to add.')


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=True, min_value=1, help_text='Updated item quantity.')


class CheckoutSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=True, help_text='Cart session UUID stored by the frontend.')
    customer_name = serializers.CharField(required=True, max_length=255, help_text='Customer full name.')
    phone = serializers.CharField(required=True, max_length=20, help_text='Customer phone number.')
    address = serializers.CharField(required=True, help_text='Shipping address.')
    
    def validate_phone(self, value):
        pattern = r'^(?:\+8801[3-9]\d{8}|01[3-9]\d{8})$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("Invalid phone number format")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'quantity', 'price_snapshot')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            'id',
            'session_id',
            'customer_name',
            'phone',
            'address',
            'total_amount',
            'status',
            'created_at',
            'items',
        )


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderStatus.CHOICES)
