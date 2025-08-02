"""
Demo view to showcase structured logging in action.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from core.logging import get_structured_logger


@method_decorator(csrf_exempt, name='dispatch')
class LoggingDemoView(View):
    """Demo view to showcase structured logging functionality."""
    
    def get(self, request):
        """Handle GET request with structured logging."""
        logger = get_structured_logger(__name__)
        
        logger.info("Demo GET request received")
        
        # Log some example data
        logger.info(
            "Processing demo request",
            method="GET",
            query_params=dict(request.GET),
            user_authenticated=request.user.is_authenticated
        )
        
        response_data = {
            "message": "Structured logging demo",
            "request_id": getattr(request, 'request_id', None),
            "user_authenticated": request.user.is_authenticated,
            "user_id": str(request.user.id) if request.user.is_authenticated else None,
        }
        
        logger.info("Demo response prepared", response_data=response_data)
        
        return JsonResponse(response_data)
    
    def post(self, request):
        """Handle POST request with structured logging."""
        logger = get_structured_logger(__name__)
        
        logger.info("Demo POST request received")
        
        try:
            # Parse JSON data if provided
            data = json.loads(request.body) if request.body else {}
            
            logger.info(
                "Processing demo POST request",
                method="POST",
                data_keys=list(data.keys()),
                content_type=request.content_type,
                user_authenticated=request.user.is_authenticated
            )
            
            # Simulate some processing
            if data.get('simulate_error'):
                raise ValueError("Simulated error for testing")
            
            response_data = {
                "message": "POST request processed",
                "request_id": getattr(request, 'request_id', None),
                "received_data": data,
                "user_authenticated": request.user.is_authenticated,
            }
            
            logger.info("Demo POST response prepared", response_data=response_data)
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError as e:
            logger.error(
                "Invalid JSON in request body",
                error=str(e),
                body_preview=request.body[:100].decode('utf-8', errors='ignore')
            )
            return JsonResponse({"error": "Invalid JSON"}, status=400)
            
        except ValueError as e:
            logger.error(
                "Processing error occurred",
                error_type=e.__class__.__name__,
                error_message=str(e)
            )
            return JsonResponse({"error": str(e)}, status=400)
        
        except Exception as e:
            logger.error(
                "Unexpected error occurred",
                error_type=e.__class__.__name__,
                error_message=str(e),
                exc_info=True
            )
            return JsonResponse({"error": "Internal server error"}, status=500)