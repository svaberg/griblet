"""
Loader abstractions for injecting external data into a Graph.

Defines loader classes that expose externally stored field values as
zero-need graph entries with associated access costs.
"""

import logging
from typing import Any, Dict, Optional, Union

from .cache import Cache
from .graph import Graph


logger = logging.getLogger(__name__)


class BaseLoader:
    """
    Minimal loader that exposes named source fields to a graph.

    Maps external data sources to zero-need graph entries.
    Subclasses provide loading logic, available fields, and access cost.
    """

    def __init__(self):
        """Start with an empty in-memory mapping of available fields."""
        self._fields = {}

    def fields(self):
        """Return the field names this loader can provide."""
        return tuple(self._fields)

    def load(self, field: str) -> Any:
        """
        Return one field directly from the loader's field mapping.

        Subclasses can override this when loading is not a simple dictionary
        lookup.
        """
        if field not in self._fields:
            raise ValueError(f"Field '{field}' not found.")
        logger.debug("Loading %s from %s", field, type(self).__name__)
        return self._fields[field]

    def cost(self, field: str) -> float:
        """
        Return the access cost for `field` in this loader.

        The base implementation uses a small fixed cost for all known fields.
        """
        if field not in self._fields:
            raise ValueError(f"Field '{field}' not found.")
        return 0.1

    def as_graph(self, cost: Optional[Union[float, Any]] = None):
        """
        Expose each field as a zero-need path in a new Graph.

        If `cost` is omitted, each graph path uses the loader's declared access
        cost at graph construction time. Passing a fixed `cost` overrides that
        value for all exported fields.
        """
        graph = Graph()
        logger.debug(
            "Exposing %d field(s) from %s as a graph",
            len(self._fields),
            type(self).__name__,
        )
        for name in self.fields():
            graph.add(
                name,
                lambda name=name: self.load(name),
                cost=self.cost(name) if cost is None else cost,
                metadata={"description": type(self).__name__},
            )
        return graph

    def __str__(self):
        """Summarize the loader and the fields it can provide."""
        return "\n".join([
            type(self).__name__,
            f"  fields: {', '.join(sorted(self._fields)) or '-'}",
        ])


class BlockLoader(BaseLoader):
    """
    Loader that reads a whole block at once and owns a graph cache.

    The first load returns the full block so the owned Cache can add cheap
    cached steps for every field in the block.
    """

    def __init__(self, file_handle: Dict[str, Any], load_cost=1.0, cached_cost=0.1):
        """
        Store the backing mapping and the costs before and after residency.

        `file_handle` is any mapping from field names to values.
        """
        super().__init__()
        self._fields = file_handle
        self._loaded = False
        self.load_cost = load_cost
        self.cached_cost = cached_cost
        self._cache = None

    def load(self, field: str) -> Any:
        """
        Load the whole block on first access.

        The first field request returns the full block so a Cache can register
        cached steps for every field that became available together.
        """
        if not self._loaded:
            logger.info(
                "Loading block for %s (%d field(s))",
                field,
                len(self._fields),
            )
            self._loaded = True
            return dict(self._fields)
        logger.debug("Serving %s from loaded block", field)
        return self._fields[field]

    def cost(self, field: str) -> float:
        """Return the declared pre-cache access cost for `field`."""
        if field not in self._fields:
            raise ValueError(f"Field '{field}' not found.")
        return self.load_cost

    def as_graph(self, cost: Optional[Union[float, Any]] = None):
        """Expose this block loader through its owned cache-backed graph."""
        if cost is not None and cost != self.load_cost:
            raise ValueError(
                "BlockLoader.as_graph() uses the loader's own load_cost; "
                "construct the loader with the desired load_cost instead."
            )
        if self._cache is None:
            self._cache = Cache(
                Graph(),
                self,
                load_cost=self.load_cost,
                cached_cost=self.cached_cost,
            )
        return self._cache.graph

    def __str__(self):
        """Summarize the block loader state, fields, and cost model."""
        return "\n".join([
            type(self).__name__,
            f"  fields: {', '.join(sorted(self._fields)) or '-'}",
            f"  state: {'loaded' if self._loaded else 'not loaded'}",
            f"  load cost: {self.load_cost}",
            f"  cached cost: {self.cached_cost}",
        ])
