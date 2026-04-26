"""
Utility mixins for common ViewSet behaviors.
"""
from apps.notifications.services import log_audit


class AuditLogMixin:
    """
    Mixin for ViewSets that auto-writes audit logs on create/update/delete.
    Subclasses must set: audit_entity_type = 'ORDER'
    """
    audit_entity_type = 'UNKNOWN'

    def _get_user_info(self, request):
        user = request.user
        token = getattr(request, 'auth', None)
        role = 'unknown'
        if token:
            try:
                role = token.payload.get('role', 'unknown')
            except AttributeError:
                pass
        return str(user.id), role

    def perform_create(self, serializer):
        instance = serializer.save()
        user_id, role = self._get_user_info(self.request)
        log_audit(user_id, role, f'{self.audit_entity_type}_CREATED',
                  self.audit_entity_type, str(instance.pk))

    def perform_destroy(self, instance):
        user_id, role = self._get_user_info(self.request)
        log_audit(user_id, role, f'{self.audit_entity_type}_DELETED',
                  self.audit_entity_type, str(instance.pk))
        instance.delete()
