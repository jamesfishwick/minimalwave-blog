"""
Visitor detection utilities for special greetings.

Detects visitors from specific companies (Anthropic) based on:
- IP address ranges
- HTTP Referer headers
- User-Agent strings
"""

import ipaddress
import logging

logger = logging.getLogger(__name__)


# Anthropic's known IP ranges (these are public/known ranges)
# Note: You may need to update these based on actual Anthropic infrastructure
ANTHROPIC_IP_RANGES = [
    # San Francisco office ranges (example - update with actual ranges if known)
    # ipaddress.ip_network('104.18.0.0/16'),  # Cloudflare range example
]

# Anthropic-related referrer patterns
ANTHROPIC_REFERRERS = [
    'anthropic.com',
    'claude.ai',
    'console.anthropic.com',
]

# User-Agent patterns (less reliable, but can supplement)
ANTHROPIC_USER_AGENTS = [
    'anthropic',
    'claude',
]


def is_anthropic_visitor(request):
    """
    Detect if a visitor is from Anthropic based on multiple signals.

    Returns a dict with detection info:
    {
        'is_anthropic': bool,
        'detection_method': str (ip/referrer/user_agent/manual),
        'confidence': str (high/medium/low)
    }
    """
    result = {
        'is_anthropic': False,
        'detection_method': None,
        'confidence': None,
    }

    # Check for manual override via query parameter (for testing)
    if request.GET.get('anthropic') == 'true':
        result['is_anthropic'] = True
        result['detection_method'] = 'manual'
        result['confidence'] = 'test'
        logger.info("Anthropic visitor detected via manual override")
        return result

    # Get client IP address
    client_ip = get_client_ip(request)

    # Check IP ranges
    if client_ip and check_ip_in_ranges(client_ip, ANTHROPIC_IP_RANGES):
        result['is_anthropic'] = True
        result['detection_method'] = 'ip'
        result['confidence'] = 'high'
        logger.info(f"Anthropic visitor detected via IP: {client_ip}")
        return result

    # Check HTTP Referer
    referer = request.META.get('HTTP_REFERER', '')
    if check_referrer(referer, ANTHROPIC_REFERRERS):
        result['is_anthropic'] = True
        result['detection_method'] = 'referrer'
        result['confidence'] = 'high'
        logger.info(f"Anthropic visitor detected via referrer: {referer}")
        return result

    # Check User-Agent (least reliable)
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    if check_user_agent(user_agent, ANTHROPIC_USER_AGENTS):
        result['is_anthropic'] = True
        result['detection_method'] = 'user_agent'
        result['confidence'] = 'low'
        logger.info(f"Anthropic visitor detected via user-agent: {user_agent}")
        return result

    return result


def get_client_ip(request):
    """Extract the client's IP address from the request."""
    # Check for X-Forwarded-For header (common with proxies/load balancers)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs, first one is the client
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    try:
        # Validate IP address
        ipaddress.ip_address(ip)
        return ip
    except ValueError:
        logger.warning(f"Invalid IP address: {ip}")
        return None


def check_ip_in_ranges(ip_str, ip_ranges):
    """Check if an IP address is within any of the given ranges."""
    if not ip_ranges:
        return False

    try:
        ip = ipaddress.ip_address(ip_str)
        for ip_range in ip_ranges:
            if ip in ip_range:
                return True
    except ValueError as e:
        logger.warning(f"Error checking IP {ip_str}: {e}")

    return False


def check_referrer(referer, patterns):
    """Check if referrer matches any of the given patterns."""
    if not referer:
        return False

    referer_lower = referer.lower()
    for pattern in patterns:
        if pattern.lower() in referer_lower:
            return True

    return False


def check_user_agent(user_agent, patterns):
    """Check if user-agent matches any of the given patterns."""
    if not user_agent:
        return False

    for pattern in patterns:
        if pattern.lower() in user_agent:
            return True

    return False
