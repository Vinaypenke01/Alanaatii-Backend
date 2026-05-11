"""
Orders views — thin controllers delegating to services.
"""
import logging
import os
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings

from utils.permissions import IsAdminUser, IsCustomerUser, IsWriterUser, IsAnyAuthenticated
from utils.pagination import StandardPagination, LargeResultsPagination
from .models import Order, Transaction, Refund, OrderStatus
from .serializers import (
    OrderCreateSerializer, OrderListSerializer, OrderDetailSerializer,
    TransactionSerializer, ScriptVersionSerializer, RefundSerializer,
    QuestionnaireSubmitSerializer, ScriptSubmitSerializer, RevisionRequestSerializer,
    OrderStatusUpdateSerializer, RefundCreateSerializer,
)
from . import services

logger = logging.getLogger('apps')


# ─── Customer: Order Lifecycle ────────────────────────────────────────────────

class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Order is now strictly tied to the logged-in user
        order = services.create_order(serializer.validated_data, user=request.user)
        return Response({
            'message': 'Order placed successfully! Payment is pending verification.',
            'order': OrderListSerializer(order).data,
        }, status=status.HTTP_201_CREATED)


class UserOrderListView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerUser]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        paginator = StandardPagination()
        page = paginator.paginate_queryset(orders, request)
        return paginator.get_paginated_response(OrderListSerializer(page, many=True).data)


class UserScriptReviewListView(APIView):
    """Fetch only orders that have a script ready for customer review."""
    permission_classes = [IsAuthenticated, IsCustomerUser]

    def get(self, request):
        from .models import OrderStatus
        orders = Order.objects.filter(
            user=request.user,
            status__in=[OrderStatus.CUSTOMER_REVIEW, OrderStatus.REVISION_REQUESTED, OrderStatus.SCRIPT_SUBMITTED]
        ).order_by('-created_at')
        return Response(OrderListSerializer(orders, many=True).data)


class UserOrderDetailView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerUser]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': True, 'message': 'Order not found.'}, status=404)
        return Response(OrderDetailSerializer(order).data)


class QuestionnaireSubmitView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerUser]

    def post(self, request, order_id):
        serializer = QuestionnaireSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = services.submit_questionnaire(order_id, serializer.validated_data['answers'], request.user)
        return Response({'message': 'Details submitted. Your order is now being processed.', 'status': order.status})


class ScriptApprovalView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerUser]

    def post(self, request, order_id):
        action = request.data.get('action')  # 'approve' or 'revision'
        if action == 'approve':
            order = services.approve_script(order_id, request.user)
            return Response({'message': 'Script approved! We will begin writing your letter.', 'status': order.status})
        elif action == 'revision':
            ser = RevisionRequestSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            order = services.request_revision(order_id, ser.validated_data['feedback'], request.user)
            return Response({'message': 'Revision request submitted.', 'status': order.status})
        return Response({'error': True, 'message': 'Invalid action. Use "approve" or "revision".'}, status=400)


class UserCancelOrderView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerUser]

    def post(self, request, order_id):
        order = services.cancel_order(order_id, request.user, role='user')
        return Response({'message': 'Order cancelled.', 'status': order.status})


class PaymentScreenshotUploadView(APIView):
    """Allow customer to re-upload payment screenshot (for rejected payments)."""
    permission_classes = [IsAuthenticated, IsCustomerUser]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': True, 'message': 'Order not found.'}, status=404)

        if order.status not in [OrderStatus.PAYMENT_PENDING, OrderStatus.PAYMENT_REJECTED]:
            return Response({'error': True, 'message': 'Cannot upload screenshot at this stage.'}, status=400)

        file = request.FILES.get('screenshot')
        if not file:
            return Response({'error': True, 'message': 'No file uploaded.'}, status=400)

        # Save file to Cloudinary (via default_storage)
        from django.core.files.storage import default_storage
        filename = f'payment_screenshots/{order_id}_{timezone.now().strftime("%Y%m%d%H%M%S")}_{file.name}'
        saved_path = default_storage.save(filename, file)
        file_url = default_storage.url(saved_path)

        order.payment_ss = file_url
        order.status = OrderStatus.PAYMENT_PENDING
        order.save(update_fields=['payment_ss', 'status'])

        # Update pending transaction or create new one
        txn = order.transactions.filter(status='pending').order_by('-created_at').first()
        if txn:
            txn.screenshot_url = file_url
            txn.save(update_fields=['screenshot_url'])
        else:
            Transaction.objects.create(order=order, amount=order.total_amount, screenshot_url=file_url)

        return Response({'message': 'Payment screenshot uploaded.', 'url': file_url})


# ─── Writer: Script Management ────────────────────────────────────────────────

class WriterScriptSubmitView(APIView):
    permission_classes = [IsAuthenticated, IsWriterUser]

    def post(self, request, order_id):
        ser = ScriptSubmitSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        script = services.submit_script(
            order_id, ser.validated_data['content'],
            ser.validated_data.get('writer_note', ''),
            request.user,
        )
        return Response({
            'message': 'Script submitted successfully.',
            'version': ScriptVersionSerializer(script).data,
        })


class WriterDraftView(APIView):
    """Auto-save draft endpoint."""
    permission_classes = [IsAuthenticated, IsWriterUser]

    def get(self, request, order_id):
        from apps.writers.models import WriterDraft
        try:
            draft = WriterDraft.objects.get(order_id=order_id, writer=request.user)
            return Response({'draft_content': draft.draft_content, 'last_saved_at': draft.last_saved_at})
        except WriterDraft.DoesNotExist:
            return Response({'draft_content': '', 'last_saved_at': None})

    def put(self, request, order_id):
        from apps.writers.models import WriterDraft
        content = request.data.get('draft_content', '')
        draft, _ = WriterDraft.objects.update_or_create(
            order_id=order_id, writer=request.user,
            defaults={'draft_content': content, 'last_saved_at': timezone.now()},
        )
        return Response({'message': 'Draft saved.', 'last_saved_at': draft.last_saved_at})


class WriterOrderListView(APIView):
    """Writer sees their assigned orders."""
    permission_classes = [IsAuthenticated, IsWriterUser]

    def get(self, request):
        from apps.writers.models import WriterAssignment
        status_filter = request.query_params.get('status', 'accepted')
        assignments = WriterAssignment.objects.filter(
            writer=request.user, status=status_filter
        ).select_related('order').order_by('-assigned_at')
        data = [
            {
                'assignment_id': str(a.id),
                'order': OrderListSerializer(a.order).data,
                'status': a.status,
                'assigned_at': a.assigned_at,
            }
            for a in assignments
        ]
        return Response(data)


class WriterOrderDetailView(APIView):
    """Writer sees full details of an order assigned to them."""
    permission_classes = [IsAuthenticated, IsWriterUser]

    def get(self, request, order_id):
        from apps.writers.models import WriterAssignment
        # Verify this writer is assigned to this order
        try:
            assignment = WriterAssignment.objects.get(
                order_id=order_id, writer=request.user, status='accepted'
            )
        except WriterAssignment.DoesNotExist:
            return Response({'error': True, 'message': 'Access denied or assignment not found.'}, status=403)
        
        return Response(OrderDetailSerializer(assignment.order).data)


# ─── Admin: Order Management ──────────────────────────────────────────────────

class AdminOrderListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = Order.objects.all().order_by('-created_at')
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(customer_name__icontains=search) | 
                Q(customer_email__icontains=search) | 
                Q(id__icontains=search) |
                Q(transactions__bank_transaction_id__icontains=search)
            ).distinct()
        paginator = LargeResultsPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(OrderListSerializer(page, many=True).data)


class AdminOrderDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': True, 'message': 'Order not found.'}, status=404)
        return Response(OrderDetailSerializer(order).data)


class AdminOrderStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, order_id):
        from apps.accounts.models import Admin
        ser = OrderStatusUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        admin = Admin.objects.get(id=request.user.id)

        extra_data = {}
        for field in ['tracking_id', 'courier_name', 'est_arrival', 'internal_notes']:
            if field in data and data[field] is not None:
                extra_data[field] = data[field]

        order = services.admin_update_order_status(
            order_id, data['new_status'], admin, note=data.get('note'), extra_data=extra_data or None
        )
        return Response({'message': f'Order status updated to {order.status}.', 'status': order.status})


class AdminOrderCancelView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, order_id):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        order = services.cancel_order(order_id, admin, role='admin')
        return Response({'message': 'Order cancelled.', 'status': order.status})


class AdminReassignOrderView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, order_id):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        exclude_writer = request.data.get('exclude_writer_id', '')
        assignment = services.reassign_order(order_id, exclude_writer, admin)
        return Response({'message': 'Order reassigned.', 'assignment_id': str(assignment.id)})


class AdminOrderResendNotificationView(APIView):
    """Manually re-trigger email for the current status."""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, order_id):
        from apps.accounts.models import Admin
        admin = Admin.objects.get(id=request.user.id)
        services.resend_order_notification(order_id, admin)
        return Response({'message': 'Notification resent successfully.'})


# ─── Admin: Payment Verification ─────────────────────────────────────────────

class AdminPaymentListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        status_filter = request.query_params.get('status', 'pending')
        qs = Transaction.objects.filter(status=status_filter).select_related('order').order_by('-created_at')
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        data = []
        for txn in page:
            row = TransactionSerializer(txn).data
            row['order'] = OrderListSerializer(txn.order).data
            data.append(row)
        return paginator.get_paginated_response(data)


class AdminPaymentVerifyView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, transaction_id):
        from apps.accounts.models import Admin
        bank_txn_id = request.data.get('bank_transaction_id')
        if not bank_txn_id:
            return Response({'error': True, 'message': 'bank_transaction_id is required.'}, status=400)
            
        admin = Admin.objects.get(id=request.user.id)
        order = services.verify_payment(str(transaction_id), bank_txn_id, admin)
        return Response({'message': 'Payment verified.', 'order_status': order.status})


class AdminPaymentRejectView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, transaction_id):
        from apps.accounts.models import Admin
        reason = request.data.get('reason', 'Payment could not be verified.')
        admin = Admin.objects.get(id=request.user.id)
        order = services.reject_payment(str(transaction_id), reason, admin)
        return Response({'message': 'Payment rejected.', 'order_status': order.status})


# ─── Admin: Refunds ───────────────────────────────────────────────────────────

class AdminRefundListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = Refund.objects.all().order_by('-created_at')
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(RefundSerializer(page, many=True).data)

    def post(self, request):
        from apps.accounts.models import Admin
        from decimal import Decimal
        ser = RefundCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        admin = Admin.objects.get(id=request.user.id)
        refund = services.process_refund(
            ser.validated_data['order_id'],
            Decimal(str(ser.validated_data['amount'])),
            ser.validated_data['reason'],
            admin,
        )
        return Response(RefundSerializer(refund).data, status=status.HTTP_201_CREATED)


class AdminRefundUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        try:
            refund = Refund.objects.get(pk=pk)
        except Refund.DoesNotExist:
            return Response({'error': True, 'message': 'Refund not found.'}, status=404)
        refund_status = request.data.get('status')
        if refund_status in ['completed', 'rejected']:
            refund.status = refund_status
            if refund_status == 'completed':
                refund.processed_at = timezone.now()
            refund.save(update_fields=['status', 'processed_at'])
        return Response(RefundSerializer(refund).data)


# ─── Analytics ───────────────────────────────────────────────────────────────

class AdminAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from django.db.models import Count, Sum, Q
        from apps.writers.models import WriterAssignment

        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status=OrderStatus.PAYMENT_PENDING).count()
        completed_orders = Order.objects.filter(status=OrderStatus.DELIVERED).count()
        cancelled_orders = Order.objects.filter(status=OrderStatus.CANCELLED).count()
        total_revenue = Order.objects.filter(
            transactions__status='verified'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        pending_payments = Transaction.objects.filter(status='pending').count()
        pending_scripts = Order.objects.filter(status__in=[
            OrderStatus.ACCEPTED_BY_WRITER, OrderStatus.REVISION_REQUESTED
        ]).count()

        orders_by_status = list(
            Order.objects.values('status').annotate(count=Count('id')).order_by('-count')
        )
        orders_by_type = list(
            Order.objects.values('product_type').annotate(count=Count('id')).order_by('-count')
        )
        recent_orders = OrderListSerializer(
            Order.objects.order_by('-created_at')[:10], many=True
        ).data

        return Response({
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'cancelled_orders': cancelled_orders,
            'total_revenue': float(total_revenue),
            'pending_payments_count': pending_payments,
            'pending_scripts_count': pending_scripts,
            'orders_by_status': orders_by_status,
            'orders_by_product_type': orders_by_type,
            'recent_orders': recent_orders,
        })


# ─── Coupon Validation (public-ish) ──────────────────────────────────────────

class CouponValidateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from apps.admin_ops.services import validate_coupon
        from decimal import Decimal
        code = request.data.get('code', '')
        order_total = Decimal(str(request.data.get('order_total', '0')))
        discount = validate_coupon(code, order_total)
        return Response({'discount_amount': float(discount), 'code': code.upper()})
