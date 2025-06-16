<table>
<tr>
<td><img src="griblet-logo-256.png" alt="griblet logo" width="128"/></td>
<td><h1>griblet</h1></td>
</tr>
</table>


**Carve computation trees from a burl of dependencies.**

Griblet is a dynamic, cache-aware calculation engine for building and evaluating omputation trees from a flexible graph of possible dependencies and recipes.

- Supports alternative computation paths for each result
- Dynamic costs, including cache- and disk-aware lazy evaluation
- Clean separation of recipes, cache, loader, and evaluation logic
- Suitable for scientific postprocessing, engineering workflows, and flexible data rocessing pipelines

## Developer install
```bash
git clone https://github.com/svaberg/griblet.git
cd griblet
pip install -e '.[dev]'
```
## Example

See [`examples/demo_griblet.py`](examples/demo_griblet.py) for a demonstration.

---

