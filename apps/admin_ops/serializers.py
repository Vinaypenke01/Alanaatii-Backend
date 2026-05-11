from rest_framework import serializers
from .models import PricingDayRule, PincodeRule, MandatoryQuestion, Coupon, SiteSettings, SupportMessage


class PricingDayRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingDayRule
        fields = ['id', 'days_limit', 'extra_charge', 'label', 'created_at']
        read_only_fields = ['id', 'created_at']


class PincodeRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PincodeRule
        fields = ['id', 'zip_prefix', 'delivery_fee', 'region_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class MandatoryQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MandatoryQuestion
        fields = ['id', 'question_text', 'display_order', 'is_required', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'discount_val', 'discount_type', 'max_uses', 'current_uses',
                  'valid_from', 'valid_until', 'min_order', 'is_active', 'created_at']
        read_only_fields = ['id', 'current_uses', 'created_at']


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = ['master_upi_id', 'support_email', 'support_whatsapp',
                  'maintenance_mode', 'auto_assign_writers', 'default_delivery_fee', 'updated_at']
        read_only_fields = ['updated_at']


class PublicSiteSettingsSerializer(serializers.ModelSerializer):
    """Subset exposed to the public — no sensitive toggles."""
    class Meta:
        model = SiteSettings
        fields = ['master_upi_id', 'support_email', 'support_whatsapp']


class SupportMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportMessage
        fields = ['id', 'name', 'email', 'phone', 'message', 'status', 'admin_reply', 'created_at']
        read_only_fields = ['id', 'status', 'admin_reply', 'created_at']


class SupportMessageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportMessage
        fields = ['status', 'admin_reply']
