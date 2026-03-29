"""
Path representation for resolved graphs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Step:
    """
    One step in a chosen path.
    """

    name: str
    cost: float
    way_index: Optional[int] = None
    is_source: bool = False
    needs: List["Step"] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    last_actual_cost: Optional[float] = None

    def _format_lines(self, indent=0):
        leaf = " [source]" if self.is_source else ""
        desc = self.metadata.get("description", "")
        unit = self.metadata.get("unit", "")
        line = " " * indent + f"{self.name} (cost: {self.cost}){leaf} {desc} {unit}".rstrip()
        lines = [line]
        for need in self.needs:
            lines.extend(need._format_lines(indent + 4))
        return lines

    def __str__(self):
        return "\n".join(self._format_lines())


@dataclass
class Path:
    """
    A chosen path through the graph.
    """

    cost: float
    root: Step

    def __str__(self):
        return f"Path to {self.root.name} (total cost: {self.cost})\n{self.root}"
