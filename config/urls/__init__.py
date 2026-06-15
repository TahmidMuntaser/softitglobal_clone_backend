from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.accounts.views import (
    token_obtain_pair,
    token_refresh,
    logout,
    group_list,
    group_detail,
    group_set_permissions,
    permission_list,
    admin_user_list,
    admin_user_detail,
    admin_user_assign_roles,
)
from apps.catalog.views import CategoryViewSet, ProductViewSet
from apps.orders.views import OrderViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("orders", OrderViewSet, basename="order")


def home(request):
    return redirect("/api/docs/")


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),

    path("api/token/", token_obtain_pair),
    path("api/token/refresh/", token_refresh),
    path("api/logout/", logout),

    path("api/openapi/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    path("api/", include(router.urls)),
    
    # rbac endptn 
    path("api/roles/", group_list, name="group-list"),
    path("api/roles/<int:pk>/", group_detail, name="group-detail"),
    path("api/roles/<int:pk>/permissions/", group_set_permissions, name="group-set-permissions"),
    path("api/permissions/", permission_list, name="permission-list"),
    path("api/admin-users/", admin_user_list, name="admin-user-list"),
    path("api/admin-users/<int:pk>/", admin_user_detail, name="admin-user-detail"),
    path("api/admin-users/<int:pk>/roles/", admin_user_assign_roles, name="admin-user-assign-roles"),

    path("api/public/", include("apps.catalog.urls")),
    path("api/public/", include("apps.orders.urls")),
]