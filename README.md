<table>
<tr>
<td><img src="griblet-logo-256.png" alt="griblet logo" width="128"/></td>
<td><h1>griblet</h1></td>
</tr>
</table>


**Carve computation trees from a burl of dependencies.**

Griblet is a dynamic, cache-aware calculation engine for building and evaluating computation trees from a flexible graph of possible dependencies and recipes.

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
## Example

Start by building a graph. The graph below can reach `volume` in two ways: one through `area`, and one directly from `length`, `width`, and `height`.

```python
from griblet import Graph

graph = Graph()

graph.add("length", lambda: 5.0)
graph.add("width", lambda: 4.0)
graph.add("height", lambda: 3.0)

graph.add(
    "area",
    lambda length, width: length * width,
    needs=["length", "width"],
    cost=2.0,
)

graph.add(
    "volume",
    lambda area, height: area * height,
    needs=["area", "height"],
    cost=2.0,
)
graph.add(
    "volume",
    lambda length, width, height: length * width * height,
    needs=["length", "width", "height"],
    cost=3.0,
)

print(graph.compute("volume"))
```

If the graph has no valid path to the requested field, `griblet` raises `NoPathError`.

---
