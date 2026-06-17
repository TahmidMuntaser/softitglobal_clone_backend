from uuid import UUID

from django.http import Http404
from django.db import transaction
from django.db.models import Q

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import DjangoModelPermissions
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.orders.models import Cart, CartItem, Order
from apps.accounts.permissions import IsSuperUser
from apps.orders.constants import OrderStatus
from apps.orders.serializers import (
    CartAddSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartSerializer,
    CheckoutSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
)
from apps.catalog.models import Product
from apps.orders.services import add_item_to_cart, create_order_from_cart, deliver_order

# public endptn 

@api_view(["POST"])
def deliver_order_api(request, pk):
    order = deliver_order(pk)
    return Response(
        {
            "status": "delivered",
            "order_id": str(order.id),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def cart_add(request):
    serializer = CartAddSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        cart = add_item_to_cart(
            session_id=serializer.validated_data["session_id"],
            product_id=serializer.validated_data["product_id"],
            quantity=serializer.validated_data["quantity"],
        )
    except Product.DoesNotExist:
        return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def cart_detail(request):
    session_id = request.query_params.get("session_id")
    if not session_id:
        return Response({"detail": "session_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cart = Cart.objects.prefetch_related("items__product").get(session_id=session_id)
    except Cart.DoesNotExist:
        raise Http404

    return Response(CartSerializer(cart).data)


@api_view(["PATCH", "DELETE"])
def cart_item_detail(request, pk):
    try:
        cart_item = CartItem.objects.select_related("cart", "product").get(pk=pk)
    except CartItem.DoesNotExist:
        raise Http404

    if request.method == "PATCH":
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart_item.quantity = serializer.validated_data["quantity"]
        cart_item.save(update_fields=["quantity"])

        return Response(CartItemSerializer(cart_item).data)

    if request.method == "DELETE":
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def checkout(request):
    serializer = CheckoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        cart = Cart.objects.prefetch_related("items__product").get(
            session_id=serializer.validated_data["session_id"]
        )
    except Cart.DoesNotExist:
        return Response({"detail": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

    if not cart.items.exists():
        return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

    order = create_order_from_cart(
        cart=cart,
        customer_name=serializer.validated_data["customer_name"],
        phone=serializer.validated_data["phone"],
        address=serializer.validated_data["address"],
    )

    return Response(
        {
            "message": "Order placed successfully.",
            "order_id": order.id,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def order_detail(request, pk):
    try:
        order = Order.objects.prefetch_related("items__product").get(pk=pk)
    except Order.DoesNotExist:
        return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


#  admin endptn 

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related("items__product").all().order_by("-created_at")
    serializer_class = OrderSerializer
    permission_classes = [DjangoModelPermissions]
    http_method_names = ["get", "patch", "head", "options"]

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]

        if new_status == OrderStatus.DELIVERED and order.status != OrderStatus.DELIVERED:
            order = deliver_order(order.id)
        else:
            order.status = new_status
            order.save(update_fields=["status"])

        return Response(self.get_serializer(order).data, status=status.HTTP_200_OK)