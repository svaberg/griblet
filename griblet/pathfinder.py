"""
Find and follow paths through a Graph.
"""

import logging
from typing import Optional, Set, Tuple

from .path import PathNode


logger = logging.getLogger(__name__)


class NoPathError(Exception):
    """Raised when no path can reach the requested data."""


def explain_field(graph, target: str) -> str:
    """
    Return a readable explanation of the chosen path for `target`.
    """
    cost, path = Pathfinder(graph).find_path(target)
    lines = [f"{target} total_cost={cost}"]

    def walk(node: PathNode, depth: int = 0) -> None:
        desc = (node.metadata or {}).get("description", "")
        parts = [node.name, f"(cost={node.cost})"]
        if desc:
            parts.append(f"- {desc}")
        lines.append("  " * depth + " ".join(parts))
        for need in node.needs:
            walk(need, depth + 1)

    walk(path)
    return "\n".join(lines)


def follow_path(node: PathNode, graph):
    """
    Follow a chosen path and return the computed result.
    """
    if node.is_source:
        for way in graph.ways[node.name]:
            if not way["needs"]:
                cost_val = way["cost"]() if callable(way["cost"]) else way["cost"]
                break
        else:
            raise RuntimeError(f"No source way for {node.name}")
        prev = node.last_actual_cost
        node.last_actual_cost = cost_val
        if prev is not None and prev != cost_val:
            logger.info("Cost change for %s: %s -> %s", node.name, prev, cost_val)
        return way["func"]()

    values = [follow_path(need, graph) for need in node.needs]
    need_names = tuple(need.name for need in node.needs)
    for way in graph.ways[node.name]:
        if need_names == way["needs"]:
            cost_val = way["cost"]() if callable(way["cost"]) else way["cost"]
            break
    else:
        raise RuntimeError(f"No matching way for {node.name}")

    child_cost = sum(need.last_actual_cost for need in node.needs)
    total_cost = cost_val + child_cost
    prev = node.last_actual_cost
    node.last_actual_cost = total_cost
    if prev is not None and prev != total_cost:
        logger.info("Cost change for %s: %s -> %s", node.name, prev, total_cost)
    return way["func"](*values)


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
    ) -> Tuple[float, Optional[PathNode]]:
        if trail is None:
            trail = set()
        if target in trail:
            logger.warning("Cycle detected on %s", target)
            return float("inf"), None

        if target in self.memo:
            logger.debug("Memo hit for %s: %s", target, self.memo[target])
            return self.memo[target]

        best_cost = float("inf")
        best_path = None
        trail.add(target)
        ways = self.graph.ways.get(target, [])
        if not ways:
            logger.debug("No ways found for %s", target)

        for i, way in enumerate(ways):
            needs = way["needs"]
            desc = way.get("metadata", {}).get("description", "")
            logger.debug("Trying way %s for %s: needs=%s desc=%r", i + 1, target, needs, desc)
            subpaths = []
            fail = False
            cost_val = way["cost"]() if callable(way["cost"]) else way["cost"]
            total = cost_val
            for need in needs:
                try:
                    need_cost, need_path = self._find_path(need, trail)
                except NoPathError:
                    logger.debug("Need %s of %s raised NoPathError", need, target)
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
                best_path = PathNode(
                    name=target,
                    cost=cost_val,
                    is_source=(len(needs) == 0),
                    needs=subpaths,
                    metadata=way.get("metadata", {}),
                )

        trail.remove(target)

        if best_path is None:
            logger.warning("Cannot find path to %s", target)
            missing = [way["needs"] for way in self.graph.ways.get(target, []) if way["needs"]]
            if not self.graph.ways.get(target, []):
                msg = f"No path to {target} (no ways at all)."
            else:
                msg = f"No path to {target} (all ways failed; needs tried: {missing})."
            self.memo[target] = (float("inf"), None)
            raise NoPathError(msg)

        self.memo[target] = (best_cost, best_path)
        logger.debug("Found path to %s with cost=%s", target, best_cost)
        return best_cost, best_path

    def find_path(self, target: str) -> Tuple[float, PathNode]:
        """
        Find the lowest-cost path to `target`.
        """
        cost, path = self._find_path(target)
        if path is None:
            raise NoPathError(f"No path to {target}.")
        return cost, path
