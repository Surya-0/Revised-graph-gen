# graph_analyzer.py

import matplotlib.pyplot as plt



class SupplyChainAnalyzer:
    def __init__(self, graph):
        self.G = graph

    def plot_node_distribution(self, save_path=None):
        """Plot distribution of different node types"""
        node_types = {}
        for node, data in self.G.nodes(data=True):
            node_type = data.get('node_type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1

        plt.figure(figsize=(10, 6))
        plt.bar(node_types.keys(), node_types.values())
        plt.title('Distribution of Node Types in Supply Chain')
        plt.xlabel('Node Type')
        plt.ylabel('Count')
        plt.xticks(rotation=45)

        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            plt.close()
        else:
            plt.show()

    def plot_degree_distribution(self, save_path=None):
        """Plot degree distribution of nodes"""
        degrees = [d for n, d in self.G.degree()]

        plt.figure(figsize=(10, 6))
        plt.hist(degrees, bins=20)
        plt.title('Node Degree Distribution')
        plt.xlabel('Degree')
        plt.ylabel('Frequency')

        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            plt.close()
        else:
            plt.show()

    def plot_supplier_connections(self, save_path=None):
        """Plot supplier warehouse connections distribution"""
        supplier_connections = {}
        for node, data in self.G.nodes(data=True):
            if data.get('node_type') == 'supplier':
                supplier_connections[node] = len(list(self.G.neighbors(node)))

        plt.figure(figsize=(12, 6))
        plt.bar(supplier_connections.keys(), supplier_connections.values())
        plt.title('Supplier Warehouse Connections')
        plt.xlabel('Supplier ID')
        plt.ylabel('Number of Connections')
        plt.xticks(rotation=90)

        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            plt.close()
        else:
            plt.show()