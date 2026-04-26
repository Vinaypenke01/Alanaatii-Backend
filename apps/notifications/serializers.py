from rest_framework import serializers
from .models import Notification, AuditLog, SecureLink


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'title', 'message', 'is_read', 'order_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'user_id', 'user_role', 'action_key', 'entity_type', 'entity_id', 'changes', 'created_at']
