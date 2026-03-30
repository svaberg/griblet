"""Find and follow paths through a Graph."""

import logging
from typing import Optional, Set

from .path import Path


logger = logging.getLogger(__name__)


class NoPathError(Exception):
    """
    Raised when a known target has no valid path through the graph.

    This is different from `KeyError`, which is used when the graph does not
    know the requested target name at all.
    """


def _way_cost(way):
    """
    Resolve a way cost stored as either a number or a zero-argument callable.

    This keeps dynamic cost functions and fixed costs on the same footing.
    """
    cost = way["cost"]
    return cost() if callable(cost) else cost


def follow_path(path: Path, graph):
    """
    Evaluate a resolved path and record the actual cost paid at each node.

    The returned value is the computed result at the root of the path. As the
    path is followed, each node's `last_actual_cost` is updated with the cost
    actually paid during that evaluation.
    """

    def set_actual_cost(node: Path, actual_cost: float):
        prev = node.last_actual_cost
        node.last_actual_cost = actual_cost
        if prev is not None and prev != actual_cost:
            logger.info("Cost change for %s: %s -> %s", node.name, prev, actual_cost)

    def follow(node: Path):
        if node.way_index is None:
            raise RuntimeError(f"No chosen way for {node.name}")

        way = graph.ways[node.name][node.way_index]
        local_cost = _way_cost(way)
        logger.debug(
            "Following %s via way %s with local cost %s",
            node.name,
            node.way_index,
            local_cost,
        )

        if node.is_source:
            set_actual_cost(node, local_cost)
            logger.debug("Loaded source %s", node.name)
            return way["func"]()

        values = [follow(need) for need in node.needs]
        total_cost = local_cost + sum(need.last_actual_cost for need in node.needs)
        set_actual_cost(node, total_cost)
        logger.debug("Computed %s with actual cost %s", node.name, total_cost)
        return way["func"](*values)

    return follow(path)


class Pathfinder:
    """
    Search a graph for the lowest-cost path to a requested target.

    The search memoizes subpaths by target name, so repeated subproblems are
    only solved once per Pathfinder instance.
    """

    def __init__(self, graph):
        """Bind the graph to search and initialize the memo table for subpaths."""
        self.graph = graph
        self.memo = {}

    def __str__(self):
        """Summarize the graph being searched and the current memo table size."""
        fields = ", ".join(sorted(self.graph.fields())) or "-"
        return "\n".join([
            "Pathfinder",
            f"  fields: {fields}",
            f"  memoized targets: {len(self.memo)}",
        ])

    def _find_path(self, target: str, trail: Optional[Set[str]] = None) -> Optional[Path]:
        """
        Return the cheapest path to `target`, or `None` if no path works.

        This is the recursive worker behind `find_path`.
        """
        logger.debug("Searching for a path to %s", target)
        trail = set() if trail is None else trail
        if target in trail:
            logger.debug("Cycle encountered while searching for %s", target)
            return None

        if target in self.memo:
            logger.debug("Using memoized path to %s", target)
            return self.memo[target]

        if target not in self.graph.ways:
            raise KeyError(target)

        best_path = None
        trail.add(target)

        for i, way in enumerate(self.graph.ways[target]):
            needs = way["needs"]
            child_paths = []
            local_cost = _way_cost(way)
            total_cost = local_cost
            logger.debug(
                "Trying way %d for %s with needs=%s and local cost=%s",
                i,
                target,
                needs,
                local_cost,
            )
            for need in needs:
                try:
                    need_path = self._find_path(need, trail)
                except (NoPathError, KeyError):
                    need_path = None
                if need_path is None:
                    logger.debug("Way %d for %s failed at need %s", i, target, need)
                    break
                total_cost += need_path.cost
                child_paths.append(need_path)
            else:
                if best_path is None or total_cost < best_path.cost:
                    best_path = Path(
                        name=target,
                        cost=total_cost,
                        way_index=i,
                        is_source=not needs,
                        needs=child_paths,
                        metadata=way.get("metadata", {}),
                    )
                    logger.debug(
                        "Way %d is the new best path to %s with total cost %s",
                        i,
                        target,
                        total_cost,
                    )

        trail.remove(target)
        self.memo[target] = best_path

        if best_path is None:
            logger.warning("No path found to %s", target)
            raise NoPathError(f"No path to {target}.")

        return best_path

    def find_path(self, target: str) -> Path:
        """
        Return the lowest-cost Path object that reaches `target`.

        Raises
        ------
        KeyError
            If the graph has no ways at all for `target`.
        NoPathError
            If the graph knows `target`, but every way to reach it fails.
        """
        path = self._find_path(target)
        logger.info("Found path to %s with total cost %s", target, path.cost)
        return path
