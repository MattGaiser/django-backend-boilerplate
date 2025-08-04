"""
Enhanced caching utilities for the Django Backend Boilerplate.

Provides decorators, utilities, and patterns for efficient caching
across the application with organization-scoped cache keys.
"""

import functools
import hashlib
import json
import time
from typing import Any, Callable, Optional, Union

import structlog
from django.core.cache import cache
from django.conf import settings
from django.http import HttpRequest

logger = structlog.get_logger(__name__)


def make_cache_key(*args, prefix: str = "djboiler", max_length: int = 250) -> str:
    """
    Create a standardized cache key from arguments.
    
    Args:
        *args: Arguments to include in the cache key
        prefix: Cache key prefix (default: "djboiler")
        max_length: Maximum length of cache key (default: 250)
    
    Returns:
        str: Formatted cache key
    """
    # Convert all args to strings and join
    key_parts = [str(prefix)] + [str(arg) for arg in args if arg is not None]
    key = ":".join(key_parts)
    
    # If key is too long, hash the end part
    if len(key) > max_length:
        # Keep the prefix and hash the rest
        prefix_part = f"{prefix}:"
        remaining_length = max_length - len(prefix_part) - 1  # -1 for the colon
        
        # Hash the full key to get a consistent shorter version
        key_hash = hashlib.md5(key.encode()).hexdigest()[:remaining_length]
        key = f"{prefix_part}{key_hash}"
    
    return key


def cache_key_for_user(user_id: Union[str, int], *args, prefix: str = "user") -> str:
    """
    Create a cache key scoped to a specific user.
    
    Args:
        user_id: User ID to scope the cache key to
        *args: Additional arguments for the cache key
        prefix: Cache key prefix (default: "user")
    
    Returns:
        str: User-scoped cache key
    """
    return make_cache_key(prefix, user_id, *args)


def cache_key_for_org(org_id: Union[str, int], *args, prefix: str = "org") -> str:
    """
    Create a cache key scoped to a specific organization.
    
    Args:
        org_id: Organization ID to scope the cache key to
        *args: Additional arguments for the cache key
        prefix: Cache key prefix (default: "org")
    
    Returns:
        str: Organization-scoped cache key
    """
    return make_cache_key(prefix, org_id, *args)


def cached_property_with_timeout(timeout: int = 300):
    """
    Decorator for caching property values with timeout.
    
    Args:
        timeout: Cache timeout in seconds (default: 300)
    
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self):
            # Create cache key based on object and method
            cache_key = make_cache_key(
                "property",
                self.__class__.__name__,
                str(getattr(self, 'pk', 'no_pk')),
                func.__name__
            )
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug("Cache hit for property", 
                           cache_key=cache_key, 
                           method=func.__name__)
                return cached_value
            
            # Calculate and cache the value
            value = func(self)
            cache.set(cache_key, value, timeout=timeout)
            logger.debug("Cached property value", 
                        cache_key=cache_key, 
                        method=func.__name__,
                        timeout=timeout)
            
            return value
        
        return wrapper
    return decorator


def cache_result(timeout: int = 300, key_prefix: str = "result"):
    """
    Decorator for caching function results.
    
    Args:
        timeout: Cache timeout in seconds (default: 300)
        key_prefix: Cache key prefix (default: "result")
    
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [
                key_prefix,
                func.__module__,
                func.__name__,
            ]
            
            # Add positional arguments
            for arg in args:
                if hasattr(arg, 'pk'):
                    # For model instances, use their PK
                    key_parts.append(f"{arg.__class__.__name__}:{arg.pk}")
                else:
                    key_parts.append(str(arg))
            
            # Add keyword arguments (sorted for consistency)
            for k, v in sorted(kwargs.items()):
                if hasattr(v, 'pk'):
                    key_parts.append(f"{k}:{v.__class__.__name__}:{v.pk}")
                else:
                    key_parts.append(f"{k}:{v}")
            
            cache_key = make_cache_key(*key_parts)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug("Cache hit for function result",
                           cache_key=cache_key,
                           function=func.__name__)
                return cached_result
            
            # Calculate and cache the result
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            cache.set(cache_key, result, timeout=timeout)
            logger.debug("Cached function result",
                        cache_key=cache_key,
                        function=func.__name__,
                        execution_time_ms=round(execution_time, 2),
                        timeout=timeout)
            
            return result
        
        return wrapper
    return decorator


def cache_page_for_user(timeout: int = 300):
    """
    Decorator for caching API responses per user.
    
    Args:
        timeout: Cache timeout in seconds (default: 300)
    
    Returns:
        Decorator function
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            # Only cache for authenticated users
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            # Create cache key from view, user, and request parameters
            cache_key = make_cache_key(
                "page",
                view_func.__name__,
                request.user.pk,
                request.method,
                request.path,
                # Include query parameters
                hashlib.md5(request.GET.urlencode().encode()).hexdigest()[:8] if request.GET else "no_params"
            )
            
            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                logger.debug("Cache hit for page response",
                           cache_key=cache_key,
                           view=view_func.__name__,
                           user_id=request.user.pk)
                return cached_response
            
            # Generate and cache the response
            start_time = time.time()
            response = view_func(request, *args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            # Only cache successful responses
            if hasattr(response, 'status_code') and 200 <= response.status_code < 300:
                cache.set(cache_key, response, timeout=timeout)
                logger.debug("Cached page response",
                            cache_key=cache_key,
                            view=view_func.__name__,
                            user_id=request.user.pk,
                            execution_time_ms=round(execution_time, 2),
                            timeout=timeout)
            
            return response
        
        return wrapper
    return decorator


class CacheManager:
    """
    Centralized cache management utility.
    
    Provides methods for managing cache keys, invalidation patterns,
    and cache statistics.
    """
    
    def __init__(self, default_timeout: int = 300):
        """
        Initialize cache manager.
        
        Args:
            default_timeout: Default cache timeout in seconds
        """
        self.default_timeout = default_timeout
        self.prefix = getattr(settings, "CACHE_KEY_PREFIX", "djboiler")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with logging."""
        value = cache.get(key, default)
        
        if value is not default:
            logger.debug("Cache hit", cache_key=key)
        else:
            logger.debug("Cache miss", cache_key=key)
        
        return value
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in cache with logging."""
        timeout = timeout or self.default_timeout
        
        try:
            cache.set(key, value, timeout=timeout)
            logger.debug("Cache set", cache_key=key, timeout=timeout)
            return True
        except Exception as e:
            logger.error("Cache set failed", cache_key=key, error=str(e))
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache with logging."""
        try:
            result = cache.delete(key)
            logger.debug("Cache delete", cache_key=key, found=result)
            return result
        except Exception as e:
            logger.error("Cache delete failed", cache_key=key, error=str(e))
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete cache keys matching a pattern.
        
        Note: This requires django-redis or similar backend that supports pattern deletion.
        
        Args:
            pattern: Pattern to match (e.g., "user:123:*")
        
        Returns:
            int: Number of keys deleted
        """
        try:
            if hasattr(cache, 'delete_pattern'):
                # django-redis supports this
                deleted_count = cache.delete_pattern(pattern)
                logger.info("Cache pattern delete", pattern=pattern, deleted_count=deleted_count)
                return deleted_count
            else:
                logger.warning("Cache backend does not support pattern deletion", pattern=pattern)
                return 0
        except Exception as e:
            logger.error("Cache pattern delete failed", pattern=pattern, error=str(e))
            return 0
    
    def invalidate_user_cache(self, user_id: Union[str, int]) -> int:
        """
        Invalidate all cache entries for a specific user.
        
        Args:
            user_id: User ID to invalidate cache for
        
        Returns:
            int: Number of cache entries invalidated
        """
        pattern = f"{self.prefix}:user:{user_id}:*"
        return self.delete_pattern(pattern)
    
    def invalidate_org_cache(self, org_id: Union[str, int]) -> int:
        """
        Invalidate all cache entries for a specific organization.
        
        Args:
            org_id: Organization ID to invalidate cache for
        
        Returns:
            int: Number of cache entries invalidated
        """
        pattern = f"{self.prefix}:org:{org_id}:*"
        return self.delete_pattern(pattern)
    
    def get_stats(self) -> dict:
        """
        Get cache statistics if available.
        
        Returns:
            dict: Cache statistics
        """
        stats = {
            "backend": getattr(settings, "CACHES", {}).get("default", {}).get("BACKEND", "unknown"),
            "prefix": self.prefix,
            "default_timeout": self.default_timeout,
        }
        
        try:
            # Test cache operation and measure performance
            start_time = time.time()
            test_key = make_cache_key("stats_test", int(time.time()))
            cache.set(test_key, "test", timeout=10)
            cache.get(test_key)
            cache.delete(test_key)
            operation_time = (time.time() - start_time) * 1000
            
            stats["operation_time_ms"] = round(operation_time, 2)
            stats["status"] = "healthy"
            
        except Exception as e:
            stats["status"] = "error"
            stats["error"] = str(e)
        
        return stats
    
    def warm_up(self, data: dict) -> int:
        """
        Warm up cache with initial data.
        
        Args:
            data: Dictionary of cache_key -> value mappings
        
        Returns:
            int: Number of cache entries set
        """
        count = 0
        for key, value in data.items():
            if self.set(key, value):
                count += 1
        
        logger.info("Cache warm-up completed", entries_set=count, total_entries=len(data))
        return count


# Global cache manager instance
cache_manager = CacheManager()


# Convenience functions
def invalidate_user_cache(user_id: Union[str, int]) -> int:
    """Invalidate all cache entries for a user."""
    return cache_manager.invalidate_user_cache(user_id)


def invalidate_org_cache(org_id: Union[str, int]) -> int:
    """Invalidate all cache entries for an organization."""
    return cache_manager.invalidate_org_cache(org_id)


def get_cache_stats() -> dict:
    """Get cache statistics."""
    return cache_manager.get_stats()