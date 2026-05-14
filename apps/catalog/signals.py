"""Cache invalidation signals for the catalog app.

Fires on any CatalogItem save or delete to ensure the public catalog
API always reflects the latest admin changes immediately.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import CatalogItem
from utils.cache_keys import CATALOG_ALL, CATALOG_CAT, CATALOG_CATEGORIES


@receiver([post_save, post_delete], sender=CatalogItem)
def invalidate_catalog_cache(sender, **kwargs):
    """Clear all catalog cache keys whenever a catalog item changes."""
    cache.delete(CATALOG_ALL)
    for category in CATALOG_CATEGORIES:
        cache.delete(CATALOG_CAT.format(category=category))
