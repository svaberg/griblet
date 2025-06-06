from collections import defaultdict

class ComputationGraph:
    def __init__(self, other_graph=None):
        self.recipes = defaultdict(list)
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
        if deps is None:
            deps = []

        recipe = dict(
            deps=list(deps),
            func=func,
            cost=cost,
            metadata=metadata or {},
        )
        self.recipes[field].append(recipe)

    def merge(self, other):
        """
        Merge all recipes from another ComputationGraph into this one (mutating self).
        Returns self for method chaining.
        """
        for field, recipes in other.recipes.items():
            self.recipes[field].extend([r.copy() for r in recipes])
        return self
        
    # def update_all_costs(self, loader):
    #     """
    #     Update costs for all loader fields from the current state of the loader.
    #     TODO this is not used or even working yet.
    #     """
    #     for field, recipe_list in self.recipes.items():
    #         for recipe in recipe_list:
    #             # You may want to check if this recipe is a loader recipe (e.g. by metadata or a flag)
    #             if recipe['metadata'].get('description', '').startswith('Loader'):
    #                 recipe['cost'] = loader.cost(field)


    def list_fields(self):
        return set(self.recipes)

    def list_recipes(self, field):
        return [r['deps'] for r in self.recipes.get(field, [])]

    def describe_field(self, field):
        print(f"{field}:")
        for i, r in enumerate(self.recipes.get(field, []), 1):
            print(f"  Recipe {i}: deps={r['deps']}, cost={r['cost']}, meta={r['metadata']}")

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
