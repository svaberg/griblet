from collections import defaultdict

class ComputationGraph:
    def __init__(self):
        self.recipes = defaultdict(list)

    def add_recipe(self, output, func, *, deps=None, cost=1.0, metadata=None):
        """
        Add a recipe for how to compute `output`.
        - output: field name
        - deps: list of dependency field names (all required)
        - func: function accepting resolved dependencies in order
        - cost: number or callable (no-arg or with field name)
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
        self.recipes[output].append(recipe)

    def add_loader_fields(self, loader, field_cache):
        """
        Add fields provided by a loader to the computation graph.
        This allows the graph to resolve these fields directly.
        """
        for field in loader.fields():
            self.add_recipe(
                field,
                lambda field=field: field_cache.get(field),
                cost=lambda field=field: field_cache.cost(field),
                metadata={'description': f'Loader'},
            )

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
