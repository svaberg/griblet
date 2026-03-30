"""
Path representation for resolved graphs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Step:
    """
    One chosen derivation step inside a resolved path.

    Attributes
    ----------
    name:
        Name produced by this step.
    cost:
        Local cost of taking this step.
    needs:
        Child steps that must be evaluated first.
    last_actual_cost:
        Total cost actually paid the last time this step was followed.
    """

    name: str
    cost: float
    step_index: Optional[int] = None
    is_source: bool = False
    needs: List["Step"] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    last_actual_cost: Optional[float] = None

    def _format_lines(self, indent=0):
        """
        Render this step and its dependencies as an indented tree of lines.

        This is the internal formatter used by `__str__`.
        """
        leaf = " [source]" if self.is_source else ""
        desc = self.metadata.get("description", "")
        unit = self.metadata.get("unit", "")
        line = " " * indent + f"{self.name} (cost: {self.cost}){leaf} {desc} {unit}".rstrip()
        lines = [line]
        for need in self.needs:
            lines.extend(need._format_lines(indent + 4))
        return lines

    def __str__(self):
        """Return the subtree rooted at this step as a readable multi-line string."""
        return "\n".join(self._format_lines())


@dataclass
class Path:
    """
    A resolved path with its total cost and root step.

    Attributes
    ----------
    cost:
        Total cost of the chosen path.
    root:
        Root step producing the requested output.
    """

    cost: float
    root: Step

    def __str__(self):
        """
        Return a readable summary of the full path and its total cost.

        The output starts with a one-line header and then shows the step tree.
        """
        return f"Path to {self.root.name} (total cost: {self.cost})\n{self.root}"
