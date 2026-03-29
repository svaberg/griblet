"""
Graph of ways to reach data.
"""

import logging

from .path import Path

logger = logging.getLogger(__name__)


class Graph:
    """
    Registry of all known ways to derive named data.

    Each output name can have more than one way to reach it. A way consists of
    the function to call, the names it needs, its cost, and optional metadata
    used for display.
    """

    def __init__(self, other_graph=None):
        """Start an empty graph, optionally seeded with another graph's ways."""
        self.ways = {}
        if other_graph is not None:
            self.merge(other_graph)

    def add(self, name, func, *, needs=None, cost=1.0, metadata=None):
        """
        Register one way to produce `name`.

        Parameters
        ----------
        name:
            Output name produced by this way.
        func:
            Callable used when this way is followed.
        needs:
            Names that must be available before `func` can be called.
        cost:
            Numeric cost, or a zero-argument callable returning the current
            cost, used when comparing alternative ways.
        metadata:
            Optional display metadata such as descriptions or units.
        """
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
        """
        Copy all ways from `other` into this graph and return `self`.

        This is an additive merge: existing ways are kept, and the ways from
        `other` are appended alongside them.
        """
        for name, ways in other.ways.items():
            self.ways.setdefault(name, []).extend(ways)
        logger.debug(
            "Merged %d way(s) across %d field(s)",
            sum(map(len, other.ways.values())),
            len(other.ways),
        )
        return self

    def path(self, name):
        """
        Resolve and return the lowest-cost path to `name`.

        The returned Path can be inspected, printed, or passed back to
        `compute` for evaluation.

        Raises
        ------
        KeyError
            If the graph has no ways at all for `name`.
        NoPathError
            If `name` is known, but none of its ways can be completed.
        """
        from .pathfinder import Pathfinder

        logger.info("Finding path to %s", name)
        path = Pathfinder(self).find_path(name)
        logger.debug("Chosen path for %s:\n%s", name, path)
        return path

    def compute(self, target):
        """
        Evaluate either a target name or a previously chosen Path.

        Passing a name first resolves the lowest-cost path. Passing a Path uses
        that exact path directly.

        Raises
        ------
        KeyError
            If a requested target name is unknown to the graph.
        NoPathError
            If a requested target name is known, but no valid path exists.
        TypeError
            If `target` is neither a name nor a Path.
        """
        from .pathfinder import follow_path

        if isinstance(target, Path):
            path = target
        elif isinstance(target, str):
            path = self.path(target)
        else:
            raise TypeError("compute() takes a field name or a Path")

        logger.info("Computing %s", path.root.name)
        value = follow_path(path, self)
        logger.info("Computed %s with total cost %s", path.root.name, path.cost)
        return value

    def fields(self):
        """
        Return the output names for which the graph has at least one way.

        These are the names this graph knows how to produce, not necessarily
        the names that are reachable from every source configuration.
        """
        return set(self.ways)

    def __str__(self):
        """
        Summarize the graph as fields followed by their registered ways.

        This is meant for inspection, not for round-tripping or serialization.
        """
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
