from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, StreamingHttpResponse
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from core.renderers import SSERenderer
from .models import Debate
from .serializers import (
    DebateListSerializer,
    DebateDetailSerializer,
    DebateCreateSerializer
)
from .throttles import DebateGenerationThrottle
from .tasks import generate_debate_task
from .pdf_export import generate_debate_pdf
import redis
import json
import time
from django.conf import settings


@extend_schema_view(
    list=extend_schema(
        summary="List debates",
        description="Retrieve all debates created by the authenticated user.",
        tags=["Debates"],
    ),
    retrieve=extend_schema(
        summary="Get debate details",
        description="Retrieve a specific debate with all messages and citations.",
        tags=["Debates"],
    ),
    create=extend_schema(
        summary="Create new debate",
        description=(
            "Create a new debate with selected personas and topic. "
            "Credits are deducted immediately upon creation. "
            "Use the /generate/ endpoint to start the AI debate generation."
        ),
        tags=["Debates"],
        examples=[
            OpenApiExample(
                "Basic Debate",
                value={
                    "topic": "What is the nature of reality?",
                    "participant_ids": [1, 5, 12],
                    "max_rounds": 3,
                    "depth_level": "intermediate",
                    "context": "Focus on metaphysical perspectives"
                },
                request_only=True,
            )
        ],
    ),
    destroy=extend_schema(
        summary="Delete debate",
        description="Delete a debate. Only the owner can delete their debates.",
        tags=["Debates"],
    ),
)
class DebateViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing debates.

    Debates are AI-generated conversations between historical personas discussing
    philosophical, scientific, or theological topics.

    **Workflow:**
    1. Create debate (POST /api/debates/) - deducts credits
    2. Generate debate (POST /api/debates/{slug}/generate/) - starts AI generation
    3. Stream updates (GET /api/debates/{slug}/stream/) - real-time progress
    4. Export PDF (GET /api/debates/{slug}/export/) - download completed debate
    """
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    queryset = Debate.objects.all()

    def get_throttles(self):
        """
        Apply custom throttling for debate generation endpoint.
        """
        if self.action == 'generate':
            return [DebateGenerationThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        """
        Return only debates owned by the authenticated user.

        Query optimization: Prefetch participants to prevent N+1 queries
        when accessing debate.participants in list views and serializers.
        """
        return Debate.objects.filter(
            user=self.request.user
        ).prefetch_related('participants')

    def get_serializer_class(self):
        if self.action == 'create':
            return DebateCreateSerializer
        elif self.action == 'retrieve':
            return DebateDetailSerializer
        return DebateListSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single debate with optimized queries.

        Query optimization: For detail views, prefetch messages with their
        related persona data to prevent N+1 queries when serializing messages.
        """
        # Override queryset for this specific request to add prefetching
        self.queryset = self.get_queryset().prefetch_related(
            'messages__persona',
            'messages__text_citations__primary_text'
        )
        # Use get_object() to properly handle DoesNotExist and return 404
        debate = self.get_object()
        serializer = self.get_serializer(debate)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Create debate and trigger generation."""
        debate = serializer.save()
        # TODO: Trigger async debate generation
        # For now, just return the created debate
        return debate

    @extend_schema(
        summary="Generate debate",
        description=(
            "Start AI-powered debate generation. This triggers a background Celery task "
            "that uses Claude AI to generate authentic dialogue between the selected personas. "
            "Use the /stream/ endpoint to monitor progress in real-time."
        ),
        tags=["Debates"],
        responses={
            200: DebateDetailSerializer,
            400: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=True, methods=['post'])
    def generate(self, request, **kwargs):
        """
        Start debate generation.
        POST /api/debates/{slug}/generate/
        """
        debate = self.get_object()

        # Check if already completed
        if debate.status == 'completed':
            return Response(
                {'error': 'Debate already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already generating
        if debate.status == 'generating':
            return Response(
                {'error': 'Debate generation already in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update status to generating
        debate.status = 'generating'
        debate.save()

        # Dispatch Celery task for background processing
        task = generate_debate_task.delay(debate.id)

        # Return immediately with generating status and task ID
        serializer = DebateDetailSerializer(debate)
        response_data = serializer.data
        response_data['task_id'] = task.id

        return Response(response_data)

    @extend_schema(
        summary="Export debate as PDF",
        description=(
            "Download a PDF version of a completed debate with full transcript "
            "and citations. Useful for academic purposes and archiving."
        ),
        tags=["Debates"],
        responses={
            200: OpenApiTypes.BINARY,
            400: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=True, methods=['get'])
    def export(self, request, **kwargs):
        """
        Export debate as PDF.
        GET /api/debates/{slug}/export/
        """
        debate = self.get_object()

        # Check if debate is completed
        if debate.status != 'completed':
            return Response(
                {'error': 'Debate must be completed before exporting'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Generate PDF
            pdf_bytes = generate_debate_pdf(debate)

            # Create response
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            filename = f"{debate.slug}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        except Exception as e:
            return Response(
                {'error': f'Failed to generate PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Stream debate updates",
        description=(
            "Stream real-time debate generation progress via Server-Sent Events (SSE). "
            "Subscribe to this endpoint after calling /generate/ to receive live updates "
            "on debate status, rounds completed, and messages as they are generated."
        ),
        tags=["Debates"],
        responses={
            200: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=True, methods=['get'], renderer_classes=[SSERenderer])
    def stream(self, request, **kwargs):
        """
        Stream debate status updates via Server-Sent Events (SSE).
        GET /api/debates/{slug}/stream/
        """
        from django.db import connection

        debate = self.get_object()

        # Extract data we need before closing DB connection
        debate_slug = debate.slug
        initial_status = debate.status
        initial_rounds = debate.rounds_completed
        max_rounds = debate.max_rounds

        # Close database connection to prevent connection pool exhaustion
        # SSE streams can last minutes, we don't need DB connection open
        connection.close()

        def event_stream():
            """Generator function that yields SSE formatted events."""
            # Connect to Redis for pub/sub
            redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
            pubsub = redis_client.pubsub()
            channel_name = f"debate:{debate_slug}"

            try:
                # Subscribe to debate-specific channel
                pubsub.subscribe(channel_name)

                # Send initial status
                initial_data = {
                    'type': 'status',
                    'status': initial_status,
                    'rounds_completed': initial_rounds,
                    'max_rounds': max_rounds
                }
                yield f"data: {json.dumps(initial_data)}\n\n"

                # Listen for updates with timeout
                timeout = 60  # 60 seconds timeout for each message
                for message in pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            yield f"data: {json.dumps(data)}\n\n"

                            # Close stream if debate is complete or failed
                            if data.get('status') in ['completed', 'failed']:
                                break
                        except json.JSONDecodeError:
                            continue

            except GeneratorExit:
                # Client disconnected
                pubsub.unsubscribe(channel_name)
                pubsub.close()
                redis_client.close()
            except Exception as e:
                # Log error and close connections
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"SSE stream error for debate {debate_slug}: {str(e)}")
                pubsub.unsubscribe(channel_name)
                pubsub.close()
                redis_client.close()
                raise
            finally:
                # Cleanup
                try:
                    pubsub.unsubscribe(channel_name)
                    pubsub.close()
                    redis_client.close()
                except:
                    pass

        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
        return response
