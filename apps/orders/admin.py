from django.contrib import admin
from .models import Order, Transaction, ScriptVersion, OrderStatusHistory, Refund


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'product_type', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'product_type']
    search_fields = ['id', 'customer_name', 'customer_email']
    readonly_fields = ['created_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'amount', 'status', 'created_at']
    list_filter = ['status']


@admin.register(ScriptVersion)
class ScriptVersionAdmin(admin.ModelAdmin):
    list_display = ['order', 'version_num', 'writer', 'created_at']


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'old_status', 'new_status', 'changed_by_role', 'created_at']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'amount', 'status', 'created_at']
    list_filter = ['status']
