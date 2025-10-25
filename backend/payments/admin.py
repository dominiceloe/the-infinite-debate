from django.contrib import admin
from .models import StripeEvent, StripePayment, StripeSubscriptionHistory


@admin.register(StripeEvent)
class StripeEventAdmin(admin.ModelAdmin):
    list_display = ['event_id', 'event_type', 'processed', 'created_at']
    list_filter = ['event_type', 'processed', 'created_at']
    search_fields = ['event_id', 'event_type']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(StripePayment)
class StripePaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['user__username', 'payment_intent_id', 'subscription_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(StripeSubscriptionHistory)
class StripeSubscriptionHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'tier', 'status', 'created_at']
    list_filter = ['action', 'tier', 'status', 'created_at']
    search_fields = ['user__username', 'subscription_id']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
