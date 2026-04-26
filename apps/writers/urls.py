from django.urls import path
from .views import (
    WriterAssignmentListView, WriterAssignmentAcceptView, WriterAssignmentDeclineView,
    WriterPayoutListView, WriterStatsView,
    AdminPayoutListCreateView, AdminPayoutProcessView, AdminWriterAssignmentsView,
)

urlpatterns = [
    # Writer portal
    path('writer/assignments/', WriterAssignmentListView.as_view(), name='writer-assignments'),
    path('writer/assignments/<int:pk>/accept/', WriterAssignmentAcceptView.as_view(), name='writer-assignment-accept'),
    path('writer/assignments/<int:pk>/decline/', WriterAssignmentDeclineView.as_view(), name='writer-assignment-decline'),
    path('writer/payouts/', WriterPayoutListView.as_view(), name='writer-payouts'),
    path('writer/stats/', WriterStatsView.as_view(), name='writer-stats'),
    # Admin portal
    path('admin/payouts/', AdminPayoutListCreateView.as_view(), name='admin-payouts'),
    path('admin/payouts/<uuid:pk>/process/', AdminPayoutProcessView.as_view(), name='admin-payout-process'),
    path('admin/writers/<uuid:writer_id>/assignments/', AdminWriterAssignmentsView.as_view(), name='admin-writer-assignments'),
]
