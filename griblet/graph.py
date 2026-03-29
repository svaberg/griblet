"""
Graph of ways to reach data.
"""

import logging


logger = logging.getLogger(__name__)


class Graph:
    """
    Registry of ways to reach named data.
    """

    def __init__(self, other_graph=None):
        self.ways = {}
        if other_graph is not None:
            self.merge(other_graph)

    def add(self, name, func, *, needs=None, cost=1.0, metadata=None):
        needs = tuple(needs or ())
        metadata = dict(metadata or {})
        self.ways.setdefault(name, []).append({
            "needs": needs,
            "func": func,
            "cost": cost,
            "metadata": metadata,
        })
        logger.debug(
            "Added way %d for %s with needs=%s and cost=%s",
            len(self.ways[name]),
            name,
            needs,
            "callable" if callable(cost) else cost,
        )

    def merge(self, other):
        for name, ways in other.ways.items():
            self.ways.setdefault(name, []).extend(ways)
        logger.debug(
            "Merged %d way(s) across %d field(s)",
            sum(map(len, other.ways.values())),
            len(other.ways),
        )
        return self

    def compute(self, name):
        from .pathfinder import Pathfinder, follow_path

        logger.info("Computing %s", name)
        path = Pathfinder(self).find_path(name)
        logger.debug("Chosen path for %s:\n%s", name, path)
        value = follow_path(path, self)
        logger.info("Computed %s with total cost %s", name, path.cost)
        return value

    def fields(self):
        return set(self.ways)

    def __str__(self):
        lines = []
        for name in sorted(self.ways):
            lines.append(f"{name}:")
            for i, way in enumerate(self.ways[name], 1):
                cost = way["cost"]
                cost_str = "callable" if callable(cost) else cost
                meta_str = ", ".join(f"{k}={v}" for k, v in way["metadata"].items())
                lines.append(
                    f"  Way {i}: needs={way['needs']}, cost={cost_str}"
                    + (f", meta={meta_str}" if meta_str else "")
                )
        return "\n".join(lines)
