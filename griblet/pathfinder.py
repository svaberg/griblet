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
    path = Pathfinder(graph).find_path(target)
    return f"{target} total_cost={path.cost}\n{path}"


def follow_path(path: Path, graph):
    """
    Follow a chosen path and return the computed result.
    """
    def follow_step(node: Step):
        if node.way_index is None:
            raise RuntimeError(f"No chosen way for {node.name}")

        way = graph.ways[node.name][node.way_index]
        cost_val = _way_cost(way)

        if node.is_source:
            prev = node.last_actual_cost
            node.last_actual_cost = cost_val
            if prev is not None and prev != cost_val:
                logger.info("Cost change for %s: %s -> %s", node.name, prev, cost_val)
            return way["func"]()

        values = [follow_step(need) for need in node.needs]
        total_cost = cost_val + sum(need.last_actual_cost for need in node.needs)
        prev = node.last_actual_cost
        node.last_actual_cost = total_cost
        if prev is not None and prev != total_cost:
            logger.info("Cost change for %s: %s -> %s", node.name, prev, total_cost)
        return way["func"](*values)

    return follow_step(path.root)


class Pathfinder:
    """
    Find the lowest-cost path through a Graph.
    """

    def __init__(self, graph):
        self.graph = graph
        self.memo = {}

    def _find_path(
        self,
        target: str,
        trail: Optional[Set[str]] = None,
    ) -> Tuple[float, Optional[Step]]:
        if trail is None:
            trail = set()
        if target in trail:
            logger.warning("Cycle detected on %s", target)
            return float("inf"), None

        if target in self.memo:
            logger.debug("Memo hit for %s: %s", target, self.memo[target])
            return self.memo[target]

        if target not in self.graph.ways:
            logger.warning("Unknown field %s", target)
            raise KeyError(target)

        best_cost = float("inf")
        best_step = None
        trail.add(target)
        ways = self.graph.ways[target]

        for i, way in enumerate(ways):
            needs = way["needs"]
            desc = way.get("metadata", {}).get("description", "")
            logger.debug("Trying way %s for %s: needs=%s desc=%r", i + 1, target, needs, desc)
            subpaths = []
            fail = False
            cost_val = _way_cost(way)
            total = cost_val
            for need in needs:
                try:
                    need_cost, need_path = self._find_path(need, trail)
                except NoPathError:
                    logger.debug("Need %s of %s raised NoPathError", need, target)
                    fail = True
                    break
                except KeyError:
                    logger.debug("Need %s of %s is unknown", need, target)
                    fail = True
                    break
                if need_cost == float("inf") or need_path is None:
                    logger.debug("Need %s of %s failed", need, target)
                    fail = True
                    break
                total += need_cost
                subpaths.append(need_path)

            if fail:
                logger.debug("Way %s for %s failed", i + 1, target)
                continue

            logger.debug("Way %s for %s succeeded, total cost=%s", i + 1, target, total)
            if total < best_cost:
                best_cost = total
                best_step = Step(
                    name=target,
                    cost=cost_val,
                    way_index=i,
                    is_source=(len(needs) == 0),
                    needs=subpaths,
                    metadata=way.get("metadata", {}),
                )

        trail.remove(target)

        if best_step is None:
            logger.warning("Cannot find path to %s", target)
            self.memo[target] = (float("inf"), None)
            raise NoPathError(f"No path to {target}.")

        self.memo[target] = (best_cost, best_step)
        logger.debug("Found path to %s with cost=%s", target, best_cost)
        return best_cost, best_step

    def find_path(self, target: str) -> Path:
        """
        Find the lowest-cost path to `target`.
        """
        cost, root = self._find_path(target)
        return Path(cost=cost, root=root)
