# supply_chain_manager.py

import networkx as nx
import pandas as pd
from config import *
import csv
import os
import random
from datetime import datetime


class SupplyChainManager:
    def __init__(self, supply_chain_generator):
        self.generator = supply_chain_generator
        self.G = supply_chain_generator.get_graph()
        self.data = supply_chain_generator.get_data()

    def add_supplier(self, name, location, reliability, size):
        """Add a new supplier to the supply chain"""
        # Generate new supplier ID
        supplier_ids = [n for n in self.G.nodes if n.startswith('S_')]
        new_id = f"S_{len(supplier_ids) + 1:03d}"

        size_value = size
        size_category = self._determine_size_category(size_value)

        supplier_data = {
            'id': new_id,
            'name': name,
            'location': location,
            'reliability': reliability,
            'size': size_value,
            'size_category': size_category,
            'node_type': 'supplier'
        }

        # Add to graph
        self.G.add_node(new_id, **supplier_data)
        self.data['suppliers'].append(supplier_data)

        # Connect to appropriate warehouses
        self._connect_new_supplier_to_warehouses(supplier_data)

        return new_id

    def add_warehouse(self, name, warehouse_type, location, max_capacity):
        """Add a new warehouse to the supply chain"""
        # Generate new warehouse ID
        warehouse_ids = [n for n in self.G.nodes if n.startswith('W_')]
        new_id = f"W_{len(warehouse_ids) + 1:03d}"

        size_category = self._determine_warehouse_size_category(max_capacity)

        warehouse_data = {
            'id': new_id,
            'name': name,
            'type': warehouse_type,
            'location': location,
            'size_category': size_category,
            'max_capacity': max_capacity,
            'current_capacity': 0,
            'safety_stock': random.randint(*INVENTORY_RANGE),
            'max_parts': WAREHOUSE_SIZES[size_category]['max_parts'],
            'node_type': 'warehouse'
        }

        # Add to graph
        self.G.add_node(new_id, **warehouse_data)
        self.data['warehouses'].append(warehouse_data)

        return new_id

    def add_facility(self, name, facility_type, location, max_capacity, operating_cost):
        """Add a new facility to the supply chain"""
        # Generate new facility ID
        facility_ids = [n for n in self.G.nodes if n.startswith('F_')]
        new_id = f"F_{len(facility_ids) + 1:03d}"

        facility_data = {
            'id': new_id,
            'name': name,
            'type': facility_type,
            'location': location,
            'max_capacity': max_capacity,
            'operating_cost': operating_cost,
            'node_type': 'facility'
        }

        # Add to graph
        self.G.add_node(new_id, **facility_data)
        self.data['facilities'].append(facility_data)

        return new_id

    def add_part(self, name, part_type, cost, importance_factor):
        """Add a new part to the supply chain"""
        # Generate new part ID
        part_ids = [n for n in self.G.nodes if n.startswith('P_')]
        new_id = f"P_{len(part_ids) + 1:03d}"

        part_data = {
            'id': new_id,
            'name': name,
            'type': part_type,
            'cost': cost,
            'importance_factor': importance_factor,
            'node_type': 'part'
        }

        # Add to graph
        self.G.add_node(new_id, **part_data)
        self.data['parts'].append(part_data)

        return new_id

    def export_to_csv(self, export_dir='exports'):
        """Export all supply chain data to CSV files"""
        # Create export directory if it doesn't exist
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Export all node types
        node_types = {
            'business_group': [self.data['business_group']],  # Convert single dict to list
            'product_families': self.data['product_families'],
            'product_offerings': self.data['product_offerings'],
            'suppliers': self.data['suppliers'],
            'warehouses': self.data['warehouses'],
            'facilities': self.data['facilities'],
            'parts': self.data['parts']
        }

        # Export each node type to a separate CSV
        for node_type, data in node_types.items():
            filename = f"{export_dir}/{node_type}.csv"
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)

        # Export edges with detailed information
        edges_data = []
        for u, v, data in self.G.edges(data=True):
            # Get node types for source and target
            source_type = self.G.nodes[u].get('node_type', 'unknown')
            target_type = self.G.nodes[v].get('node_type', 'unknown')

            edge_data = {
                'source_id': u,
                'source_type': source_type,
                'target_id': v,
                'target_type': target_type,
                'edge_type': f"{source_type}_to_{target_type}",
                **data
            }
            edges_data.append(edge_data)

        edges_df = pd.DataFrame(edges_data)
        edges_df.to_csv(f"{export_dir}/edges.csv", index=False)

        # return timestamp

    def _determine_size_category(self, size_value):
        """Determine size category for suppliers"""
        if size_value <= 300:
            return 'small'
        elif size_value <= 600:
            return 'medium'
        else:
            return 'large'

    def _determine_warehouse_size_category(self, capacity):
        """Determine size category for warehouses based on capacity"""
        if capacity <= 3000:
            return 'small'
        elif capacity <= 6000:
            return 'medium'
        else:
            return 'large'

    def _connect_new_supplier_to_warehouses(self, supplier_data):
        """Connect a new supplier to appropriate warehouses"""
        size_category = supplier_data['size_category']
        max_connections = SUPPLIER_SIZES[size_category]['max_connections']

        # Get supplier warehouses
        supplier_warehouses = [w for w in self.data['warehouses'] if w['type'] == 'supplier']

        # Select random warehouses based on size category
        num_connections = min(max_connections, len(supplier_warehouses))
        selected_warehouses = random.sample(supplier_warehouses, num_connections)

        # Create connections
        for warehouse in selected_warehouses:
            edge_data = {
                'transportation_cost': random.uniform(*TRANSPORTATION_COST_RANGE),
                'lead_time': random.uniform(*TRANSPORTATION_TIME_RANGE)
            }
            self.G.add_edge(supplier_data['id'], warehouse['id'], **edge_data)