"""
Orders serializers.
"""
import uuid
from rest_framework import serializers
from django.utils import timezone
from .models import Order, Transaction, Refund, OrderStatus, ScriptVersion, OrderStatusHistory


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'


class OrderCreateSerializer(serializers.ModelSerializer):
    # Customer provides these during checkout
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    # Catalog FK ids
    letter_theme = serializers.UUIDField(required=False, allow_null=True)
    text_style = serializers.UUIDField(required=False, allow_null=True)
    paper = serializers.UUIDField(required=False, allow_null=True)
    box = serializers.UUIDField(required=False, allow_null=True)
    gift = serializers.UUIDField(required=False, allow_null=True)
    script_package = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Order
        fields = [
            'id', 'product_type', 'customer_name', 'customer_country_code', 'customer_phone', 'customer_email',
            'recipient_name', 'recipient_country_code', 'recipient_phone', 'primary_contact', 'relation',
            'address', 'city', 'pincode', 'message_content', 'special_notes', 'paper_quantity',
            'delivery_date', 'coupon_code', 'letter_theme', 'text_style', 'paper', 'box', 'gift', 'script_package'
        ]
        read_only_fields = ['id']


class OrderListSerializer(serializers.ModelSerializer):
    paper_name = serializers.SerializerMethodField()
    letter_theme_name = serializers.SerializerMethodField()
    text_style_name = serializers.SerializerMethodField()
    box_name = serializers.SerializerMethodField()
    gift_name = serializers.SerializerMethodField()
    script_package_name = serializers.SerializerMethodField()
    writer_name = serializers.SerializerMethodField()
    accepted_at = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'product_type', 'status', 'customer_name', 'customer_country_code', 'customer_phone', 'customer_email',
            'recipient_name', 'recipient_country_code', 'recipient_phone', 'primary_contact', 'relation',
            'total_amount', 'base_price', 'style_price', 'box_price', 'gift_price', 
            'delivery_price', 'express_price', 'pincode_fee', 'early_fee', 'discount_amt', 'pincode', 'paper',
            'paper_quantity', 'delivery_date', 'created_at', 'assigned_at', 'accepted_at', 'submitted_at', 'user_answers', 'writer',
            'letter_theme_name', 'text_style_name', 'paper_name', 'box_name', 'gift_name', 'script_package_name',
            'writer_name', 'script_content'
        ]

    def get_paper_name(self, obj): return obj.paper.title if obj.paper else None
    def get_letter_theme_name(self, obj): return obj.letter_theme.title if obj.letter_theme else None
    def get_text_style_name(self, obj): return obj.text_style.title if obj.text_style else None
    def get_box_name(self, obj): return obj.box.title if obj.box else None
    def get_gift_name(self, obj): return obj.gift.title if obj.gift else None
    def get_script_package_name(self, obj): return obj.script_package.title if obj.script_package else None
    def get_writer_name(self, obj): return obj.writer.full_name if obj.writer else None

    def get_accepted_at(self, obj):
        assignment = obj.assignments.filter(status='accepted', writer=obj.writer).first()
        return assignment.responded_at if assignment else None

    def get_user_answers(self, obj):
        return obj.user_answers or []


class ScriptTrackingSerializer(OrderListSerializer):
    writer_phone = serializers.SerializerMethodField()
    writer_email = serializers.SerializerMethodField()
    submission_due_at = serializers.SerializerMethodField()
    user_answers = serializers.SerializerMethodField()

    class Meta(OrderListSerializer.Meta):
        fields = OrderListSerializer.Meta.fields + [
            'writer_phone', 'writer_email', 'submission_due_at', 
            'message_content', 'special_notes', 'address', 'city', 'pincode'
        ]

    def get_writer_phone(self, obj): return obj.writer.phone if obj.writer else None
    def get_writer_email(self, obj): return obj.writer.email if obj.writer else None
    
    def get_submission_due_at(self, obj):
        assignment = obj.assignments.filter(status='accepted').first()
        return assignment.submission_due_at if assignment else None

    def get_user_answers(self, obj):
        from apps.admin_ops.models import MandatoryQuestion
        answers = obj.user_answers or []
        q_map = {q.id: q.question_text for q in MandatoryQuestion.objects.all()}
        
        enriched = []
        for a in answers:
            q_id = a.get('question_id')
            enriched.append({
                'question_id': q_id,
                'question': q_map.get(q_id, "Additional Info"),
                'answer': a.get('answer')
            })
        return enriched


class OrderDetailSerializer(serializers.ModelSerializer):
    status_history = serializers.SerializerMethodField()
    script_versions = serializers.SerializerMethodField()
    latest_transaction = serializers.SerializerMethodField()
    # Catalog names
    paper_name = serializers.SerializerMethodField()
    letter_theme_name = serializers.SerializerMethodField()
    text_style_name = serializers.SerializerMethodField()
    box_name = serializers.SerializerMethodField()
    gift_name = serializers.SerializerMethodField()
    script_package_name = serializers.SerializerMethodField()
    # Catalog images
    paper_image = serializers.SerializerMethodField()
    letter_theme_image = serializers.SerializerMethodField()
    text_style_image = serializers.SerializerMethodField()
    box_image = serializers.SerializerMethodField()
    gift_image = serializers.SerializerMethodField()
    script_package_image = serializers.SerializerMethodField()
    user_answers = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = '__all__'

    def get_paper_name(self, obj): return obj.paper.title if obj.paper else None
    def get_letter_theme_name(self, obj): return obj.letter_theme.title if obj.letter_theme else None
    def get_text_style_name(self, obj): return obj.text_style.title if obj.text_style else None
    def get_box_name(self, obj): return obj.box.title if obj.box else None
    def get_gift_name(self, obj): return obj.gift.title if obj.gift else None
    def get_script_package_name(self, obj): return obj.script_package.title if obj.script_package else None

    def get_paper_image(self, obj): return obj.paper.image_url.url if obj.paper and obj.paper.image_url else None
    def get_letter_theme_image(self, obj): return obj.letter_theme.image_url.url if obj.letter_theme and obj.letter_theme.image_url else None
    def get_text_style_image(self, obj): return obj.text_style.image_url.url if obj.text_style and obj.text_style.image_url else None
    def get_box_image(self, obj): return obj.box.image_url.url if obj.box and obj.box.image_url else None
    def get_gift_image(self, obj): return obj.gift.image_url.url if obj.gift and obj.gift.image_url else None
    def get_script_package_image(self, obj): return obj.script_package.image_url.url if obj.script_package and obj.script_package.image_url else None

    def get_status_history(self, obj):
        history = obj.status_history.order_by('-created_at')[:10]
        return OrderStatusHistorySerializer(history, many=True).data

    def get_script_versions(self, obj):
        versions = obj.script_versions.order_by('-version_num')
        return ScriptVersionSerializer(versions, many=True).data

    def get_latest_transaction(self, obj):
        txn = obj.transactions.order_by('-created_at').first()
        return TransactionSerializer(txn).data if txn else None

    def get_user_answers(self, obj):
        from apps.admin_ops.models import MandatoryQuestion
        answers = obj.user_answers or []
        q_map = {q.id: q.question_text for q in MandatoryQuestion.objects.all()}
        
        enriched = []
        for a in answers:
            q_id = a.get('question_id')
            enriched.append({
                'question_id': q_id,
                'question': q_map.get(q_id, "Additional Info"),
                'answer': a.get('answer')
            })
        return enriched


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'


class ScriptVersionSerializer(serializers.ModelSerializer):
    writer_name = serializers.SerializerMethodField()
    revision_request = serializers.SerializerMethodField()

    class Meta:
        model = ScriptVersion
        fields = '__all__'

    def get_writer_name(self, obj):
        return obj.writer.full_name if obj.writer else "System"

    def get_revision_request(self, obj):
        # Version 1 is the initial submission, so it has no revision request
        if obj.version_num <= 1:
            return None
        
        # Find the most recent 'revision_requested' history record created before this version
        history = OrderStatusHistory.objects.filter(
            order=obj.order,
            new_status=OrderStatus.REVISION_REQUESTED,
            created_at__lt=obj.created_at
        ).order_by('-created_at').first()
        
        return history.note if history else None


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = '__all__'


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = '__all__'


class RefundCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ['order', 'amount', 'reason']


class QuestionnaireSubmitSerializer(serializers.Serializer):
    answers = serializers.ListField(child=serializers.DictField())


class ScriptSubmitSerializer(serializers.Serializer):
    content = serializers.CharField(required=True)
    writer_note = serializers.CharField(required=False, allow_blank=True)


class RevisionRequestSerializer(serializers.Serializer):
    feedback = serializers.CharField(required=True)


class OrderStatusUpdateSerializer(serializers.Serializer):
    new_status = serializers.CharField(required=True)
    note = serializers.CharField(required=False, allow_blank=True)
    tracking_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    courier_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    est_arrival = serializers.DateField(required=False, allow_null=True)
    internal_notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
