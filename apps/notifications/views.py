"""Notifications views."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from utils.permissions import IsAdminUser, IsAnyAuthenticated
from .models import Notification, AuditLog, SecureLink
from .serializers import NotificationSerializer, AuditLogSerializer
from . import services


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated, IsAnyAuthenticated]

    def get(self, request):
        from utils.permissions import get_role
        role = get_role(request)
        qs = Notification.objects.filter(
            target_id=str(request.user.id), target_role=role
        ).order_by('-created_at')[:50]
        return Response(NotificationSerializer(qs, many=True).data)


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated, IsAnyAuthenticated]

    def post(self, request, pk):
        Notification.objects.filter(id=pk, target_id=str(request.user.id)).update(is_read=True)
        return Response({'message': 'Marked as read.'})

    def patch(self, request):
        """Mark all as read."""
        from utils.permissions import get_role
        role = get_role(request)
        Notification.objects.filter(target_id=str(request.user.id), target_role=role, is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read.'})


class SecureLinkResolveView(APIView):
    """Validate a secure token from an email link."""
    permission_classes = []

    def get(self, request):
        token = request.query_params.get('token', '')
        link = services.validate_secure_link(token)
        link.is_used = True
        link.save(update_fields=['is_used'])
        return Response({
            'valid': True,
            'link_type': link.link_type,
            'order_id': link.order_id,
        })


class AdminAuditLogView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = AuditLog.objects.all().order_by('-created_at')[:100]
        return Response(AuditLogSerializer(qs, many=True).data)


class UnreadNotificationCountView(APIView):
    permission_classes = [IsAuthenticated, IsAnyAuthenticated]

    def get(self, request):
        from utils.permissions import get_role
        role = get_role(request)
        count = Notification.objects.filter(
            target_id=str(request.user.id), target_role=role, is_read=False
        ).count()
        return Response({'unread_count': count})
