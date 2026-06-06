from django.contrib import admin

from apps.catalog.models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'image_url', 'is_popular', 'parent_category')
    search_fields = ('name', 'slug', 'is_popular', 'parent_category')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'category')
    search_fields = ('name', 'slug')
    list_filter = ('category',)
