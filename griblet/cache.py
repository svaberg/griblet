"""
Field-level cache with cost model for loaders.

Wraps a loader and memoizes loaded field values. Supports loaders that return
either a single field value or a dict of multiple fields (bulk load), updating
the cache accordingly. Exposes a simple dynamic cost: cached vs uncached.
"""

import logging


logger = logging.getLogger(__name__)

class Cache:
    """
    Cache wrapper around a loader with a cached/uncached cost model.

    `get()` memoizes loaded values; if the loader returns a dict, all returned
    fields are cached at once. `cost(field)` reflects current cache state.
    """
    def __init__(self, loader, uncached_cost=50, cached_cost=0.1):
        self.loader = loader
        self._cache = {}
        self.uncached_cost = uncached_cost
        self.cached_cost = cached_cost

    def get(self, field):
        if field in self._cache:
            return self._cache[field]
        loaded = self.loader.load(field)
        if isinstance(loaded, dict):
            self._cache.update(loaded)
            for key in loaded:
                logger.info("Added %s to cache", key)
            if field not in loaded:
                raise KeyError(f"Field {field} not found in loaded data")
            return loaded[field]
        else:
            self._cache[field] = loaded
            logger.info("Added %s to cache", field)
            return loaded

    def is_cached(self, field):
        return field in self._cache

    def cost(self, field):
        return self.cached_cost if self.is_cached(field) else self.uncached_cost

    def remove(self, field):
        if field in self._cache:
            del self._cache[field]
            logger.info("Removed %s from cache", field)
        else:
            logger.info("%s not in cache; nothing to remove", field)
