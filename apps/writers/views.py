"""
Writers views.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from utils.permissions import IsAdminUser, IsWriterUser
from utils.pagination import StandardPagination
from .models import WriterAssignment, Payout
from .serializers import (
    WriterAssignmentSerializer, AssignmentDeclineSerializer,
    PayoutSerializer, PayoutCreateSerializer, PayoutProcessSerializer,
)
from . import services


class WriterAssignmentListView(APIView):
    permission_classes = [IsAuthenticated, IsWriterUser]

    def get(self, request):
        status_filter = request.query_params.get('status')
        qs = WriterAssignment.objects.filter(writer=request.user).select_related('order')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response(WriterAssignmentSerializer(qs.order_by('-assigned_at'), many=True).data)


class WriterAssignmentAcceptView(APIView):
    permission_classes = [IsAuthenticated, IsWriterUser]

    def post(self, request, pk):
        assignment = services.accept_assignment(pk, request.user)
        return Response({'message': 'Assignment accepted.', 'status': assignment.status})


class WriterAssignmentDeclineView(APIView):
    permission_classes = [IsAuthenticated, IsWriterUser]

    def post(self, request, pk):
        ser = AssignmentDeclineSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        assignment = services.decline_assignment(pk, request.user, ser.validated_data['reason'])
        return Response({'message': 'Assignment declined.', 'status': assignment.status})


class WriterPayoutListView(APIView):
    permission_classes = [IsAuthenticated, IsWriterUser]

    def get(self, request):
        payouts = Payout.objects.filter(writer=request.user).order_by('-created_at')
        return Response(PayoutSerializer(payouts, many=True).data)


class WriterStatsView(APIView):
    permission_classes = [IsAuthenticated, IsWriterUser]

    def get(self, request):
        stats = services.get_writer_stats(str(request.user.id))
        return Response(stats)


# Admin views
class AdminPayoutListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = Payout.objects.all().order_by('-created_at')
        writer_filter = request.query_params.get('writer_id')
        if writer_filter:
            qs = qs.filter(writer_id=writer_filter)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(PayoutSerializer(page, many=True).data)

    def post(self, request):
        from apps.accounts.models import Admin
        ser = PayoutCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        admin = Admin.objects.get(id=request.user.id)
        payout = services.create_payout(
            ser.validated_data['writer_id'],
            ser.validated_data['amount'],
            ser.validated_data['period_start'],
            ser.validated_data['period_end'],
            admin,
        )
        return Response(PayoutSerializer(payout).data, status=status.HTTP_201_CREATED)


class AdminPayoutProcessView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        try:
            payout = Payout.objects.get(pk=pk)
        except Payout.DoesNotExist:
            return Response({'error': True, 'message': 'Payout not found.'}, status=404)
        ser = PayoutProcessSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payout.status = 'processed'
        payout.reference_id = ser.validated_data['reference_id']
        payout.processed_at = timezone.now()
        payout.save(update_fields=['status', 'reference_id', 'processed_at'])
        return Response(PayoutSerializer(payout).data)


class AdminWriterAssignmentsView(APIView):
    """Admin: view all assignments for a specific writer."""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, writer_id):
        qs = WriterAssignment.objects.filter(writer_id=writer_id).select_related('order').order_by('-assigned_at')
        return Response(WriterAssignmentSerializer(qs, many=True).data)
