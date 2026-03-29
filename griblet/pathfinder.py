"""
Find and follow paths through a Graph.
"""

import logging
from typing import Optional, Set, Tuple

from .path import Path, Step


logger = logging.getLogger(__name__)


class NoPathError(Exception):
    """Raised when no path can reach the requested data."""


def _way_cost(way):
    cost = way["cost"]
    return cost() if callable(cost) else cost


def explain_field(graph, target: str) -> str:
    """
    Return a readable explanation of the chosen path for `target`.
    """
    logger.debug("Explaining path to %s", target)
    return str(Pathfinder(graph).find_path(target))


def follow_path(path: Path, graph):
    """
    Follow a chosen path and return the computed result.
    """
    def set_actual_cost(node: Step, actual_cost: float):
        prev = node.last_actual_cost
        node.last_actual_cost = actual_cost
        if prev is not None and prev != actual_cost:
            logger.info("Cost change for %s: %s -> %s", node.name, prev, actual_cost)

    def follow_step(node: Step):
        if node.way_index is None:
            raise RuntimeError(f"No chosen way for {node.name}")

        way = graph.ways[node.name][node.way_index]
        cost_val = _way_cost(way)
        logger.debug(
            "Following %s via way %s with local cost %s",
            node.name,
            node.way_index,
            cost_val,
        )

        if node.is_source:
            set_actual_cost(node, cost_val)
            logger.debug("Loaded source %s", node.name)
            return way["func"]()

        values = [follow_step(need) for need in node.needs]
        total_cost = cost_val + sum(need.last_actual_cost for need in node.needs)
        set_actual_cost(node, total_cost)
        logger.debug("Computed %s with actual cost %s", node.name, total_cost)
        return way["func"](*values)

    return follow_step(path.root)


class Pathfinder:
    """
    Find the lowest-cost path through a Graph.
    """

    def __init__(self, graph):
        self.graph = graph
        self.memo = {}

    def __str__(self):
        fields = ", ".join(sorted(self.graph.fields())) or "-"
        return "\n".join([
            "Pathfinder",
            f"  fields: {fields}",
            f"  memoized targets: {len(self.memo)}",
        ])

    def _find_path(
        self,
        target: str,
        trail: Optional[Set[str]] = None,
    ) -> Tuple[float, Optional[Step]]:
        logger.debug("Searching for a path to %s", target)
        trail = set() if trail is None else trail
        if target in trail:
            logger.debug("Cycle encountered while searching for %s", target)
            return float("inf"), None

        if target in self.memo:
            logger.debug("Using memoized path to %s", target)
            return self.memo[target]

        if target not in self.graph.ways:
            raise KeyError(target)

        best_cost = float("inf")
        best_step = None
        trail.add(target)

        for i, way in enumerate(self.graph.ways[target]):
            needs = way["needs"]
            subpaths = []
            cost_val = _way_cost(way)
            total = cost_val
            logger.debug(
                "Trying way %d for %s with needs=%s and local cost=%s",
                i,
                target,
                needs,
                cost_val,
            )
            for need in needs:
                try:
                    need_cost, need_path = self._find_path(need, trail)
                except (NoPathError, KeyError):
                    need_path = None
                if need_path is None:
                    logger.debug("Way %d for %s failed at need %s", i, target, need)
                    break
                total += need_cost
                subpaths.append(need_path)
            else:
                if total < best_cost:
                    best_cost = total
                    best_step = Step(
                        name=target,
                        cost=cost_val,
                        way_index=i,
                        is_source=not needs,
                        needs=subpaths,
                        metadata=way.get("metadata", {}),
                    )
                    logger.debug(
                        "Way %d is the new best path to %s with total cost %s",
                        i,
                        target,
                        total,
                    )

        trail.remove(target)

        if best_step is None:
            self.memo[target] = (float("inf"), None)
            logger.warning("No path found to %s", target)
            raise NoPathError(f"No path to {target}.")

        self.memo[target] = (best_cost, best_step)
        return best_cost, best_step

    def find_path(self, target: str) -> Path:
        """
        Find the lowest-cost path to `target`.
        """
        path = Path(*self._find_path(target))
        logger.info("Found path to %s with total cost %s", target, path.cost)
        return path
