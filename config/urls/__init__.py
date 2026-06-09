from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.accounts.api import token_obtain_pair, token_refresh
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

    path("api/openapi/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    path("api/", include(router.urls)),

    path("api/public/", include("apps.catalog.urls")),
    path("api/public/", include("apps.orders.urls")),
]