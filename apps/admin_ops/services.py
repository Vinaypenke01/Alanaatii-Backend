"""
Admin ops services — pricing engine helpers, coupon validation, settings.
"""
import logging
import cloudinary.api
from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction
from rest_framework.exceptions import ValidationError

logger = logging.getLogger('apps')


def get_pincode_fee(pincode: str) -> Decimal:
    """
    Look up delivery fee by pincode prefix.
    Fetches all rules and finds the longest matching prefix.
    """
    from .models import PincodeRule, SiteSettings
    if not pincode:
        return SiteSettings.get().default_delivery_fee

    pincode = str(pincode).strip().replace(" ", "")
    logger.info(f"Checking delivery fee for pincode: '{pincode}'")

    rules = list(PincodeRule.objects.all())
    # Sort rules by prefix length descending to match most specific first
    rules.sort(key=lambda r: len(r.zip_prefix.strip()), reverse=True)

    for rule in rules:
        clean_prefix = rule.zip_prefix.strip().replace(" ", "")
        if pincode.startswith(clean_prefix):
            logger.info(f"Found match for prefix '{clean_prefix}': {rule.delivery_fee}")
            return rule.delivery_fee

    default_fee = SiteSettings.get().default_delivery_fee
    logger.info(f"No specific match found for '{pincode}'. Falling back to default: {default_fee}")
    return default_fee


def get_early_fee(delivery_date) -> Decimal:
    """Calculate early delivery surcharge if date is within threshold."""
    from .models import PricingDayRule
    if not delivery_date:
        return Decimal('0')

    today = timezone.now().date()
    if hasattr(delivery_date, 'date'):
        delivery_date = delivery_date.date()

    days_until = (delivery_date - today).days

    # Find applicable rule: rule with smallest days_limit >= days_until
    rules = PricingDayRule.objects.filter(days_limit__gte=days_until).order_by('days_limit')
    if rules.exists():
        return rules.first().extra_charge

    # Fallback: if any rule with days_limit >= days_until exists
    all_rules = PricingDayRule.objects.order_by('days_limit')
    for rule in all_rules:
        if days_until <= rule.days_limit:
            return rule.extra_charge

    return Decimal('0')


def validate_coupon(code: str, order_total: Decimal) -> Decimal:
    """
    Validate coupon code and return the discount amount.
    Raises ValidationError if invalid/expired.
    """
    from .models import Coupon
    today = timezone.now().date()

    try:
        coupon = Coupon.objects.get(code__iexact=code, is_active=True)
    except Coupon.DoesNotExist:
        raise ValidationError('Invalid coupon code.')

    if today < coupon.valid_from or today > coupon.valid_until:
        raise ValidationError('This coupon has expired.')

    if coupon.max_uses is not None and coupon.current_uses >= coupon.max_uses:
        raise ValidationError('This coupon has reached its usage limit.')

    if order_total < coupon.min_order:
        raise ValidationError(f'Minimum order of ₹{coupon.min_order} required for this coupon.')

    if coupon.discount_type == 'percentage':
        discount = (order_total * coupon.discount_val) / Decimal('100')
    else:
        discount = coupon.discount_val

    return min(discount, order_total)


def get_questions_for_relation(relation_type: str = None) -> list:
    """Return ordered universal questions for all orders."""
    from .models import MandatoryQuestion
    from .serializers import MandatoryQuestionSerializer
    questions = MandatoryQuestion.objects.filter(is_active=True).order_by('display_order')
    return MandatoryQuestionSerializer(questions, many=True).data


def get_site_settings():
    """Cached singleton site settings fetch."""
    from .models import SiteSettings
    return SiteSettings.get()


@db_transaction.atomic
def wipe_all_orders_data():
    """
    DANGEROUS: Deletes all orders and their associated media.
    1. Deletes payment_screenshots folder content from Cloudinary.
    2. Deletes all Order records (cascades to Transactions, History, etc).
    """
    from apps.orders.models import Order
    
    logger.warning("FACTORY RESET INITIATED: Wiping all order data.")
    
    # 1. Cloudinary Cleanup
    try:
        # Delete all resources in the payment_screenshots prefix
        # Note: This only deletes images. If there are other file types, 
        # they might need separate calls or resource_type='raw'.
        cloudinary.api.delete_resources_by_prefix('payment_screenshots/')
        logger.info("Cloudinary assets in 'payment_screenshots/' deleted.")
    except Exception as e:
        logger.error(f"Cloudinary wipe failed: {e}")
        # We continue even if Cloudinary fails, to ensure DB is cleared
    
    # 2. Database Cleanup
    order_count = Order.objects.count()
    Order.objects.all().delete()
    
    logger.warning(f"FACTORY RESET COMPLETE: {order_count} orders deleted from DB.")
    return order_count
