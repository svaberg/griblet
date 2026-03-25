"""
Execution of resolved computation trees.

Evaluates a ComputationTreeNode tree against a ComputationGraph by invoking
the selected recipe functions, propagating values bottom-up, and updating
actual (runtime) costs with optional change logging.
"""

def evaluate_tree(node, graph):
    """
    Execute a resolved computation tree node.

    Recursively evaluates dependencies, calls the matching recipe function,
    updates actual costs on each node, and returns the computed value.
    """
    if node.used_primary:
        # Find the zero-argument recipe and get cost (dynamic if callable)
        for recipe in graph.recipes[node.field]:
            if not recipe['deps']:
                cost_val = recipe['cost']() if callable(recipe['cost']) else recipe['cost']
                break
        else:
            raise RuntimeError(f"No zero-dependency recipe for {node.field}")
        prev = node.last_actual_cost
        node.last_actual_cost = cost_val
        if prev is not None and prev != cost_val:
            print(f"[COST CHANGE] Node '{node.field}': {prev} → {cost_val}")
        return recipe['func']()
    # Otherwise, evaluate dependencies and recipe
    values = [evaluate_tree(dep, graph) for dep in node.deps]
    dep_fields = tuple(dep.field for dep in node.deps)
    for recipe in graph.recipes[node.field]:
        if dep_fields == tuple(recipe['deps']):
            cost_val = recipe['cost']() if callable(recipe['cost']) else recipe['cost']
            break
    else:
        raise RuntimeError(f"No matching recipe for {node.field}")
    child_cost = sum(dep.last_actual_cost for dep in node.deps)
    total_cost = cost_val + child_cost
    prev = node.last_actual_cost
    node.last_actual_cost = total_cost
    if prev is not None and prev != total_cost:
        print(f"[COST CHANGE] Node '{node.field}': {prev} → {total_cost}")
    return recipe['func'](*values)
