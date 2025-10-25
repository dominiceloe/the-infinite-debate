from django.contrib import admin
from .models import PrimaryText, TextSection, TextCitation


@admin.register(PrimaryText)
class PrimaryTextAdmin(admin.ModelAdmin):
    """
    Admin interface for managing primary source texts.
    """
    list_display = [
        'title',
        'author',
        'category',
        'era',
        'publication_year',
        'word_count',
        'is_published',
        'processing_status',
    ]
    list_filter = [
        'category',
        'era',
        'is_published',
        'processing_status',
        'reading_difficulty',
        'source_type',
    ]
    search_fields = ['title', 'author', 'description', 'translator']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'word_count']

    fieldsets = (
        ('Identity', {
            'fields': ('title', 'slug', 'author')
        }),
        ('Context', {
            'fields': ('category', 'era', 'publication_year', 'original_language')
        }),
        ('Source Information', {
            'fields': ('source_url', 'source_type', 'license')
        }),
        ('Translation', {
            'fields': ('translator', 'translation_year', 'edition_notes'),
            'classes': ('collapse',)
        }),
        ('Content', {
            'fields': ('description', 'full_content', 'word_count', 'reading_difficulty'),
            'description': 'For small texts, use full_content. For large texts, use TextSection models.'
        }),
        ('Status', {
            'fields': ('is_published', 'processing_status', 'error_message')
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['publish_texts', 'unpublish_texts', 'mark_as_ready']

    def publish_texts(self, request, queryset):
        """Bulk action to publish texts"""
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} text(s) published successfully.')
    publish_texts.short_description = 'Publish selected texts'

    def unpublish_texts(self, request, queryset):
        """Bulk action to unpublish texts"""
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} text(s) unpublished.')
    unpublish_texts.short_description = 'Unpublish selected texts'

    def mark_as_ready(self, request, queryset):
        """Bulk action to mark texts as ready"""
        updated = queryset.update(processing_status='ready')
        self.message_user(request, f'{updated} text(s) marked as ready.')
    mark_as_ready.short_description = 'Mark as ready'


@admin.register(TextSection)
class TextSectionAdmin(admin.ModelAdmin):
    """
    Admin interface for managing hierarchical text sections.
    """
    list_display = [
        'get_text_title',
        'section_type',
        'get_section_label',
        'order_index',
        'get_parent_label',
        'word_count',
    ]
    list_filter = ['text', 'section_type']
    search_fields = ['title', 'content', 'reference_id']
    raw_id_fields = ['text', 'parent']
    readonly_fields = ['created_at', 'updated_at', 'word_count', 'breadcrumb']

    fieldsets = (
        ('Relationships', {
            'fields': ('text', 'parent')
        }),
        ('Structure', {
            'fields': ('section_type', 'order_index', 'title', 'reference_id')
        }),
        ('Content', {
            'fields': ('content', 'word_count')
        }),
        ('Navigation', {
            'fields': ('breadcrumb',),
            'classes': ('collapse',),
            'description': 'Hierarchical path to this section'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_text_title(self, obj):
        """Display text title in list view"""
        return obj.text.title
    get_text_title.short_description = 'Text'
    get_text_title.admin_order_field = 'text__title'

    def get_section_label(self, obj):
        """Display section label (title or type + index)"""
        return obj.title or f"{obj.section_type.title()} {obj.order_index}"
    get_section_label.short_description = 'Section'

    def get_parent_label(self, obj):
        """Display parent section label"""
        if obj.parent:
            return obj.parent.title or f"{obj.parent.section_type.title()} {obj.parent.order_index}"
        return "-"
    get_parent_label.short_description = 'Parent'


@admin.register(TextCitation)
class TextCitationAdmin(admin.ModelAdmin):
    """
    Admin interface for managing text citations from debates.
    """
    list_display = [
        'get_debate_title',
        'get_text_title',
        'get_section',
        'match_confidence',
        'match_method',
        'verified',
        'created_at',
    ]
    list_filter = [
        'verified',
        'match_method',
        'text',
        'created_at',
    ]
    search_fields = [
        'citation_text',
        'extracted_quote',
        'text__title',
        'debate_message__debate__title',
    ]
    raw_id_fields = ['debate_message', 'text', 'text_section']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Relationships', {
            'fields': ('debate_message', 'text', 'text_section')
        }),
        ('Citation Content', {
            'fields': ('citation_text', 'extracted_quote')
        }),
        ('Matching & Verification', {
            'fields': ('match_confidence', 'match_method', 'verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['verify_citations', 'unverify_citations']

    def get_debate_title(self, obj):
        """Display debate title"""
        return obj.debate_message.debate.title
    get_debate_title.short_description = 'Debate'
    get_debate_title.admin_order_field = 'debate_message__debate__title'

    def get_text_title(self, obj):
        """Display cited text title"""
        return obj.text.title
    get_text_title.short_description = 'Text'
    get_text_title.admin_order_field = 'text__title'

    def get_section(self, obj):
        """Display section if available"""
        if obj.text_section:
            return obj.text_section.breadcrumb
        return "-"
    get_section.short_description = 'Section'

    def verify_citations(self, request, queryset):
        """Bulk action to verify citations"""
        updated = queryset.update(verified=True)
        self.message_user(request, f'{updated} citation(s) verified.')
    verify_citations.short_description = 'Mark as verified'

    def unverify_citations(self, request, queryset):
        """Bulk action to unverify citations"""
        updated = queryset.update(verified=False)
        self.message_user(request, f'{updated} citation(s) unverified.')
    unverify_citations.short_description = 'Mark as unverified'
