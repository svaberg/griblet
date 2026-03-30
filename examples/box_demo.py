"""Small box-geometry example used by the demo scripts and tests."""

import json
from pathlib import Path

import numpy as np
import pint

from griblet import Graph
from griblet.cache import Cache
from griblet.loader import Loader

ureg = pint.UnitRegistry()


class BoxLoader(Loader):
    """Load primitive box fields from the example JSON data file."""

    def __init__(self):
        super().__init__()
        raw_fields = json.loads(Path(__file__).with_name("box_data.json").read_text())
        self._fields = {
            name: np.array(spec["value"]) * ureg(spec["unit"])
            for name, spec in raw_fields.items()
        }


def make_box_graph():
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


def build_box_graph():
    """Build the full box example graph with cached loader-backed sources."""
    graph = make_box_graph()
    Cache(graph, BoxLoader(), cached_cost=0.05)
    return graph
