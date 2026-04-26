"""
Writers serializers, views, urls — all in one pattern file.
"""
from rest_framework import serializers
from .models import WriterAssignment, WriterDraft, Payout


class WriterAssignmentSerializer(serializers.ModelSerializer):
    order_detail = serializers.SerializerMethodField()

    class Meta:
        model = WriterAssignment
        fields = ['id', 'order_id', 'writer_id', 'status', 'decline_reason',
                  'assigned_at', 'responded_at', 'order_detail']

    def get_order_detail(self, obj):
        from apps.orders.serializers import OrderListSerializer
        return OrderListSerializer(obj.order).data


class AssignmentDeclineSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=5)


class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = ['id', 'writer_id', 'amount', 'status', 'reference_id',
                  'period_start', 'period_end', 'processed_at', 'created_at']


class PayoutCreateSerializer(serializers.Serializer):
    writer_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    period_start = serializers.DateField()
    period_end = serializers.DateField()


class PayoutProcessSerializer(serializers.Serializer):
    reference_id = serializers.CharField()
