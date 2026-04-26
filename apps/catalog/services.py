"""Catalog services."""
import logging
from apps.notifications.services import log_audit

logger = logging.getLogger('apps')


def get_catalog_by_category(category: str):
    from .models import CatalogItem
    return CatalogItem.objects.filter(category=category, is_active=True).order_by('title')


def create_catalog_item(data: dict, admin) -> 'CatalogItem':
    from .models import CatalogItem
    item = CatalogItem.objects.create(created_by=admin, **data)
    log_audit(str(admin.id), 'admin', 'CATALOG_ITEM_CREATED', 'CATALOG', str(item.id), {'title': item.title})
    return item


def update_catalog_item(item_id: str, data: dict, admin) -> 'CatalogItem':
    from .models import CatalogItem
    from rest_framework.exceptions import NotFound
    try:
        item = CatalogItem.objects.get(id=item_id)
    except CatalogItem.DoesNotExist:
        raise NotFound('Catalog item not found.')
    for attr, val in data.items():
        setattr(item, attr, val)
    item.save()
    log_audit(str(admin.id), 'admin', 'CATALOG_ITEM_UPDATED', 'CATALOG', str(item.id), data)
    return item


def delete_catalog_item(item_id: str, admin):
    from .models import CatalogItem
    from rest_framework.exceptions import NotFound
    try:
        item = CatalogItem.objects.get(id=item_id)
    except CatalogItem.DoesNotExist:
        raise NotFound('Catalog item not found.')
    log_audit(str(admin.id), 'admin', 'CATALOG_ITEM_DELETED', 'CATALOG', str(item.id), {'title': item.title})
    item.delete()
