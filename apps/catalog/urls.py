from django.urls import path
from apps.catalog.views import (category_list, product_list, product_detail,)

urlpatterns = [
    path("categories/", category_list, name="public-category-list"),
    path("products/", product_list, name="public-product-list"),
    path("products/<uuid:pk>/", product_detail, name="public-product-detail"),
]