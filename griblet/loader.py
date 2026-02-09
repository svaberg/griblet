"""
Loader abstractions for injecting external data into a ComputationGraph.

Defines loader classes that expose externally stored field values as
zero-dependency computation recipes with associated access costs.
Supports simple per-field loading and block-style bulk loading with caching.
"""

from typing import Any, Dict, Union, List
from griblet.computation_graph import ComputationGraph  # avoid circular import


class BaseLoader:
    """
    Base class for field loaders.

    Maps external data sources to zero-dependency graph recipes.
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

    def as_graph(self, cost: float = 0.1):
        """
        Returns a ComputationGraph with a loader recipe for each field.
        """
        cg = ComputationGraph()
        for field in self.fields():
            # Bind field name into default func/cost lambdas
            cg.add_recipe(
                field=field,
                func=lambda field=field: self.load(field),
                deps=[],
                cost=lambda field=field: self.cost(field),
                metadata={'description': 'Loader'}
            )
        return cg


from typing import Any, Dict, List
from griblet.computation_graph import ComputationGraph

class BlockLoader:
    """
    Block-based loader with implicit caching.

    Simulates bulk I/O by loading all fields on first access, then serving
    subsequent accesses from memory at reduced cost. Exposes each field
    as a zero-dependency recipe.
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
            print(f"BlockLoader: Loading all fields in a single operation.")
            self._cache = dict(self.file_handle)
            self._loaded = True
        return self._cache[field]

    def cost(self, field: str) -> float:
        return self.cached_cost if self._loaded else self.load_cost

    def fields(self) -> List[str]:
        return list(self.file_handle.keys())

    def as_graph(self) -> ComputationGraph:
        cg = ComputationGraph()
        for field in self.fields():
            # bind field name for lambda (avoid late-binding bug)
            cg.add_recipe(
                output=field,
                func=lambda field=field: self.load(field),
                deps=[],
                cost=lambda field=field: self.cost(field),
                metadata={'description': 'BlockLoader'}
            )
        return cg
