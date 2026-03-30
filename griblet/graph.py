"""Graph of paths to reach data."""

from dataclasses import dataclass
import logging

from .path import Path


logger = logging.getLogger(__name__)


@dataclass
class _PathRecord:
    """One local graph entry for reaching a field."""

    needs: tuple
    func: object
    cost: float
    metadata: dict


class Graph:
    """
    Registry of all known paths that derive named data.

    Each output name can have more than one local graph path to reach it.
    """

    def __init__(self, other_graph=None):
        """Start an empty graph, optionally seeded with another graph's paths."""
        self.paths = {}
        if other_graph is not None:
            self.merge(other_graph)

    def add(self, name, func, *, needs=None, cost=1.0, metadata=None):
        """
        Register one path that produces `name`.

        Parameters
        ----------
        name:
            Output name produced by this path.
        func:
            Callable used when this path is followed.
        needs:
            Names that must be available before `func` can be called.
        cost:
            Numeric cost used when comparing alternative paths.
        metadata:
            Optional display metadata such as descriptions or units.
        """
        needs = tuple(needs or ())
        metadata = dict(metadata or {})
        self.paths.setdefault(name, []).append(
            _PathRecord(needs=needs, func=func, cost=cost, metadata=metadata)
        )
        logger.debug(
            "Added path %d for %s with needs=%s and cost=%s",
            len(self.paths[name]),
            name,
            needs,
            cost,
        )

    def merge(self, other):
        """
        Copy all paths from `other` into this graph and return `self`.

        This is an additive merge: existing paths are kept, and the paths from
        `other` are appended alongside them.
        """
        for name, paths in other.paths.items():
            self.paths.setdefault(name, []).extend(paths)
        logger.debug(
            "Merged %d path(s) across %d field(s)",
            sum(map(len, other.paths.values())),
            len(other.paths),
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
            If the graph has no paths at all for `name`.
        NoPathError
            If `name` is known, but none of its paths can be completed.
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

        logger.info("Computing %s", path.name)
        value = follow_path(path)
        logger.info("Computed %s with total cost %s", path.name, path.cost)
        return value

    def fields(self):
        """
        Return the output names for which the graph has at least one path.

        These are the names this graph knows how to produce, not necessarily
        the names that are reachable from every source configuration.
        """
        return set(self.paths)

    def __str__(self):
        """
        Summarize the graph as fields followed by their registered paths.

        This is meant for inspection, not for round-tripping or serialization.
        """
        lines = []
        for name in sorted(self.paths):
            lines.append(f"{name}:")
            for i, record in enumerate(self.paths[name], 1):
                meta_str = ", ".join(f"{k}={v}" for k, v in record.metadata.items())
                lines.append(
                    f"  Path {i}: needs={record.needs}, cost={record.cost}"
                    + (f", meta={meta_str}" if meta_str else "")
                )
        return "\n".join(lines)
