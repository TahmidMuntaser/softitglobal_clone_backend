import uuid

from django.db import models
from django.core.exceptions import ValidationError


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    image_url = models.URLField(blank=True, null=True)
    is_popular = models.BooleanField(default=False)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(is_popular=False) | models.Q(image_url__isnull=False),
                name="popular_category_requires_image"
            )
        ]

    def __str__(self):
        return self.name
    
    def clean(self):
        if self.is_popular and not self.image_url:
            raise ValidationError("Popular category must have an image.")


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return self.name

