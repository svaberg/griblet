import networkx as nx
import matplotlib.pyplot as plt
import logging
import astropy.units as u
import pytest
logging.basicConfig(level=logging.INFO)

from griblet import ComputationGraph
from griblet import UnresolvableFieldError

from room_demo import make_room_recipes_graph, RoomLoader


def build_graph():
    loader = RoomLoader()
    loader_graph = loader.as_graph()
    computation_graph = ComputationGraph(loader_graph)
    room_recipies_graph = make_room_recipes_graph()
    computation_graph.merge(room_recipies_graph)
    return computation_graph


def test_demo_rerouting_flow():
    computation_graph = build_graph()

    cost1, _tree1 = computation_graph.plan('volume')
    val1 = computation_graph.compute('volume')

    computation_graph.recipes.pop('area', None)
    cost2, _tree2 = computation_graph.plan('volume')
    val2 = computation_graph.compute('volume')

    assert val1.to_value(u.m**3) == pytest.approx([60.0])
    assert val2.to_value(u.m**3) == pytest.approx([60.0])
    assert cost2 > cost1

    computation_graph.recipes.pop('length', None)
    with pytest.raises(UnresolvableFieldError):
        computation_graph.plan('volume')


if __name__ == "__main__":
    computation_graph = build_graph()
    
    # Initial graph with all recipes
    cost1, tree1 = computation_graph.plan('volume')
    val1 = computation_graph.compute('volume')
    print(f"{'volume'}: {val1} (cost: {cost1:.2f})")

    # Remove 'area' recipe and resolve again
    computation_graph.recipes.pop('area', None)
    cost2, tree2 = computation_graph.plan('volume')
    val2 = computation_graph.compute('volume')
    print(f"{'volume'}: {val2} (cost: {cost2:.2f})")

    # Remove 'length' recipe and resolve again
    computation_graph.recipes.pop('length', None)
    try:
        cost3, tree3 = computation_graph.plan('volume')
        val3 = computation_graph.compute('volume')
        print(f"{'volume'}: {val3} (cost: {cost3:.2f})")
        assert False, "Expected UnresolvableFieldError but got a valid result"
    except UnresolvableFieldError as e:
        print(f"Got expected error: {e}")
