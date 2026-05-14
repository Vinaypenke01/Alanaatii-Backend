"""Cache invalidation signals for the content app.

Fires on any Review, FAQ, or SiteContentStep save/delete so the
public API always serves fresh data immediately after admin changes.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import Review, FAQ, SiteContentStep
from utils.cache_keys import PUBLIC_REVIEWS, PUBLIC_FAQS, SITE_STEPS


@receiver([post_save, post_delete], sender=Review)
def invalidate_reviews_cache(sender, **kwargs):
    """Clear reviews cache on any review publish/unpublish/delete."""
    cache.delete(PUBLIC_REVIEWS)


@receiver([post_save, post_delete], sender=FAQ)
def invalidate_faqs_cache(sender, **kwargs):
    """Clear FAQ cache on any FAQ create/update/delete."""
    cache.delete(PUBLIC_FAQS)


@receiver([post_save, post_delete], sender=SiteContentStep)
def invalidate_steps_cache(sender, **kwargs):
    """Clear homepage steps cache on any step update."""
    cache.delete(SITE_STEPS)
