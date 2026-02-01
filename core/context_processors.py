"""
Context processors for adding global template variables.
"""

from core.visitor_detection import is_anthropic_visitor


def anthropic_detection(request):
    """
    Add Anthropic visitor detection to template context.

    Usage in templates:
        {% if anthropic_visitor.is_anthropic %}
            <div class="anthropic-greeting">Hello, Anthropic! 👋</div>
        {% endif %}
    """
    return {
        'anthropic_visitor': is_anthropic_visitor(request)
    }
