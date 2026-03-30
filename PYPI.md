<table>
<tr>
<td><img src="https://raw.githubusercontent.com/svaberg/griblet/master/griblet-logo-256.png" alt="griblet logo" width="128"/></td>
<td><h1>griblet</h1></td>
</tr>
</table>

[![PyPI](https://img.shields.io/badge/PyPI-griblet-blue)](https://pypi.org/project/griblet/) [![Version](https://img.shields.io/pypi/v/griblet)](https://pypi.org/project/griblet/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![DOI](https://zenodo.org/badge/996606023.svg)](https://doi.org/10.5281/zenodo.19239863) [![Codacy Badge](https://app.codacy.com/project/badge/Grade/0a9aa6e148d845a780466a718a1f96b6)](https://app.codacy.com/gh/svaberg/griblet/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

The griblet knows the easiest path through your data.

- It thrives where there are multiple, looping paths.
- It can account for cache and disk state.
- It loves scientific post-processing.

## Installation

Install `griblet` in the usual way:

```bash
pip install griblet
```

The `griblet` has no runtime dependencies.

## Example

Start by describing common computational paths in your data. For example, below one can compute `volume` via two paths: via `area`, and directly from `length`, `width`, and `height`.

```python
from griblet import Graph

graph = Graph()

graph.add("length", lambda: 5.0)
graph.add("width", lambda: 4.0)
graph.add("height", lambda: 3.0)

graph.add(
    "area",
    lambda length, width: length * width,
    needs=("length", "width"),
    cost=2.0,
)

graph.add(
    "volume",
    lambda area, height: area * height,
    needs=("area", "height"),
    cost=2.0,
)
graph.add(
    "volume",
    lambda length, width, height: length * width * height,
    needs=("length", "width", "height"),
    cost=3.0,
)

print(graph.compute("volume"))
```

The griblet finds the easiest path.

The griblet is okay with disconnected graphs; when there is no path to the requested field, `griblet` raises `NoPathError`. The user can then consider adding further computational paths with `graph.add`.
