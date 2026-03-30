"""
Graph-attached cache that adds explicit cached ways for loaded fields.
"""

import logging


logger = logging.getLogger(__name__)


class Cache:
    """
    Cache wrapper that augments a graph with explicit cached source ways.

    The wrapped loader provides the expensive source ways. As fields are loaded,
    this cache adds cheap direct ways for the cached fields to the same graph.
    Fresh pathfinding then sees those cached ways explicitly.
    """

    def __init__(self, graph, loader, *, load_cost=None, cached_cost=0.1):
        """
        Attach loader-backed source ways to `graph` and manage cached ways.

        Parameters
        ----------
        graph:
            Graph to augment with source and cached ways.
        loader:
            Loader with `fields()` and `load(field)`. If `load_cost` is not
            given, the loader must also provide `cost(field)`.
        load_cost:
            Optional fixed cost for every uncached loader way.
        cached_cost:
            Cost assigned to direct cached ways.
        """
        self.graph = graph
        self.loader = loader
        self.load_cost = load_cost
        self.cached_cost = cached_cost
        self._cache = {}
        self._cached_ways = {}

        for field in self.loader.fields():
            graph.add(
                field,
                lambda field=field: self.load(field),
                cost=self._uncached_cost(field),
                metadata={"description": type(loader).__name__},
            )

    def _uncached_cost(self, field):
        """Return the declared cost of loading `field` from the wrapped loader."""
        if self.load_cost is not None:
            return self.load_cost
        return self.loader.cost(field)

    def _add_cached_way(self, field):
        """Add one cheap direct cached way for `field` if it is not present yet."""
        if field in self._cached_ways:
            return
        way = {
            "needs": (),
            "func": lambda field=field: self._cache[field],
            "cost": self.cached_cost,
            "metadata": {"description": "Cache"},
        }
        self.graph.ways.setdefault(field, []).append(way)
        self._cached_ways[field] = way
        logger.info("Added cached way for %s", field)

    def _store(self, field, value):
        """Store one cached value and ensure the matching cached way exists."""
        self._cache[field] = value
        self._add_cached_way(field)

    def load(self, field):
        """
        Return `field`, loading it if needed and caching the result explicitly.

        If the wrapped loader returns a dict, all returned fields are cached at
        once and each gains a direct cached way in the graph.
        """
        if field in self._cache:
            logger.debug("Cache hit for %s", field)
            return self._cache[field]

        logger.debug("Cache miss for %s", field)
        loaded = self.loader.load(field)
        if isinstance(loaded, dict):
            logger.info(
                "Loaded %d field(s) while fetching %s",
                len(loaded),
                field,
            )
            for loaded_field, value in loaded.items():
                self._store(loaded_field, value)
            if field in loaded:
                return loaded[field]
            logger.warning(
                "Loader %s did not provide requested field %s",
                type(self.loader).__name__,
                field,
            )
            raise KeyError(f"Field {field} not found in loaded data")

        self._store(field, loaded)
        return loaded

    def discard(self, field):
        """Remove one cached field and its cached way if present."""
        self._cache.pop(field, None)
        way = self._cached_ways.pop(field, None)
        if way is None:
            return
        self.graph.ways[field].remove(way)
        if not self.graph.ways[field]:
            self.graph.ways.pop(field)
        logger.info("Removed cached way for %s", field)

    def __str__(self):
        """Summarize the wrapped loader and the currently cached fields."""
        return "\n".join([
            "Cache",
            f"  loader: {type(self.loader).__name__}",
            f"  load cost: {self.load_cost if self.load_cost is not None else 'loader-defined'}",
            f"  cached cost: {self.cached_cost}",
            f"  cached fields: {', '.join(sorted(self._cache)) or '-'}",
        ])
