import numpy as np
import pint

from griblet import Graph
from griblet.loader import BaseLoader

ureg = pint.UnitRegistry()


class BoxLoader(BaseLoader):
    def __init__(self):
        super().__init__()
        self._fields = {
            'length': np.array([5.0]) * ureg.meter,
            'width': np.array([4.0]) * ureg.meter,
            'height': np.array([3.0]) * ureg.meter,
            'area': np.array([20.0]) * ureg.meter**2,
        }


def make_box_graph():
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
