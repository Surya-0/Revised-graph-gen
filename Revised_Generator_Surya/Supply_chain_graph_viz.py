from pyvis.network import Network
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import pandas as pd
from IPython.display import display, HTML
from collections import defaultdict


class SupplyChainVisualizer:
    def __init__(self, graph, width="100%", height="800px"):
        self.graph = graph
        self.width = width
        self.height = height

        # Define color scheme for different node types
        self.node_colors = {
            'supplier': '#FF6B6B',  # Coral Red
            'warehouse': '#4ECDC4',  # Turquoise
            'facility': '#45B7D1',  # Sky Blue
            'part': '#96CEB4',  # Sage Green
            'product_offering': '#FFEEAD',  # Light Yellow
            'product_family': '#FFD93D',  # Golden Yellow
            'business_group': '#FF9F1C'  # Orange
        }

        # Define edge colors based on edge types
        self.edge_colors = {
            'hierarchy': '#2C3E50',
            'supply': '#95A5A6',
            'production': '#E74C3C',
            'storage': '#3498DB'
        }

    def create_interactive_graph(self, filename='supply_chain.html'):
        """Create an interactive PyVis visualization"""
        # Initialize PyVis network
        net = Network(height=self.height, width=self.width, bgcolor='#ffffff',
                      font_color='#333333')
        net.force_atlas_2based()

        # Add nodes with custom styling
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            node_type = node_data.get('node_type', '')

            # Create label with node attributes
            label = f"{node_id}\n{node_data.get('name', '')}"
            for key, value in node_data.items():
                if key not in ['id', 'name', 'node_type'] and not isinstance(value, dict):
                    label += f"\n{key}: {value}"

            # Add node with styling
            net.add_node(node_id,
                         label=label,
                         color=self.node_colors.get(node_type, '#grey'),
                         title=label.replace('\n', '<br>'),
                         size=20,
                         shape='dot' if node_type in ['part', 'supplier'] else 'box')

        # Add edges with custom styling
        for edge in self.graph.edges(data=True):
            source, target, data = edge

            # Determine edge type and color
            edge_type = data.get('type', 'supply')

            # Create edge label
            edge_label = '\n'.join([f"{k}: {v}" for k, v in data.items()
                                    if k != 'type' and not isinstance(v, dict)])

            net.add_edge(source, target,
                         title=edge_label,
                         color=self.edge_colors.get(edge_type, '#grey'),
                         physics=True)

        # Add navigation controls
        net.show_buttons(filter_=['physics'])

        # Save the network
        net.show(filename)
        return HTML(filename=filename)

    def create_growth_visualization(self, generator_instance):
        """Create a visualization showing the growth of nodes during generation"""
        # Track node growth
        node_counts = defaultdict(list)
        timestamps = []

        # Monitor node addition
        for i, node in enumerate(self.graph.nodes(data=True)):
            node_type = node[1].get('node_type', 'unknown')

            # Update counts
            for type_key in self.node_colors.keys():
                current_count = len([n for n in self.graph.nodes(data=True)
                                     if n[1].get('node_type', '') == type_key])
                node_counts[type_key].append(current_count)

            timestamps.append(i)

        # Create growth plot using plotly
        fig = go.Figure()

        for node_type, counts in node_counts.items():
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=counts,
                name=node_type,
                mode='lines+markers',
                line=dict(color=self.node_colors.get(node_type, '#grey'))
            ))

        fig.update_layout(
            title='Supply Chain Network Growth',
            xaxis_title='Time Step',
            yaxis_title='Number of Nodes',
            template='plotly_white',
            hovermode='x unified'
        )

        return fig

    def create_network_statistics(self):
        """Generate and visualize network statistics"""
        stats = {
            'Node Types': dict(pd.Series([data['node_type']
                                          for _, data in self.graph.nodes(data=True)]).value_counts()),
            'Total Nodes': self.graph.number_of_nodes(),
            'Total Edges': self.graph.number_of_edges(),
            'Average Degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(),
            'Network Density': nx.density(self.graph),
            'Average Clustering Coefficient': nx.average_clustering(self.graph.to_undirected()),
        }

        # Create a sunburst chart for node hierarchy
        hierarchy_data = self.extract_hierarchy_data()
        fig_sunburst = px.sunburst(
            hierarchy_data,
            names='name',
            parents='parent',
            values='value',
            title='Supply Chain Hierarchy'
        )

        return stats, fig_sunburst

    def extract_hierarchy_data(self):
        """Extract hierarchical structure for visualization"""
        hierarchy_data = []

        # Add root
        hierarchy_data.append({
            'name': 'Supply Chain',
            'parent': '',
            'value': 1
        })

        # Add nodes by type
        for node, data in self.graph.nodes(data=True):
            node_type = data.get('node_type', 'unknown')
            hierarchy_data.append({
                'name': data.get('name', node),
                'parent': node_type,
                'value': 1
            })

            # Add node types if not already added
            if not any(d['name'] == node_type for d in hierarchy_data):
                hierarchy_data.append({
                    'name': node_type,
                    'parent': 'Supply Chain',
                    'value': 1
                })

        return pd.DataFrame(hierarchy_data)

    def create_location_analysis(self):
        """Create geographical distribution analysis"""
        location_data = defaultdict(lambda: defaultdict(int))

        for _, data in self.graph.nodes(data=True):
            if 'location' in data:
                node_type = data.get('node_type', 'unknown')
                location = data['location']
                location_data[location][node_type] += 1

        # Create stacked bar chart
        locations = list(location_data.keys())
        node_types = list(self.node_colors.keys())

        fig = go.Figure()

        for node_type in node_types:
            values = [location_data[loc][node_type] for loc in locations]
            if sum(values) > 0:  # Only add node types that exist in the data
                fig.add_trace(go.Bar(
                    name=node_type,
                    x=locations,
                    y=values,
                    marker_color=self.node_colors.get(node_type, '#grey')
                ))

        fig.update_layout(
            title='Geographical Distribution of Supply Chain Nodes',
            xaxis_title='Location',
            yaxis_title='Number of Nodes',
            barmode='stack',
            template='plotly_white'
        )

        return fig


def visualize_supply_chain(generator_instance):
    """Main function to create all visualizations"""
    graph = generator_instance.get_graph()
    visualizer = SupplyChainVisualizer(graph)

    # Create interactive network visualization
    network_viz = visualizer.create_interactive_graph()

    # Create growth visualization
    growth_viz = visualizer.create_growth_visualization(generator_instance)

    # Create network statistics and hierarchy visualization
    stats, hierarchy_viz = visualizer.create_network_statistics()

    # Create location analysis
    location_viz = visualizer.create_location_analysis()

    return {
        'network': network_viz,
        'growth': growth_viz,
        'stats': stats,
        'hierarchy': hierarchy_viz,
        'location': location_viz
    }