"""Graph-attached cache that adds explicit cached steps for loaded fields."""

import logging


logger = logging.getLogger(__name__)


class Cache:
    """
    Cache wrapper that augments a graph with explicit cached source steps.

    The wrapped loader provides the expensive source paths. As fields are
    loaded, this cache adds cheap direct steps for the cached fields to the
    same graph. Fresh pathfinding then sees those cached steps explicitly.
    """

    def __init__(self, graph, loader, *, load_cost=None, cached_cost=0.1):
        """
        Attach loader-backed source paths to `graph` and manage cached steps.

        Parameters
        ----------
        graph:
            Graph to augment with source paths and cached steps.
        loader:
            Loader with `fields()` and `load(field)`. If `load_cost` is not
            given, the loader must also provide `cost(field)`.
        load_cost:
            Optional fixed cost for every uncached loader path.
        cached_cost:
            Cost assigned to direct cached steps.
        """
        self.graph = graph
        self.loader = loader
        self.load_cost = load_cost
        self.cached_cost = cached_cost
        self._cache = {}
        self._cached_steps = {}

        for field in self.loader.fields():
            graph.add(
                field,
                lambda field=field: self.load(field),
                cost=self.load_cost if self.load_cost is not None else self.loader.cost(field),
                metadata={"description": type(loader).__name__},
            )

    def _add_cached_step(self, field):
        """Add one cheap direct cached step for `field` if it is not present yet."""
        if field in self._cached_steps:
            return
        self.graph.add(
            field,
            lambda field=field: self._cache[field],
            cost=self.cached_cost,
            metadata={"description": "Cache"},
        )
        self._cached_steps[field] = self.graph.paths[field][-1]
        logger.info("Added cached step for %s", field)

    def load(self, field):
        """
        Return `field`, loading it if needed and caching the result explicitly.

        If the wrapped loader returns a dict, all returned fields are cached at
        once and each gains a direct cached step in the graph.
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
                self._cache[loaded_field] = value
                self._add_cached_step(loaded_field)
            if field in loaded:
                return loaded[field]
            raise KeyError(f"Field {field} not found in loaded data")

        self._cache[field] = loaded
        self._add_cached_step(field)
        return loaded

    def discard(self, field):
        """Remove one cached field and its cached step if present."""
        self._cache.pop(field, None)
        step = self._cached_steps.pop(field, None)
        if step is None:
            return
        self.graph.paths[field].remove(step)
        if not self.graph.paths[field]:
            self.graph.paths.pop(field)
        logger.info("Removed cached step for %s", field)

    def __str__(self):
        """Summarize the wrapped loader and the currently cached fields."""
        return "\n".join([
            "Cache",
            f"  loader: {type(self.loader).__name__}",
            f"  load cost: {self.load_cost if self.load_cost is not None else 'loader-defined'}",
            f"  cached cost: {self.cached_cost}",
            f"  cached fields: {', '.join(sorted(self._cache)) or '-'}",
        ])
