from rest_framework import serializers
from .models import CatalogItem, RelationCategory


class CatalogItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogItem
        fields = ['id', 'category', 'title', 'price', 'description', 'image_url', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class CatalogItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogItem
        fields = ['category', 'title', 'price', 'description', 'image_url', 'is_active']


class RelationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationCategory
        fields = ['id', 'name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
