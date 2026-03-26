import numpy as np
import pint

from griblet import ComputationGraph
from griblet import BaseLoader

ureg = pint.UnitRegistry()


class RoomLoader(BaseLoader):
    def __init__(self):
        super().__init__()
        self._fields = {
            'length': np.array([5.0]) * ureg.meter,
            'width': np.array([4.0]) * ureg.meter,
            'height': np.array([3.0]) * ureg.meter,
            'area': np.array([20.0]) * ureg.meter**2,
            'perimeter': np.array([18.0]) * ureg.meter,
        }


def make_room_recipes_graph():

    cg = ComputationGraph()

    def area_from_lw(length, width): return length * width
    cg.add_recipe('area', area_from_lw, deps=['length', 'width'], cost=2.0, metadata={'unit': ureg.meter**2})

    def perim_from_lw(length, width): return 2 * (length + width)
    cg.add_recipe('perimeter', perim_from_lw, deps=['length', 'width'], cost=1.5, metadata={'unit': ureg.meter})

    def length_from_perim_width(perimeter, width): return (perimeter / 2) - width
    cg.add_recipe('length', length_from_perim_width, deps=['perimeter', 'width'], cost=5.0, metadata={'unit': ureg.meter})

    def volume_from_area_height(area, height): return area * height
    cg.add_recipe('volume', volume_from_area_height, deps=['area', 'height'], cost=2.0, metadata={'unit': ureg.meter**3})

    def volume_from_lw_ceil(length, width, height): return length * width * height
    cg.add_recipe('volume', volume_from_lw_ceil, deps=['length', 'width', 'height'], cost=3.0, metadata={'unit': ureg.meter**3})

    return cg
