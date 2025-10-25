"""
Celery tasks for asynchronous debate generation.
"""
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.utils import timezone
from django.conf import settings
from .models import Debate
from .generator import DebateGenerator
import redis
import json
import logging

logger = logging.getLogger(__name__)


def publish_debate_event(debate_slug, event_type, data):
    """
    Publish an event to Redis pub/sub for SSE streaming.

    Args:
        debate_slug: Slug of the debate
        event_type: Type of event (status, message, error)
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
        # Log error but don't fail the task
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to publish event for debate {debate_slug}: {str(e)}")


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,       # Wait 60s between retries
    task_time_limit=600,           # Hard limit: 10 minutes
    task_soft_time_limit=540       # Soft limit: 9 minutes (cleanup time)
)
def generate_debate_task(self, debate_id):
    """
    Celery task to generate a debate asynchronously.
    Publishes SSE events to Redis for real-time updates.

    Implements production-ready timeout and retry logic:
    - Soft timeout at 9 minutes (allows cleanup)
    - Hard timeout at 10 minutes (forceful termination)
    - 3 retries with exponential backoff

    Args:
        debate_id: ID of the debate to generate

    Returns:
        dict: Result summary with debate ID and status

    Raises:
        Exception: If generation fails after retries
    """
    try:
        # Fetch the debate instance
        debate = Debate.objects.get(id=debate_id)

        # Ensure debate is in the correct state
        if debate.status == 'completed':
            return {
                'debate_id': debate_id,
                'status': 'already_completed',
                'message': 'Debate was already completed'
            }

        # Update status to generating if not already set
        if debate.status != 'generating':
            debate.status = 'generating'
            debate.save()

            # Publish status change
            publish_debate_event(debate.slug, 'status', {
                'status': 'generating',
                'rounds_completed': 0,
                'max_rounds': debate.max_rounds
            })

        # Generate the debate (generator will update progress)
        generator = DebateGenerator()
        generator.generate(debate)

        # Publish completion event
        publish_debate_event(debate.slug, 'status', {
            'status': 'completed',
            'rounds_completed': debate.rounds_completed,
            'max_rounds': debate.max_rounds
        })

        return {
            'debate_id': debate_id,
            'status': 'completed',
            'completed_at': timezone.now().isoformat(),
            'rounds_completed': debate.rounds_completed
        }

    except SoftTimeLimitExceeded:
        # Soft timeout reached - save partial progress and retry
        logger.warning(f"Debate {debate_id} exceeded soft time limit (9 minutes)")
        try:
            debate = Debate.objects.get(id=debate_id)
            debate.status = 'failed'
            debate.error_message = 'Task exceeded time limit (9 minutes). Will retry.'
            debate.save()

            # Publish timeout event
            publish_debate_event(debate.slug, 'status', {
                'status': 'failed',
                'error_message': 'Task timeout - retrying...'
            })
        except Exception as e:
            logger.error(f"Failed to update debate {debate_id} after timeout: {e}")

        # Retry with exponential backoff
        retry_countdown = min(60 * (2 ** self.request.retries), 300)  # Max 5 minutes
        logger.info(f"Retrying debate {debate_id} in {retry_countdown} seconds (attempt {self.request.retries + 1}/3)")
        raise self.retry(countdown=retry_countdown)

    except Debate.DoesNotExist:
        logger.error(f"Debate {debate_id} not found")
        return {
            'debate_id': debate_id,
            'status': 'error',
            'message': f'Debate with ID {debate_id} not found'
        }

    except Exception as exc:
        # Update debate status to failed
        logger.error(f"Debate {debate_id} generation failed: {exc}")
        try:
            debate = Debate.objects.get(id=debate_id)
            debate.status = 'failed'
            debate.error_message = str(exc)
            debate.save()

            # Publish failure event
            publish_debate_event(debate.slug, 'status', {
                'status': 'failed',
                'error_message': str(exc)
            })
        except Exception as e:
            logger.error(f"Failed to update debate {debate_id} after error: {e}")

        # Retry with exponential backoff (60s, 120s, 240s, max 300s)
        retry_countdown = min(60 * (2 ** self.request.retries), 300)
        logger.info(f"Retrying debate {debate_id} in {retry_countdown} seconds (attempt {self.request.retries + 1}/3)")
        raise self.retry(exc=exc, countdown=retry_countdown)
