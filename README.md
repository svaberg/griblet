# griblet

**Carve computation trees from a burl of dependencies.**

Griblet is a dynamic, cache-aware calculation engine for building and evaluating omputation trees from a flexible graph of possible dependencies and recipes.

- Supports alternative computation paths for each result
- Dynamic costs, including cache- and disk-aware lazy evaluation
- Clean separation of recipes, cache, loader, and evaluation logic
- Suitable for scientific postprocessing, engineering workflows, and flexible data rocessing pipelines

## Quickstart

Clone and install in editable mode:

```bash
git clone https://github.com/svaberg/griblet.git
cd griblet
pip install -e .
```

## Example

See [`examples/demo_griblet.py`](examples/demo_griblet.py) for a demonstration.

---

