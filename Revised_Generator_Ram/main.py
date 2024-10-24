from data_generator import SupplyChainGenerator
from graph_visualisation import EnhancedSupplyChainVisualizer
import json


def main():
    # Create and generate supply chain data
    print("Generating supply chain data...")
    generator = SupplyChainGenerator()
    generator.generate_data()

    # Get the generated graph and data
    graph = generator.get_graph()
    data = generator.get_data()

    # Create visualizer
    print("\nCreating interactive visualization...")
    visualizer = EnhancedSupplyChainVisualizer(graph)

    # Generate and save visualization
    fig = visualizer.save_visualization('interactive_supply_chain.html')
    print("Saved interactive visualization as 'interactive_supply_chain.html'")

    # Calculate and display network metrics
    metrics = visualizer.get_supply_chain_metrics()

    print("\nSupply Chain Network Metrics:")
    print(f"Total nodes: {metrics['total_nodes']}")
    print(f"Total edges: {metrics['total_edges']}")
    print(f"Average degree: {metrics['avg_degree']:.2f}")
    print(f"Network density: {metrics['density']:.3f}")
    print(f"Average clustering coefficient: {metrics['avg_clustering']:.3f}")
    print(f"Number of connected components: {metrics['connected_components']}")

    print("\nNode distribution:")
    for node_type, count in metrics['node_types'].items():
        print(f"- {node_type}: {count}")

    # Save network data as JSON for further analysis
    network_data = {
        'metrics': metrics,
        'data': data
    }

    with open('supply_chain_data.json', 'w') as f:
        json.dump(network_data, f, indent=2)
    print("\nSaved network data to 'supply_chain_data.json'")

    return graph


if __name__ == "__main__":
    main()