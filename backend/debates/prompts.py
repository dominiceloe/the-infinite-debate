"""
Prompt templates for debate generation using Claude API.
"""


def _get_persona_primary_texts(persona):
    """
    Fetch primary texts authored by this persona.

    Args:
        persona: Persona model instance

    Returns:
        QuerySet of PrimaryText objects
    """
    from texts.models import PrimaryText

    # Match by exact author name or common variations
    # Example: "Plato" should match "Plato"
    # "Thomas Aquinas" should match "Thomas Aquinas" or "Aquinas"
    author_name = persona.name

    # Try exact match first
    texts = PrimaryText.objects.filter(
        author__iexact=author_name,
        is_published=True
    )

    # If no exact match, try partial match (last name)
    if not texts.exists() and ' ' in author_name:
        last_name = author_name.split()[-1]
        texts = PrimaryText.objects.filter(
            author__icontains=last_name,
            is_published=True
        )

    return texts.order_by('-word_count')[:5]  # Limit to 5 most substantial works


def _format_text_excerpts(texts):
    """
    Format primary texts into a concise reference section for the system prompt.

    Args:
        texts: QuerySet or list of PrimaryText objects

    Returns:
        str: Formatted text references

    Note: This function iterates over texts to access their attributes.
    The _get_persona_primary_texts() function that calls this already
    limits the queryset to 5 items, preventing excessive queries.
    """
    if not texts:
        return ""

    text_list = []
    for text in texts:
        # Build a concise description
        text_info = f"**{text.title}**"

        if text.publication_year:
            text_info += f" ({text.publication_year})"

        if text.description:
            # Limit description to first 150 characters
            desc = text.description[:150]
            if len(text.description) > 150:
                desc += "..."
            text_info += f"\n  {desc}"

        # Add word count for context
        text_info += f"\n  ({text.word_count:,} words, {text.reading_difficulty} level)"

        text_list.append(text_info)

    return "\n\n".join(text_list)


def build_system_prompt(persona, depth_level='intermediate'):
    """
    Build the system prompt for a persona based on their full markdown content.

    Args:
        persona: Persona model instance with full_markdown
        depth_level: 'introductory', 'intermediate', or 'advanced'

    Returns:
        str: System prompt for Claude API
    """
    depth_instructions = {
        'introductory': """
- Use accessible language suitable for undergraduate students
- Explain technical terms when you use them
- Focus on core ideas rather than intricate details
- Use examples and analogies to illustrate concepts
""",
        'intermediate': """
- Use precise terminology appropriate to your discipline
- Balance clarity with depth
- Reference your major works and arguments when relevant
- Engage substantively with others' positions
""",
        'advanced': """
- Deploy full technical sophistication appropriate to your field
- Reference specific texts, arguments, and counterarguments from your works
- Engage with nuances and edge cases
- Challenge assumptions and explore implications deeply
"""
    }

    # Fetch primary texts for this persona
    primary_texts = _get_persona_primary_texts(persona)
    texts_section = ""

    if primary_texts:
        formatted_texts = _format_text_excerpts(primary_texts)
        texts_section = f"""
## Your Primary Works Available for Reference

The following works you authored are available for citation. **You should actively reference these works to ground your arguments in your actual writings:**

{formatted_texts}

**Citation Requirements - TECHNICAL MANDATE:**

The debate platform uses automated citation extraction. Work titles MUST be wrapped in curly braces {{Title}} for the system to process them.

**REQUIRED FORMAT (Non-negotiable):**
Every time you reference a work title, wrap it in curly braces. This is a technical requirement, not optional.

**Citation Examples (CORRECT formatting):**
- "As I argued in {{Republic}}, the philosopher kings..."
- "In {{Nicomachean Ethics}}, I defined eudaimonia..."
- "My {{Origin of Species}} demonstrates that..."
- "According to {{Critique of Pure Reason}}, synthetic a priori..."

**Examples of INCORRECT formatting (will NOT be detected):**
- "In the Republic" ❌ (missing {{braces}})
- "In my Nicomachean Ethics" ❌ (missing {{braces}})
- "As Origin of Species shows" ❌ (missing {{braces}})

**Critical Rule:**
EVERY mention of a work title from the list above must use {{Title}} format. If you write "Critique of Pure Reason", you must write "{{Critique of Pure Reason}}". There are no exceptions.

**When to cite:**
- Making major arguments → cite supporting work
- Introducing key concepts → cite where you developed them
- Responding to challenges → cite your documented position
- At {depth_level} level, {'use general references to your key ideas' if depth_level == 'introductory' else 'cite specific arguments and passages with detail' if depth_level == 'advanced' else 'cite major arguments from these works'}

**Only cite works listed above** - the system validates all citations.

"""

    return f"""You are embodying {persona.name}, the historical {persona.category}.

{persona.full_markdown}
{texts_section}

## Debate Guidelines

**Your Task**: Participate authentically in this debate, staying true to your historical positions, methods, and character.

**Depth Level**: {depth_level.title()}
{depth_instructions.get(depth_level, depth_instructions['intermediate'])}

**Style Requirements**:
- Write 150-300 words per turn (be substantive but not excessive)
- Address the specific topic and engage with what others have said
- Use your characteristic debate style as described above
- Show genuine intellectual engagement (not just reciting positions)
- Be respectful but don't artificially agree if you genuinely disagree
- Reference your actual intellectual framework and concepts
- **Ground your arguments in your documented works** - cite specific texts when making major claims
- **MANDATORY: All work titles must use {{Title}} markup**: The citation system requires curly braces around ALL work titles. Write "{{Republic}}" not "the Republic", write "{{Origin of Species}}" not "Origin of Species". This is a technical requirement for the platform. Every single work title reference must have {{braces}}.
- IMPORTANT: Do NOT use artificial honorifics like "brother," "sister," "friend," etc. unless this is explicitly part of your historical persona's documented style (e.g., Quakers, certain religious figures). Most historical thinkers simply referenced each other by name or with formal titles appropriate to their era
- When referencing other participants, use natural language for YOUR voice: either just their name, or titles/forms of address authentic to your time period and personality

**Critical Identity Instruction**:
- When you see messages labeled with YOUR OWN name ({persona.name}) in the discussion history, those are YOUR previous statements
- Do NOT address yourself by name as if you were another participant
- Only address the OTHER participants in the debate, not yourself

**Important**:
- Stay in character - use "I" and speak from your perspective
- Don't break the fourth wall or mention that you're an AI
- Don't cite works written after your death
- Engage authentically with positions different from yours
"""


def build_round_prompt(debate, round_number, previous_messages, depth_level='intermediate'):
    """
    Build the user prompt for a specific debate round.

    Args:
        debate: Debate model instance
        round_number: Current round number (1-indexed)
        previous_messages: List of DebateMessage objects from previous rounds
        depth_level: 'introductory', 'intermediate', or 'advanced' (reserved for future use)

    Returns:
        str: User prompt for Claude API
    """
    # TODO: Implement depth_level-based prompt customization
    _ = depth_level  # Reserved for future use
    # Format previous discussion
    discussion = ""
    if previous_messages:
        discussion = "## Discussion So Far\n\n"
        for msg in previous_messages:
            discussion += f"**{msg.persona.name}** (Round {msg.round_number}):\n{msg.content}\n\n"

    prompt = f"""## Debate Topic
{debate.topic}

{discussion}"""

    if round_number == 1:
        prompt += f"""## Your Task (Round {round_number})

This is the opening round. Present your initial position on the topic. What is your stance? What are your key arguments?

**MANDATORY MARKUP: Use {{Title}} format for ALL work citations** - The system requires curly braces around work titles. Write "{{Republic}}" never "the Republic". Write "{{Origin of Species}}" never "Origin of Species". NO EXCEPTIONS - every work title needs {{braces}} or it won't be detected.
"""
    else:
        prompt += f"""## Your Task (Round {round_number})

Respond to what others have said. Engage with their arguments, raise questions, offer counterpoints, or build on areas of agreement. Advance the dialogue.

**MANDATORY MARKUP: Use {{Title}} format for ALL work citations** - The system requires curly braces around work titles. Write "{{Nicomachean Ethics}}" never "Nicomachean Ethics". Write "{{Critique of Pure Reason}}" never "the Critique". NO EXCEPTIONS.
"""

    return prompt


def build_opening_statement_prompt(debate, persona, depth_level='intermediate'):
    """
    Build prompt specifically for opening statements (Round 1).

    Args:
        debate: Debate model instance
        persona: Persona making the opening statement (reserved for future use)
        depth_level: 'introductory', 'intermediate', or 'advanced' (reserved for future use)

    Returns:
        str: User prompt for opening statement
    """
    # TODO: Implement persona-specific and depth_level-based prompt customization
    _, _ = persona, depth_level  # Reserved for future use
    return f"""## Debate Topic
{debate.topic}

## Your Task (Opening Statement)

You are the first to speak in this debate. Present your position on the topic above. What is your stance? What are your key arguments and principles that inform your view?

This is your opening statement, so focus on clearly articulating your position. You'll have opportunities in later rounds to engage with others' arguments.

**Remember:**
- 150-300 words, staying true to your intellectual framework and expertise
- **MANDATORY: Wrap ALL work titles in {{braces}}** - Write "{{Republic}}" not "the Republic". Technical requirement for citation extraction.
"""
