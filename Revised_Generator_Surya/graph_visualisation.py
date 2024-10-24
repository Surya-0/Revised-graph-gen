import networkx as nx
import plotly.graph_objects as go
import pandas as pd
import colorsys
import random


class EnhancedSupplyChainVisualizer:
    def __init__(self, graph):
        self.G = graph
        self.node_colors = {
            'business_group': '#FF9999',  # Light red
            'product_family': '#99FF99',  # Light green
            'product_offering': '#9999FF',  # Light blue
            'supplier': '#FFB366',  # Light orange
            'warehouse': '#FF99FF',  # Light purple
            'facility': '#99FFFF',  # Light cyan
            'part': '#FFFF99'  # Light yellow
        }

    def create_visualization(self):
        """Create an interactive visualization of the supply chain"""
        # Use Kamada-Kawai layout for better visualization of hierarchical structures
        pos = nx.kamada_kawai_layout(self.G)

        # Create node traces for each node type
        node_traces = {}
        for node_type in self.node_colors.keys():
            node_traces[node_type] = go.Scatter(
                x=[],
                y=[],
                text=[],
                mode='markers',  # We remove text labels here for hover-only behavior
                hoverinfo='text',  # Show only on hover
                name=node_type.replace('_', ' ').title(),
                marker=dict(
                    color=self.node_colors[node_type],
                    size=15,
                    line=dict(width=2)
                )
            )

        # Add nodes to appropriate traces
        for node, attrs in self.G.nodes(data=True):
            x, y = pos[node]
            node_type = attrs.get('node_type', 'unknown')
            if node_type in node_traces:
                node_traces[node_type]['x'] += tuple([x])
                node_traces[node_type]['y'] += tuple([y])

                # Create hover text with node attributes
                hover_text = f"ID: {node}<br>"
                hover_text += "<br>".join([f"{k}: {v}" for k, v in attrs.items()
                                           if k != 'pos' and k != 'node_type'])

                node_traces[node_type]['text'] += tuple([hover_text])

        # Create edge trace
        edge_x = []
        edge_y = []
        edge_hover = []

        for edge in self.G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]

            # Add edge line coordinates
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

            # Create edge hover text
            source_type = self.G.nodes[edge[0]].get('node_type', 'unknown')
            target_type = self.G.nodes[edge[1]].get('node_type', 'unknown')

            hover_text = f"From: {edge[0]} ({source_type})<br>"
            hover_text += f"To: {edge[1]} ({target_type})<br>"
            hover_text += "<br>".join([f"{k}: {v}" for k, v in edge[2].items()])
            edge_hover += [hover_text, hover_text, None]

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=0.7, color='#888'),
            hoverinfo='text',  # Only show edge details on hover
            text=edge_hover,
            mode='lines'
        )

        # Create figure
        fig = go.Figure(
            data=[edge_trace] + list(node_traces.values()),
            layout=go.Layout(
                title='Interactive Supply Chain Network Visualization',
                showlegend=True,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white'
            )
        )

        # Add buttons to toggle node types
        updatemenus = [
            dict(
                type="buttons",
                direction="right",
                buttons=list([
                    dict(
                        args=[{"visible": [True] * len(fig.data)}],
                        label="Show All",
                        method="restyle"
                    ),
                    dict(
                        args=[{"visible": [False] * len(fig.data)}],
                        label="Hide All",
                        method="restyle"
                    )
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.9,
                xanchor="right",
                y=1.1,
                yanchor="top"
            )
        ]

        fig.update_layout(updatemenus=updatemenus)

        return fig
    def save_visualization(self, filename='supply_chain_visualization.html'):
        """Save the visualization to an HTML file"""
        fig = self.create_visualization()
        fig.write_html(filename)
        return fig

    def get_supply_chain_metrics(self):
        metrics = {
            'total_nodes': self.G.number_of_nodes(),
            'total_edges': self.G.number_of_edges(),
            'avg_degree': sum(dict(self.G.degree()).values()) / self.G.number_of_nodes(),
            'density': nx.density(self.G),
            'avg_clustering': nx.average_clustering(self.G.to_undirected()),
            'connected_components': nx.number_weakly_connected_components(self.G)
        }
        node_types = {}
        for _, data in self.G.nodes(data=True):
            node_type = data.get('node_type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        metrics['node_types'] = node_types
        return metrics