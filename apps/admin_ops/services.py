"""
Admin ops services — pricing engine helpers, coupon validation, settings.
"""
import logging
from decimal import Decimal
from django.utils import timezone
from rest_framework.exceptions import ValidationError

logger = logging.getLogger('apps')


def get_pincode_fee(pincode: str) -> Decimal:
    """Look up delivery fee by first 3 digits of pincode."""
    from .models import PincodeRule, SiteSettings
    if not pincode or len(pincode) < 3:
        return SiteSettings.get().default_delivery_fee

    prefix = pincode[:3]
    try:
        rule = PincodeRule.objects.get(zip_prefix=prefix)
        return rule.delivery_fee
    except PincodeRule.DoesNotExist:
        # Try first 2 digits
        try:
            rule = PincodeRule.objects.get(zip_prefix=pincode[:2])
            return rule.delivery_fee
        except PincodeRule.DoesNotExist:
            return SiteSettings.get().default_delivery_fee


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


def get_questions_for_relation(relation_type: str) -> list:
    """Return ordered questions for a given relation type."""
    from .models import MandatoryQuestion
    questions = MandatoryQuestion.objects.filter(
        relation_type__iexact=relation_type
    ).order_by('display_order')
    return list(questions.values('id', 'question_text', 'is_required', 'display_order'))


def get_site_settings():
    """Cached singleton site settings fetch."""
    from .models import SiteSettings
    return SiteSettings.get()
