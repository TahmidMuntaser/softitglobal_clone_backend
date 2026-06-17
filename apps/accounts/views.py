from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import (extend_schema, extend_schema_view,)
from django.http import HttpResponse
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.serializers import (
    TokenObtainPairRequestSerializer,
    TokenObtainPairResponseSerializer,
    TokenRefreshRequestSerializer,
    TokenRefreshResponseSerializer,
    GroupSerializer,
    PermissionSerializer,
    AdminUserSerializer,
    GroupPermissionSerializer,
    UserRoleSerializer,
    GroupCreateSerializer,
    GroupUpdateSerializer,
    AdminUserCreateSerializer,
    AdminUserUpdateSerializer,
)
from apps.accounts.permissions import IsSuperUser

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


    if not (user.is_superuser or user.is_staff):
        return Response(
            {"detail": "Admin access only."},
            status=status.HTTP_403_FORBIDDEN,
        )
        
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    return Response(
        {
            "access": str(access),
            "refresh": str(refresh),
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

    try:
        token_obj = RefreshToken(refresh)
        payload = token_obj.payload
    except Exception:
        return Response(
            {"detail": "Invalid refresh token."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    User = get_user_model()
    try:
        user = User.objects.get(pk=payload.get("user_id"))
    except User.DoesNotExist:
        return Response(
            {"detail": "User not found."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active or not (user.is_superuser or user.is_staff):
        return Response(
            {"detail": "Admin access only."},
            status=status.HTTP_403_FORBIDDEN,
        )
        
    new_access = token_obj.access_token
    return Response(
        {"access": str(new_access)},
        status=status.HTTP_200_OK,
    )

User = get_user_model()


# grp / role

@extend_schema(responses=GroupSerializer(many=True))
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSuperUser])
def group_list_get(request):
    groups = Group.objects.all()
    return Response(GroupSerializer(groups, many=True).data)


@extend_schema(request=GroupCreateSerializer, responses=GroupSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSuperUser])
def group_list_post(request):
    serializer = GroupCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    group = serializer.save()
    return Response(GroupSerializer(group).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSuperUser])
def group_detail_get(request, pk):
    try:
        group = Group.objects.get(pk=pk)
    except Group.DoesNotExist:
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response(GroupSerializer(group).data)


@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsSuperUser])
def group_detail_manage(request, pk):
    
    try:
        group = Group.objects.get(pk=pk)
    except Group.DoesNotExist:
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        serializer = GroupUpdateSerializer(group, data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(GroupSerializer(group).data)

    group.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# permissions

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSuperUser])
def permission_list(request):
    permissions = Permission.objects.select_related("content_type")
    return Response(PermissionSerializer(permissions, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSuperUser])
def group_set_permissions(request, pk):
    try:
        group = Group.objects.get(pk=pk)
    except Group.DoesNotExist:
        return Response({"detail": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = GroupPermissionSerializer(group, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({"message": "Permissions updated"})


# admin user management

@extend_schema_view(
    get=extend_schema(responses=AdminUserSerializer(many=True)),
    post=extend_schema(request=AdminUserCreateSerializer, responses=AdminUserSerializer),
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsSuperUser])
def admin_user_list(request):

    if request.method == "GET":
        users = User.objects.filter(is_staff=True)
        return Response(AdminUserSerializer(users, many=True).data)

    serializer = AdminUserCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.save()
    return Response(AdminUserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(responses=AdminUserSerializer),
    put=extend_schema(request=AdminUserUpdateSerializer, responses=AdminUserSerializer),
    delete=extend_schema(responses={204: None}),
)
@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsSuperUser])
def admin_user_detail(request, pk):

    try:
        user = User.objects.get(pk=pk, is_staff=True)
    except User.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(AdminUserSerializer(user).data)

    if request.method == "PUT":

        if request.user == user:
            return Response(
                {"detail": "Cannot modify own account."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(AdminUserSerializer(user).data)

    if request.user == user:
        return Response(
            {"detail": "Cannot delete own account."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# role assaign

@extend_schema(request=UserRoleSerializer, responses={200: None})
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSuperUser])
def admin_user_assign_roles(request, pk):

    try:
        user = User.objects.get(pk=pk, is_staff=True)
    except User.DoesNotExist:
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserRoleSerializer(user, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({"message": "Roles updated"})



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user

    if user.is_superuser:
        permissions = list(
            Permission.objects.values_list("codename", flat=True)
        )
    else:
        permissions = list(user.get_all_permissions())

    return Response({
        "id": user.id,        
        "username": user.username,        
        "is_superuser": user.is_superuser,
        "is_staff": user.is_staff,
        "groups": list(user.groups.values_list("name", flat=True)),
        "permissions": permissions,
    })