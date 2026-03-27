"""
Path representation for resolved graphs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PathNode:
    """
    One node in a chosen path.
    """

    name: str
    cost: float
    is_source: bool = False
    needs: List["PathNode"] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    last_actual_cost: Optional[float] = None

    def _format_lines(self, indent=0, show_costs=True, show_actual=True):
        leaf = " [source]" if self.is_source else ""
        desc = self.metadata.get("description", "")
        unit = self.metadata.get("unit", "")
        planned = f"planned: {self.cost}" if show_costs else ""
        actual = (
            f" actual: {self.last_actual_cost}" if show_actual and self.last_actual_cost is not None else ""
        )
        paren = ""
        if planned or actual:
            paren = "(" + planned + actual + ")"
        line = " " * indent + f"{self.name} {paren}{leaf} {desc} {unit}".rstrip()
        lines = [line]
        for need in self.needs:
            lines.extend(need._format_lines(indent + 4, show_costs=show_costs, show_actual=show_actual))
        return lines

    def __str__(self):
        return "\n".join(self._format_lines())

    def __repr__(self):
        return f"PathNode(name={self.name!r}, cost={self.cost!r}, needs={len(self.needs)})"
