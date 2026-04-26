from django.urls import path
from .views import (
    PublicReviewListView, ReviewSubmitView, AdminReviewView,
    PublicFAQView, AdminFAQView,
    SiteContentStepView, AdminSiteContentStepView,
)

urlpatterns = [
    path('reviews/', PublicReviewListView.as_view(), name='public-reviews'),
    path('reviews/submit/', ReviewSubmitView.as_view(), name='submit-review'),
    path('admin/reviews/', AdminReviewView.as_view(), name='admin-reviews'),
    path('admin/reviews/<int:pk>/', AdminReviewView.as_view(), name='admin-review-detail'),
    path('faq/', PublicFAQView.as_view(), name='public-faq'),
    path('admin/faq/', AdminFAQView.as_view(), name='admin-faq'),
    path('admin/faq/<int:pk>/', AdminFAQView.as_view(), name='admin-faq-detail'),
    path('site-steps/', SiteContentStepView.as_view(), name='site-steps'),
    path('admin/site-steps/<int:step_num>/', AdminSiteContentStepView.as_view(), name='admin-site-step'),
]
