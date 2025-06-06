from typing import Any, Dict, Union, List
from griblet.computation_graph import ComputationGraph  # avoid circular import

class BaseLoader:
    """
    Abstract base class for field loaders.
    Subclasses must implement `load(field)`, and optionally override `fields()` and `cost()`.
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


# class SimpleArrayLoader(BaseLoader):
#     """
#     Loader that simulates loading a named field from a data source (dict-like or file handle).

#     Parameters
#     ----------
#     data_source : dict[str, Any]
#         Source of fields.

#     Returns
#     -------
#     Any
#         The value for the given field.
#     """
#     def __init__(self, data_source: Dict[str, Any]):
#         super().__init__()
#         self.data_source = data_source

#     def load(self, field: str) -> Any:
#         print(f"Loading field '{field}' from file...")
#         return self.data_source[field]


# class BlockLoader(BaseLoader):
#     """
#     Loader that loads all fields as a block from a data source on first access.

#     Parameters
#     ----------
#     file_handle : dict[str, Any]
#         Source of fields.

#     Returns
#     -------
#     dict[str, Any]
#         Dictionary mapping all available field names to their values.
#     """
#     def __init__(self, file_handle: Dict[str, Any]):
#         super().__init__()
#         self.file_handle = file_handle
#         self._loaded = False
#         self._data: Dict[str, Any] = {}

#     def load(self, field: str) -> Dict[str, Any]:
#         if not self._loaded:
#             print(f"Loading block from file for fields: {list(self.file_handle.keys())}")
#             self._data = {key: self.file_handle[key] for key in self.file_handle}
#             self._loaded = True
#         return self._data
