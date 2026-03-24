<table>
<tr>
<td><img src="griblet-logo-256.png" alt="griblet logo" width="128"/></td>
<td><h1>griblet</h1></td>
</tr>
</table>

The griblet knows the best path to data inside a graph.
- It thrives where there are multiple, looping paths.
- It can take cache and disk state into account.
- It works well for scientific post-processing.

## Installation
Install `griblet` in the usual way:

```bash
pip install griblet
```

The `griblet` package has no runtime dependencies.

## Example

To use `griblet`, build a data graph. Each call to `graph.add(...)` adds one path by which data can be reached. The first three calls add `length`, `width`, and `height` directly. The later calls add two different paths to `volume`: one through `area`, and one directly from `length`, `width`, and `height`. 

```python
from griblet import Graph

graph = Graph()

graph.add("length", lambda: 5.0)
graph.add("width", lambda: 4.0)
graph.add("height", lambda: 3.0)

graph.add("area", lambda length, width: length * width,
          needs=["length", "width"], cost=2.0)

graph.add("volume", lambda area, height: area * height,
          needs=["area", "height"], cost=2.0)
graph.add("volume", lambda length, width, height: length * width * height,
          needs=["length", "width", "height"], cost=3.0)

print(graph.compute("volume"))
```

When `graph.compute("volume")` is called, the griblet follows the better path and computes it.

If the graph has no path to the requested data, `griblet` raises `NoPathError`.

## Further Examples

The files in [`examples/`](examples/) showcase larger graphs and more realistic use.

---
