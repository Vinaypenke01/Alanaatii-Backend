from rest_framework import serializers
from .models import CatalogItem


class CatalogItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogItem
        fields = [
            'id', 'category', 'title', 'price', 'description', 'image_url', 
            'is_active', 'requires_custom_length', 'fits_all_boxes', 
            'compatible_boxes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CatalogItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogItem
        exclude = ('created_by', 'created_at', 'updated_at')
