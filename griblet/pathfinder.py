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


def follow_path(path: Path):
    """
    Evaluate a resolved path.

    The returned value is the computed result at the root of the path.
    """

    def follow(node: Path):
        logger.debug("Following %s", node.name)
        if node.is_source:
            logger.debug("Loaded source %s", node.name)
            return node.func()

        values = [follow(need) for need in node.needs]
        logger.debug("Computed %s", node.name)
        return node.func(*values)

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
        Return the cheapest path to `target`, or fail if no path works.

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

        if target not in self.graph.paths:
            raise KeyError(target)

        best_path = None
        trail.add(target)

        for i, step in enumerate(self.graph.paths[target], 1):
            needs = step.needs
            child_paths = []
            total_cost = step.cost
            logger.debug(
                "Trying step %d for %s with needs=%s and cost=%s",
                i,
                target,
                needs,
                step.cost,
            )
            for need in needs:
                try:
                    need_path = self._find_path(need, trail)
                except (NoPathError, KeyError):
                    need_path = None
                if need_path is None:
                    logger.debug("Step %d for %s failed at need %s", i, target, need)
                    break
                total_cost += need_path.cost
                child_paths.append(need_path)
            else:
                if best_path is None or total_cost < best_path.cost:
                    best_path = Path(
                        name=target,
                        cost=total_cost,
                        func=step.func,
                        is_source=not needs,
                        needs=child_paths,
                        metadata=dict(step.metadata),
                    )
                    logger.debug(
                        "Step %d is the new best path to %s with total cost %s",
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
            If the graph has no paths at all for `target`.
        NoPathError
            If the graph knows `target`, but every path to reach it fails.
        """
        path = self._find_path(target)
        logger.info("Found path to %s with total cost %s", target, path.cost)
        return path
