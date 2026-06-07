from rest_framework import serializers

from apps.catalog.models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'image_url', 'parent_category', 'delivered_count',)


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=Category.objects.all(),
        write_only=True,
        required=False,
        help_text='Optional category UUID for writes.',
    )

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'price', 'image_url', 'category', 'category_id')
