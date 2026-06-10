import uuid

from django.db import models
from django.core.exceptions import ValidationError


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    image_url = models.URLField(blank=True, null=True)
    # is_popular = models.BooleanField(default=False)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="subcategories")
    delivered_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
    
    def clean(self):
        if self.parent_category_id == self.id:
            raise ValidationError("Category cannot be its own parent.")

    def _ensure_unique_slug(self):
        original_slug = self.slug
        qs = Category.objects.filter(slug=self.slug)
        
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        counter = 1        
        while qs.exists():
            self.slug = f"{original_slug}-{counter}"
            qs = Category.objects.filter(slug=self.slug)
            counter += 1

    def save(self, *args, **kwargs):
        self._ensure_unique_slug()
        models.Model.save(self, *args, **kwargs)


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return self.name

    def _ensure_unique_slug(self):
        original_slug = self.slug
        qs = Product.objects.filter(slug=self.slug)
        
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        
        counter = 1
        while qs.exists():
            self.slug = f"{original_slug}-{counter}"
            qs = Product.objects.filter(slug=self.slug)
            counter += 1

    def save(self, *args, **kwargs):
        self._ensure_unique_slug()
        models.Model.save(self, *args, **kwargs)

