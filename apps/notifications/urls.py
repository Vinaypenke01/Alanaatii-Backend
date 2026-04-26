from django.urls import path
from .views import NotificationListView, NotificationMarkReadView, SecureLinkResolveView, AdminAuditLogView

urlpatterns = [
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification-read'),
    path('notifications/read-all/', NotificationMarkReadView.as_view(), name='notification-read-all'),
    path('secure-link/', SecureLinkResolveView.as_view(), name='secure-link-resolve'),
    path('admin/audit-logs/', AdminAuditLogView.as_view(), name='admin-audit-logs'),
]
