from django.urls import path

from apps.orders.views import CartAddAPIView, CartDetailAPIView, CartItemDetailAPIView, CheckoutAPIView, OrderDetailAPIView

urlpatterns = [
    path('cart/add/', CartAddAPIView.as_view(), name='cart-add'),
    path('cart/', CartDetailAPIView.as_view(), name='cart-detail'),
    path('cart/item/<uuid:pk>/', CartItemDetailAPIView.as_view(), name='cart-item-detail'),
    path('checkout/', CheckoutAPIView.as_view(), name='checkout'),
    path('orders/<uuid:pk>/', OrderDetailAPIView.as_view(), name='order-detail'),
]
