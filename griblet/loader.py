"""
Loader abstractions for injecting external data into a Graph.

Defines loader classes that expose externally stored field values as
zero-need graph entries with associated access costs.
Supports simple per-field loading and block-style bulk loading with caching.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from .graph import Graph


logger = logging.getLogger(__name__)


class BaseLoader:
    """
    Base class for field loaders.

    Maps external data sources to zero-need graph entries.
    Subclasses provide loading logic, available fields, and access cost.
    """
    def __init__(self):
        # By default, an empty _fields dict (can be overridden by subclass)
        self._fields = {}

    def load(self, field: str) -> Any:
        """
        Load a field by name. By default, looks up in self._fields.
        Subclasses can override for custom loading logic.
        """
        try:
            return self._fields[field]
        except KeyError:
            raise ValueError(f"Field '{field}' not found.")

    def fields(self) -> List[str]:
        """
        Return a list of all available fields.
        """
        return list(self._fields.keys())

    def cost(self, field: str) -> float:
        """
        Return the cost of fetching the field. Subclasses can override.
        """
        if field in self._fields:
            return 0.1  # Default "load cost"
        else:
            raise ValueError(f"Field '{field}' not found.")

    def as_graph(self, cost: Optional[Union[float, Any]] = None):
        """
        Return a Graph with one source path for each field.
        """
        graph = Graph()
        for name in self.fields():
            way_cost = (lambda name=name: self.cost(name)) if cost is None else cost
            graph.add(
                name,
                lambda name=name: self.load(name),
                cost=way_cost,
                metadata={"description": "Loader"},
            )
        return graph


class BlockLoader:
    """
    Block-based loader with implicit caching.

    Simulates bulk I/O by loading all fields on first access, then serving
    subsequent accesses from memory at reduced cost. Exposes each field
    as a zero-need graph entry.
    """
    def __init__(self, file_handle: Dict[str, Any], load_cost=1.0, cached_cost=0.05):
        """
        file_handle: dict-like, mapping field names to values (can be adapted for real files)
        load_cost: cost to access a field if not yet loaded (simulates slow IO)
        cached_cost: cost for future accesses (simulates cheap in-memory access)
        """
        self.file_handle = file_handle
        self._cache = {}          # field -> value
        self._loaded = False
        self.load_cost = load_cost
        self.cached_cost = cached_cost

    def load(self, field: str) -> Any:
        if not self._loaded:
            logger.info("BlockLoader loading all fields in a single operation")
            self._cache = dict(self.file_handle)
            self._loaded = True
        return self._cache[field]

    def cost(self, field: str) -> float:
        return self.cached_cost if self._loaded else self.load_cost

    def fields(self) -> List[str]:
        return list(self.file_handle.keys())

    def as_graph(self) -> Graph:
        graph = Graph()
        for name in self.fields():
            graph.add(
                name,
                lambda name=name: self.load(name),
                cost=lambda name=name: self.cost(name),
                metadata={"description": "BlockLoader"},
            )
        return graph
