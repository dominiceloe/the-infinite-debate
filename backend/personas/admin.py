from django.contrib import admin
from .models import Persona, PersonaRequest


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'era', 'birth_year']
    list_filter = ['category']
    search_fields = ['name', 'title', 'era']
    readonly_fields = ['slug', 'created_at', 'last_updated']
    fieldsets = (
        ('Identity', {
            'fields': ('name', 'slug', 'title', 'category')
        }),
        ('Historical Context', {
            'fields': ('era', 'birth_year', 'death_year', 'religion_worldview')
        }),
        ('Content', {
            'fields': ('primary_works', 'core_positions', 'debate_style',
                      'key_concepts', 'character_notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('file_path', 'created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PersonaRequest)
class PersonaRequestAdmin(admin.ModelAdmin):
    list_display = ['persona_name', 'user', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['persona_name', 'user__username', 'user__email', 'justification']
    readonly_fields = ['user', 'created_at', 'updated_at']

    fieldsets = (
        ('Request Details', {
            'fields': ('user', 'persona_name', 'justification', 'suggested_sources')
        }),
        ('Status & Review', {
            'fields': ('status', 'admin_notes', 'created_persona', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        # Auto-set reviewed_at when status changes from pending
        if change and 'status' in form.changed_data and obj.status != 'pending':
            from django.utils import timezone
            if not obj.reviewed_at:
                obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
