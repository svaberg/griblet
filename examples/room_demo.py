import numpy as np
import astropy.units as u

from griblet import Graph
from griblet.loader import BaseLoader


class RoomLoader(BaseLoader):
    def __init__(self):
        super().__init__()
        self._fields = {
            'length': np.array([5.0]) * u.m,
            'width': np.array([4.0]) * u.m,
            'height': np.array([3.0]) * u.m,
            'area': np.array([20.0]) * u.m**2,
            'perimeter': np.array([18.0]) * u.m,
        }


def make_room_graph():

    graph = Graph()

    def area_from_lw(length, width): return length * width
    graph.add('area', area_from_lw, needs=['length', 'width'], cost=2.0, metadata={'unit': u.m**2})

    def perim_from_lw(length, width): return 2 * (length + width)
    graph.add('perimeter', perim_from_lw, needs=['length', 'width'], cost=1.5, metadata={'unit': u.m})

    def length_from_perim_width(perimeter, width): return (perimeter / 2) - width
    graph.add('length', length_from_perim_width, needs=['perimeter', 'width'], cost=5.0, metadata={'unit': u.m})

    def volume_from_area_height(area, height): return area * height
    graph.add('volume', volume_from_area_height, needs=['area', 'height'], cost=2.0, metadata={'unit': u.m**3})

    def volume_from_lw_ceil(length, width, height): return length * width * height
    graph.add('volume', volume_from_lw_ceil, needs=['length', 'width', 'height'], cost=3.0, metadata={'unit': u.m**3})

    return graph
