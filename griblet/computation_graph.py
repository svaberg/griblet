from collections import defaultdict

class ComputationGraph:
    def __init__(self):
        self.recipes = defaultdict(list)

    def add_recipe(self, output, deps, func, cost=1.0, metadata=None):
        """
        Add a recipe for how to compute `output`.
        - output: field name
        - deps: list of dependency field names (all required)
        - func: function accepting resolved dependencies in order
        - cost: number or callable (no-arg or with field name)
        - metadata: optional dict with other info
        """
        recipe = dict(
            deps=list(deps),
            func=func,
            cost=cost,
            metadata=metadata or {},
        )
        self.recipes[output].append(recipe)

    def list_fields(self):
        return set(self.recipes)

    def list_recipes(self, field):
        return [r['deps'] for r in self.recipes.get(field, [])]

    def describe_field(self, field):
        print(f"{field}:")
        for i, r in enumerate(self.recipes.get(field, []), 1):
            print(f"  Recipe {i}: deps={r['deps']}, cost={r['cost']}, meta={r['metadata']}")
