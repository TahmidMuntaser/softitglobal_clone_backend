from django.urls import path
from apps.orders.views import (cart_add, cart_detail, cart_item_detail, checkout,order_detail,)

urlpatterns = [
    path("cart/add/", cart_add),
    path("cart/", cart_detail),
    path("cart/item/<uuid:pk>/", cart_item_detail),
    path("checkout/", checkout),
    path("orders/<uuid:pk>/", order_detail),
]