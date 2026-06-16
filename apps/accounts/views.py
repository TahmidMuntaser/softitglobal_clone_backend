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
    AdminUserCreateSerializer,
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


# GET /api/roles/
@extend_schema(
    responses=GroupSerializer(many=True),
    description="List all roles"
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSuperUser])
def group_list_get(request):
    return Response(Group.objects.values("id", "name"))


# POST /api/roles/create/
@extend_schema(
    request=GroupSerializer,
    responses=GroupSerializer,
    description="Create a role"
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSuperUser])
def group_list_post(request):
    serializer = GroupCreateSerializer(data=request.data)
    if serializer.is_valid():
        group = serializer.save()
        return Response(GroupSerializer(group).data, status=201)
    return Response(serializer.errors, status=400)


# GET /api/roles/{id}/
@extend_schema(
    responses=GroupSerializer,
    description="Retrieve a role"
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSuperUser])
def group_detail_get(request, pk):
    try:
        group = Group.objects.get(pk=pk)
    except Group.DoesNotExist:
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"id": group.id, "name": group.name})


# PUT and DELETE /api/roles/{id}/update/
@extend_schema(
    methods=["PUT"],
    request=GroupCreateSerializer,
    responses=GroupSerializer,
    description="Update a role"
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None},
    description="Delete a role"
)
@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsSuperUser])
def group_detail_manage(request, pk):
    try:
        group = Group.objects.get(pk=pk)
    except Group.DoesNotExist:
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        serializer = GroupCreateSerializer(group, data=request.data)
        if serializer.is_valid():
            group = serializer.save()
            return Response(GroupSerializer(group).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    group.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# GET /api/permissions/
@extend_schema(
    responses={200: PermissionSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSuperUser])
def permission_list(request):
    permissions = Permission.objects.select_related("content_type")
    return Response(PermissionSerializer(permissions, many=True).data)


# POST /api/roles/{id}/permissions/
@extend_schema(
    request=GroupPermissionSerializer,
    responses={200: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSuperUser])
def group_set_permissions(request, pk):
    try:
        group = Group.objects.get(pk=pk)
    except Group.DoesNotExist:
        return Response({"detail": "Group not found."}, status=404)

    serializer = GroupPermissionSerializer(group, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"message": "Permissions updated."})


# GET, POST /api/admin-users/
@extend_schema_view(
    get=extend_schema(
        responses={200: AdminUserSerializer(many=True)},
    ),
    post=extend_schema(
        request=AdminUserCreateSerializer,
        responses={201: AdminUserSerializer},
    ),
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsSuperUser])
def admin_user_list(request):
    User = get_user_model()

    if request.method == "GET":
        users = User.objects.filter(is_staff=True)
        return Response(AdminUserSerializer(users, many=True).data)

    serializer = AdminUserCreateSerializer(data=request.data)
    if serializer.is_valid():
        role_ids = serializer.validated_data.pop("role_ids", [])
        user = serializer.save()
        if role_ids:
            user.groups.set(Group.objects.filter(id__in=role_ids))
        return Response(AdminUserSerializer(user).data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# GET, PUT, DELETE /api/admin-users/{id}/
@extend_schema_view(
    get=extend_schema(
        responses={200: AdminUserSerializer},
    ),
    put=extend_schema(
        request=AdminUserSerializer,
        responses={200: AdminUserSerializer},
    ),
    delete=extend_schema(
        responses={204: None},
    ),
)
@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsSuperUser])
def admin_user_detail(request, pk):
    User = get_user_model()
    try:
        user = User.objects.get(pk=pk, is_staff=True)
    except User.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(AdminUserSerializer(user).data)

    if request.method == "PUT":
        serializer = AdminUserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# POST /api/admin-users/{id}/roles/
@extend_schema(
    request=UserRoleSerializer,
    responses={200: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSuperUser])
def admin_user_assign_roles(request, pk):
    User = get_user_model()
    try:
        user = User.objects.get(pk=pk, is_staff=True)
    except User.DoesNotExist:
        return Response({"detail": "Not found."}, status=404)

    serializer = UserRoleSerializer(user, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"message": "Roles updated."})