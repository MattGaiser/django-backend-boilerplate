"""
Content negotiation classes for API versioning support.

Supports both URL path versioning and Accept header versioning (e.g. application/json; version=1.0).
"""

from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.versioning import AcceptHeaderVersioning


class VersionedContentNegotiation(DefaultContentNegotiation):
    """
    Content negotiation class that supports version specification in Accept headers.
    
    Supports headers like:
    - Accept: application/json; version=1.0
    - Accept: application/json; version=v1
    """
    
    def determine_version(self, request, *args, **kwargs):
        """
        Determine the API version from the Accept header or URL.
        
        First tries URL path versioning, then falls back to Accept header versioning.
        """
        # Try URL path versioning first (default behavior)
        version = getattr(request, 'version', None)
        if version:
            return version
        
        # Fall back to Accept header versioning
        accept_header = request.META.get('HTTP_ACCEPT', '')
        if 'version=' in accept_header:
            try:
                # Extract version from Accept header like "application/json; version=1.0"
                version_part = [part.strip() for part in accept_header.split(';') if 'version=' in part][0]
                version = version_part.split('=')[1].strip()
                
                # Normalize version format (remove 'v' prefix if present)
                if version.startswith('v'):
                    version = version[1:]
                
                # Map version numbers to version names
                version_mapping = {
                    '1.0': 'v1',
                    '1': 'v1',
                }
                
                return version_mapping.get(version, f'v{version}')
            except (IndexError, KeyError):
                pass
        
        # Default to v1 if no version specified
        return 'v1'