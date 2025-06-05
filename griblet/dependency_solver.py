from typing import Set, Tuple, Optional
from .computation_tree import ComputationTreeNode

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
        return (best_cost, best_tree)
