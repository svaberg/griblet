"""Recursive path representation for resolved graphs."""

from dataclasses import dataclass, field
from typing import Callable, Dict, List


@dataclass
class Path:
    """
    One resolved path node together with the subpaths it depends on.

    A leaf path is still a Path: it simply has no child paths in `needs`.

    Attributes
    ----------
    name:
        Name produced at this node.
    cost:
        Total declared cost of this path, including all child paths.
    func:
        Callable used to compute this node once its child paths are available.
    needs:
        Child paths that must be evaluated first.
    """

    name: str
    cost: float
    func: Callable
    needs: List["Path"] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def _format_lines(self, indent=0):
        """
        Render this path and its dependencies as an indented tree of lines.

        This is the internal formatter used by `__str__`.
        """
        meta_str = ", ".join(f"{key}={value}" for key, value in self.metadata.items())
        line = " " * indent + f"{self.name} (cost: {self.cost})"
        if meta_str:
            line += f", meta={{{meta_str}}}"
        lines = [line]
        for need in self.needs:
            lines.extend(need._format_lines(indent + 4))
        return lines

    def __str__(self):
        """
        Return a readable summary of the full path and its total cost.

        The output starts with a one-line header and then shows the path tree.
        """
        return f"Path to {self.name} (total cost: {self.cost})\n" + "\n".join(self._format_lines())
