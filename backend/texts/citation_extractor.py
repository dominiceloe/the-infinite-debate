"""
Citation extraction utility for automatically detecting text references in debate messages.
"""

import re
from typing import List, Dict, Optional
from .models import PrimaryText, TextCitation, TextSection


class CitationExtractor:
    """
    Extracts citations from debate messages using pattern matching.

    Detects references like:
    - "In the Republic, I argued..."
    - "As I wrote in my Apology..."
    - "My Meditations on First Philosophy demonstrate..."
    - "The Summa Theologica addresses this..."
    """

    # Common citation patterns
    CITATION_PATTERNS = [
        # "In the [Title]" or "In my [Title]"
        r'(?:in|from)\s+(?:the|my)?\s*([A-Z][A-Za-z\s]+?)(?:\s+Book\s+[IVX\d]+)?(?:,|\.|;|\s+I\s)',

        # "As I wrote in [Title]"
        r'as\s+I\s+(?:wrote|argued|stated|demonstrated|showed)\s+in\s+(?:the|my)?\s*([A-Z][A-Za-z\s]+?)(?:,|\.|;)',

        # "My [Title] demonstrates/shows/argues"
        r'my\s+([A-Z][A-Za-z\s]+?)\s+(?:demonstrates|shows|argues|establishes|proves)',

        # "The [Title] addresses/discusses"
        r'the\s+([A-Z][A-Za-z\s]+?)\s+(?:addresses|discusses|examines|explores|considers)',

        # Direct quotes: "[Title]: 'quote'"
        r'([A-Z][A-Za-z\s]+?):\s*["\']',
    ]

    def __init__(self):
        """Initialize extractor with cached text titles."""
        self._text_cache = {}
        self._refresh_cache()

    def _refresh_cache(self):
        """Refresh cache of all published texts."""
        self._text_cache = {
            text.title.lower(): text
            for text in PrimaryText.objects.filter(is_published=True)
        }

    def extract_citations_from_markers(self, message_content: str, persona_name: str = None) -> List[Dict]:
        """
        Extract citations from {Title} markers in debate message.

        This is the preferred extraction method - Claude explicitly marks citations.

        Args:
            message_content: The text content with {Title} markers
            persona_name: Optional persona name to filter texts by author

        Returns:
            List of citation dictionaries with:
            - text: PrimaryText object
            - citation_text: The context around the citation
            - match_confidence: 1.0 (explicit marking)
            - match_method: 'marker'
            - title_marked: The title as marked by Claude
        """
        citations = []

        # Pattern to find {Title} markers
        marker_pattern = r'\{([^}]+)\}'
        matches = re.finditer(marker_pattern, message_content)

        for match in matches:
            potential_title = match.group(1).strip()

            # Try to match against known texts
            text = self._match_text(potential_title, persona_name)

            if text:
                # Extract context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(message_content), match.end() + 50)
                context = message_content[start:end]

                citations.append({
                    'text': text,
                    'citation_text': context,
                    'match_confidence': 1.0,  # Explicit marking = 100% confidence
                    'match_method': 'marker',
                    'title_marked': potential_title,
                })

        return self._deduplicate_citations(citations)

    @staticmethod
    def remove_citation_markers(content: str) -> str:
        """
        Remove {Title} markers from content, leaving just the title text.

        Args:
            content: Text with {Title} markers

        Returns:
            Clean text with markers removed: "In {Republic}" → "In Republic"
        """
        return re.sub(r'\{([^}]+)\}', r'\1', content)

    def extract_citations(self, message_content: str, persona_name: str = None) -> List[Dict]:
        """
        Extract citations from a debate message.

        First tries marker-based extraction ({Title}), then falls back to regex patterns.

        Args:
            message_content: The text content of the debate message
            persona_name: Optional persona name to filter texts by author

        Returns:
            List of citation dictionaries with:
            - text: PrimaryText object
            - citation_text: The matched citation string
            - match_confidence: 0.0-1.0 confidence score
            - match_method: 'marker' or 'regex'
        """
        # First, try marker-based extraction
        marker_citations = self.extract_citations_from_markers(message_content, persona_name)
        if marker_citations:
            return marker_citations

        # Fall back to regex patterns for backwards compatibility
        citations = []

        # Try each pattern
        for pattern in self.CITATION_PATTERNS:
            matches = re.finditer(pattern, message_content, re.IGNORECASE)

            for match in matches:
                # Extract the potential title
                potential_title = match.group(1).strip()

                # Try to match against known texts
                text = self._match_text(potential_title, persona_name)

                if text:
                    # Extract the full citation context (surrounding text)
                    start = max(0, match.start() - 50)
                    end = min(len(message_content), match.end() + 50)
                    context = message_content[start:end]

                    # Calculate confidence based on match quality
                    confidence = self._calculate_confidence(
                        potential_title,
                        text.title,
                        persona_name,
                        text.author
                    )

                    citations.append({
                        'text': text,
                        'citation_text': context,
                        'match_confidence': confidence,
                        'match_method': 'regex',
                    })

        # Deduplicate citations to the same text
        return self._deduplicate_citations(citations)

    def _match_text(self, potential_title: str, persona_name: str = None) -> Optional[PrimaryText]:
        """
        Match a potential title string against known texts.

        Args:
            potential_title: The extracted potential title
            persona_name: Optional persona name to prioritize author matches

        Returns:
            PrimaryText object if matched, None otherwise
        """
        potential_title_lower = potential_title.lower().strip()

        # Filter out single common words that are unlikely to be titles
        common_words = {'nature', 'god', 'being', 'world', 'truth', 'good', 'evil', 'life', 'death',
                       'soul', 'mind', 'body', 'reason', 'faith', 'love', 'knowledge', 'wisdom',
                       'justice', 'virtue', 'beauty', 'time', 'space', 'matter', 'form', 'essence'}

        # Reject single common words (less than 2 words AND in common list)
        word_count = len(potential_title_lower.split())
        if word_count == 1 and potential_title_lower in common_words:
            return None

        # Require at least 2 words for a valid title match (prevents "nature" matching)
        if word_count < 2:
            return None

        # Exact match
        if potential_title_lower in self._text_cache:
            return self._text_cache[potential_title_lower]

        # Partial match - but ONLY if the persona authored the text
        # This prevents false positives like Plato citing Adam Smith
        if persona_name:
            for title, text in self._text_cache.items():
                # Only consider texts by this persona's author
                if persona_name.lower() not in text.author.lower():
                    continue

                # Check if potential title is in the full title or vice versa
                if potential_title_lower in title or title in potential_title_lower:
                    return text

        # Check for common abbreviations - but only for persona's own works
        if persona_name:
            abbreviations = {
                'republic': 'republic',
                'apology': 'apology',
                'meditations': 'meditations',
                'summa': 'summa theologica',
                'critique': 'critique of pure reason',
                'ethics': 'nicomachean ethics',  # Could be Aristotle or Spinoza
                'politics': 'politics',
            }

            for abbr, full_title in abbreviations.items():
                if abbr in potential_title_lower:
                    if full_title in self._text_cache:
                        text = self._text_cache[full_title]
                        # Only return if author matches
                        if persona_name.lower() in text.author.lower():
                            return text

        return None

    def _calculate_confidence(
        self,
        matched_title: str,
        actual_title: str,
        persona_name: str,
        text_author: str
    ) -> float:
        """
        Calculate confidence score for a citation match.

        Factors:
        - Exact title match: +0.3
        - Partial title match: +0.1
        - Author matches persona: +0.4
        - Pattern strength: +0.3 (baseline)

        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.3  # Baseline for regex pattern match

        # Title match quality
        if matched_title.lower() == actual_title.lower():
            confidence += 0.3  # Exact match
        elif matched_title.lower() in actual_title.lower():
            confidence += 0.2  # Partial match
        else:
            confidence += 0.1  # Fuzzy match

        # Author match
        if persona_name and persona_name.lower() in text_author.lower():
            confidence += 0.4  # Author matches persona

        return min(confidence, 1.0)

    def _deduplicate_citations(self, citations: List[Dict]) -> List[Dict]:
        """
        Remove duplicate citations to the same text, keeping highest confidence.
        """
        seen_texts = {}

        for citation in citations:
            text_id = citation['text'].id

            if text_id not in seen_texts:
                seen_texts[text_id] = citation
            else:
                # Keep the one with higher confidence
                if citation['match_confidence'] > seen_texts[text_id]['match_confidence']:
                    seen_texts[text_id] = citation

        return list(seen_texts.values())

    def create_citations_for_message(self, debate_message, save=True) -> List[TextCitation]:
        """
        Extract and create TextCitation objects for a debate message.

        Args:
            debate_message: DebateMessage object
            save: Whether to save citations to database (default True)

        Returns:
            List of created TextCitation objects
        """
        # Get persona name from the message
        persona_name = debate_message.persona.name if hasattr(debate_message, 'persona') else None

        # Extract citations
        extracted = self.extract_citations(debate_message.content, persona_name)

        # Create TextCitation objects
        created_citations = []

        for citation_data in extracted:
            citation = TextCitation(
                debate_message=debate_message,
                text=citation_data['text'],
                citation_text=citation_data['citation_text'],
                match_confidence=citation_data['match_confidence'],
                match_method=citation_data['match_method'],
                verified=False,
            )

            if save:
                citation.save()

            created_citations.append(citation)

        return created_citations
