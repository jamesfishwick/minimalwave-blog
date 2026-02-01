"""
Test views for debugging.
"""

from django.http import HttpResponse


def test_anthropic_detection(request):
    """Test view to verify Anthropic detection context processor."""
    from core.context_processors import anthropic_detection

    context = anthropic_detection(request)

    html = f"""
    <html>
    <head><title>Anthropic Detection Test</title></head>
    <body>
        <h1>Anthropic Detection Test</h1>
        <pre>
Context: {context}
        </pre>
        <p>is_anthropic: {context['anthropic_visitor']['is_anthropic']}</p>
        <p>detection_method: {context['anthropic_visitor']['detection_method']}</p>
        <p>confidence: {context['anthropic_visitor']['confidence']}</p>
    </body>
    </html>
    """

    return HttpResponse(html)
