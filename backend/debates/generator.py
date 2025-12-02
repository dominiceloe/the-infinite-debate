"""
Debate generation engine using Anthropic Claude API.
Orchestrates multi-round philosophical debates between historical thinkers.
"""

import os
from datetime import datetime
from anthropic import Anthropic
from django.utils import timezone
from django.conf import settings
from .models import Debate, DebateMessage
from .prompts import build_system_prompt, build_round_prompt, build_opening_statement_prompt
import redis
import json


class DebateGenerator:
    """
    Generates philosophical debates by orchestrating Claude API calls
    for each persona across multiple rounds.
    """

    def __init__(self, api_key=None):
        """
        Initialize the debate generator.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-5-20250929"  # Latest Sonnet 4.5

    def _publish_event(self, debate_slug, event_type, data):
        """
        Publish an event to Redis pub/sub for SSE streaming.

        Args:
            debate_slug: Slug of the debate
            event_type: Type of event (status, message)
            data: Event data to publish
        """
        try:
            redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
            channel_name = f"debate:{debate_slug}"
            message = {
                'type': event_type,
                **data
            }
            redis_client.publish(channel_name, json.dumps(message))
            redis_client.close()
        except Exception as e:
            # Log error but don't fail generation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to publish event for debate {debate_slug}: {str(e)}")

    def generate(self, debate):
        """
        Generate a complete debate.

        Args:
            debate: Debate model instance

        Returns:
            Debate: Updated debate instance

        Raises:
            Exception: If generation fails
        """
        try:
            # Update status to generating
            debate.status = 'generating'
            debate.save()

            # Get participants in chronological order
            participants = list(debate.participants.all().order_by('birth_year'))

            if not participants:
                raise ValueError("No participants found for debate")

            # Initialize transcript
            transcript = self._build_transcript_header(debate, participants)

            # Generate each round
            for round_num in range(1, debate.max_rounds + 1):
                transcript += f"\n## Round {round_num}\n\n"

                # Query optimization: Fetch all previous messages once per round
                # with select_related to avoid N+1 queries inside the participant loop
                previous_messages = list(
                    DebateMessage.objects.filter(
                        debate=debate
                    ).select_related('persona').order_by('round_number', 'persona__birth_year')
                )

                # Each participant speaks in chronological order
                for persona in participants:
                    # Generate response (uses cached previous_messages list)
                    # Beta: Now returns (content, tokens_used) tuple
                    content, tokens_used = self._generate_response(
                        debate=debate,
                        persona=persona,
                        round_number=round_num,
                        previous_messages=previous_messages
                    )

                    # Save message with token usage tracking
                    message = DebateMessage.objects.create(
                        debate=debate,
                        persona=persona,
                        round_number=round_num,
                        content=content,
                        tokens_used=tokens_used  # Beta: Track actual token usage from Claude API
                    )

                    # Append to transcript
                    transcript += f"### {persona.name}\n\n{content}\n\n"

                    # Update debate progress
                    debate.rounds_completed = round_num
                    debate.transcript = transcript
                    debate.save()

                    # Publish message event for real-time updates
                    self._publish_event(debate.slug, 'message', {
                        'message_id': message.id,
                        'persona_id': persona.id,
                        'persona_name': persona.name,
                        'persona_slug': persona.slug,
                        'round_number': round_num,
                        'content': content,
                        'rounds_completed': round_num
                    })

                    # Add newly created message to previous_messages list for next iteration
                    # This avoids re-querying the database
                    previous_messages.append(message)

            # Generate AI summary of each persona's final position
            summary = self._generate_summary(debate, participants)

            # Mark as completed
            debate.status = 'completed'
            debate.completed_at = timezone.now()
            debate.transcript = transcript
            debate.summary = summary
            debate.save()

            return debate

        except Exception as e:
            # Mark as failed and store error
            debate.status = 'failed'
            debate.error_message = str(e)
            debate.save()
            raise

    def _generate_response(self, debate, persona, round_number, previous_messages):
        """
        Generate a single response from a persona using Claude API.

        Args:
            debate: Debate instance
            persona: Persona making the response
            round_number: Current round number
            previous_messages: List of previous DebateMessage objects

        Returns:
            tuple: (content, tokens_used) - Generated response and token usage
        """
        # Build prompts
        system_prompt = build_system_prompt(persona, debate.depth_level)

        if round_number == 1 and not previous_messages:
            # First speaker gets opening statement prompt
            user_prompt = build_opening_statement_prompt(debate, persona, debate.depth_level)
        else:
            # Everyone else gets regular round prompt
            user_prompt = build_round_prompt(
                debate,
                round_number,
                previous_messages,
                debate.depth_level
            )

        # Call Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,  # Allow up to ~500 words per response
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        # Extract text content
        content = response.content[0].text

        # Beta: Track token usage from Claude API response
        # usage.input_tokens = prompt tokens, usage.output_tokens = completion tokens
        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        return content, tokens_used

    def _build_transcript_header(self, debate, participants):
        """
        Build the header section of the debate transcript.

        Args:
            debate: Debate instance
            participants: List of Persona instances

        Returns:
            str: Markdown transcript header
        """
        participant_list = "\n".join([
            f"- **{p.name}** ({p.era})" for p in participants
        ])

        header = f"""# {debate.title}

## Topic
{debate.topic}

## Participants ({len(participants)})
{participant_list}

## Configuration
- **Depth Level**: {debate.depth_level.title()}
- **Max Rounds**: {debate.max_rounds}
- **Generated**: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
        return header

    def _generate_summary(self, debate, participants):
        """
        Generate an AI summary of the debate showing each persona's final position.

        Args:
            debate: Debate instance
            participants: List of Persona instances

        Returns:
            str: Formatted summary with each persona's key position (3-5 lines each)
        """
        # Query optimization: Use select_related to fetch persona data in single query
        # This prevents N queries when accessing msg.persona.name in the loop below
        all_messages = DebateMessage.objects.filter(
            debate=debate
        ).select_related('persona').order_by('round_number', 'persona__birth_year')

        # Build conversation history for Claude
        conversation_context = ""
        for msg in all_messages:
            conversation_context += f"\n**{msg.persona.name} (Round {msg.round_number}):**\n{msg.content}\n"

        # Create prompt for summary generation
        prompt = f"""You are analyzing a philosophical debate to create a concise summary of each participant's final position.

**Debate Topic:** {debate.topic}

**Participants:** {', '.join([p.name for p in participants])}

**Full Debate Transcript:**
{conversation_context}

**Instructions:**
Please provide a summary of each participant's final position. For each participant, write 3-5 lines capturing:
1. Their core argument or stance on the topic
2. Key philosophical principles they invoked
3. How their position evolved (if it did) or remained consistent

Format the output as:
**[Persona Name]:**
[3-5 lines of summary]

Be precise, philosophical, and capture the essence of each thinker's contribution."""

        # Call Claude API for summary
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system="You are an expert philosophical analyst who summarizes complex debates with precision and clarity.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract summary text
        summary = response.content[0].text

        return summary


def generate_debate(debate_id):
    """
    Convenience function to generate a debate by ID.

    Args:
        debate_id: ID of the debate to generate

    Returns:
        Debate: Updated debate instance
    """
    debate = Debate.objects.get(id=debate_id)
    generator = DebateGenerator()
    return generator.generate(debate)
