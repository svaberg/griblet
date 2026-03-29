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
            logger.debug("Cache hit for %s", field)
            return self._cache[field]
        logger.debug("Cache miss for %s", field)
        loaded = self.loader.load(field)
        loaded_fields = loaded if isinstance(loaded, dict) else {field: loaded}
        self._cache.update(loaded_fields)
        if isinstance(loaded, dict):
            logger.info(
                "Loaded %d field(s) while fetching %s",
                len(loaded_fields),
                field,
            )
        if field not in loaded_fields:
            logger.warning(
                "Loader %s did not provide requested field %s",
                type(self.loader).__name__,
                field,
            )
            raise KeyError(f"Field {field} not found in loaded data")
        return loaded_fields[field]

    def cost(self, field):
        return self.cached_cost if field in self._cache else self.uncached_cost

    def __str__(self):
        cached = ", ".join(sorted(self._cache)) or "-"
        return "\n".join([
            "Cache",
            f"  loader: {type(self.loader).__name__}",
            f"  uncached cost: {self.uncached_cost}",
            f"  cached cost: {self.cached_cost}",
            f"  cached fields: {cached}",
        ])
