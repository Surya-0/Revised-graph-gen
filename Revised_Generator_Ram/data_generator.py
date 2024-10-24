import random
import networkx as nx
from config import *


class SupplyChainGenerator:
    def __init__(self, total_variable_nodes=1000):
        self.G = nx.DiGraph()
        # Fixed nodes as per ontology
        self.FIXED_BUSINESS_GROUPS = 1
        self.FIXED_PRODUCT_FAMILIES = 4
        self.FIXED_PRODUCT_OFFERINGS = 21

        # Calculate variable nodes distribution
        self.total_variable_nodes = total_variable_nodes
        self.calculate_node_distribution()

        # Initialize node storage
        self.suppliers = []
        self.warehouses = {'supplier': [], 'subassembly': [], 'lam': []}
        self.facilities = {'external': [], 'lam': []}
        self.parts = {'raw': [], 'subassembly': []}
        self.product_offerings = []
        self.product_families = []
        self.business_group = None

    def calculate_node_distribution(self):
        """Calculate the number of nodes for each category based on ratios"""
        self.node_counts = {
            'parts': int(self.total_variable_nodes * 0.50),
            'suppliers': int(self.total_variable_nodes * 0.15),
            'warehouses': int(self.total_variable_nodes * 0.20),
            'facilities': int(self.total_variable_nodes * 0.15)
        }

        # Adjust internal distributions
        self.parts_distribution = {
            'raw': int(self.node_counts['parts'] * 0.6),
            'subassembly': int(self.node_counts['parts'] * 0.4)
        }

        self.supplier_distribution = {
            'small': int(self.node_counts['suppliers'] * 0.4),
            'medium': int(self.node_counts['suppliers'] * 0.35),
            'large': int(self.node_counts['suppliers'] * 0.25)
        }

        self.warehouse_distribution = {
            'supplier': int(self.node_counts['warehouses'] * 0.4),
            'subassembly': int(self.node_counts['warehouses'] * 0.35),
            'lam': int(self.node_counts['warehouses'] * 0.25)
        }

        self.facility_distribution = {
            'external': int(self.node_counts['facilities'] * 0.6),
            'lam': int(self.node_counts['facilities'] * 0.4)
        }

    def _determine_size_category(self, size_value):
        if size_value <= 300:
            return 'small'
        elif size_value <= 600:
            return 'medium'
        else:
            return 'large'

    def _generate_suppliers(self):
        counter = 1
        for size_category, count in self.supplier_distribution.items():
            size_range = SUPPLIER_SIZES[size_category]['range']
            for _ in range(count):
                size_value = random.randint(*size_range)
                supplier_data = {
                    'id': f'S_{counter:03d}',
                    'name': f'Supplier_{counter}',
                    'location': random.choice(LOCATIONS),
                    'reliability': random.uniform(*RELIABILITY_RANGE),
                    'size': size_value,
                    'size_category': size_category
                }
                self.suppliers.append(supplier_data)
                self.G.add_node(supplier_data['id'], **supplier_data, node_type='supplier')
                counter += 1
    def generate_data(self):
        self._generate_business_hierarchy()
        self._generate_suppliers()
        self._generate_warehouses()
        self._generate_facilities()
        self._generate_parts()
        self._generate_edges()
        self._calculate_distances()

    def _generate_business_hierarchy(self):
        # Generate business group
        self.business_group = {
            'id': 'BG_001',
            'name': BUSINESS_GROUP,
            'description': f'{BUSINESS_GROUP} Business Unit',
            'revenue': random.uniform(*COST_RANGE)
        }
        self.G.add_node('BG_001', **self.business_group, node_type ='business_group')

        # Generate product families
        for i, pf in enumerate(PRODUCT_FAMILIES, 1):
            pf_data = {
                'id': f'PF_{i:03d}',
                'name': pf,
                'revenue': random.uniform(*COST_RANGE)
            }
            self.product_families.append(pf_data)
            self.G.add_node(pf_data['id'], **pf_data, node_type='product_family')

        # Generate product offerings
        po_counter = 1
        for pf in self.product_families:
            pf_name = pf['name']
            if pf_name in PRODUCT_OFFERINGS:
                for po in PRODUCT_OFFERINGS[pf_name]:
                    po_data = {
                        'id': f'PO_{po_counter:03d}',
                        'name': po,
                        'cost': random.uniform(*COST_RANGE),
                        'demand': random.randint(*DEMAND_RANGE)
                    }
                    self.product_offerings.append(po_data)
                    self.G.add_node(po_data['id'], **po_data, node_type='product_offering')
                    po_counter += 1

    def _generate_warehouses(self):
        counter = 1
        for w_type, count in self.warehouse_distribution.items():
            for _ in range(count):
                # Distribute warehouse sizes evenly within each type
                size_category = random.choice(['small', 'medium', 'large'])
                capacity_range = WAREHOUSE_SIZES[size_category]['capacity']

                warehouse_data = {
                    'id': f'W_{counter:03d}',
                    'name': f'Warehouse_{counter}',
                    'type': w_type,
                    'location': random.choice(LOCATIONS),
                    'size_category': size_category,
                    'max_capacity': random.randint(*capacity_range),
                    'current_capacity': 0,
                    'safety_stock': random.randint(*INVENTORY_RANGE),
                    'max_parts': WAREHOUSE_SIZES[size_category]['max_parts']
                }
                self.warehouses[w_type].append(warehouse_data)
                self.G.add_node(warehouse_data['id'], **warehouse_data, node_type='warehouse')
                counter += 1

    def _generate_facilities(self):
        counter = 1
        for f_type, count in self.facility_distribution.items():
            for _ in range(count):
                facility_data = {
                    'id': f'F_{counter:03d}',
                    'name': f'Facility_{counter}',
                    'type': f_type,
                    'location': random.choice(LOCATIONS),
                    'max_capacity': random.randint(*CAPACITY_RANGE),
                    'operating_cost': random.uniform(*COST_RANGE)
                }
                self.facilities[f_type].append(facility_data)
                self.G.add_node(facility_data['id'], **facility_data, node_type='facility')
                counter += 1

    def _generate_parts(self):
        counter = 1
        for p_type, count in self.parts_distribution.items():
            for _ in range(count):
                part_data = {
                    'id': f'P_{counter:03d}',
                    'name': f'Part_{counter}',
                    'type': p_type,
                    'cost': random.uniform(*COST_RANGE),
                    'importance_factor': random.uniform(*IMPORTANCE_FACTOR_RANGE)
                }
                self.parts[p_type].append(part_data)
                self.G.add_node(part_data['id'], **part_data, node_type='part')
                counter += 1


    def _generate_edges(self):
        # Connect suppliers to warehouses
        self._connect_suppliers_to_warehouses()
        # Connect warehouses to parts
        self._connect_warehouses_to_parts()
        # Connect parts to facilities
        self._connect_parts_to_facilities()
        # Connect facilities to products
        self._connect_facilities_to_products()
        # Connect hierarchy
        self._connect_hierarchy()

    def _connect_suppliers_to_warehouses(self):
        for supplier in self.suppliers:
            size_category = supplier['size_category']
            max_connections = SUPPLIER_SIZES[size_category]['max_connections']

            # Select warehouses based on supplier size
            possible_warehouses = self.warehouses['supplier']
            num_connections = min(max_connections, len(possible_warehouses))
            selected_warehouses = random.sample(possible_warehouses, num_connections)

            for warehouse in selected_warehouses:
                edge_data = {
                    'transportation_cost': random.uniform(*TRANSPORTATION_COST_RANGE),
                    'lead_time': random.uniform(*TRANSPORTATION_TIME_RANGE)
                }
                self.G.add_edge(supplier['id'], warehouse['id'], **edge_data)

    def _connect_warehouses_to_parts(self):
        for warehouse in sum(self.warehouses.values(), []):
            max_parts = warehouse['max_parts']
            available_capacity = warehouse['max_capacity']
            current_inventory = 0

            # Select random parts based on warehouse size
            possible_parts = self.parts['raw'] if warehouse['type'] == 'supplier' else self.parts['subassembly']
            selected_parts = random.sample(
                possible_parts,
                min(max_parts, len(possible_parts))
            )

            for part in selected_parts:
                # Calculate inventory level ensuring we don't exceed capacity
                max_possible_inventory = min(
                    random.randint(*INVENTORY_RANGE),
                    available_capacity - current_inventory
                )

                if max_possible_inventory <= 0:
                    continue

                inventory_level = max_possible_inventory
                current_inventory += inventory_level

                edge_data = {
                    'inventory_level': inventory_level,
                    'storage_cost': random.uniform(*COST_RANGE)
                }
                self.G.add_edge(warehouse['id'], part['id'], **edge_data)

                # Update warehouse current capacity
                self.G.nodes[warehouse['id']]['current_capacity'] = current_inventory

    def _connect_parts_to_facilities(self):
        # Connect raw parts to external facilities to create subassemblies
        for facility in self.facilities['external']:
            # Each external facility uses multiple raw parts to create subassemblies
            raw_parts = random.sample(
                self.parts['raw'],
                random.randint(2, max(3, len(self.parts['raw']) // 2))
            )
            for part in raw_parts:
                edge_data = {
                    'quantity': random.randint(*QUANTITY_RANGE),
                    'distance': random.randint(*DISTANCE_RANGE),
                    'transport_cost': random.uniform(*TRANSPORTATION_COST_RANGE),
                    'lead_time': random.uniform(*TRANSPORTATION_TIME_RANGE)
                }
                self.G.add_edge(part['id'], facility['id'], **edge_data)

            # Each external facility produces subassembly parts
            subassembly_parts = random.sample(
                self.parts['subassembly'],
                random.randint(1, 3)
            )
            for part in subassembly_parts:
                edge_data = {
                    'production_cost': random.uniform(*COST_RANGE),
                    'lead_time': random.uniform(*TRANSPORTATION_TIME_RANGE),
                    'quantity': random.randint(*QUANTITY_RANGE)
                }
                self.G.add_edge(facility['id'], part['id'], **edge_data)

        # Connect subassembly parts to LAM facilities to create products
        for facility in self.facilities['lam']:
            # Each LAM facility uses multiple subassembly parts
            subassembly_parts = random.sample(
                self.parts['subassembly'],
                random.randint(2, max(3, len(self.parts['subassembly']) // 2))
            )
            for part in subassembly_parts:
                edge_data = {
                    'quantity': random.randint(*QUANTITY_RANGE),
                    'distance': random.randint(*DISTANCE_RANGE),
                    'transport_cost': random.uniform(*TRANSPORTATION_COST_RANGE),
                    'lead_time': random.uniform(*TRANSPORTATION_TIME_RANGE)
                }
                self.G.add_edge(part['id'], facility['id'], **edge_data)

    def _connect_facilities_to_products(self):
        # LAM facilities produce final products (product offerings)
        for facility in self.facilities['lam']:
            # Each LAM facility produces multiple product offerings
            products = random.sample(
                self.product_offerings,
                random.randint(2, max(3, len(self.product_offerings) // 2))
            )
            for product in products:
                edge_data = {
                    'product_cost': random.uniform(*COST_RANGE),
                    'lead_time': random.uniform(*TRANSPORTATION_TIME_RANGE),
                    'quantity': random.randint(*QUANTITY_RANGE)
                }
                self.G.add_edge(facility['id'], product['id'], **edge_data)

                # Connect to LAM warehouse for storage
                for warehouse in self.warehouses['lam']:
                    edge_data = {
                        'inventory_level': random.randint(*INVENTORY_RANGE),
                        'storage_cost': random.uniform(*COST_RANGE)
                    }
                    self.G.add_edge(product['id'], warehouse['id'], **edge_data)

    def _connect_hierarchy(self):
        # Connect business group to product families
        for pf in self.product_families:
            self.G.add_edge('BG_001', pf['id'], type='hierarchy')

        # Connect product families to their respective product offerings
        for pf in self.product_families:
            # Find all product offerings belonging to this family
            family_offerings = [
                po for po in self.product_offerings
                if po['name'] in PRODUCT_OFFERINGS[pf['name']]
            ]
            for po in family_offerings:
                self.G.add_edge(pf['id'], po['id'], type='hierarchy')

    def _calculate_distances(self):
        # Simple distance calculation between warehouses and facilities
        for warehouse in sum(self.warehouses.values(), []):
            for facility in sum(self.facilities.values(), []):
                if warehouse['location'] == facility['location']:
                    distance = random.randint(10, 50)
                else:
                    distance = random.randint(*DISTANCE_RANGE)
                self.G.nodes[warehouse['id']]['distances'] = self.G.nodes[warehouse['id']].get('distances', {})
                self.G.nodes[warehouse['id']]['distances'][facility['id']] = distance



    def get_graph(self):
        return self.G

    def get_data(self):
        return {
            'business_group': self.business_group,
            'product_families': self.product_families,
            'product_offerings': self.product_offerings,
            'suppliers': self.suppliers,
            'warehouses': sum(self.warehouses.values(), []),
            'facilities': sum(self.facilities.values(), []),
            'parts': sum(self.parts.values(), [])
        }

    def get_node_distribution(self):
        """Return the current node distribution statistics"""
        return {
            'fixed_nodes': {
                'business_groups': self.FIXED_BUSINESS_GROUPS,
                'product_families': self.FIXED_PRODUCT_FAMILIES,
                'product_offerings': self.FIXED_PRODUCT_OFFERINGS
            },
            'variable_nodes': {
                'total': self.total_variable_nodes,
                'parts': self.parts_distribution,
                'suppliers': self.supplier_distribution,
                'warehouses': self.warehouse_distribution,
                'facilities': self.facility_distribution
            }
        }