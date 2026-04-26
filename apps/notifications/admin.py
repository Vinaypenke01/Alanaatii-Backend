from django.contrib import admin
from .models import Notification, AuditLog, SecureLink

admin.site.register(Notification)
admin.site.register(AuditLog)
admin.site.register(SecureLink)
