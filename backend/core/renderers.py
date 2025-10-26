"""
Custom DRF renderers for specialized response formats.
"""
from rest_framework.renderers import BaseRenderer


class SSERenderer(BaseRenderer):
    """
    Renderer for Server-Sent Events (SSE) streaming.

    This renderer allows DRF to properly handle StreamingHttpResponse
    without trying to serialize the data. The data is already formatted
    by the generator function in the view.
    """
    media_type = 'text/event-stream'
    format = 'txt'
    charset = None
    render_style = 'text'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Return data as-is since StreamingHttpResponse handles formatting.

        Args:
            data: The streaming response data (already formatted)
            accepted_media_type: The accepted media type from content negotiation
            renderer_context: Additional context from the view

        Returns:
            The data unchanged (StreamingHttpResponse handles actual rendering)
        """
        # StreamingHttpResponse data is a generator that yields pre-formatted
        # SSE messages. We don't need to transform it.
        return data
