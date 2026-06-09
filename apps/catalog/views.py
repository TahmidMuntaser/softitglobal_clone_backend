from uuid import UUID
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import viewsets
from apps.accounts.jwt import IsSuperUser
from apps.catalog.models import Category, Product
from apps.catalog.serializers import CategorySerializer, ProductSerializer

# public endptn 

@api_view(["GET"])
def category_list(request):
    categories = Category.objects.all().order_by("name")
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def product_list(request):
    queryset = Product.objects.select_related("category").all().order_by("name")

    search = request.query_params.get("search")
    category = request.query_params.get("category")

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(slug__icontains=search)
            | Q(category__name__icontains=search)
        )

    if category:
        try:
            queryset = queryset.filter(category_id=UUID(category))
        except ValueError:
            queryset = queryset.filter(category__slug=category)

    serializer = ProductSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def product_detail(request, pk):
    product = Product.objects.select_related("category").get(pk=pk)
    serializer = ProductSerializer(product)
    return Response(serializer.data)

# admin endptn 
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [IsSuperUser]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all().order_by("name")
    serializer_class = ProductSerializer
    permission_classes = [IsSuperUser]