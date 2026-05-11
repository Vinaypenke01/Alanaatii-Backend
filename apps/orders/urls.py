from django.urls import path
from .views import (
    OrderCreateView, UserOrderListView, UserScriptReviewListView, UserOrderDetailView,
    QuestionnaireSubmitView, ScriptApprovalView, UserCancelOrderView,
    PaymentScreenshotUploadView,
    WriterScriptSubmitView, WriterDraftView, WriterOrderListView, WriterOrderDetailView,
    AdminOrderListView, AdminOrderDetailView, AdminOrderStatusUpdateView,
    AdminOrderCancelView, AdminReassignOrderView, AdminOrderResendNotificationView,
    AdminPaymentListView, AdminPaymentVerifyView, AdminPaymentRejectView,
    AdminRefundListCreateView, AdminRefundUpdateView,
    AdminAnalyticsView, CouponValidateView,
)

urlpatterns = [
    # Customer: orders
    path('orders/', OrderCreateView.as_view(), name='order-create'),
    path('orders/my/', UserOrderListView.as_view(), name='user-order-list'),
    path('orders/scripts-to-review/', UserScriptReviewListView.as_view(), name='user-scripts-review-list'),
    path('orders/<str:order_id>/', UserOrderDetailView.as_view(), name='user-order-detail'),
    path('orders/<str:order_id>/questionnaire/', QuestionnaireSubmitView.as_view(), name='order-questionnaire'),
    path('orders/<str:order_id>/script-action/', ScriptApprovalView.as_view(), name='order-script-action'),
    path('orders/<str:order_id>/cancel/', UserCancelOrderView.as_view(), name='order-cancel'),
    path('orders/<str:order_id>/upload-screenshot/', PaymentScreenshotUploadView.as_view(), name='order-upload-screenshot'),

    # Writer: script
    path('writer/orders/', WriterOrderListView.as_view(), name='writer-order-list'),
    path('writer/orders/<str:order_id>/', WriterOrderDetailView.as_view(), name='writer-order-detail'),
    path('writer/orders/<str:order_id>/submit-script/', WriterScriptSubmitView.as_view(), name='writer-submit-script'),
    path('writer/orders/<str:order_id>/draft/', WriterDraftView.as_view(), name='writer-draft'),

    # Admin: orders
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/orders/<str:order_id>/', AdminOrderDetailView.as_view(), name='admin-order-detail'),
    path('admin/orders/<str:order_id>/status/', AdminOrderStatusUpdateView.as_view(), name='admin-order-status'),
    path('admin/orders/<str:order_id>/cancel/', AdminOrderCancelView.as_view(), name='admin-order-cancel'),
    path('admin/orders/<str:order_id>/reassign/', AdminReassignOrderView.as_view(), name='admin-order-reassign'),
    path('admin/orders/<str:order_id>/resend-notification/', AdminOrderResendNotificationView.as_view(), name='admin-order-resend-notification'),

    # Admin: payments
    path('admin/payments/', AdminPaymentListView.as_view(), name='admin-payment-list'),
    path('admin/payments/<uuid:transaction_id>/verify/', AdminPaymentVerifyView.as_view(), name='admin-payment-verify'),
    path('admin/payments/<uuid:transaction_id>/reject/', AdminPaymentRejectView.as_view(), name='admin-payment-reject'),

    # Admin: refunds
    path('admin/refunds/', AdminRefundListCreateView.as_view(), name='admin-refund-list'),
    path('admin/refunds/<uuid:pk>/', AdminRefundUpdateView.as_view(), name='admin-refund-update'),

    # Admin: analytics
    path('admin/analytics/', AdminAnalyticsView.as_view(), name='admin-analytics'),

    # Public: coupon validation
    path('coupons/validate/', CouponValidateView.as_view(), name='coupon-validate'),
]
