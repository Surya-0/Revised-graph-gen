import plotly.graph_objects as go
import networkx as nx
import numpy as np
from typing import Dict, Any
import json


class EnhancedSupplyChainVisualizer:
    def __init__(self, graph):
        self.G = graph
        self.color_scheme = {
            'supplier': '#FF6B6B',  # Coral red for suppliers
            'warehouse': '#4ECDC4',  # Turquoise for warehouses
            'part': '#45B7D1',  # Light blue for parts
            'facility': '#96CEB4',  # Sage green for facilities
            'product_offering': '#FFBE0B',  # Golden yellow for products
            'product_family': '#FF9F1C',  # Orange for product families
            'business_group': '#9B5DE5'  # Purple for business group
        }

        self.node_sizes = {
            'supplier': 30,
            'warehouse': 35,
            'part': 25,
            'facility': 35,
            'product_offering': 30,
            'product_family': 40,
            'business_group': 50
        }

    def _create_node_trace(self, pos: Dict[Any, np.ndarray]):
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []

        for node in self.G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            # Create detailed node information
            node_info = self.G.nodes[node]
            node_type = node_info.get('node_type', 'unknown')

            # Create hover text
            hover_text = [
                f"ID: {node}",
                f"Type: {node_type}",
                f"Name: {node_info.get('name', 'N/A')}"
            ]

            # Add specific attributes based on node type
            if 'location' in node_info:
                hover_text.append(f"Location: {node_info['location']}")
            if 'cost' in node_info:
                hover_text.append(f"Cost: ${node_info['cost']:,.2f}")
            if 'demand' in node_info:
                hover_text.append(f"Demand: {node_info['demand']}")
            if 'capacity' in node_info:
                hover_text.append(f"Capacity: {node_info['capacity']}")

            node_text.append('<br>'.join(hover_text))
            node_color.append(self.color_scheme.get(node_type, '#888'))
            node_size.append(self.node_sizes.get(node_type, 25))

        return go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                color=node_color,
                size=node_size,
                line=dict(width=2, color='white'),
                symbol='circle'
            ),
            name='Nodes'
        )

    def _create_edge_trace(self, pos: Dict[Any, np.ndarray]):
        edge_x = []
        edge_y = []
        edge_text = []

        for edge in self.G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]

            # Create curved edges
            edge_x.append(x0)
            edge_x.append(x1)
            edge_x.append(None)
            edge_y.append(y0)
            edge_y.append(y1)
            edge_y.append(None)

            # Create edge hover text
            edge_data = edge[2]
            hover_text = [
                f"From: {self.G.nodes[edge[0]].get('name', edge[0])}",
                f"To: {self.G.nodes[edge[1]].get('name', edge[1])}"
            ]

            # Add edge attributes to hover text
            for key, value in edge_data.items():
                if isinstance(value, (int, float)):
                    hover_text.append(f"{key}: {value:,.2f}")
                else:
                    hover_text.append(f"{key}: {value}")

            edge_text.append('<br>'.join(hover_text))

        return go.Scatter(
            x=edge_x, y=edge_y,
            mode='lines',
            hoverinfo='text',
            text=edge_text,
            line=dict(color='rgba(150,150,150,0.5)', width=1),
            name='Connections'
        )

    def create_interactive_visualization(self):
        # Use force-directed layout
        pos = nx.spring_layout(self.G, k=1 / np.sqrt(len(self.G.nodes())), iterations=50)

        # Create figure
        fig = go.Figure()

        # Add edges first (so they're behind nodes)
        edge_trace = self._create_edge_trace(pos)
        fig.add_trace(edge_trace)

        # Add nodes
        node_trace = self._create_node_trace(pos)
        fig.add_trace(node_trace)

        # Create legend entries for node types
        for node_type, color in self.color_scheme.items():
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                marker=dict(size=10, color=color),
                name=node_type.replace('_', ' ').title(),
                showlegend=True
            ))

        # Update layout
        fig.update_layout(
            title=dict(
                text='Interactive Supply Chain Network Visualization',
                x=0.5,
                y=0.95,
                font=dict(size=20)
            ),
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[dict(
                text="Hover over nodes and edges for details",
                showarrow=False,
                xref="paper", yref="paper",
                x=0, y=-0.1
            )],
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            legend=dict(
                x=1.05,
                y=0.5,
                title=dict(text='Node Types'),
                bordercolor='#E2E2E2',
                borderwidth=1
            )
        )

        return fig

    def save_visualization(self, filename='supply_chain_visualization.html'):
        fig = self.create_interactive_visualization()
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