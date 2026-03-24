"""
Declarative dependency graph for field-based computations.

Defines a computation graph that records how fields can be computed from
other fields via alternative recipes, each with dependencies and cost.
The graph is descriptive only.
"""

class ComputationGraph:
    """
    Registry of alternative recipes for computing named fields.
    Stores, but does not execute, dependency relationships between fields.
    Each field may have multiple recipes with associated costs and metadata.
    """
    def __init__(self, other_graph=None):
        self.recipes = {}
        if other_graph is not None:
            self.merge(other_graph)

    def add_recipe(self, field, func, *, deps=None, cost=1.0, metadata=None):
        """
        Add a recipe for how to compute `field`.
        - field: field name of this recipe's output (e.g. 'volume')
        - func: function that computes the output from its dependencies
        - deps: list of dependency field names (e.g. ['length', 'width'])
        - cost: fixed cost to compute this field (or a callable that returns the cost)
        - metadata: optional dict with other info
        """
        recipe = {
            "deps": tuple(deps or ()),
            "func": func,
            "cost": cost,
            "metadata": dict(metadata or {}),
        }
        self.recipes.setdefault(field, []).append(recipe)

    def merge(self, other):
        """
        Merge all recipes from another ComputationGraph into this one (mutating self).
        Returns self for method chaining.
        """
        for field, recipes in other.recipes.items():
            self.recipes.setdefault(field, []).extend(recipes)
        return self

    def plan(self, target):
        """
        Return the cheapest computation path for `target`.
        """
        from .dependency_solver import DependencySolver

        return DependencySolver(self).resolve_field(target)

    def compute(self, target):
        """
        Compute `target` by planning and evaluating the cheapest path.
        """
        from .evaluate_tree import evaluate_tree

        _, tree = self.plan(target)
        return evaluate_tree(tree, self)
      
    def list_fields(self):
        return set(self.recipes)

    def list_recipes(self, field):
        return [r['deps'] for r in self.recipes.get(field, [])]

    def __str__(self):
        lines = []
        for field in sorted(self.recipes):
            lines.append(f"{field}:")
            for i, r in enumerate(self.recipes[field], 1):
                cost_str = r['cost'] if isinstance(r['cost'], (int, float)) else "callable"
                meta = r['metadata'] or {}
                meta_str = ', '.join(f"{k}={v}" for k, v in meta.items())
                lines.append(
                    f"  Recipe {i}: deps={r['deps']}, cost={cost_str}"
                    + (f", meta={meta_str}" if meta_str else "")
                )
        return "\n".join(lines)

    __repr__ = __str__
