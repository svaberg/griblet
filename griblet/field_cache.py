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
