"""
Computation tree representation for resolved dependency graphs.

Defines a tree node that records a chosen recipe for a field, its planned
(static) cost, and optional runtime (actual) cost. Supports cost aggregation,
re-evaluation against a graph, and human-readable tree printing.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict


logger = logging.getLogger(__name__)

@dataclass
class ComputationTreeNode:
    """
    Node in a resolved computation tree.

    Represents one field resolved via a specific recipe, with references to
    dependency nodes, planned cost, optional actual cost, and recipe metadata.
    """
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
        dep_fields = tuple(dep.field for dep in self.deps)
        for recipe in graph.recipes[self.field]:
            if dep_fields == recipe['deps']:
                cost_val = recipe['cost']() if callable(recipe['cost']) else recipe['cost']
                break
        else:
            cost_val = self.cost

        child_cost = sum(dep.update_actual_cost(graph, log_changes=log_changes) for dep in self.deps)
        total_actual_cost = cost_val + child_cost

        prev = self.last_actual_cost
        self.last_actual_cost = total_actual_cost
        if log_changes and prev is not None and prev != total_actual_cost:
            logger.info("Cost change for %s: %s -> %s", self.field, prev, total_actual_cost)
        return total_actual_cost

    def _format_lines(self, indent=0, show_costs=True, show_actual=True):
        leaf = " [primary]" if self.used_primary else ""
        desc = self.recipe_metadata.get('description', '')
        unit = self.recipe_metadata.get('unit', '')
        planned = f"planned: {self.cost}" if show_costs else ""
        actual = (
            f" actual: {self.last_actual_cost}" if show_actual and self.last_actual_cost is not None else ""
        )
        paren = ""
        if planned or actual:
            paren = "(" + planned + actual + ")"
        line = " " * indent + f"{self.field} {paren}{leaf} {desc} {unit}".rstrip()
        lines = [line]
        for dep in self.deps:
            lines.extend(dep._format_lines(indent + 4, show_costs=show_costs, show_actual=show_actual))
        return lines

    def __str__(self):
        return "\n".join(self._format_lines())

    def __repr__(self):
        return f"ComputationTreeNode(field={self.field!r}, cost={self.cost!r}, deps={len(self.deps)})"
