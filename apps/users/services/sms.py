"""Minimal JSON webhook adapter for delivering phone verification messages."""
import json
from urllib.parse import urlparse
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def send_sms(phone_number, message):
    """POST {phone_number, message} to the configured SMS gateway webhook."""
    endpoint = getattr(settings, "SMS_PROVIDER_URL", "")
    if not endpoint:
        raise ImproperlyConfigured("SMS_PROVIDER_URL must be configured to enable phone OTP.")
    parsed_endpoint = urlparse(endpoint)
    if parsed_endpoint.scheme != "https" or not parsed_endpoint.netloc:
        raise ImproperlyConfigured("SMS_PROVIDER_URL must use HTTPS.")

    payload = json.dumps({"phone_number": phone_number, "message": message}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = getattr(settings, "SMS_PROVIDER_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(endpoint, data=payload, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=10) as response:
            if not 200 <= response.status < 300:
                raise RuntimeError("SMS gateway rejected the delivery request.")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("SMS gateway delivery failed.") from exc
