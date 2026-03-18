"""
Cost-based dependency solver for ComputationGraph.

Searches a declarative computation graph and selects a minimal-cost
recipe tree for a requested target field. Assigns execution semantics
to stored recipes but does not evaluate field values.
Builds an explicit ComputationTreeNode representing the chosen plan.
"""

import logging
from typing import Optional, Set, Tuple

from .computation_tree import ComputationTreeNode

class UnresolvableFieldError(Exception):
    """Raised when no recipe chain can resolve a requested field."""
    pass

class FallbackResolutionFailed(Exception):
    """Raised when all fallback resolution strategies fail."""
    pass

class DependencySolver:
    """
    Resolve fields in a ComputationGraph by minimal total cost.

    Recursively explores all recipe dependencies, detects cycles,
    memoizes intermediate results, and returns a computation tree
    describing the cheapest valid resolution.
    """
    def __init__(self, graph):
        self.graph = graph
        self.memo = {}

    def _resolve_field(
        self,
        target: str,
        path: Optional[Set[str]] = None,
    ) -> Tuple[float, Optional[ComputationTreeNode]]:
        """
        Internal recursive resolver used by `resolve_field()`.
        """
        logger = logging.getLogger("DependencySolver")
        if path is None:
            path = set()
        if target in path:
            logger.warning(f"Cycle detected on field '{target}'")
            return (float("inf"), None)  # cycle detected

        memo_key = target
        if memo_key in self.memo:
            logger.debug(f"Memo hit for '{target}': {self.memo[memo_key]}")
            return self.memo[memo_key]

        best_cost = float("inf")
        best_tree = None
        path.add(target)
        recipes = self.graph.recipes.get(target, [])
        if not recipes:
            logger.debug(f"No recipes found for '{target}'")
        for i, recipe in enumerate(recipes):
            deps = recipe['deps']
            recipe_desc = recipe.get('metadata', {}).get('description', '')
            logger.debug(f"Trying recipe {i+1} for '{target}': deps={deps} desc={recipe_desc!r}")
            subtrees = []
            fail = False
            cost_val = recipe['cost']() if callable(recipe['cost']) else recipe['cost']
            total = cost_val
            for dep in deps:
                try:
                    dep_cost, dep_tree = self._resolve_field(dep, path)
                    if dep_cost == float("inf") or dep_tree is None:
                        logger.debug(f"  Dependency '{dep}' of '{target}' failed (unresolvable)")
                        fail = True
                        break
                    total += dep_cost
                    subtrees.append(dep_tree)
                except UnresolvableFieldError:
                    logger.debug(f"  Dependency '{dep}' of '{target}' raised UnresolvableFieldError")
                    fail = True
                    break
            if not fail:
                logger.debug(f"  Recipe {i+1} for '{target}' succeeded, total cost={total}")
                if total < best_cost:
                    best_cost = total
                    best_tree = ComputationTreeNode(
                        field=target,
                        cost=cost_val,
                        used_primary=(len(deps) == 0),
                        deps=subtrees,
                        recipe_metadata=recipe.get('metadata', {})
                    )
            else:
                logger.debug(f"  Recipe {i+1} for '{target}' failed")
        path.remove(target)

        
        if best_tree is None:
            logger.warning(f"Cannot resolve field '{target}' (all recipes failed)")
            missing = [r['deps'] for r in self.graph.recipes.get(target, []) if r['deps']]
            if not self.graph.recipes.get(target, []):
                msg = f"Cannot resolve field '{target}' (no recipes at all)."
            else:
                msg = f"Cannot resolve field '{target}' (all recipes failed; dependencies tried: {missing})."
            self.memo[memo_key] = (float("inf"), None)
            raise UnresolvableFieldError(msg)
        else:
            self.memo[memo_key] = (best_cost, best_tree)
            logger.debug(f"Field '{target}' resolved, best_cost={best_cost}")
            return (best_cost, best_tree)

    def resolve_field(self, target: str) -> Tuple[float, ComputationTreeNode]:
        """
        Find the minimal-cost computation tree for `target`.

        Returns `(total_cost, tree)` on success and raises
        `UnresolvableFieldError` if the target cannot be resolved.
        """
        cost, tree = self._resolve_field(target)
        if tree is None:
            raise UnresolvableFieldError(f"Cannot resolve field '{target}'.")
        return cost, tree
