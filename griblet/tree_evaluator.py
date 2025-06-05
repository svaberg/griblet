def evaluate_tree(node, graph):
    """Evaluate the computation tree node, and update/log actual cost."""
    if node.used_primary:
        # Find the zero-argument recipe and get cost (dynamic if callable)
        for recipe in graph.recipes[node.field]:
            if recipe['deps'] == []:
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
    for recipe in graph.recipes[node.field]:
        if [dep.field for dep in node.deps] == recipe['deps']:
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
