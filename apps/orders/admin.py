from django.contrib import admin
from apps.orders.models import Cart, CartItem, Order, OrderItem
from apps.orders.services import deliver_order


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'created_at', 'updated_at')
    search_fields = ('session_id',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')
    search_fields = ('cart__session_id', 'product__name')
    list_filter = ('product',)
    

@admin.action(description="Mark selected orders as delivered")
def make_delivered(modeladmin, request, queryset):
    for order in queryset:
        deliver_order(order.id)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_id', 'customer_name', 'phone', 'total_amount', 'created_at')
    search_fields = ('customer_name', 'phone', 'session_id')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price_snapshot')
    search_fields = ('order__customer_name', 'product__name')
    list_filter = ('product',)
