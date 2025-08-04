"""
Webhook system for external integrations.

Provides a flexible webhook framework for sending notifications
to external services when certain events occur in the application.
"""

import hashlib
import hmac
import json
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
import structlog
from django.conf import settings
from django.utils import timezone

from core.cache import cache_manager

logger = structlog.get_logger(__name__)


class WebhookDeliveryError(Exception):
    """Exception raised when webhook delivery fails."""
    pass


class WebhookSignatureError(Exception):
    """Exception raised when webhook signature is invalid."""
    pass


class WebhookEvent:
    """
    Represents a webhook event to be sent to external services.
    """
    
    def __init__(
        self,
        event_type: str,
        data: Dict[str, Any],
        user_id: Optional[Union[str, int]] = None,
        organization_id: Optional[Union[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize webhook event.
        
        Args:
            event_type: Type of event (e.g., "user.created", "organization.updated")
            data: Event data payload
            user_id: User ID associated with the event
            organization_id: Organization ID associated with the event
            metadata: Additional metadata for the event
        """
        self.event_type = event_type
        self.data = data
        self.user_id = user_id
        self.organization_id = organization_id
        self.metadata = metadata or {}
        self.timestamp = timezone.now()
        self.event_id = self._generate_event_id()
    
    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        import uuid
        return str(uuid.uuid4())
    
    def to_payload(self) -> Dict[str, Any]:
        """
        Convert event to webhook payload format.
        
        Returns:
            dict: Webhook payload
        """
        payload = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }
        
        if self.user_id:
            payload["user_id"] = str(self.user_id)
        
        if self.organization_id:
            payload["organization_id"] = str(self.organization_id)
        
        if self.metadata:
            payload["metadata"] = self.metadata
        
        return payload


class WebhookClient:
    """
    HTTP client for delivering webhooks to external endpoints.
    """
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 1,
        signature_header: str = "X-Webhook-Signature",
    ):
        """
        Initialize webhook client.
        
        Args:
            timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            signature_header: HTTP header name for webhook signature
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.signature_header = signature_header
    
    def deliver(
        self,
        url: str,
        event: WebhookEvent,
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Deliver webhook event to external endpoint.
        
        Args:
            url: Webhook endpoint URL
            event: WebhookEvent to deliver
            secret: Secret key for signature generation
            headers: Additional HTTP headers
        
        Returns:
            dict: Delivery result information
        
        Raises:
            WebhookDeliveryError: If delivery fails after all retries
        """
        payload = event.to_payload()
        json_payload = json.dumps(payload, separators=(",", ":"))
        
        # Prepare headers
        request_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Django-Backend-Boilerplate-Webhook/1.0",
            "X-Event-Type": event.event_type,
            "X-Event-ID": event.event_id,
            "X-Timestamp": event.timestamp.isoformat(),
        }
        
        if headers:
            request_headers.update(headers)
        
        # Generate signature if secret is provided
        if secret:
            signature = self._generate_signature(json_payload, secret)
            request_headers[self.signature_header] = signature
        
        # Attempt delivery with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                response = requests.post(
                    url,
                    data=json_payload,
                    headers=request_headers,
                    timeout=self.timeout,
                )
                
                delivery_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Log delivery attempt
                logger.info(
                    "Webhook delivered",
                    event_type=event.event_type,
                    event_id=event.event_id,
                    url=url,
                    status_code=response.status_code,
                    delivery_time_ms=round(delivery_time, 2),
                    attempt=attempt + 1,
                )
                
                # Check if delivery was successful
                if 200 <= response.status_code < 300:
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "delivery_time_ms": round(delivery_time, 2),
                        "attempt": attempt + 1,
                        "response_body": response.text[:1000],  # Truncate response
                    }
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:500]}"
                    
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                logger.warning(
                    "Webhook delivery failed",
                    event_type=event.event_type,
                    event_id=event.event_id,
                    url=url,
                    error=str(e),
                    attempt=attempt + 1,
                )
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        # All attempts failed
        error_msg = f"Webhook delivery failed after {self.max_retries} attempts: {last_error}"
        logger.error(
            "Webhook delivery completely failed",
            event_type=event.event_type,
            event_id=event.event_id,
            url=url,
            error=last_error,
        )
        
        raise WebhookDeliveryError(error_msg)
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """
        Generate HMAC signature for webhook payload.
        
        Args:
            payload: JSON payload string
            secret: Secret key
        
        Returns:
            str: HMAC signature
        """
        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"


class WebhookManager:
    """
    Manager for webhook configuration and delivery.
    """
    
    def __init__(self):
        """Initialize webhook manager."""
        self.client = WebhookClient(
            timeout=getattr(settings, "WEBHOOKS", {}).get("TIMEOUT", 30),
            max_retries=getattr(settings, "WEBHOOKS", {}).get("RETRY_ATTEMPTS", 3),
            signature_header=getattr(settings, "WEBHOOKS", {}).get("SIGNATURE_HEADER", "X-Webhook-Signature"),
        )
        self.enabled = getattr(settings, "WEBHOOKS", {}).get("ENABLED", False)
        self.endpoints = getattr(settings, "NOTIFICATIONS", {}).get("WEBHOOK_ENDPOINTS", [])
    
    def send_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        user_id: Optional[Union[str, int]] = None,
        organization_id: Optional[Union[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Send webhook event to all configured endpoints.
        
        Args:
            event_type: Type of event
            data: Event data
            user_id: User ID associated with event
            organization_id: Organization ID associated with event
            metadata: Additional metadata
        
        Returns:
            list: Delivery results for each endpoint
        """
        if not self.enabled:
            logger.debug("Webhooks disabled, skipping event", event_type=event_type)
            return []
        
        if not self.endpoints:
            logger.debug("No webhook endpoints configured", event_type=event_type)
            return []
        
        # Check if event type is allowed
        allowed_events = getattr(settings, "WEBHOOKS", {}).get("EVENTS", [])
        if allowed_events and event_type not in allowed_events:
            logger.debug("Event type not in allowed list", event_type=event_type)
            return []
        
        # Create webhook event
        event = WebhookEvent(
            event_type=event_type,
            data=data,
            user_id=user_id,
            organization_id=organization_id,
            metadata=metadata,
        )
        
        # Send to all endpoints
        results = []
        for endpoint_url in self.endpoints:
            try:
                result = self.client.deliver(
                    url=endpoint_url,
                    event=event,
                    secret=getattr(settings, "SECRET_KEY", ""),  # Use Django secret as webhook secret
                )
                results.append({
                    "endpoint": endpoint_url,
                    "success": True,
                    **result,
                })
                
            except WebhookDeliveryError as e:
                results.append({
                    "endpoint": endpoint_url,
                    "success": False,
                    "error": str(e),
                })
        
        return results
    
    def send_user_event(self, event_type: str, user, additional_data: Optional[Dict] = None):
        """
        Send user-related webhook event.
        
        Args:
            event_type: Event type (e.g., "user.created", "user.updated")
            user: User instance
            additional_data: Additional data to include
        """
        data = {
            "user_id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
        }
        
        if additional_data:
            data.update(additional_data)
        
        return self.send_event(
            event_type=event_type,
            data=data,
            user_id=user.id,
        )
    
    def send_organization_event(self, event_type: str, organization, additional_data: Optional[Dict] = None):
        """
        Send organization-related webhook event.
        
        Args:
            event_type: Event type (e.g., "organization.created", "organization.updated")
            organization: Organization instance
            additional_data: Additional data to include
        """
        data = {
            "organization_id": str(organization.id),
            "name": organization.name,
            "slug": getattr(organization, "slug", ""),
            "plan": getattr(organization, "plan", ""),
            "is_active": getattr(organization, "is_active", True),
            "created_at": organization.created_at.isoformat() if hasattr(organization, "created_at") else None,
        }
        
        if additional_data:
            data.update(additional_data)
        
        return self.send_event(
            event_type=event_type,
            data=data,
            organization_id=organization.id,
        )


# Global webhook manager instance
webhook_manager = WebhookManager()


# Convenience functions
def send_webhook_event(
    event_type: str,
    data: Dict[str, Any],
    user_id: Optional[Union[str, int]] = None,
    organization_id: Optional[Union[str, int]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Send webhook event using global manager."""
    return webhook_manager.send_event(
        event_type=event_type,
        data=data,
        user_id=user_id,
        organization_id=organization_id,
        metadata=metadata,
    )


def send_user_webhook(event_type: str, user, additional_data: Optional[Dict] = None):
    """Send user webhook event using global manager."""
    return webhook_manager.send_user_event(event_type, user, additional_data)


def send_organization_webhook(event_type: str, organization, additional_data: Optional[Dict] = None):
    """Send organization webhook event using global manager."""
    return webhook_manager.send_organization_event(event_type, organization, additional_data)


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Verify webhook signature for incoming webhooks.
    
    Args:
        payload: Raw payload string
        signature: Signature header value
        secret: Secret key
    
    Returns:
        bool: True if signature is valid
    
    Raises:
        WebhookSignatureError: If signature format is invalid
    """
    if not signature.startswith("sha256="):
        raise WebhookSignatureError("Invalid signature format")
    
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    provided_signature = signature[7:]  # Remove "sha256=" prefix
    
    return hmac.compare_digest(expected_signature, provided_signature)