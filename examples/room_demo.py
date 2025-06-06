import numpy as np
import astropy.units as u

from griblet.computation_graph import ComputationGraph
from griblet.field_cache import FieldCache


class RoomLoader:

    _fields = {
        'length': np.array([5.0]) * u.m,
        'width': np.array([4.0]) * u.m,
        'height': np.array([3.0]) * u.m,
        'area': np.array([20.0]) * u.m**2,
        'perimeter': np.array([18.0]) * u.m,
    }

    def load(self, field):
        return self._fields.copy()
    
    def fields(self):
        return list(self._fields.keys())


def add_room_recipes(computation_graph):

    def area_from_lw(length, width): return length * width
    computation_graph.add_recipe('area', area_from_lw, deps=['length', 'width'], cost=2.0, metadata={'unit': u.m**2})

    def perim_from_lw(length, width): return 2 * (length + width)
    computation_graph.add_recipe('perimeter', perim_from_lw, deps=['length', 'width'], cost=1.5, metadata={'unit': u.m})

    def length_from_perim_width(perimeter, width): return (perimeter / 2) - width
    computation_graph.add_recipe('length', length_from_perim_width, deps=['perimeter', 'width'], cost=5.0, metadata={'unit': u.m})

    def volume_from_area_height(area, height): return area * height
    computation_graph.add_recipe('volume', volume_from_area_height, deps=['area', 'height'], cost=2.0, metadata={'unit': u.m**3})

    def volume_from_lw_ceil(length, width, ceiling_height): return length * width * ceiling_height
    computation_graph.add_recipe('volume', volume_from_lw_ceil, deps=['length', 'width', 'height'], cost=3.0, metadata={'unit': u.m**3})
