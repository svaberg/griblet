from typing import Set, Tuple, Optional
from .computation_tree import ComputationTreeNode

class UnresolvableFieldError(Exception):
    """Raised when a computation field cannot be resolved."""
    pass

class FallbackResolutionFailed(Exception):
    pass


class DependencySolver:
    def __init__(self, graph):
        self.graph = graph
        self.memo = {}

    def resolve_field(self, target: str, path=None) -> Tuple[float, Optional[ComputationTreeNode]]:
        """
        Find the minimal-cost computation tree for `target`.
        Returns (total_cost, ComputationTreeNode or None if impossible).
        """
        if path is None:
            path = set()
        if target in path:
            return (float("inf"), None)  # cycle detected

        memo_key = target
        if memo_key in self.memo:
            return self.memo[memo_key]

        best_cost = float("inf")
        best_tree = None
        path.add(target)
        for recipe in self.graph.recipes.get(target, []):
            deps = recipe['deps']
            subtrees = []
            fail = False
            total = recipe['cost']() if callable(recipe['cost']) else recipe['cost']
            for dep in deps:
                dep_cost, dep_tree = self.resolve_field(dep, path)
                if dep_cost == float("inf") or dep_tree is None:
                    fail = True
                    break
                total += dep_cost
                subtrees.append(dep_tree)
            if not fail and total < best_cost:
                best_cost = total
                best_tree = ComputationTreeNode(
                    field=target,
                    cost=recipe['cost']() if callable(recipe['cost']) else recipe['cost'],
                    used_primary=(len(deps) == 0),
                    deps=subtrees,
                    recipe_metadata=recipe.get('metadata', {})
                )
        path.remove(target)
        self.memo[memo_key] = (best_cost, best_tree)
        
        if best_tree is None:
            raise UnresolvableFieldError(f"Cannot resolve field '{target}'")
        
        return (best_cost, best_tree)


class PenaltyDependencySolver(DependencySolver):
    """Dependency solver that penalizes missing dependencies to force fallback paths."""

    def penalize_missing_recipes(self, missing_fields, huge_cost=1e30):
        for field, recipes in self.graph.recipes.items():
            for recipe in recipes:
                if any(dep in missing_fields for dep in recipe['deps']):
                    recipe['cost'] = huge_cost

    def resolve_with_penalty(self, target, max_attempts=3, huge_cost=1e30):
        last_missing = set()
        for attempt in range(max_attempts):
            self.memo.clear()
            try:
                cost, tree = self.resolve_field(target)
                return cost, tree
            except UnresolvableFieldError as err:
                import re
                missing = set(re.findall(r"'([^']+)'", str(err)))
                if not missing or missing == last_missing:
                    break
                self.penalize_missing_recipes(missing, huge_cost=huge_cost)
                last_missing = missing
        raise FallbackResolutionFailed(
            f"Could not resolve '{target}' after {max_attempts} penalty attempts; last missing fields: {last_missing}"
        )
