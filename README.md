<table>
<tr>
<td><img src="griblet-logo-256.png" alt="griblet logo" width="128"/></td>
<td><h1>griblet</h1></td>
</tr>
</table>


**Carve computation trees from a burl of dependencies.**

Griblet is a dynamic, cost-aware pathfinding library for planning computation trees through a flexible graph of possible dependencies and recipes.

- Supports alternative computation paths for each result
- Dynamic costs, including cache- and disk-aware lazy evaluation
- Clean separation of recipes, cache, loader, and evaluation logic
- Suitable for scientific post-processing, engineering workflows, and flexible data processing pipelines

## Developer install
```bash
git clone https://github.com/svaberg/griblet.git
cd griblet
pip install -e '.[dev]'
```

## What it does

Griblet finds the cheapest valid path to a requested result through a graph of alternative computation recipes.

You describe the search space by defining which fields can be loaded directly and which fields can be derived from other fields. Griblet then selects a computation path through that graph and evaluates it.

## Example

```python
from griblet import ComputationGraph


graph = ComputationGraph()

graph.add_recipe("length", lambda: 5.0, deps=[], cost=0.1)
graph.add_recipe("width", lambda: 4.0, deps=[], cost=0.1)
graph.add_recipe("height", lambda: 3.0, deps=[], cost=0.1)

# Area can be derived from the box base.
graph.add_recipe("area", lambda length, width: length * width, deps=["length", "width"], cost=2.0)

# Volume can be computed either from area and height...
graph.add_recipe("volume", lambda area, height: area * height, deps=["area", "height"], cost=2.0)

# ...or directly from the three box dimensions.
graph.add_recipe("volume", lambda length, width, height: length * width * height, deps=["length", "width", "height"], cost=3.0)

value = graph.compute("volume")

print(value)
```

This is where griblet earns its keep: `volume` has more than one valid computation path. The graph chooses the cheapest complete path through the recipe space before evaluation.

## Path inspection

If you want to inspect the selected path:

```python
cost, tree = graph.plan("volume")
print(cost)
print(tree)
```

`graph.plan(...)` returns a `(cost, ComputationTreeNode)` pair.

## Errors

If a target cannot be resolved, griblet raises `UnresolvableFieldError`.

## Advanced API

The graph-centered API should cover the common case:

```python
cost, tree = graph.plan("volume")
print(cost)
print(tree)
```

## Examples

See [`examples/demo_dependency_solver.py`](examples/demo_dependency_solver.py) for the basic solve-and-evaluate flow, [`examples/demo_rerouting.py`](examples/demo_rerouting.py) for path changes when recipes are removed, and [`examples/demo_networkx.py`](examples/demo_networkx.py) for plotting and graph visualization.

---
