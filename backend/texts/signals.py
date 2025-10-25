"""
Signal handlers for automatic citation extraction.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from debates.models import DebateMessage
from .citation_extractor import CitationExtractor


@receiver(post_save, sender=DebateMessage)
def extract_citations_from_message(sender, instance, created, **kwargs):
    """
    Automatically extract citations when a new debate message is created.
    Also removes citation markers from the saved content.

    Args:
        sender: DebateMessage model class
        instance: The DebateMessage instance
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    # Only process new messages (not updates)
    if not created:
        return

    # Skip if message has no content
    if not instance.content:
        return

    # Extract and create citations
    extractor = CitationExtractor()

    try:
        # Extract citations from markers/regex
        citations = extractor.create_citations_for_message(instance, save=True)

        # Optional: Log citation extraction for debugging
        if citations:
            print(f"[Citation Extractor] Found {len(citations)} citations in message {instance.id}")

        # Remove citation markers from content if any exist
        original_content = instance.content
        cleaned_content = CitationExtractor.remove_citation_markers(original_content)

        # Only update if content changed (had markers)
        if cleaned_content != original_content:
            # Use update() to avoid triggering signal again
            DebateMessage.objects.filter(pk=instance.pk).update(content=cleaned_content)
            # Also update the in-memory instance
            instance.content = cleaned_content
            print(f"[Citation Extractor] Removed citation markers from message {instance.id}")

    except Exception as e:
        # Don't let citation extraction errors break message creation
        print(f"[Citation Extractor] Error processing message {instance.id}: {e}")
