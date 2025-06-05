# griblet

**Distill the optimal computation tree from a field of possibilities.**

Griblet is a dynamic, cache-aware, cost-sensitive calculation engine for building and evaluating optimal computation trees from a graph of possible dependencies and recipes.

- Supports multiple alternative computation paths for each result
- Dynamic costs, including cache- and disk-aware lazy evaluation
- Clean separation of recipes, cache, loader, and evaluation logic
- Suitable for scientific postprocessing, engineering workflows, and flexible data processing pipelines

## Quickstart

Clone and install in editable mode:

```bash
git clone https://github.com/svaberg/griblet.git
cd griblet
pip install -e .
