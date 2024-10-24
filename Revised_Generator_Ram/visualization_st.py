import streamlit as st
import networkx as nx
import plotly.graph_objects as go
from typing import Dict, Optional, Any
import colorsys
import main as m


def generate_distinct_colors(n: int) -> list:
    """Generate n visually distinct colors"""
    colors = []
    for i in range(n):
        hue = i / n
        saturation = 0.7
        value = 0.9
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        colors.append(f'rgb({int(rgb[0] * 255)},{int(rgb[1] * 255)},{int(rgb[2] * 255)})')
    return colors


def visualize_network(
        G: nx.Graph,
        node_color_attribute: Optional[str] = None,
        custom_color_map: Optional[Dict[Any, str]] = None,
        layout_algorithm: str = "layout_kamada_kawai",
        title: str = "Network Visualization"
) -> None:
    """
    Create an interactive network visualization in Streamlit.

    Parameters:
    -----------
    G : networkx.Graph
        The NetworkX graph to visualize
    node_color_attribute : str, optional
        Node attribute to use for coloring nodes
    custom_color_map : dict, optional
        Mapping of node attribute values to colors
    layout_algorithm : str
        The layout algorithm to use
    title : str
        Title of the visualization
    """

    # Layout algorithms dictionary
    layout_algorithms = {
        "layout_kamada_kawai": nx.kamada_kawai_layout,
        "layout_spring": nx.spring_layout,
        "layout_circular": nx.circular_layout,
        "layout_shell": nx.shell_layout,
        "layout_spiral": nx.spiral_layout,
        "layout_spectral": nx.spectral_layout,
        "layout_multipartite": lambda G: nx.multipartite_layout(G) if hasattr(G,
                                                                              "graph") and "subset" in G.graph else nx.spring_layout(
            G)
    }

    # Get the layout function
    layout_func = layout_algorithms.get(layout_algorithm, nx.spring_layout)

    # Calculate node positions
    pos = layout_func(G)

    # Prepare node colors
    node_colors = []
    color_legend_data = []

    if node_color_attribute and node_color_attribute in next(iter(G.nodes(data=True)))[1]:
        # Get unique values for the color attribute
        unique_values = set(nx.get_node_attributes(G, node_color_attribute).values())

        # Generate or use custom colors
        if custom_color_map:
            color_mapping = custom_color_map
        else:
            distinct_colors = generate_distinct_colors(len(unique_values))
            color_mapping = dict(zip(unique_values, distinct_colors))

        # Assign colors to nodes
        node_colors = [color_mapping[G.nodes[node][node_color_attribute]]
                       for node in G.nodes()]

        # Prepare legend data
        for value, color in color_mapping.items():
            color_legend_data.append(
                go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(size=10, color=color),
                    name=str(value),
                    showlegend=True
                )
            )
    else:
        node_colors = ['#6495ED'] * len(G.nodes())

    # Create edge trace
    edge_x = []
    edge_y = []
    edge_text = []

    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

        # Create edge hover text
        edge_info = f"From: {edge[0]}<br>To: {edge[1]}"
        for key, value in edge[2].items():
            edge_info += f"<br>{key}: {value}"
        edge_text.extend([edge_info, edge_info, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#777'),
        hoverinfo='text',
        text=edge_text,
        mode='lines'
    )

    # Create node trace
    node_x = [pos[node][0] for node in G.nodes()]
    node_y = [pos[node][1] for node in G.nodes()]

    # Create hover text with all node attributes
    node_text = []
    for node in G.nodes(data=True):
        hover_text = f"Node: {node[0]}"
        for key, value in node[1].items():
            if key != "distances":
                hover_text += f"<br>{key}: {value}"
        node_text.append(hover_text)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        # text=list(G.nodes()),
        textposition="bottom center",
        hoverinfo='text',
        hovertext=node_text,
        marker=dict(
            size=20,
            color=node_colors,
            line_width=0.5,
            line=dict(color='white')
        )
    )

    # Create the figure
    fig = go.Figure(
        data=[edge_trace, node_trace] + color_legend_data,
        layout=go.Layout(
            title=dict(text=title, x=0.5, y=0.95),
            titlefont_size=16,
            showlegend=bool(node_color_attribute),
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
    )

    # Add buttons for layout control
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(label="Reset Zoom",
                         method="relayout",
                         args=[{"xaxis.range": None,
                                "yaxis.range": None}]),
                    dict(label="Zoom to Fit",
                         method="relayout",
                         args=[{"xaxis.autorange": True,
                                "yaxis.autorange": True}])
                ],
                x=0.05,
                y=1.1,
            )
        ]
    )

    # Display the plot in Streamlit
    st.plotly_chart(fig, use_container_width=True, height=1500)


# Example usage
def main():
    st.set_page_config(layout="wide")
    st.title("Interactive Network Visualization")


    # Layout algorithm selector
    layout_options = {
        "Kamada-Kawai": "layout_kamada_kawai",
        "Spring": "layout_spring",
        "Circular": "layout_circular",
        "Shell": "layout_shell",
        "Spiral": "layout_spiral",
        "Spectral": "layout_spectral",
        "Multipartite": "layout_multipartite"
    }

    layout_choice = st.selectbox(
        "Select Layout Algorithm",
        options=list(layout_options.keys())
    )

    G = m.main()

    color_map = {
        "business_group": "#FF6B6B",  # Coral Red
        "product_family": "#4ECDC4",  # Turquoise
        "product_offering": "#45B7D1",  # Sky Blue
        "supplier": "#96CEB4",  # Sage Green
        "warehouse": "#9B59B6",  # Purple
        "facility": "#F1C40F",  # Golden Yellow
        "part": "#FF8C42"  # Orange
    }

    # Visualize the network
    visualize_network(
        G,
        node_color_attribute="node_type",
        custom_color_map=color_map,
        layout_algorithm=layout_options[layout_choice],
        title="Supply Chain Network"
    )


if __name__ == "__main__":
    main()
