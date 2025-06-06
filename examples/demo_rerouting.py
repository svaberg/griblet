import networkx as nx
import matplotlib.pyplot as plt
import logging
logging.basicConfig(level=logging.DEBUG)

from griblet.computation_graph import ComputationGraph
from griblet.dependency_solver import DependencySolver

from room_demo import add_room_recipes, RoomLoader


if __name__ == "__main__":

    computation_graph = ComputationGraph()
    loader = RoomLoader()
    computation_graph.add_loader_fields(loader)
    add_room_recipes(computation_graph)
    
    # This works
    solver = DependencySolver(computation_graph)
    cost1, tree1 = solver.resolve_field('volume')

    # This fails
    computation_graph.recipes.pop('area', None)
    solver2 = DependencySolver(computation_graph)
    cost2, tree2 = solver2.resolve_field('volume')
