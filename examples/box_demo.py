"""Small box-geometry example used by the demo scripts and tests."""

import json
from pathlib import Path

import pint

from griblet import Graph
from griblet.loader import Loader

ureg = pint.UnitRegistry()
BOX_DATA_PATH = Path(__file__).with_name("box_data.json")


class BoxLoader(Loader):
    """
    Load one requested box field at a time from the example JSON file.

    This loader is intentionally plain rather than optimized. It reads the
    JSON once in `__init__` to discover which fields exist, but it does not
    keep the field values resident. Each `load(field)` call rereads the file,
    extracts one field, and discards the rest. That keeps this example focused
    on what an ordinary file-backed loader looks like, in contrast to a block
    loader that keeps many fields resident after one read.
    """

    def __init__(self):
        super().__init__()
        self._fields = dict.fromkeys(json.loads(BOX_DATA_PATH.read_text()))

    def load(self, field):
        """
        Read the JSON file, extract one requested field, and discard the rest.

        This is deliberate example behavior, not an optimized access pattern.
        """
        if field not in self._fields:
            raise ValueError(f"Field '{field}' not found.")
        spec = json.loads(BOX_DATA_PATH.read_text())[field]
        return spec["value"] * ureg(spec["unit"])


def box_graph():
    """Build the derived box-geometry graph without any source data."""
    graph = Graph()

    def area_from_lw(length, width): return length * width
    graph.add('area', area_from_lw, needs=['length', 'width'], cost=2.0, metadata={'unit': ureg.meter**2})

    def base_perimeter(length, width): return 2 * (length + width)
    graph.add('base_perimeter', base_perimeter, needs=['length', 'width'], cost=1.5, metadata={'unit': ureg.meter})

    def linear_size(length, width, height): return length + width + height
    graph.add('linear_size', linear_size, needs=['length', 'width', 'height'], cost=1.0, metadata={'unit': ureg.meter})

    def volume_from_area_height(area, height): return area * height
    graph.add('volume', volume_from_area_height, needs=['area', 'height'], cost=2.0, metadata={'unit': ureg.meter**3})

    def volume_from_lwh(length, width, height): return length * width * height
    graph.add('volume', volume_from_lwh, needs=['length', 'width', 'height'], cost=3.0, metadata={'unit': ureg.meter**3})

    return graph


if __name__ == "__main__":
    loader = BoxLoader()
    print("\n=== Loader ===\n")
    print(loader)

    loader_graph = loader.as_graph()
    print("\n=== Loader Graph ===\n")
    print(loader_graph)

    derived_graph = box_graph()
    print("\n=== Derived Graph ===\n")
    print(derived_graph)

    graph = Graph()
    graph.merge(loader_graph)
    graph.merge(derived_graph)
    print("\n=== Full Graph ===\n")
    print(graph)

    path = graph.path("volume")
    print("\n=== Best Path to volume ===\n")
    print(path)

    volume = graph.compute("volume")
    base_perimeter = graph.compute("base_perimeter")
    linear_size = graph.compute("linear_size")

    print("\n=== Computed Values ===\n")
    print("volume:", volume)
    print("base_perimeter:", base_perimeter)
    print("linear_size:", linear_size)
