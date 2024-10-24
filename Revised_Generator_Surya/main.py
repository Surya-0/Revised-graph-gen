# main.py

from data_generator import SupplyChainGenerator
from graph_visualisation import EnhancedSupplyChainVisualizer
from Supply_chain_manager import SupplyChainManager
from graph_analyzer import SupplyChainAnalyzer
import json
import os


def main():
    # Create and generate supply chain data
    print("Generating supply chain data...")
    generator = SupplyChainGenerator()
    generator.generate_data()

    # Initialize supply chain manager
    manager = SupplyChainManager(generator)

    # Example of adding new nodes
    print("\nAdding new nodes to the supply chain...")
    new_supplier_id = manager.add_supplier(
        name="New Supplier 1",
        location="California",
        reliability=0.95,
        size=450  # Medium supplier
    )

    new_warehouse_id = manager.add_warehouse(
        name="New Warehouse 1",
        warehouse_type="supplier",
        location="Texas",
        max_capacity=5000
    )

    # Export data to CSV
    print("\nExporting supply chain data to CSV...")
    manager.export_to_csv()
    print(f"Data exported")

    # Create visualizer with enhanced features
    print("\nCreating interactive visualization...")
    visualizer = EnhancedSupplyChainVisualizer(manager.G)

    # Generate and save visualization
    fig = visualizer.save_visualization('interactive_supply_chain.html')
    print("Saved interactive visualization as 'interactive_supply_chain.html'")

    # Create analyzer and generate plots
    print("\nGenerating supply chain analysis plots...")
    analyzer = SupplyChainAnalyzer(manager.G)

    # Create plots directory if it doesn't exist
    plots_dir = 'plots'
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)

    # Generate and save plots
    analyzer.plot_node_distribution(f'{plots_dir}/node_distribution.png')
    analyzer.plot_degree_distribution(f'{plots_dir}/degree_distribution.png')
    analyzer.plot_supplier_connections(f'{plots_dir}/supplier_connections.png')
    print(f"Analysis plots saved in '{plots_dir}' directory")

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

    # Save network data as JSON
    network_data = {
        'metrics': metrics,
        'data': manager.data
    }

    with open('supply_chain_data.json', 'w') as f:
        json.dump(network_data, f, indent=2)
    print("\nSaved network data to 'supply_chain_data.json'")


if __name__ == "__main__":
    main()