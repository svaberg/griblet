from typing import Any, Dict, Union

class BaseFieldLoader:
    """
    Abstract base class for field loaders.

    Subclasses must implement `load(field)`.
    """
    def __init__(self):
        pass

    def load(self, field: str) -> Union[Any, Dict[str, Any]]:
        """
        Load a field by name.

        Parameters
        ----------
        field : str
            The name of the field to load.

        Returns
        -------
        value : Any or dict[str, Any]
            The loaded field value. Subclasses may return a single value (e.g., np.ndarray, astropy Quantity),
            or a dict mapping field names to values (for block loads).

        Raises
        ------
        NotImplementedError
            If not implemented in a subclass.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class SimpleArrayLoader(BaseFieldLoader):
    """
    Loader that simulates loading a named field from a data source (dict-like or file handle).

    Parameters
    ----------
    data_source : dict[str, Any]
        Source of fields.

    Returns
    -------
    Any
        The value for the given field.
    """
    def __init__(self, data_source: Dict[str, Any]):
        super().__init__()
        self.data_source = data_source

    def load(self, field: str) -> Any:
        print(f"Loading field '{field}' from file...")
        return self.data_source[field]


class BlockLoader(BaseFieldLoader):
    """
    Loader that loads all fields as a block from a data source on first access.

    Parameters
    ----------
    file_handle : dict[str, Any]
        Source of fields.

    Returns
    -------
    dict[str, Any]
        Dictionary mapping all available field names to their values.
    """
    def __init__(self, file_handle: Dict[str, Any]):
        super().__init__()
        self.file_handle = file_handle
        self._loaded = False
        self._data: Dict[str, Any] = {}

    def load(self, field: str) -> Dict[str, Any]:
        if not self._loaded:
            print(f"Loading block from file for fields: {list(self.file_handle.keys())}")
            self._data = {key: self.file_handle[key] for key in self.file_handle}
            self._loaded = True
        return self._data
