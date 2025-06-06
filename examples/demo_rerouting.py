import networkx as nx
import matplotlib.pyplot as plt
import logging
logging.basicConfig(level=logging.INFO)

from griblet.computation_graph import ComputationGraph
from griblet.dependency_solver import DependencySolver
from griblet.evaluate_tree import evaluate_tree

from room_demo import add_room_recipes, RoomLoader


if __name__ == "__main__":

    computation_graph = ComputationGraph()
    loader = RoomLoader()
    computation_graph.add_loader_fields(loader)
    add_room_recipes(computation_graph)
    
    # Initial graph with all recipes
    solver = DependencySolver(computation_graph)
    cost1, tree1 = solver.resolve_field('volume')
    val1 = evaluate_tree(tree1, computation_graph)
    print(f"{'volume'}: {val1} (cost: {cost1})")

    # Remove 'area' recipe and resolve again
    computation_graph.recipes.pop('area', None)
    solver2 = DependencySolver(computation_graph)
    cost2, tree2 = solver2.resolve_field('volume')
    val2 = evaluate_tree(tree2, computation_graph)
    print(f"{'volume'}: {val2} (cost: {cost2})")

    # Remove 'length' recipe and resolve again
    computation_graph.recipes.pop('length', None)
    solver3 = DependencySolver(computation_graph)
    cost3, tree3 = solver3.resolve_field('volume')
    val3 = evaluate_tree(tree3, computation_graph)
    print(f"{'volume'}: {val3} (cost: {cost3})")