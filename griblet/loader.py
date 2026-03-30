"""
Loader abstractions for injecting external data into a Graph.

Defines loader classes that expose externally stored field values as
zero-need graph entries with associated access costs.
Supports simple per-field loading and block-style bulk loading with caching.
"""
import logging
from typing import Any, Dict, Optional, Union

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
        Expose each field as a zero-need step in a new Graph.

        If `cost` is omitted, each graph step asks the loader for its current
        field cost when evaluated. Passing a fixed `cost` overrides that
        dynamic behavior for all exported fields.
        """
        graph = Graph()
        logger.debug(
            "Exposing %d field(s) from %s as a graph",
            len(self._fields),
            type(self).__name__,
        )
        for name in self._fields:
            way_cost = (lambda name=name: self.cost(name)) if cost is None else cost
            graph.add(
                name,
                lambda name=name: self.load(name),
                cost=way_cost,
                metadata={"description": "Loader"},
            )
        return graph

    def _field_summary(self):
        """Return a short comma-separated summary of the available fields."""
        return ", ".join(sorted(self._fields)) or "-"

    def __str__(self):
        """Summarize the loader and the fields it can provide."""
        return "\n".join([
            type(self).__name__,
            f"  fields: {self._field_summary()}",
        ])


class BlockLoader(BaseLoader):
    """
    Loader that simulates bulk I/O by caching an entire block on first access.

    Simulates bulk I/O by loading all fields on first access, then serving
    subsequent accesses from memory at reduced cost. Exposes each field
    as a zero-need graph entry.
    """
    def __init__(self, file_handle: Dict[str, Any], load_cost=1.0, cached_cost=0.05):
        """
        Store the backing mapping and the costs before and after the first load.

        `file_handle` is any mapping from field names to values.
        """
        super().__init__()
        self._fields = file_handle
        self._cache = {}
        self._loaded = False
        self.load_cost = load_cost
        self.cached_cost = cached_cost

    def load(self, field: str) -> Any:
        """
        Load the whole block on first access, then serve later requests from cache.

        The first field request copies the whole backing mapping into the in-
        memory cache.
        """
        if not self._loaded:
            logger.info(
                "Loading block for %s (%d field(s))",
                field,
                len(self._fields),
            )
            self._cache = dict(self._fields)
            self._loaded = True
        else:
            logger.debug("Serving %s from loaded block", field)
        return self._cache[field]

    def cost(self, field: str) -> float:
        """
        Return the pre-load or post-load access cost for `field`.

        This models expensive first access followed by cheap cached access.
        """
        return self.cached_cost if self._loaded else self.load_cost

    def __str__(self):
        """Summarize the block loader state, fields, and cost model."""
        return "\n".join([
            type(self).__name__,
            f"  fields: {self._field_summary()}",
            f"  state: {'loaded' if self._loaded else 'not loaded'}",
            f"  load cost: {self.load_cost}",
            f"  cached cost: {self.cached_cost}",
        ])
