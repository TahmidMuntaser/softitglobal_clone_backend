from decimal import Decimal

from django.db import transaction

from apps.catalog.models import Product
from apps.orders.models import Cart, CartItem, Order, OrderItem


def get_or_create_cart(session_id):
    cart, _ = Cart.objects.get_or_create(session_id=session_id)
    return cart


def calculate_cart_total(cart):
    total = Decimal('0.00')
    for item in cart.items.select_related('product').all():
        total += item.product.price * item.quantity
    return total


@transaction.atomic
def create_order_from_cart(*, cart, customer_name, phone, address):
    items = list(cart.items.select_related('product').all())
    if not items:
        raise ValueError('Cart is empty.')

    total_amount = Decimal('0.00')
    for item in items:
        total_amount += item.product.price * item.quantity

    order = Order.objects.create(
        session_id=cart.session_id,
        customer_name=customer_name,
        phone=phone,
        address=address,
        total_amount=total_amount,
    )

    order_items = [
        OrderItem(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price_snapshot=item.product.price,
        )
        for item in items
    ]
    OrderItem.objects.bulk_create(order_items)
    cart.items.all().delete()

    return order


def add_item_to_cart(*, session_id, product_id, quantity):
    cart = get_or_create_cart(session_id)
    product = Product.objects.get(pk=product_id)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity},
    )
    if not created:
        cart_item.quantity += quantity
        cart_item.save(update_fields=['quantity'])
    return cart
