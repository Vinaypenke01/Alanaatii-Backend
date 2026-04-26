from rest_framework import serializers
from .models import Review, FAQ, SiteContentStep


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'customer_name', 'rating', 'content', 'is_published', 'created_at']
        read_only_fields = ['id', 'is_published', 'created_at']

    def validate_rating(self, v):
        if not 1 <= v <= 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return v


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'category', 'is_active', 'display_order', 'created_at']
        read_only_fields = ['id', 'created_at']


class SiteContentStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteContentStep
        fields = ['step_num', 'title', 'description', 'icon_slug']
