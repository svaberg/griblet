import numpy as np
import astropy.units as u
class FieldCache:
    def __init__(self, loader, uncached_cost=50, cached_cost=0.1):
        self.loader = loader
        self._cache = {}
        self.uncached_cost = uncached_cost
        self.cached_cost = cached_cost

    def get(self, field):
        if field in self._cache:
            return self._cache[field]
        loaded = self.loader.load(field)
        if isinstance(loaded, dict):
            self._cache.update(loaded)
            for key in loaded:
                print(f"[CACHE] Added '{key}' to cache.")
            if field not in loaded:
                raise KeyError(f"Field {field} not found in loaded data")
            return loaded[field]
        else:
            self._cache[field] = loaded
            print(f"[CACHE] Added '{field}' to cache.")
            return loaded

    def is_cached(self, field):
        return field in self._cache

    def cost(self, field):
        return self.cached_cost if self.is_cached(field) else self.uncached_cost

    def remove(self, field):
        if field in self._cache:
            del self._cache[field]
            print(f"[CACHE] Removed '{field}' from cache.")
        else:
            print(f"[CACHE] '{field}' not in cache. Nothing to remove.")

class DummyLoader:
    """Loader that always returns the same array (and unit) for any requested field."""
    def __init__(self, value=None, unit=u.dimensionless_unscaled):
        if value is None:
            value = np.array([42, 42, 42])
        self.value = value * unit if not isinstance(value, u.Quantity) else value

    def load(self, field):
        # Returns as a dict so cache can handle block loads.
        return {field: self.value}

class SimpleArrayLoader:
    """
    Demo loader: simulates loading a named field from "disk".
    In practice, use h5py, np.load, fits.open, etc.
    """
    def __init__(self, data_source):
        self.data_source = data_source  # Dict or file handle

    def load(self, field):
        print(f"Loading field '{field}' from file...")
        # In a real loader, access disk here
        return self.data_source[field]

class BlockLoader:
    def __init__(self, file_handle):
        self.file_handle = file_handle
        self._loaded = False
        self._data = None

    def load(self, field):
        """
        On first call, load a block (could be all base fields), return a dict of {field: value}.
        On subsequent calls, just return the relevant field.
        """
        if not self._loaded:
            print(f"Loading block from file for fields: {list(self.file_handle.keys())}")
            self._data = {key: self.file_handle[key] for key in self.file_handle}
            self._loaded = True
        # Return *all* loaded fields, so the cache can update
        return self._data  # Will be used by cache to update multiple fields
