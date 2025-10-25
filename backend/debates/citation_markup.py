"""
Post-processing to add {Title} markup to work citations.

Since Claude resists using {Title} markup despite instructions,
this function detects work mentions and adds the markup automatically.
"""
import re
from texts.models import PrimaryText


def add_citation_markup(content, persona):
    """
    Detect work title mentions and wrap them in {Title} markup.

    Args:
        content (str): The debate message content
        persona (Persona): The persona who wrote the message

    Returns:
        str: Content with {Title} markup added to detected work citations
    """
    # Get primary texts for this persona
    texts = PrimaryText.objects.filter(
        author__icontains=persona.name.split()[-1],  # Match by last name
        is_published=True
    ).values_list('title', flat=True)

    if not texts:
        return content

    # Sort by length (longest first) to avoid partial matches
    texts_sorted = sorted(texts, key=len, reverse=True)

    modified_content = content

    for title in texts_sorted:
        # Skip if already has markup
        if f"{{{title}}}" in modified_content:
            continue

        # Pattern: match title with common prefixes
        # Matches: "in Republic", "in the Republic", "my Republic", "as Republic shows"
        patterns = [
            rf'\b(in|In)\s+(the\s+)?({re.escape(title)})\b',
            rf'\b(my|My)\s+({re.escape(title)})\b',
            rf'\b(as|As)\s+({re.escape(title)})\s+(shows|demonstrates|argues)',
            rf'\b({re.escape(title)})\s*,',  # Title followed by comma
        ]

        for pattern in patterns:
            def replacer(match):
                # Find the title in the match (last group usually)
                groups = match.groups()
                title_idx = -1
                for i, g in enumerate(groups):
                    if g and title in g:
                        title_idx = i
                        break

                if title_idx == -1:
                    return match.group(0)

                # Rebuild with markup
                result = match.group(0).replace(title, f"{{{title}}}")
                return result

            modified_content = re.sub(pattern, replacer, modified_content)

    return modified_content


def extract_work_titles_simple(content):
    """
    Extract work titles from {Title} markup.

    Args:
        content (str): Message content

    Returns:
        list: List of work titles found in {Title} format
    """
    return re.findall(r'\{([^}]+)\}', content)
