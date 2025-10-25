"""
Tests for debate prompt generation.
"""
import pytest
from debates.prompts import (
    build_system_prompt,
    build_round_prompt,
    build_opening_statement_prompt,
    _get_persona_primary_texts,
    _format_text_excerpts,
)
from personas.models import Persona
from texts.models import PrimaryText


@pytest.mark.django_db
class TestSystemPromptGeneration:
    """Test system prompt construction for debate personas."""

    def test_system_prompt_includes_persona_name(self):
        """System prompt should include the persona's name."""
        persona = Persona.objects.create(
            name="Test Philosopher",
            slug="test-philosopher",
            category="philosophers",
            era="Ancient Greece",
            full_markdown="# Test content"
        )

        prompt = build_system_prompt(persona)

        assert "Test Philosopher" in prompt
        assert "philosophers" in prompt

    def test_system_prompt_includes_full_markdown(self):
        """System prompt should include the persona's full markdown content."""
        markdown_content = """# Test Persona

## Core Positions
- Position 1
- Position 2

## Debate Style
Uses logical argumentation."""

        persona = Persona.objects.create(
            name="Test Thinker",
            slug="test-thinker",
            category="philosophers",
            era="Modern",
            full_markdown=markdown_content
        )

        prompt = build_system_prompt(persona)

        assert "# Test Persona" in prompt
        assert "Core Positions" in prompt
        assert "Debate Style" in prompt

    def test_system_prompt_citation_instructions_present(self):
        """System prompt should include citation instructions in style requirements."""
        persona, _ = Persona.objects.get_or_create(
            slug="plato-test",
            defaults={
                "name": "Plato Test",
                "category": "philosophers",
                "era": "Ancient Greece",
                "full_markdown": "# Plato"
            }
        )

        prompt = build_system_prompt(persona)

        # Check for citation guidance in main style requirements
        assert "Ground your arguments in your documented works" in prompt
        assert "{Republic}" in prompt or "cite specific texts" in prompt
        assert "cite" in prompt.lower()

    def test_system_prompt_with_primary_texts_includes_citation_section(self):
        """System prompt should include detailed citation section when primary texts exist."""
        persona, _ = Persona.objects.get_or_create(
            slug="plato-with-texts",
            defaults={
                "name": "Plato With Texts",
                "category": "philosophers",
                "era": "Ancient Greece",
                "full_markdown": "# Plato"
            }
        )

        # Create a primary text for this persona
        PrimaryText.objects.get_or_create(
            title="Republic Test",
            author="Plato With Texts",
            defaults={
                "publication_year": -380,
                "word_count": 100000,
                "reading_difficulty": "advanced",
                "is_published": True
            }
        )[0]

        prompt = build_system_prompt(persona)

        # Check for dedicated citation section
        assert "Your Primary Works Available for Reference" in prompt
        assert "Citation Requirements" in prompt or "Citation Examples" in prompt
        assert "IMPORTANT: Cite your primary works" in prompt or "should actively reference" in prompt
        assert "{Republic" in prompt or "Citation Examples" in prompt

    def test_system_prompt_depth_level_affects_citation_guidance(self):
        """Citation guidance should vary by depth level."""
        persona, _ = Persona.objects.get_or_create(
            slug="aristotle-depth-test",
            defaults={
                "name": "Aristotle Depth Test",
                "category": "philosophers",
                "era": "Ancient Greece",
                "full_markdown": "# Aristotle"
            }
        )

        PrimaryText.objects.get_or_create(
            title="Nicomachean Ethics Test",
            author="Aristotle Depth Test",
            defaults={
                "publication_year": -350,
                "word_count": 80000,
                "reading_difficulty": "advanced",
                "is_published": True
            }
        )

        intro_prompt = build_system_prompt(persona, depth_level='introductory')
        advanced_prompt = build_system_prompt(persona, depth_level='advanced')

        # Introductory should mention general references
        assert "general references" in intro_prompt or "key ideas" in intro_prompt

        # Advanced should mention specific passages
        assert "specific arguments and passages" in advanced_prompt or "with detail" in advanced_prompt


@pytest.mark.django_db
class TestRoundPromptGeneration:
    """Test round-specific prompt construction."""

    def test_round_1_prompt_includes_citation_reminder(self):
        """Round 1 prompt should remind persona to cite works."""
        from debates.models import Debate
        from users.models import User

        user, _ = User.objects.get_or_create(
            email="test-round1@example.com",
            defaults={"password": "testpass123"}
        )

        debate = Debate.objects.create(
            user=user,
            title="Test Debate",
            topic="What is justice?",
            slug="test-debate"
        )

        prompt = build_round_prompt(debate, round_number=1, previous_messages=[])

        # Check for current citation reminder wording
        assert "mandatory markup" in prompt.lower() or "wrap all work titles" in prompt.lower() or "{title}" in prompt.lower()
        assert "{" in prompt and "}" in prompt  # Citation format example

    def test_round_2_prompt_includes_citation_reminder(self):
        """Subsequent rounds should also remind persona to cite works."""
        from debates.models import Debate
        from users.models import User

        user, _ = User.objects.get_or_create(
            email="test-round2@example.com",
            defaults={"password": "testpass123"}
        )

        debate = Debate.objects.create(
            user=user,
            title="Test Debate",
            topic="What is justice?",
            slug="test-debate"
        )

        prompt = build_round_prompt(debate, round_number=2, previous_messages=[])

        # Check for current citation reminder wording (same for all rounds)
        assert "mandatory markup" in prompt.lower() or "wrap all work titles" in prompt.lower() or "{title}" in prompt.lower()
        assert "{" in prompt and "}" in prompt  # Citation format example


@pytest.mark.django_db
class TestOpeningStatementPrompt:
    """Test opening statement prompt construction."""

    def test_opening_statement_includes_citation_reminder(self):
        """Opening statement prompt should remind persona to cite works."""
        from debates.models import Debate
        from users.models import User

        user, _ = User.objects.get_or_create(
            email="test-opening@example.com",
            defaults={"password": "testpass123"}
        )

        debate = Debate.objects.create(
            user=user,
            title="Test Debate",
            topic="What is knowledge?",
            slug="test-debate-opening"
        )

        persona = Persona.objects.create(
            name="Kant",
            slug="kant",
            category="philosophers",
            era="Enlightenment",
            full_markdown="# Kant"
        )

        prompt = build_opening_statement_prompt(debate, persona)

        # Check for current citation reminder wording
        assert "mandatory" in prompt.lower() or "wrap all work titles" in prompt.lower() or "{braces}" in prompt.lower()
        assert "{" in prompt and "}" in prompt  # Citation format example


@pytest.mark.django_db
class TestPrimaryTextRetrieval:
    """Test primary text fetching and formatting."""

    def test_get_persona_primary_texts_exact_match(self):
        """Should retrieve texts by exact author name match."""
        persona = Persona.objects.create(
            name="Plato",
            slug="plato",
            category="philosophers",
            era="Ancient Greece",
            full_markdown="# Plato"
        )

        text1 = PrimaryText.objects.create(
            title="Republic",
            slug="republic-test",
            author="Plato",
            word_count=100000,
            is_published=True
        )

        text2 = PrimaryText.objects.create(
            title="Symposium",
            slug="symposium-test",
            author="Plato",
            word_count=50000,
            is_published=True
        )

        texts = _get_persona_primary_texts(persona)

        assert text1 in texts
        assert text2 in texts

    def test_get_persona_primary_texts_limits_to_five(self):
        """Should limit results to 5 most substantial works."""
        persona = Persona.objects.create(
            name="Aristotle",
            slug="aristotle",
            category="philosophers",
            era="Ancient Greece",
            full_markdown="# Aristotle"
        )

        # Create 7 texts
        for i in range(7):
            PrimaryText.objects.create(
                title=f"Work {i}",
                slug=f"work-{i}-aristotle-test",
                author="Aristotle",
                word_count=(i + 1) * 10000,
                is_published=True
            )

        texts = _get_persona_primary_texts(persona)

        assert len(texts) <= 5
        # Should be ordered by word count descending
        texts_list = list(texts)
        assert texts_list[0].word_count >= texts_list[-1].word_count

    def test_format_text_excerpts_includes_key_info(self):
        """Formatted text excerpts should include title, year, word count."""
        text = PrimaryText.objects.create(
            title="Critique of Pure Reason",
            author="Kant",
            publication_year=1781,
            word_count=200000,
            reading_difficulty="advanced",
            description="A foundational work of modern philosophy examining the limits of reason.",
            is_published=True
        )

        formatted = _format_text_excerpts([text])

        assert "Critique of Pure Reason" in formatted
        assert "1781" in formatted
        assert "200,000" in formatted
        assert "advanced" in formatted

    def test_format_text_excerpts_empty_list(self):
        """Should return empty string for empty text list."""
        formatted = _format_text_excerpts([])

        assert formatted == ""


@pytest.mark.django_db
class TestCitationInstructionCompleteness:
    """Verify all necessary citation instructions are present in prompts."""

    def test_all_prompts_include_citation_guidance(self):
        """All prompt types should include citation guidance (citations are recommended but not required)."""
        from debates.models import Debate
        from users.models import User

        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        persona = Persona.objects.create(
            name="Socrates",
            slug="socrates",
            category="philosophers",
            era="Ancient Greece",
            full_markdown="# Socrates"
        )

        debate = Debate.objects.create(
            user=user,
            title="Test",
            topic="What is virtue?",
            slug="test-debate"
        )

        # Check system prompt includes citation guidance
        system_prompt = build_system_prompt(persona)
        # Should mention citations, work titles, or the {braces} format
        assert any(term in system_prompt.lower() for term in ["cite", "citation", "{title}", "work titles", "{braces}", "markup"])

        # Check round 1 prompt includes citation format guidance
        round1_prompt = build_round_prompt(debate, 1, [])
        # Should include guidance about work title formatting
        assert any(term in round1_prompt.lower() for term in ["{title}", "work citations", "{braces}", "markup"])

        # Check round 2+ prompt includes citation format guidance
        round2_prompt = build_round_prompt(debate, 2, [])
        assert any(term in round2_prompt.lower() for term in ["{title}", "work citations", "{braces}", "markup"])

        # Check opening statement prompt includes citation guidance
        opening_prompt = build_opening_statement_prompt(debate, persona)
        assert any(term in opening_prompt.lower() for term in ["{title}", "work titles", "{braces}", "markup"])
