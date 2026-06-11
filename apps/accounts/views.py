from django.contrib.auth import authenticate, get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from django.http import HttpResponse

from apps.accounts.jwt import create_access_token, create_token_pair, decode_token
from apps.accounts.serializers import (
    TokenObtainPairRequestSerializer,
    TokenObtainPairResponseSerializer,
    TokenRefreshRequestSerializer,
    TokenRefreshResponseSerializer,
)

@extend_schema(
    request=None,
    responses={200: None},
    description="Logout endpoint: client should call this before clearing stored JWTs.",
)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    response = HttpResponse(status=200)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return response


@extend_schema(
    request=TokenObtainPairRequestSerializer,
    responses={200: TokenObtainPairResponseSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def token_obtain_pair(request):
    username = request.data.get("username", "")
    password = request.data.get("password", "")

    user = authenticate(request, username=username, password=password)

    if user is None:
        return Response(
            {"detail": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {"detail": "User is inactive."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_superuser:
        return Response(
            {"detail": "Admin access only."},
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response(
        {
            **create_token_pair(user),
            "user": {
                "id": user.id,
                "username": user.username,
                "is_superuser": user.is_superuser,
            },
        },
        status=status.HTTP_200_OK,
    )


@extend_schema(
    request=TokenRefreshRequestSerializer,
    responses={200: TokenRefreshResponseSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def token_refresh(request):
    refresh = request.data.get("refresh")

    if not refresh:
        return Response(
            {"detail": "refresh is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    payload = decode_token(refresh, "refresh")

    User = get_user_model()
    try:
        user = User.objects.get(pk=payload["user_id"])
    except User.DoesNotExist:
        return Response(
            {"detail": "User not found."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active or not user.is_superuser:
        return Response(
            {"detail": "Admin access only."},
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response(
        {"access": create_access_token(user)},
        status=status.HTTP_200_OK,
    )
