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
    Cache wrapper around a loader with a dynamic cached-versus-uncached cost.

    `get()` memoizes loaded values; if the loader returns a dict, all returned
    fields are cached at once. `cost(field)` reflects current cache state.
    This lets graph costs respond to whether data has already been loaded.
    """
    def __init__(self, loader, uncached_cost=50, cached_cost=0.1):
        """
        Bind a loader and the cost model to use before and after caching.

        `loader` must provide a `load(field)` method. It may return either a
        single value for the requested field or a dict of multiple fields loaded
        together.
        """
        self.loader = loader
        self._cache = {}
        self.uncached_cost = uncached_cost
        self.cached_cost = cached_cost

    def get(self, field):
        """
        Return `field`, populating the cache from scalar or bulk loader output.

        If the loader returns a dict, all returned fields are cached at once,
        and the requested field must be among them.
        """
        if field in self._cache:
            logger.debug("Cache hit for %s", field)
            return self._cache[field]
        logger.debug("Cache miss for %s", field)
        loaded = self.loader.load(field)
        if isinstance(loaded, dict):
            self._cache.update(loaded)
            logger.info(
                "Loaded %d field(s) while fetching %s",
                len(loaded),
                field,
            )
            if field in loaded:
                return loaded[field]
            logger.warning(
                "Loader %s did not provide requested field %s",
                type(self.loader).__name__,
                field,
            )
            raise KeyError(f"Field {field} not found in loaded data")
        self._cache[field] = loaded
        return loaded

    def cost(self, field):
        """
        Return the current access cost implied by the cache state.

        This is `uncached_cost` before a field has been seen and `cached_cost`
        afterwards.
        """
        return self.cached_cost if field in self._cache else self.uncached_cost

    def __str__(self):
        """
        Summarize the loader, cost model, and currently cached fields.

        This is a human-readable status view of the cache.
        """
        return "\n".join([
            "Cache",
            f"  loader: {type(self.loader).__name__}",
            f"  uncached cost: {self.uncached_cost}",
            f"  cached cost: {self.cached_cost}",
            f"  cached fields: {', '.join(sorted(self._cache)) or '-'}",
        ])
