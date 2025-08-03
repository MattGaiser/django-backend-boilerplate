"""
Demo API view to showcase structured logging functionality.

Provides endpoints for testing and demonstrating structured logging
capabilities with different HTTP methods.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from core.logging import get_structured_logger


class LoggingDemoView(APIView):
    """
    Demo API view to showcase structured logging functionality.
    
    Demonstrates how structured logging works across different HTTP methods
    and provides examples of error handling and data processing.
    """
    
    permission_classes = [AllowAny]  # Allow demo access without authentication
    
    def get(self, request):
        """
        Handle GET request with structured logging demonstration.
        
        Returns:
            Response: JSON response with demo data and logging examples
        """
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
            "method": "GET",
            "query_params": dict(request.GET)
        }
        
        logger.info("Demo response prepared", response_data=response_data)
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """
        Handle POST request with structured logging demonstration.
        
        Args:
            request: The HTTP request object
            
        Returns:
            Response: JSON response with processed data or error information
        """
        logger = get_structured_logger(__name__)
        
        logger.info("Demo POST request received")
        
        try:
            # Get data from request
            data = request.data
            
            logger.info(
                "Processing demo POST request",
                method="POST",
                data_keys=list(data.keys()) if data else [],
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
                "method": "POST"
            }
            
            logger.info("Demo POST response prepared", response_data=response_data)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(
                "Processing error occurred",
                error_type=e.__class__.__name__,
                error_message=str(e)
            )
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            logger.error(
                "Unexpected error occurred",
                error_type=e.__class__.__name__,
                error_message=str(e),
                exc_info=True
            )
            return Response(
                {"error": "Internal server error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )