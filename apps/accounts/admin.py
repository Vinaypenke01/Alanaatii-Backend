from django.contrib import admin
from .models import User, UserAddress, Writer, Admin as AdminModel


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone_wa', 'is_active', 'created_at']
    search_fields = ['full_name', 'email']
    list_filter = ['is_active']


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'label', 'city', 'is_primary']


@admin.register(Writer)
class WriterAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'status', 'active_job_count', 'created_at']
    list_filter = ['status']
    search_fields = ['full_name', 'email']


@admin.register(AdminModel)
class AdminModelAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'role', 'is_active']
    list_filter = ['role', 'is_active']
