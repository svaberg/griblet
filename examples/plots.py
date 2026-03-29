import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


FIELD_NODE_SIZE = 1600
RECIPE_NODE_SIZE = 450
FIELD_FONT_SIZE = 10
RECIPE_FONT_SIZE = 8
FIELD_EDGE_WIDTH = 2
RECIPE_EDGE_WIDTH = 0
OUT_EDGE_WIDTH = 4
NEED_EDGE_WIDTH = 2.2
X_PADDING = 1.8
Y_PADDING = 1.5


def field_ordinal_levels(comp_graph, direction="out_to_dep"):
    field_graph = nx.DiGraph()
    for out, ways in comp_graph.ways.items():
        field_graph.add_node(out)
        for way in ways:
            if not way["needs"]:
                continue
            for need in way["needs"]:
                field_graph.add_node(need)
                if direction == "out_to_dep":
                    field_graph.add_edge(out, need)
                else:
                    field_graph.add_edge(need, out)

    strongly_connected = list(nx.strongly_connected_components(field_graph))
    component_of = {}
    for index, component in enumerate(strongly_connected):
        for field in component:
            component_of[field] = index

    condensation = nx.DiGraph()
    condensation.add_nodes_from(range(len(strongly_connected)))
    for start, end in field_graph.edges():
        start_component = component_of[start]
        end_component = component_of[end]
        if start_component != end_component:
            condensation.add_edge(start_component, end_component)

    level = {component: 0 for component in condensation.nodes()}
    for component in nx.topological_sort(condensation):
        for successor in condensation.successors(component):
            level[successor] = max(level[successor], level[component] + 1)

    return {field: level[component_of[field]] for field in field_graph.nodes()}


def and_or_graph(computation_graph):
    """
    Build the explicit AND/OR graph for a Graph.
    """
    graph = nx.DiGraph()

    for out, ways in computation_graph.ways.items():
        field_node = ("F", out)
        graph.add_node(field_node, kind="field", field=out, label=out)

        for index, way in enumerate(ways):
            if not way["needs"]:
                continue

            recipe_node = ("R", out, index)
            graph.add_node(
                recipe_node,
                kind="recipe",
                out=out,
                idx=index,
                label=str(index + 1),
            )
            graph.add_edge(field_node, recipe_node, kind="alt")

            for need in way["needs"]:
                need_field = ("F", need)
                graph.add_node(need_field, kind="field", field=need, label=need)
                graph.add_edge(recipe_node, need_field, kind="req")

    return graph


def _and_or_layout(computation_graph, graph):
    levels = field_ordinal_levels(computation_graph, direction="out_to_dep")
    fields_by_level = {}
    for field, level in levels.items():
        fields_by_level.setdefault(level, []).append(field)

    x_gap = 6.0
    y_gap = 3.0
    recipe_x_offset = 2.0
    recipe_y_gap = 1.0

    pos = {}
    for level in sorted(fields_by_level):
        fields = sorted(fields_by_level[level], key=str)
        center = (len(fields) - 1) / 2.0
        for index, field in enumerate(fields):
            pos[("F", field)] = (
                x_gap * level,
                y_gap * (center - index),
            )

    for out, ways in sorted(computation_graph.ways.items(), key=lambda item: str(item[0])):
        field_node = ("F", out)
        if field_node not in pos:
            continue

        plotted_recipe_indices = [
            index
            for index, way in enumerate(ways)
            if way["needs"] and ("R", out, index) in graph
        ]
        if not plotted_recipe_indices:
            continue

        x0, y0 = pos[field_node]
        center = (len(plotted_recipe_indices) - 1) / 2.0
        for offset, recipe_index in enumerate(plotted_recipe_indices):
            pos[("R", out, recipe_index)] = (
                x0 + recipe_x_offset,
                y0 + recipe_y_gap * (center - offset),
            )

    return pos


def _field_nodes(graph):
    return [node for node, data in graph.nodes(data=True) if data["kind"] == "field"]


def _recipe_nodes(graph):
    return [node for node, data in graph.nodes(data=True) if data["kind"] == "recipe"]


def _sorted_recipe_nodes(graph):
    return sorted(_recipe_nodes(graph), key=lambda node: (str(node[1]), node[2]))


def _recipe_color_map(graph):
    palette = plt.cm.tab10.colors
    return {
        recipe: palette[index % len(palette)]
        for index, recipe in enumerate(_sorted_recipe_nodes(graph))
    }


def _field_labels(graph):
    return {
        node: data["label"]
        for node, data in graph.nodes(data=True)
        if data["kind"] == "field"
    }


def _recipe_labels(graph):
    return {
        node: data["label"]
        for node, data in graph.nodes(data=True)
        if data["kind"] == "recipe"
    }


def _display_need_edges(graph, recipe_node):
    return [(need_field, recipe_node) for _, need_field in graph.out_edges(recipe_node)]


def _display_out_edge(recipe_node):
    return [(recipe_node, ("F", recipe_node[1]))]


def _draw_multicolor_edges(
    graph,
    pos,
    ax,
    *,
    edgelist,
    colors,
    width,
    alpha,
    arrowsize,
    connectionstyle,
    min_source_margin,
    min_target_margin,
):
    dash_styles = [
        (0, (6, 6)),
        (6, (6, 6)),
        (3, (6, 6)),
        (9, (6, 6)),
    ]
    for index, color in enumerate(colors):
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=edgelist,
            arrows=True,
            arrowstyle="->",
            arrowsize=arrowsize,
            width=width,
            edge_color=[color],
            style=dash_styles[index % len(dash_styles)],
            connectionstyle=connectionstyle,
            min_source_margin=min_source_margin,
            min_target_margin=min_target_margin,
            alpha=alpha,
            ax=ax,
        )


def _draw_need_edges(
    graph,
    pos,
    ax,
    *,
    recipe_colors,
    recipe_styles=None,
    width=NEED_EDGE_WIDTH,
    alpha=1.0,
    arrowsize=16,
):
    if recipe_styles is None:
        recipe_styles = {}
    for recipe_node in _sorted_recipe_nodes(graph):
        need_edges = _display_need_edges(graph, recipe_node)
        if not need_edges:
            continue
        if isinstance(recipe_colors[recipe_node], list):
            _draw_multicolor_edges(
                graph,
                pos,
                ax,
                edgelist=need_edges,
                colors=recipe_colors[recipe_node],
                width=width,
                alpha=alpha,
                arrowsize=arrowsize,
                connectionstyle="arc3,rad=0.18",
                min_source_margin=20,
                min_target_margin=10,
            )
            continue
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=need_edges,
            arrows=True,
            arrowstyle="->",
            arrowsize=arrowsize,
            width=width,
            edge_color=[recipe_colors[recipe_node]],
            style=recipe_styles.get(recipe_node, "solid"),
            connectionstyle="arc3,rad=0.18",
            min_source_margin=20,
            min_target_margin=10,
            alpha=alpha,
            ax=ax,
        )


def _draw_out_edges(
    graph,
    pos,
    ax,
    *,
    recipe_colors,
    recipe_styles=None,
    width=OUT_EDGE_WIDTH,
    alpha=1.0,
    arrowsize=16,
):
    if recipe_styles is None:
        recipe_styles = {}
    for recipe_node in _sorted_recipe_nodes(graph):
        out_edge = _display_out_edge(recipe_node)
        if isinstance(recipe_colors[recipe_node], list):
            _draw_multicolor_edges(
                graph,
                pos,
                ax,
                edgelist=out_edge,
                colors=recipe_colors[recipe_node],
                width=width,
                alpha=alpha,
                arrowsize=arrowsize,
                connectionstyle="arc3,rad=0.08",
                min_source_margin=10,
                min_target_margin=20,
            )
            continue
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=out_edge,
            arrows=True,
            arrowstyle="->",
            arrowsize=arrowsize,
            width=width,
            edge_color=[recipe_colors[recipe_node]],
            style=recipe_styles.get(recipe_node, "solid"),
            connectionstyle="arc3,rad=0.08",
            min_source_margin=10,
            min_target_margin=20,
            alpha=alpha,
            ax=ax,
        )


def _draw_field_nodes(
    graph,
    pos,
    ax,
    *,
    nodelist=None,
    facecolor="lightgray",
    edgecolor="black",
    linewidth=FIELD_EDGE_WIDTH,
    node_size=FIELD_NODE_SIZE,
):
    if nodelist is None:
        nodelist = _field_nodes(graph)
    if not nodelist:
        return
    nx.draw_networkx_nodes(
        graph,
        pos,
        nodelist=nodelist,
        node_shape="o",
        node_size=node_size,
        node_color=facecolor,
        edgecolors=edgecolor,
        linewidths=linewidth,
        ax=ax,
    )


def _draw_recipe_boxes(
    graph,
    pos,
    ax,
    *,
    recipe_facecolors,
    nodelist=None,
    edgecolor="none",
    linewidth=RECIPE_EDGE_WIDTH,
    node_size=RECIPE_NODE_SIZE,
):
    if nodelist is None:
        nodelist = _sorted_recipe_nodes(graph)
    for recipe_node in nodelist:
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=[recipe_node],
            node_shape="s",
            node_size=node_size,
            node_color=[recipe_facecolors[recipe_node]],
            edgecolors=edgecolor,
            linewidths=linewidth,
            ax=ax,
        )


def _draw_labels(graph, pos, ax):
    nx.draw_networkx_labels(
        graph,
        pos,
        labels=_field_labels(graph),
        font_size=FIELD_FONT_SIZE,
        font_color="black",
        ax=ax,
    )
    nx.draw_networkx_labels(
        graph,
        pos,
        labels=_recipe_labels(graph),
        font_size=RECIPE_FONT_SIZE,
        font_color="black",
        ax=ax,
    )


def _set_axes_limits(pos, ax):
    xs = [xy[0] for xy in pos.values()]
    ys = [xy[1] for xy in pos.values()]
    ax.set_xlim(min(xs) - X_PADDING, max(xs) + X_PADDING)
    ax.set_ylim(min(ys) - Y_PADDING, max(ys) + Y_PADDING)


def _draw_and_or_base(
    computation_graph,
    ax,
    *,
    title,
    field_facecolor,
    field_edgecolor,
    recipe_facecolors,
    edge_recipe_colors=None,
    recipe_styles=None,
    recipe_edgecolor="none",
    recipe_linewidth=RECIPE_EDGE_WIDTH,
    edge_alpha=1.0,
):
    graph = and_or_graph(computation_graph)
    pos = _and_or_layout(computation_graph, graph)
    if edge_recipe_colors is None:
        edge_recipe_colors = recipe_facecolors
    _draw_need_edges(
        graph,
        pos,
        ax,
        recipe_colors=edge_recipe_colors,
        recipe_styles=recipe_styles,
        alpha=edge_alpha,
    )
    _draw_out_edges(
        graph,
        pos,
        ax,
        recipe_colors=edge_recipe_colors,
        recipe_styles=recipe_styles,
        alpha=edge_alpha,
    )
    _draw_field_nodes(
        graph,
        pos,
        ax,
        facecolor=field_facecolor,
        edgecolor=field_edgecolor,
    )
    _draw_recipe_boxes(
        graph,
        pos,
        ax,
        recipe_facecolors=recipe_facecolors,
        edgecolor=recipe_edgecolor,
        linewidth=recipe_linewidth,
    )
    _draw_labels(graph, pos, ax)
    _set_axes_limits(pos, ax)
    ax.set_title(title)
    ax.axis("off")
    return graph, pos


def _collect_path_display_nodes_edges(computation_graph, path):
    nodes = set()
    edges = set()

    def visit(node):
        field_node = ("F", node.name)
        nodes.add(field_node)

        if node.is_source or not node.needs:
            return

        need_names = tuple(need.name for need in node.needs)
        recipe_index = None
        for index, way in enumerate(computation_graph.ways[node.name]):
            if tuple(way["needs"]) == need_names:
                recipe_index = index
                break

        if recipe_index is None:
            raise RuntimeError(f"No AND/OR recipe match for path node {node.name!r}")

        recipe_node = ("R", node.name, recipe_index)
        nodes.add(recipe_node)
        edges.add((recipe_node, field_node))

        for need in node.needs:
            need_field = ("F", need.name)
            edges.add((need_field, recipe_node))
            visit(need)

    visit(path.root)
    return nodes, edges


def plot_and_or_graph(computation_graph, ax, title="Computation graph"):
    graph = and_or_graph(computation_graph)
    recipe_colors = _recipe_color_map(graph)
    graph, pos = _draw_and_or_base(
        computation_graph,
        ax,
        title=title,
        field_facecolor="lightgray",
        field_edgecolor="black",
        recipe_facecolors=recipe_colors,
    )
    return graph, pos


def plot_computation_paths(
    computation_graph,
    trees,
    ax,
    *,
    labels=None,
    colors=None,
    title="Computation paths",
    node_size=FIELD_NODE_SIZE,
    font_size=FIELD_FONT_SIZE,
):
    del node_size, font_size
    graph = and_or_graph(computation_graph)
    path_nodes_edges = [
        _collect_path_display_nodes_edges(computation_graph, tree)
        for tree in trees
    ]

    if colors is None:
        colors = [f"C{index}" for index in range(len(trees))]
    if labels is None:
        labels = [f"Path {index + 1}" for index in range(len(trees))]

    recipe_to_paths = {recipe: set() for recipe in _sorted_recipe_nodes(graph)}
    for path_index, (nodes, _edges) in enumerate(path_nodes_edges):
        for node in nodes:
            if node[0] == "R":
                recipe_to_paths[node].add(path_index)

    highlighted_fields = set()
    for nodes, _edges in path_nodes_edges:
        highlighted_fields.update(node for node in nodes if node[0] == "F")

    shared_box_color = "#f1f1f1"
    displayed_recipe_colors = {}
    displayed_edge_colors = {}
    recipe_styles = {}
    has_shared_recipe = False
    for recipe in _sorted_recipe_nodes(graph):
        path_membership = recipe_to_paths[recipe]
        if not path_membership:
            displayed_recipe_colors[recipe] = "#d9d9d9"
            displayed_edge_colors[recipe] = "#d9d9d9"
            recipe_styles[recipe] = "solid"
        elif len(path_membership) == 1:
            displayed_recipe_colors[recipe] = colors[next(iter(path_membership))]
            displayed_edge_colors[recipe] = colors[next(iter(path_membership))]
            recipe_styles[recipe] = "solid"
        else:
            displayed_recipe_colors[recipe] = shared_box_color
            displayed_edge_colors[recipe] = [
                colors[path_index] for path_index in sorted(path_membership)
            ]
            recipe_styles[recipe] = "solid"
            has_shared_recipe = True

    graph, pos = _draw_and_or_base(
        computation_graph,
        ax,
        title=title,
        field_facecolor="lightgray",
        field_edgecolor="black",
        recipe_facecolors=displayed_recipe_colors,
        edge_recipe_colors=displayed_edge_colors,
        recipe_styles=recipe_styles,
        edge_alpha=0.9,
    )

    _draw_field_nodes(
        graph,
        pos,
        ax,
        nodelist=sorted(highlighted_fields),
        facecolor="white",
        edgecolor="black",
    )
    _draw_labels(graph, pos, ax)
    legend_handles = [
        Line2D([0], [0], color=color, lw=3, label=label)
        for color, label in zip(colors, labels)
    ]
    if has_shared_recipe:
        legend_handles.append(Line2D([0], [0], color="black", lw=3, linestyle="--", label="Shared"))
    if legend_handles:
        ax.legend(handles=legend_handles, loc="upper left")
