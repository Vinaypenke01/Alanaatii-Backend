"""
Catalog models — all purchasable items managed by admin.
Single CatalogItem table with category discrimination.
"""
import uuid
from django.db import models
from django.utils import timezone


class CatalogCategory(models.TextChoices):
    PAPER = 'paper', 'Letter Paper'
    BOX = 'box', 'Gift Box'
    GIFT = 'gift', 'Gift Add-on'
    STYLE = 'style', 'Text Style'
    PACKAGE = 'package', 'Script Package'
    LETTER_THEME = 'letter_theme', 'Letter Theme'


class CatalogItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=20, choices=CatalogCategory.choices)
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    image_url = models.ImageField(upload_to='catalog/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'accounts.Admin', on_delete=models.SET_NULL, null=True, blank=True, related_name='catalog_items'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'catalog_items'
        verbose_name = 'Catalog Item'
        verbose_name_plural = 'Catalog Items'
        ordering = ['category', 'title']
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return f'[{self.category}] {self.title} – ₹{self.price}'


class RelationCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'accounts.Admin', on_delete=models.SET_NULL, null=True, blank=True, related_name='relation_categories'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'relation_categories'
        verbose_name = 'Relation Category'
        verbose_name_plural = 'Relation Categories'
        ordering = ['name']

    def __str__(self):
        return self.name
