from decimal import Decimal
from django.db import transaction
from collections import defaultdict
from apps.catalog.models import Product, Category
from apps.orders.models import Cart, CartItem, Order, OrderItem
from .constants import OrderStatus
from django.db import transaction
from django.db.models import F


# cart

def get_or_create_cart(session_id):
    return Cart.objects.get_or_create(session_id=session_id)[0]


def calculate_cart_total(cart):
    return sum(
        item.product.price * item.quantity
        for item in cart.items.select_related("product")
    )


def add_item_to_cart(*, session_id, product_id, quantity):
    cart = get_or_create_cart(session_id)
    product = Product.objects.get(pk=product_id)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": quantity},
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save(update_fields=["quantity"])

    return cart


# order create

@transaction.atomic
def create_order_from_cart(*, cart, customer_name, phone, address):

    items = list(cart.items.select_related("product__category"))

    if not items:
        raise ValueError("Cart is empty.")

    total_amount = sum(
        item.product.price * item.quantity for item in items
    )

    order = Order.objects.create(
        session_id=cart.session_id,
        customer_name=customer_name,
        phone=phone,
        address=address,
        total_amount=total_amount,
        status=OrderStatus.PENDING,
        popularity_processed=False,
    )

    OrderItem.objects.bulk_create([
        OrderItem(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price_snapshot=item.product.price,
        )
        for item in items
    ])

    cart.items.all().delete()

    return order


# transition

@transaction.atomic
def deliver_order(order_id):

    order = Order.objects.select_for_update().prefetch_related(
        "items__product__category"
    ).get(id=order_id)

    if order.status == OrderStatus.DELIVERED:
        return order

    order.status = OrderStatus.DELIVERED
    order.save(update_fields=["status"])

    category_updates = defaultdict(int)

    for item in order.items.all():
        qty = item.quantity
        category = item.product.category

        # walk up hierarchy
        while category:
            category_updates[category.id] += qty
            category = category.parent_category

    for cat_id, qty in category_updates.items():
        Category.objects.filter(id=cat_id).update(
            delivered_count=F("delivered_count") + qty
        )

    return order