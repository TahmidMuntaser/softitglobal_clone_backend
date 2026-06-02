from django.http import Http404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema

from apps.orders.models import Cart, CartItem, Order
from apps.orders.serializers import (
    CartAddSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartSerializer,
    CheckoutSerializer,
    OrderSerializer,
)
from apps.catalog.models import Product
from apps.orders.services import add_item_to_cart, create_order_from_cart


class CartAddAPIView(APIView):
    @extend_schema(
        request=CartAddSerializer,
        responses={201: CartSerializer},
    )
    def post(self, request):
        serializer = CartAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            cart = add_item_to_cart(
                session_id=serializer.validated_data['session_id'],
                product_id=serializer.validated_data['product_id'],
                quantity=serializer.validated_data['quantity'],
            )
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class CartDetailAPIView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='session_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Cart session UUID stored by the frontend.',
            )
        ],
        responses={200: CartSerializer},
    )
    def get(self, request):
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'detail': 'session_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart = Cart.objects.prefetch_related('items__product').get(session_id=session_id)
        except Cart.DoesNotExist:
            raise Http404

        return Response(CartSerializer(cart).data)


class CartItemDetailAPIView(APIView):
    @extend_schema(
        request=CartItemUpdateSerializer,
        responses={200: CartItemSerializer},
    )
    def patch(self, request, pk):
        try:
            cart_item = CartItem.objects.select_related('cart', 'product').get(pk=pk)
        except CartItem.DoesNotExist:
            raise Http404

        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_item.quantity = serializer.validated_data['quantity']
        cart_item.save(update_fields=['quantity'])
        return Response(CartItemSerializer(cart_item).data)

    def delete(self, request, pk):
        try:
            cart_item = CartItem.objects.get(pk=pk)
        except CartItem.DoesNotExist:
            raise Http404

        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckoutAPIView(APIView):
    @extend_schema(
        request=CheckoutSerializer,
        responses={201: None},
    )
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cart = Cart.objects.prefetch_related('items__product').get(
                session_id=serializer.validated_data['session_id']
            )
        except Cart.DoesNotExist:
            return Response({'detail': 'Cart not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not cart.items.exists():
            return Response({'detail': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        order = create_order_from_cart(
            cart=cart,
            customer_name=serializer.validated_data['customer_name'],
            phone=serializer.validated_data['phone'],
            address=serializer.validated_data['address'],
        )

        return Response(
            {
                'message': 'Order placed successfully.',
                'order_id': order.id,
            },
            status=status.HTTP_201_CREATED,
        )


class OrderDetailAPIView(generics.RetrieveAPIView):
    queryset = Order.objects.prefetch_related('items__product').all()
    serializer_class = OrderSerializer
    lookup_field = 'pk'
