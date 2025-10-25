from django.contrib import admin
from .models import Debate, DebateMessage


class DebateMessageInline(admin.TabularInline):
    model = DebateMessage
    extra = 0
    readonly_fields = ['persona', 'round_number', 'created_at']


@admin.register(Debate)
class DebateAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'rounds_completed', 'created_at']
    list_filter = ['status', 'depth_level', 'created_at']
    search_fields = ['title', 'topic']
    readonly_fields = ['slug', 'created_at', 'updated_at', 'completed_at']
    inlines = [DebateMessageInline]

    def get_queryset(self, request):
        """
        Query optimization: Prefetch participants and select_related user
        to prevent N+1 queries in admin list view.
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('user').prefetch_related('participants')

    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'slug', 'topic', 'user')
        }),
        ('Configuration', {
            'fields': ('depth_level', 'max_rounds')
        }),
        ('Status', {
            'fields': ('status', 'rounds_completed', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DebateMessage)
class DebateMessageAdmin(admin.ModelAdmin):
    list_display = ['debate', 'persona', 'round_number', 'created_at']
    list_filter = ['round_number', 'created_at']
    search_fields = ['content', 'debate__title', 'persona__name']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        """
        Query optimization: Use select_related for foreign keys (debate, persona)
        to prevent N+1 queries in admin list view.
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('debate', 'persona')
