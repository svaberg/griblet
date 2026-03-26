<table>
<tr>
<td><img src="https://raw.githubusercontent.com/svaberg/griblet/master/griblet-logo-256.png" alt="griblet logo" width="128"/></td>
<td><h1>griblet</h1></td>
</tr>
</table>

**Carve computation trees from a burl of dependencies.**

Griblet builds and evaluates computation trees from a graph with more than one way to reach each field.

- more than one path to a result
- dynamic cost, including cache-aware and loader-aware evaluation
- suitable for scientific post-processing and derived quantities

## Installation

Install `griblet` in the usual way:

```bash
pip install griblet
```

The `griblet` package has no runtime dependencies.

## Example

Start by building a computation graph. The graph below can reach `volume` in two ways: one through `area`, and one directly from `length`, `width`, and `height`.

```python
from griblet import ComputationGraph, DependencySolver, evaluate_tree

graph = ComputationGraph()

graph.add_recipe("length", lambda: 5.0)
graph.add_recipe("width", lambda: 4.0)
graph.add_recipe("height", lambda: 3.0)

graph.add_recipe(
    "area",
    lambda length, width: length * width,
    deps=["length", "width"],
    cost=2.0,
)

graph.add_recipe(
    "volume",
    lambda area, height: area * height,
    deps=["area", "height"],
    cost=2.0,
)
graph.add_recipe(
    "volume",
    lambda length, width, height: length * width * height,
    deps=["length", "width", "height"],
    cost=3.0,
)

solver = DependencySolver(graph)
cost, tree = solver.resolve_field("volume")
value = evaluate_tree(tree, graph)

print(cost)
print(value)
```

If the graph has no valid path to the requested field, `griblet` raises `UnresolvableFieldError`.
