import numpy as np
import astropy.units as u

from griblet.computation_graph import ComputationGraph
from griblet.field_cache import FieldCache

def make_room_graph():
    values = {
        'length': np.array([5.0]) * u.m,
        'width': np.array([4.0]) * u.m,
        'height': np.array([3.0]) * u.m,
        'area': np.array([20.0]) * u.m**2,
        'perimeter': np.array([18.0]) * u.m,
        'ceiling_height': np.array([3.0]) * u.m,
    }

    class RoomLoader:
        def load(self, field):
            return values.copy()

    room_loader = RoomLoader()
    cache = FieldCache(room_loader, uncached_cost=50, cached_cost=0.1)
    g = ComputationGraph()

    for field in values:
        g.add_recipe(
            field, [],
            lambda field=field: cache.get(field),
            cost=lambda field=field: cache.cost(field),
            metadata={'description': f'{field} (from file or measurement)', 'unit': values[field].unit}
        )

    def area_from_lw(length, width): return length * width
    g.add_recipe('area', ['length', 'width'], area_from_lw, cost=2.0, metadata={'unit': u.m**2})

    def perim_from_lw(length, width): return 2 * (length + width)
    g.add_recipe('perimeter', ['length', 'width'], perim_from_lw, cost=1.5, metadata={'unit': u.m})

    def length_from_perim_width(perimeter, width): return (perimeter / 2) - width
    g.add_recipe('length', ['perimeter', 'width'], length_from_perim_width, cost=5.0, metadata={'unit': u.m})

    def volume_from_area_height(area, height): return area * height
    g.add_recipe('volume', ['area', 'height'], volume_from_area_height, cost=2.0, metadata={'unit': u.m**3})

    def volume_from_lw_ceil(length, width, ceiling_height): return length * width * ceiling_height
    g.add_recipe('volume', ['length', 'width', 'ceiling_height'], volume_from_lw_ceil, cost=3.0, metadata={'unit': u.m**3})

    return g, cache  # <-- Return cache too for use in the demo
