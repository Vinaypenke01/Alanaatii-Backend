from django.urls import path
from .views import (
    PublicSiteSettingsView, AdminSiteSettingsView, PricingOverviewView,
    PricingDayRuleView, PincodeRuleView, MandatoryQuestionView, PublicQuestionsView,
    CouponView, SupportMessageCreateView, AdminSupportMessageView,
)

urlpatterns = [
    path('settings/', PublicSiteSettingsView.as_view(), name='public-settings'),
    path('admin/settings/', AdminSiteSettingsView.as_view(), name='admin-settings'),
    path('admin/pricing/', PricingOverviewView.as_view(), name='admin-pricing'),
    path('admin/pricing-rules/', PricingDayRuleView.as_view(), name='admin-pricing-rules'),
    path('admin/pricing-rules/<int:pk>/', PricingDayRuleView.as_view(), name='admin-pricing-rule-detail'),
    path('admin/pincode-rules/', PincodeRuleView.as_view(), name='admin-pincode-rules'),
    path('admin/pincode-rules/<int:pk>/', PincodeRuleView.as_view(), name='admin-pincode-rule-detail'),
    path('admin/questions/', MandatoryQuestionView.as_view(), name='admin-questions'),
    path('admin/questions/<int:pk>/', MandatoryQuestionView.as_view(), name='admin-question-detail'),
    path('questions/', PublicQuestionsView.as_view(), name='public-questions'),
    path('admin/coupons/', CouponView.as_view(), name='admin-coupons'),
    path('admin/coupons/<uuid:pk>/', CouponView.as_view(), name='admin-coupon-detail'),
    path('support/', SupportMessageCreateView.as_view(), name='support-create'),
    path('admin/support/', AdminSupportMessageView.as_view(), name='admin-support'),
    path('admin/support/<int:pk>/', AdminSupportMessageView.as_view(), name='admin-support-detail'),
]
