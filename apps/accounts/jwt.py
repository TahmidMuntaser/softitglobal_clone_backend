import uuid
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import permissions
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


ALGORITHM = "HS256"
ACCESS_TOKEN_LIFETIME = timedelta(minutes=30)
REFRESH_TOKEN_LIFETIME = timedelta(days=1)


def _now():
    return datetime.now(timezone.utc)


def _build_payload(user, token_type, lifetime):
    now = _now()
    return {
        "token_type": token_type,
        "user_id": str(user.pk),
        "username": user.get_username(),
        "is_superuser": user.is_superuser,
        "is_staff": user.is_staff,
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
        "jti": str(uuid.uuid4()),
    }


def create_access_token(user):
    payload = _build_payload(user, "access", ACCESS_TOKEN_LIFETIME)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user):
    payload = _build_payload(user, "refresh", REFRESH_TOKEN_LIFETIME)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_token_pair(user):
    return {
        "access": create_access_token(user),
        "refresh": create_refresh_token(user),
    }


def decode_token(token, expected_type):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationFailed("Token has expired.") from exc
    except jwt.PyJWTError as exc:
        raise AuthenticationFailed("Invalid token.") from exc

    if payload.get("token_type") != expected_type:
        raise AuthenticationFailed("Invalid token type.")

    return payload


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith("Bearer "):
            return None

        token = header.split(" ", 1)[1].strip()
        payload = decode_token(token, "access")

        User = get_user_model()
        
        try:
            user = User.objects.get(pk=payload["user_id"])
            
        except User.DoesNotExist as exc:
            raise AuthenticationFailed("User not found.") from exc

        if not user.is_active:
            raise AuthenticationFailed("User is inactive.")

        return (user, payload)


class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )
