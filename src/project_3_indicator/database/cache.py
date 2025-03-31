"""
Caching layer for database results to improve performance.
This module provides a simple in-memory cache with time-based expiration.
"""

import time
import logging
import threading
from functools import wraps

logger = logging.getLogger(__name__)

class ResultCache:
    """
    A simple in-memory cache with expiration for database results.
    Helps reduce database load for frequently requested items.
    """

    def __init__(self, max_size=1000, default_ttl=300):
        """
        Initialize the cache.

        Args:
            max_size (int): Maximum number of items to store in cache
            default_ttl (int): Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = {}  # Format: {key: (value, expiration_time)}
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "evictions": 0}

    def get(self, key):
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            The cached value or None if not found or expired
        """
        with self._lock:
            if key in self._cache:
                value, expires = self._cache[key]
                if expires > time.time():
                    self._stats["hits"] += 1
                    return value
                else:
                    # Expired
                    del self._cache[key]

            self._stats["misses"] += 1
            return None

    def set(self, key, value, ttl=None):
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to store
            ttl (int): Time-to-live in seconds, or None for default
        """
        if ttl is None:
            ttl = self.default_ttl

        with self._lock:
            # If we're at capacity, remove the oldest item
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_one()

            expires = time.time() + ttl
            self._cache[key] = (value, expires)
            self._stats["sets"] += 1

    def invalidate(self, key):
        """
        Remove an item from the cache.

        Args:
            key: Cache key to invalidate
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def invalidate_by_prefix(self, prefix):
        """
        Remove all items with keys starting with the given prefix.

        Args:
            prefix: Key prefix to match
        """
        with self._lock:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_remove:
                del self._cache[key]

            logger.debug(f"Invalidated {len(keys_to_remove)} cache entries with prefix '{prefix}'")

    def clear(self):
        """Clear the entire cache."""
        with self._lock:
            self._cache.clear()
            logger.debug("Cache cleared")

    def _evict_one(self):
        """Evict the oldest item from the cache."""
        # Find the item with the earliest expiration time
        oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]
        self._stats["evictions"] += 1

    @property
    def stats(self):
        """Get cache statistics."""
        with self._lock:
            stats = self._stats.copy()
            stats["size"] = len(self._cache)
            stats["max_size"] = self.max_size
            return stats


# Global cache instance
_cache = None

def get_cache(max_size=1000, default_ttl=300):
    """Get the global cache instance, creating it if necessary."""
    global _cache
    if _cache is None:
        _cache = ResultCache(max_size=max_size, default_ttl=default_ttl)
    return _cache

def cached(prefix, ttl=None):
    """
    Decorator for caching method results.

    Args:
        prefix (str): Cache key prefix
        ttl (int): Time-to-live in seconds

    Example:
        @cached("molecule")
        def get_molecule(self, molecule_id):
            # Database access...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key from prefix and arguments
            key_parts = [prefix]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            # Try to get from cache
            cache = get_cache()
            result = cache.get(cache_key)

            if result is not None:
                return result

            # Not in cache, call the function
            result = func(self, *args, **kwargs)

            # Store in cache if not None
            if result is not None:
                cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator

def invalidate_cache(prefix, *args):
    """
    Invalidate cache entries with the given prefix and arguments.

    Args:
        prefix (str): Cache key prefix
        *args: Additional parts of the key
    """
    cache = get_cache()

    if not args:
        # Invalidate all with this prefix
        cache.invalidate_by_prefix(prefix)
    else:
        # Invalidate specific key
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        cache_key = ":".join(key_parts)
        cache.invalidate(cache_key)