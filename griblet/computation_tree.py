from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class ComputationTreeNode:
    field: str
    cost: float
    used_primary: bool = False
    deps: List["ComputationTreeNode"] = field(default_factory=list)
    recipe_metadata: Dict = field(default_factory=dict)
    last_actual_cost: Optional[float] = None   # Most recent actual cost only

    def sum_planned_cost(self):
        """Recursively sum the planned (static) cost in the tree."""
        return self.cost + sum(dep.sum_planned_cost() for dep in self.deps)

    def update_actual_cost(self, graph, log_changes=True):
        """
        Recursively compute and store the *actual* cost, based on current cache state.
        Logs a cost change if the value differs from the previous evaluation.
        Returns total actual cost for this subtree.
        """
        # Find matching recipe for this node
        for recipe in graph.recipes[self.field]:
            if [dep.field for dep in self.deps] == recipe['deps']:
                cost_val = recipe['cost']() if callable(recipe['cost']) else recipe['cost']
                break
        else:
            cost_val = self.cost

        child_cost = sum(dep.update_actual_cost(graph, log_changes=log_changes) for dep in self.deps)
        total_actual_cost = cost_val + child_cost

        prev = self.last_actual_cost
        self.last_actual_cost = total_actual_cost
        if log_changes and prev is not None and prev != total_actual_cost:
            print(f"[COST CHANGE] Node '{self.field}': {prev} → {total_actual_cost}")
        return total_actual_cost

    def print_tree(self, indent=0, show_costs=True, show_actual=True):
        """Pretty-print the computation tree, optionally showing costs."""
        leaf = " [primary]" if self.used_primary else ""
        desc = self.recipe_metadata.get('description', '')
        unit = self.recipe_metadata.get('unit', '')
        planned = f"planned: {self.cost}" if show_costs else ""
        actual = (
            f" actual: {self.last_actual_cost}" if show_actual and self.last_actual_cost is not None else ""
        )
        # Only print parentheses if there is planned or actual cost info
        paren = ""
        if planned or actual:
            paren = "(" + planned + actual + ")"
        print(" " * indent + f"{self.field} {paren}{leaf} {desc} {unit}")
        for dep in self.deps:
            dep.print_tree(indent + 4, show_costs=show_costs, show_actual=show_actual)
