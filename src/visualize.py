from typing import Callable
from rdflib import RDFS, Graph
import plotly.graph_objects as go
import networkx as nx
from pathlib import Path
from peps_to_rdf import DEFAULT_NS, SCHEMA_NS
import datetime

GRAPH_COLORS = {
    "green": "#2c7c3c",
    "blue": "#1e40af",
    "lightblue": "#A0D8F1",
    "gray": "#64748b",
    "crimson": "#dc2626",
    "teal": "#0d9488",
    "white": "#FFFFFF",
    "brown": "#A36A00",
    "pink": "#ff13f0",
}

PEP_STATUS_COLORS = {
    "Active": GRAPH_COLORS["green"],
    "Final": GRAPH_COLORS["blue"],
    "Superseded": GRAPH_COLORS["gray"],
    "Rejected": GRAPH_COLORS["crimson"],
    "Draft": GRAPH_COLORS["brown"],
    "Accepted": GRAPH_COLORS["teal"],
    "Deferred": GRAPH_COLORS["pink"],
    "Withdrawn": GRAPH_COLORS["lightblue"],
}

ARROW_STYLES = {
    "color": GRAPH_COLORS.get("white"),
    "width": 2,
    "head_length": 1,
    "opacity": 0.5,
}


def generate_edge_annotations(G: nx.DiGraph, positions: dict, node_sizes: list) -> list:
    """
    Generate a list of edge arrow annotations for nodes in the graph.
    """
    edge_annotations = []
    node_size_map = dict(zip(G.nodes(), node_sizes))

    for edge in G.edges():
        x0, y0 = positions[edge[0]]  # source node
        x1, y1 = positions[edge[1]]  # target node

        target_node_size = node_size_map.get(edge[1])

        edge_annotations.append(
            dict(
                ax=x0,
                ay=y0,
                x=x1,
                y=y1,
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                arrowhead=2,
                arrowsize=ARROW_STYLES["head_length"],
                arrowwidth=ARROW_STYLES["width"],
                arrowcolor=ARROW_STYLES["color"],
                opacity=ARROW_STYLES["opacity"],
                standoff=target_node_size / 2,  # Apply standoff at the target node
            )
        )

    return edge_annotations


def generate_node_click_navigate_to_pep_page(G: nx.DiGraph, positions: dict) -> list:
    """
    Generate a list of annotations for each pep node that navigates to the PEP URL when clicked.
    """
    node_annotations = []
    for node in G.nodes():
        try:
            int(node)
        except ValueError:
            continue
        x, y = positions[node]
        node_annotations.append(
            dict(
                x=x,
                y=y,
                text=f"""<a href="https://peps.python.org/pep-{node}/" target="_blank"> </a>""",
                showarrow=False,
                xanchor="center",
                yanchor="middle",
                font=dict(family="Maple Mono", color="white"),
            )
        )
    return node_annotations


def add_pep_status_legend(fig: go.Figure, modebar_orientation: str = "v") -> None:
    """
    Adds a legend to the Plotly figure for PEP statuses.
    """
    for status, color in PEP_STATUS_COLORS.items():
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(size=10, color=color),
                showlegend=True,
                name=status,
            )
        )
    # Update layout to accommodate legend
    fig.update_layout(
        showlegend=True,
        legend=dict(
            yanchor="bottom",
            y=0.01,
            xanchor="right",
            x=0.99,
            bordercolor="rgba(255, 255, 255, 0.9)",
            bgcolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1,
            font=dict(size=12, family="Maple Mono", color="white"),
            itemclick=False,
        ),
        modebar=dict(
            orientation=modebar_orientation,
            bgcolor="rgba(255, 255, 255, 0.7)",
            color=GRAPH_COLORS["gray"],
            activecolor=GRAPH_COLORS["pink"],
        ),
    )


def visualize_one_peps_authors_contributions(
    data_graph: Graph, pep_id: int = 484
) -> go.Figure:
    """
    Create a visualization of a single PEP with its authors and their contributions.
    By default, visualizes the contributions the authors of PEP 484 made.
    """

    query = f"""
    SELECT DISTINCT ?pepTitle ?pepId ?dateCreated ?status ?type ?authorName
    WHERE {{
        :pep-{pep_id} peps:hasAuthor ?author .
        ?author rdfs:label ?authorName .
        ?pep a peps:PythonEnhancementProposal ;
             peps:hasAuthor ?author ;
             peps:title ?pepTitle ;
             peps:id ?pepId ;
             peps:dateCreated ?dateCreated ;
             peps:status ?status ;
             peps:type ?type .
    }}
    """

    G = nx.DiGraph()
    nodes = set()
    node_colors = []
    node_texts = []
    node_labels = []
    node_sizes = []
    authors = set()

    results = list(
        data_graph.query(
            query, initNs={"": DEFAULT_NS, "peps": SCHEMA_NS, "rdfs": RDFS}
        )
    )

    # print(f"| pepTitle | pepId | dateCreated | status | type | authorName |")
    # print(f"| --- | --- | --- | --- | --- | --- |")
    for row in results:
        author_name = str(row.authorName)
        pep_title = str(row.pepTitle)
        id = str(row.pepId)
        created_date = str(row.dateCreated)
        status = str(row.status)
        pep_type = str(row.type)
        # print(
        #     f"| {pep_title} | {id} | {created_date} | {status} | {pep_type} | {author_name} |"
        # )

        if author_name not in nodes:
            G.add_node(author_name)
            nodes.add(author_name)
            node_colors.append(GRAPH_COLORS["lightblue"])
            node_texts.append(author_name)
            node_labels.append(author_name)
            node_sizes.append(50)
            authors.add(author_name)

        if id not in nodes:
            G.add_node(id)
            nodes.add(id)
            if pep_id == int(id):
                node_colors.append(GRAPH_COLORS["pink"])
            else:
                node_colors.append(GRAPH_COLORS["green"])
            node_texts.append(id)
            node_labels.append(
                f"<em>PEP {id}</em><br>{pep_title}<br>Type: {pep_type}<br>Created: {created_date}<br>Status: {status}"
            )
            node_sizes.append(15)

        G.add_edge(author_name, id)

    pos = nx.spring_layout(G, k=2)

    node_trace = go.Scatter(
        x=[pos[node][0] for node in G.nodes()],
        y=[pos[node][1] for node in G.nodes()],
        mode="markers+text",
        hoverinfo="text",
        text=node_texts,
        hovertext=node_labels,
        textposition="top center",
        textfont=dict(
            family="Maple Mono",
            color="white",
            size=[20 if node in authors else 15 for node in G.nodes()],
        ),
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line_color="white",
        ),
        showlegend=False,
    )

    fig = go.Figure(
        data=[node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            dragmode="pan",
            margin=dict(b=1, l=1, r=1, t=0),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="black",
            annotations=generate_edge_annotations(G, pos, node_sizes)
            + generate_node_click_navigate_to_pep_page(G, pos),
        ),
    )
    fig.update_layout(
        showlegend=True,
        modebar=dict(
            orientation="v",
            bgcolor="rgba(255, 255, 255, 0.7)",
            color=GRAPH_COLORS["gray"],
            activecolor=GRAPH_COLORS["pink"],
        ),
    )

    return fig


def visualize_pep_supersession(data_graph: Graph) -> go.Figure:
    """
    Creates an interactive PEP supersession visualization using Plotly.
    """

    supersession_query = """
    SELECT DISTINCT ?title ?status ?id ?python_version ?date_created ?super_title ?super_status ?super_id ?super_python_version ?super_date_created
    WHERE {
        ?pep peps:supersededBy ?superseded_by ;
            peps:title ?title ;
            peps:status ?status ;
            peps:id ?id ;
            peps:pythonVersion ?python_version ;
            peps:dateCreated ?date_created .
        ?superseded_by peps:title ?super_title ;
            peps:status ?super_status ;
            peps:id ?super_id ;
            peps:pythonVersion ?super_python_version ;
            peps:dateCreated ?super_date_created .
    }
    """

    def format_node_text(
        id: str, title: str, created: str, status: str, python_version: str
    ) -> str:
        """
        Format the hover text for a node in the PEP supersession graph.
        """
        return f"<em>PEP {id}</em><br>{title}<br>Created: {created}<br>Status: {status}<br>Python Version: {python_version}"

    def add_unique_node(
        G: nx.Graph,
        nodes: set[str],
        node_info: dict[str, str],
        node_colors: list[str],
        node_texts: list[str],
        node_labels: list[str],
        node_sizes: list[int],
    ) -> None:
        """
        Add a node to the graph if it doesn't already exist.
        """
        if node_info["id"] not in nodes:
            nodes.add(node_info["id"])
            G.add_node(node_info["id"])
            node_colors.append(PEP_STATUS_COLORS.get(node_info["status"]))
            node_texts.append(
                format_node_text(
                    node_info["id"],
                    node_info["title"],
                    node_info["date_created"],
                    node_info["status"],
                    node_info["python_version"],
                )
            )
            node_labels.append(node_info["id"])
            node_sizes.append(25)

    G = nx.DiGraph()
    nodes = set()
    node_colors = []
    node_texts = []
    node_labels = []
    node_sizes = []

    # print(
    #     "| ?title  | ?status | ?id | ?python_version | ?date_created | ?super_title | ?super_status | ?super_id | ?super_python_version | ?super_date_created |"
    # )
    # print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in data_graph.query(supersession_query, initNs={"peps": SCHEMA_NS}):
        # Prepare node information for the current PEP
        pep_info = {
            "id": str(row.id),
            "status": str(row.status),
            "date_created": str(row.date_created),
            "python_version": str(row.python_version),
            "title": row.title,
        }

        # Prepare node information for the superseding PEP
        super_info = {
            "id": str(row.super_id),
            "status": str(row.super_status),
            "date_created": str(row.super_date_created),
            "python_version": str(row.super_python_version),
            "title": row.super_title,
        }
        # print(
        #     f"| {pep_info.get('title')} | {pep_info.get('status')}| {pep_info.get('id')}| {pep_info.get('python_version')}| {pep_info.get('date_created')}| {super_info.get('title')}| {super_info.get('status')}| {super_info.get('id')}| {super_info.get('python_version')}| {super_info.get('date_created')} |"
        # )

        add_unique_node(
            G, nodes, pep_info, node_colors, node_texts, node_labels, node_sizes
        )
        add_unique_node(
            G, nodes, super_info, node_colors, node_texts, node_labels, node_sizes
        )
        G.add_edge(pep_info["id"], super_info["id"])

    pos = nx.forceatlas2_layout(G, gravity=15)

    node_trace = go.Scatter(
        x=[pos[node][0] for node in G.nodes()],
        y=[pos[node][1] for node in G.nodes()],
        mode="markers+text",
        hoverinfo="text",
        text=node_labels,
        hovertext=node_texts,
        textposition="top center",
        textfont=dict(family="Maple Mono", color="white", size=15),
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line_color="white",
        ),
        showlegend=False,
    )

    fig = go.Figure(
        data=[node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            dragmode="pan",
            margin=dict(b=1, l=1, r=1, t=1),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="black",
            annotations=generate_edge_annotations(G, pos, node_sizes)
            + generate_node_click_navigate_to_pep_page(G, pos),
        ),
    )
    add_pep_status_legend(fig)
    return fig


def visualize_pep_dependencies(data_graph: Graph) -> go.Figure:
    """
    Creates an interactive PEP dependencies visualization using Plotly.
    """

    query = """
    SELECT DISTINCT ?title ?status ?id ?python_version ?date_created ?required_title ?required_status ?required_id ?required_python_version ?required_date_created
    WHERE {
        ?pep peps:requires ?required_by ;
            peps:title ?title ;
            peps:status ?status ;
            peps:id ?id ;
            peps:pythonVersion ?python_version ;
            peps:dateCreated ?date_created .
        ?required_by peps:title ?required_title ;
            peps:status ?required_status ;
            peps:id ?required_id ;
            peps:pythonVersion ?required_python_version ;
            peps:dateCreated ?required_date_created .
    }
    """

    def format_node_text(
        id: str, title: str, created: str, status: str, python_version: str
    ) -> str:
        """
        Format the hover text for a node in the PEP supersession graph.
        """
        return f"<em>PEP {id}</em><br>{title}<br>Created: {created}<br>Status: {status}<br>Python Version: {python_version}"

    def add_unique_node(
        G: nx.Graph,
        nodes: set[str],
        node_info: dict[str, str],
        node_colors: list[str],
        node_texts: list[str],
        node_labels: list[str],
        node_sizes: list[int],
    ) -> None:
        """
        Add a node to the graph if it doesn't already exist.
        """
        if node_info["id"] not in nodes:
            nodes.add(node_info["id"])
            G.add_node(node_info["id"])
            node_colors.append(PEP_STATUS_COLORS.get(node_info["status"]))
            node_texts.append(
                format_node_text(
                    node_info["id"],
                    node_info["title"],
                    node_info["date_created"],
                    node_info["status"],
                    node_info["python_version"],
                )
            )
            node_labels.append(node_info["id"])
            node_sizes.append(25)

    G = nx.DiGraph()
    nodes = set()
    node_colors = []
    node_texts = []
    node_labels = []
    node_sizes = []

    # print(
    #     "| ?title  | ?status | ?id | ?python_version | ?date_created | ?required_title | ?required_status | ?required_id | ?required_python_version | ?required_date_created |"
    # )
    # print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in data_graph.query(query, initNs={"peps": SCHEMA_NS}):
        # Prepare node information for the current PEP
        pep_info = {
            "id": str(row.id),
            "status": str(row.status),
            "date_created": str(row.date_created),
            "python_version": str(row.python_version),
            "title": row.title,
        }

        # Prepare node information for the superseding PEP
        required_info = {
            "id": str(row.required_id),
            "status": str(row.required_status),
            "date_created": str(row.required_date_created),
            "python_version": str(row.required_python_version),
            "title": row.required_title,
        }
        # print(
        #     f"| {pep_info.get('title')} | {pep_info.get('status')}| {pep_info.get('id')}| {pep_info.get('python_version')}| {pep_info.get('date_created')}| {required_info.get('title')}| {required_info.get('status')}| {required_info.get('id')}| {required_info.get('python_version')}| {required_info.get('date_created')} |"
        # )
        #
        add_unique_node(
            G, nodes, pep_info, node_colors, node_texts, node_labels, node_sizes
        )
        add_unique_node(
            G, nodes, required_info, node_colors, node_texts, node_labels, node_sizes
        )
        G.add_edge(pep_info["id"], required_info["id"])

    pos = nx.forceatlas2_layout(G, gravity=15)

    node_trace = go.Scatter(
        x=[pos[node][0] for node in G.nodes()],
        y=[pos[node][1] for node in G.nodes()],
        mode="markers+text",
        hoverinfo="text",
        text=node_labels,
        hovertext=node_texts,
        textposition="top center",
        textfont=dict(family="Maple Mono", color="white"),
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line_color="white",
        ),
        showlegend=False,
    )

    fig = go.Figure(
        data=[node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            dragmode="pan",
            margin=dict(b=1, l=1, r=1, t=1),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="black",
            annotations=generate_edge_annotations(G, pos, node_sizes)
            + generate_node_click_navigate_to_pep_page(G, pos),
        ),
    )
    add_pep_status_legend(fig)
    return fig


def visualize_pep_status_distribution(data_graph: Graph) -> go.Figure:
    """
    Create a pie chart showing the distribution of PEPs by status.
    """
    query = """
    SELECT ?status (COUNT(?pep) AS ?pepCount)
    WHERE {
      ?pep a peps:PythonEnhancementProposal ;
           peps:status ?status .
    }
    GROUP BY ?status
    """

    labels = []
    values = []
    colors = []

    results = list(data_graph.query(query, initNs={"peps": SCHEMA_NS}))

    # print("| status | pepCount |")
    # print("| --- | --- |")
    for row in results:
        # print(f"| {row.status} | {row.pepCount} |")
        color = PEP_STATUS_COLORS.get(str(row.status))
        labels.append(str(row.status))
        colors.append(color)
        values.append(int(row.pepCount))

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.2,
                textfont=dict(family="Maple Mono"),
            )
        ],
        layout=go.Layout(
            plot_bgcolor="black",
            paper_bgcolor="black",
            font=dict(color="white", family="Maple Mono", size=16),
            margin=dict(b=1, l=1, r=1, t=1),
            legend=dict(font=dict(color="white", family="Maple Mono")),
        ),
    )

    fig.update_traces(
        marker=dict(colors=colors, line=dict(color="black", width=2)),
        textinfo="percent+label",
    )

    return fig


def visualize_guidos_peps(data_graph: Graph) -> go.Figure:
    """
    Create a simple timeline of PEPs authored by Guido van Rossum.
    Highlights important PEPs.
    """
    query = """
    SELECT ?dateCreated ?id ?title ?status ?type ?pythonVersion
    WHERE {
      ?pep a peps:PythonEnhancementProposal ;
           peps:dateCreated ?dateCreated ;
           peps:id ?id ;
           peps:title ?title ;
           peps:status ?status ;
           peps:pythonVersion ?pythonVersion ;
           peps:type ?type ;
           peps:hasAuthor ?author.
      ?author rdfs:label "Guido van Rossum".
    }
    ORDER BY ?dateCreated
    """

    dates = []
    pep_labels = []
    marker_sizes = []
    marker_colors = []
    annotations = []

    results = list(data_graph.query(query, initNs={"peps": SCHEMA_NS, "": DEFAULT_NS}))

    peps_to_annotate = {207: -100, 8: 100, 3119: 50, 484: -100, 572: 100, 750: -100}
    # print("| dateCreated | id | title | status | type | pythonVersion |")
    # print("| --- | --- | --- | --- |")
    for row in results:
        # print(
        #     f"| {row.dateCreated} | {row.id} | {row.title} | {row.status} | {row.type} | {row.pythonVersion} |"
        # )
        pep_id = int(row.id)
        date = datetime.datetime.strptime(str(row.dateCreated), "%Y-%m-%d")
        label = f"<em>PEP {pep_id}</em><br>{row.title}<br>Status: {row.status}<br>Type: {row.type}"
        if str(row.pythonVersion) != "None":
            label += f"<br>Python Version: {row.pythonVersion}"

        dates.append(date)
        pep_labels.append(label)
        marker_colors.append(PEP_STATUS_COLORS.get(str(row.status)))

        if pep_id in peps_to_annotate:
            marker_sizes.append(18)
            annotations.append(
                dict(
                    ax=0,
                    ay=peps_to_annotate[pep_id],
                    x=date,
                    y=0,
                    text=f"PEP {pep_id}<br><em>{row.title}</em><br>{row.status}<br>{row.type}<br>{row.dateCreated}",
                    showarrow=True,
                    arrowhead=1,
                    arrowsize=1,
                    arrowcolor="white",
                    font=dict(color="white", size=12, family="Maple Mono"),
                )
            )
        else:
            marker_sizes.append(12)

        # click to navigate to PEP page
        annotations.append(
            dict(
                x=date,
                y=0,
                text=f"""<a href="https://peps.python.org/pep-{pep_id}/" target="_blank"> </a>""",
                showarrow=False,
                xanchor="center",
                yanchor="middle",
                font=dict(family="Maple Mono", color="white"),
            )
        )

    fig = go.Figure(
        data=[
            go.Scatter(
                x=dates,
                y=[0] * len(dates),  # Flat timeline
                mode="markers+lines",
                marker=dict(size=marker_sizes, color=marker_colors),
                line=dict(color="white"),
                text=pep_labels,
                hoverinfo="text",
                showlegend=False,
            )
        ],
        layout=go.Layout(
            height=650,
            xaxis=dict(title="Year", showgrid=False, zeroline=False),
            yaxis=dict(visible=False),  # Hide y-axis
            plot_bgcolor="black",
            paper_bgcolor="black",
            font=dict(color="white", family="Maple Mono", size=16),
            margin=dict(b=1, l=1, r=1, t=1),
            annotations=annotations,
            hovermode="x",
        ),
    )
    add_pep_status_legend(fig, modebar_orientation="h")

    return fig


def generate_visualizations(
    data_graph: Graph,
    output_dir: str,
    visualizers: dict[str, Callable[[Graph], go.Figure]],
) -> None:
    """
    Generate visualizations for the given data graph using the specified visualizers.
    The `visualizers` dictionary should map filenames to visualization functions.
    These visualizations will be saved as HTML files in the specified output directory.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, viz_func in visualizers.items():
        print(f"Generating visualization for {filename}...")
        fig = viz_func(data_graph)
        output_path = output_dir / filename
        fig.write_html(
            output_path,
            full_html=True,
            include_plotlyjs="cdn",
            config={
                "responsive": True,
                "scrollZoom": True,
                "displayModeBar": True,
                "displaylogo": False,
            },
        )
