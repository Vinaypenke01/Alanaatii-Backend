"""
Orders serializers.
"""
from rest_framework import serializers
from .models import Order, Transaction, ScriptVersion, OrderStatusHistory, Refund


class OrderCreateSerializer(serializers.Serializer):
    """Validates incoming order creation payload from the frontend."""
    product_type = serializers.ChoiceField(choices=['script', 'letterPaper', 'letter', 'letterBox', 'letterBoxGift'])
    customer_name = serializers.CharField(max_length=100)
    customer_phone = serializers.CharField(max_length=20)
    customer_email = serializers.EmailField()
    recipient_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    recipient_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    primary_contact = serializers.ChoiceField(choices=['sender', 'recipient'], required=False, allow_null=True)
    relation = serializers.CharField(max_length=50, required=False, allow_blank=True)
    message_content = serializers.CharField(required=False, allow_blank=True)
    special_notes = serializers.CharField(required=False, allow_blank=True)
    express_script = serializers.BooleanField(required=False, default=False)
    custom_letter_length = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    pincode = serializers.CharField(max_length=6, required=False, allow_blank=True)
    delivery_date = serializers.DateField(required=False, allow_null=True)
    paper_quantity = serializers.IntegerField(required=False, default=1, min_value=1)
    payment_screenshot = serializers.CharField(required=False, allow_blank=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    # Catalog FK ids
    letter_theme = serializers.UUIDField(required=False, allow_null=True)
    text_style = serializers.UUIDField(required=False, allow_null=True)
    paper = serializers.UUIDField(required=False, allow_null=True)
    box = serializers.UUIDField(required=False, allow_null=True)
    gift = serializers.UUIDField(required=False, allow_null=True)
    script_package = serializers.UUIDField(required=False, allow_null=True)


class OrderListSerializer(serializers.ModelSerializer):
    paper_name = serializers.SerializerMethodField()
    letter_theme_name = serializers.SerializerMethodField()
    text_style_name = serializers.SerializerMethodField()
    box_name = serializers.SerializerMethodField()
    gift_name = serializers.SerializerMethodField()
    script_package_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'product_type', 'status', 'customer_name', 'customer_phone', 'customer_email',
            'recipient_name', 'recipient_phone', 'primary_contact', 'relation',
            'total_amount', 'base_price', 'style_price', 'box_price', 'gift_price', 
            'delivery_price', 'express_price', 'discount_amt', 'pincode', 'paper',
            'paper_quantity', 'delivery_date', 'created_at', 'user_answers',
            'letter_theme_name', 'text_style_name', 'paper_name', 'box_name', 'gift_name', 'script_package_name'
        ]

    def get_paper_name(self, obj): return obj.paper.title if obj.paper else None
    def get_letter_theme_name(self, obj): return obj.letter_theme.title if obj.letter_theme else None
    def get_text_style_name(self, obj): return obj.text_style.title if obj.text_style else None
    def get_box_name(self, obj): return obj.box.title if obj.box else None
    def get_gift_name(self, obj): return obj.gift.title if obj.gift else None
    def get_script_package_name(self, obj): return obj.script_package.title if obj.script_package else None


class OrderDetailSerializer(serializers.ModelSerializer):
    status_history = serializers.SerializerMethodField()
    script_versions = serializers.SerializerMethodField()
    latest_transaction = serializers.SerializerMethodField()
    # Display names for catalog FKs
    paper_name = serializers.SerializerMethodField()
    letter_theme_name = serializers.SerializerMethodField()
    text_style_name = serializers.SerializerMethodField()
    box_name = serializers.SerializerMethodField()
    gift_name = serializers.SerializerMethodField()
    script_package_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = '__all__'

    def get_paper_name(self, obj): return obj.paper.title if obj.paper else None
    def get_letter_theme_name(self, obj): return obj.letter_theme.title if obj.letter_theme else None
    def get_text_style_name(self, obj): return obj.text_style.title if obj.text_style else None
    def get_box_name(self, obj): return obj.box.title if obj.box else None
    def get_gift_name(self, obj): return obj.gift.title if obj.gift else None
    def get_script_package_name(self, obj): return obj.script_package.title if obj.script_package else None

    def get_status_history(self, obj):
        history = obj.status_history.order_by('-created_at')[:10]
        return OrderStatusHistorySerializer(history, many=True).data

    def get_script_versions(self, obj):
        versions = obj.script_versions.order_by('-version_num')
        return ScriptVersionSerializer(versions, many=True).data

    def get_latest_transaction(self, obj):
        txn = obj.transactions.order_by('-created_at').first()
        return TransactionSerializer(txn).data if txn else None


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'order_id', 'amount', 'screenshot_url', 'status', 'notes', 'created_at']


class ScriptVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScriptVersion
        fields = ['id', 'order_id', 'version_num', 'content', 'writer_note', 'created_at']


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ['old_status', 'new_status', 'changed_by_role', 'note', 'created_at']


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ['id', 'order_id', 'amount', 'reason', 'status', 'processed_at', 'created_at']


class QuestionnaireSubmitSerializer(serializers.Serializer):
    """Validates the answers array submitted by customer."""
    answers = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        help_text='List of {question_id, answer} dicts',
    )


class ScriptSubmitSerializer(serializers.Serializer):
    content = serializers.CharField(min_length=10)
    writer_note = serializers.CharField(required=False, allow_blank=True)


class RevisionRequestSerializer(serializers.Serializer):
    feedback = serializers.CharField(min_length=5)


class OrderStatusUpdateSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=[])
    note = serializers.CharField(required=False, allow_blank=True)
    internal_notes = serializers.CharField(required=False, allow_blank=True)
    tracking_id = serializers.CharField(required=False, allow_blank=True)
    courier_name = serializers.CharField(required=False, allow_blank=True)
    est_arrival = serializers.DateField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import OrderStatus
        self.fields['new_status'] = serializers.ChoiceField(
            choices=[s.value for s in OrderStatus]
        )


class PaymentScreenshotUploadSerializer(serializers.Serializer):
    """For re-uploading a payment screenshot on rejected orders."""
    screenshot = serializers.ImageField()
    order_id = serializers.CharField()


class RefundCreateSerializer(serializers.Serializer):
    order_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reason = serializers.CharField()
