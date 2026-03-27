"""
Graph of ways to reach data.
"""


class Graph:
    """
    Registry of ways to reach named data.
    """

    def __init__(self, other_graph=None):
        self.ways = {}
        if other_graph is not None:
            self.merge(other_graph)

    def add(self, name, func, *, needs=None, cost=1.0, metadata=None):
        """
        Add one way to reach `name`.
        """
        way = {
            "needs": tuple(needs or ()),
            "func": func,
            "cost": cost,
            "metadata": dict(metadata or {}),
        }
        self.ways.setdefault(name, []).append(way)

    def merge(self, other):
        """
        Merge all ways from another Graph into this one.
        """
        for name, ways in other.ways.items():
            self.ways.setdefault(name, []).extend(ways)
        return self

    def compute(self, name):
        """
        Follow the best path to `name` and return the result.
        """
        from .pathfinder import Pathfinder, follow_path

        _, path = Pathfinder(self).find_path(name)
        return follow_path(path, self)

    def fields(self):
        return set(self.ways)

    def __str__(self):
        lines = []
        for name in sorted(self.ways):
            lines.append(f"{name}:")
            for i, way in enumerate(self.ways[name], 1):
                cost_str = way["cost"] if isinstance(way["cost"], (int, float)) else "callable"
                meta = way["metadata"] or {}
                meta_str = ", ".join(f"{k}={v}" for k, v in meta.items())
                lines.append(
                    f"  Way {i}: needs={way['needs']}, cost={cost_str}"
                    + (f", meta={meta_str}" if meta_str else "")
                )
        return "\n".join(lines)

    __repr__ = __str__
