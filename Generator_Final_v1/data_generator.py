# data_generator.py
import json
import math
import os
import random
import networkx as nx
import pandas as pd
from datetime import datetime, timedelta
from config import *


class SupplyChainGenerator:
    def __init__(self, total_variable_nodes=1000, base_periods=12,version = "NSS_V1"):
        self.G = nx.DiGraph()
        self.temporal_graphs = {}
        self.temporal_data = {}
        self.FIXED_BUSINESS_GROUPS = 1
        self.FIXED_PRODUCT_FAMILIES = 4
        self.FIXED_PRODUCT_OFFERINGS = 21
        self.total_variable_nodes = total_variable_nodes
        self.base_periods = base_periods
        self.current_period = 0
        self.calculate_node_distribution()
        self.initialize_storage()

        self.operations_log = []  # List to store all create/update operations
        self.version = version

        self.timestamp = 0

    def _log_node_operation(self, action, node_id, node_type, properties):
        """Log node creation/update operations"""
        operation = {
            "action": action,
            "type": "schema",
            "payload": {
                "node_id": node_id,
                "node_type": node_type,
                "properties": properties
            },
            "timestamp": self.timestamp,
            "version": self.version
        }
        self.operations_log.append(operation)

    def _log_edge_operation(self, action, source_id, target_id, properties,edge_type):
        """Log edge creation/update operations"""
        operation = {
            "action": action,
            "type": "schema",
            "payload": {
                "source_id": source_id,
                "target_id": target_id,
                "edge_type":edge_type,
                "properties": properties
            },
            "timestamp": self.timestamp,
            "version": self.version
        }
        self.operations_log.append(operation)
        # print("The edge operation is : ",operation)

    def return_operation(self):
        return self.operations_log

    def simulate_next_period(self):
        """Generate data for the next time period based on the last period's data"""
        last_period = max(self.temporal_graphs.keys())
        next_period = last_period + 1

        # Get the last period's graph as base
        base_graph = self.temporal_graphs[last_period].copy()
        current_date = BASE_DATE + timedelta(days=30 * next_period)
        period_data = {'date': current_date}

        # Update node attributes for the new period
        self._update_period_attributes(base_graph, next_period, period_data)

        # Store the new period's data
        self.temporal_graphs[next_period] = base_graph
        self.temporal_data[next_period] = period_data
        self.current_period = next_period

        return next_period

    def simulate_multiple_periods(self, num_periods):
        """Generate data for multiple future periods"""
        new_periods = []
        for _ in range(num_periods):
            new_period = self.simulate_next_period()
            new_periods.append(new_period)
        return new_periods

    def regenerate_all_periods(self):
        """Regenerate all periods from scratch"""
        self.temporal_graphs = {}
        self.temporal_data = {}
        self.current_period = 0
        self.generate_temporal_data()

    def _update_period_attributes(self, graph, time_period, period_data):
        """Update attributes for a new time period"""
        # Update Business Group attributes
        bg_revenue = self._generate_temporal_value(
            self.business_group['revenue'], 'revenue', time_period)
        graph.nodes[self.business_group['id']]['revenue'] = bg_revenue
        period_data['business_group_revenue'] = bg_revenue

        # Update Product Family attributes
        for family in self.product_families:
            family_revenue = self._generate_temporal_value(
                family['revenue'], 'revenue', time_period)
            graph.nodes[family['id']]['revenue'] = family_revenue
            period_data[f"family_{family['id']}_revenue"] = family_revenue

        # Update other node and edge attributes (similar to generate_temporal_data)
        self._update_product_attributes(graph, time_period, period_data)
        self._update_warehouse_attributes(graph, time_period, period_data)
        self._update_supplier_attributes(graph, time_period, period_data)
        self._update_part_attributes(graph, time_period, period_data)
        self._update_edge_attributes(graph, time_period, period_data)

    def _update_product_attributes(self, graph, time_period, period_data):
        """Update product offering attributes"""
        for offering in self.product_offerings:
            offering_id = offering['id']
            new_cost = self._generate_temporal_value(
                offering['cost'], 'cost', time_period)
            new_demand = self._generate_temporal_value(
                offering['demand'], 'demand', time_period)
            graph.nodes[offering_id]['cost'] = new_cost
            graph.nodes[offering_id]['demand'] = new_demand
            period_data[f"offering_{offering_id}_cost"] = new_cost
            period_data[f"offering_{offering_id}_demand"] = new_demand

    def _update_warehouse_attributes(self, graph, time_period, period_data):
        """Update warehouse attributes"""
        for warehouse_type, warehouses in self.warehouses.items():
            for warehouse in warehouses:
                warehouse_id = warehouse['id']
                new_capacity = self._generate_temporal_value(
                    warehouse['current_capacity'], 'capacity', time_period)
                graph.nodes[warehouse_id]['current_capacity'] = new_capacity
                period_data[f"warehouse_{warehouse_id}_capacity"] = new_capacity

    def _update_supplier_attributes(self, graph, time_period, period_data):
        """Update supplier attributes"""
        for supplier in self.suppliers:
            supplier_id = supplier['id']
            new_reliability = self._generate_temporal_value(
                supplier['reliability'], 'reliability', time_period)
            graph.nodes[supplier_id]['reliability'] = new_reliability
            period_data[f"supplier_{supplier_id}_reliability"] = new_reliability

    def _update_part_attributes(self, graph, time_period, period_data):
        """Update part attributes"""
        current_date = BASE_DATE + timedelta(days=30 * time_period)
        for part_type, parts in self.parts.items():
            for part in parts:
                if part['valid_from'] <= current_date <= part['valid_till']:
                    part_id = part['id']
                    new_cost = self._generate_temporal_value(
                        part['cost'], 'cost', time_period)
                    graph.nodes[part_id]['cost'] = new_cost
                    period_data[f"part_{part_id}_cost"] = new_cost

    def _update_edge_attributes(self, graph, time_period, period_data):
        """Update edge attributes"""
        for u, v, attrs in graph.edges(data=True):
            if 'transportation_cost' in attrs:
                new_transport_cost = self._generate_temporal_value(
                    attrs['transportation_cost'], 'transportation_cost', time_period)
                graph.edges[u, v]['transportation_cost'] = new_transport_cost
                period_data[f"edge_{u}_{v}_transport_cost"] = new_transport_cost

            if 'inventory_level' in attrs:
                new_inventory = self._generate_temporal_value(
                    attrs['inventory_level'], 'inventory', time_period)
                graph.edges[u, v]['inventory_level'] = new_inventory
                period_data[f"edge_{u}_{v}_inventory"] = new_inventory

    def initialize_storage(self):
        """Initialize storage for all node types"""
        self.suppliers = []
        self.warehouses = {'supplier': [], 'subassembly': [], 'lam': []}
        self.facilities = {'external': [], 'lam': []}
        self.parts = {'raw': [], 'subassembly': []}
        self.product_offerings = []
        self.product_families = []
        self.business_group = None
        self.data = {}  # Store all data for easy export

    def calculate_node_distribution(self):
        """Calculate the number of nodes for each category based on ratios"""
        self.node_counts = {
            'parts': int(self.total_variable_nodes * 0.50),
            'suppliers': int(self.total_variable_nodes * 0.15),
            'warehouses': int(self.total_variable_nodes * 0.20),
            'facilities': int(self.total_variable_nodes * 0.15)
        }

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

    def generate_data(self):
        """Generate all supply chain data"""

        # Static Schema creation
        self._generate_business_hierarchy()
        self._generate_suppliers()
        self._generate_warehouses()
        self._generate_facilities()
        self._generate_parts()
        self._generate_edges()
        self._calculate_distances()

        # Temporal data generation
        self.generate_temporal_data()

        # Store all data for easy access
        self.data = {
            'business_group': self.business_group,
            'product_families': self.product_families,
            'product_offerings': self.product_offerings,
            'suppliers': self.suppliers,
            'warehouses': sum(self.warehouses.values(), []),
            'facilities': sum(self.facilities.values(), []),
            'parts': sum(self.parts.values(), [])
        }

    def _generate_temporal_value(self, base_value, feature_type, time_period):
        """
        Generate temporal value incorporating both trend and seasonality

        Args:
            base_value: Initial value
            feature_type: Type of feature (cost, demand, etc.)
            time_period: Current time period (0-11 for months)
        """
        config = TEMPORAL_VARIATION.get(feature_type, {'max_change': 0.1, 'trend': 0})

        # Add trend component
        trend_factor = 1 + (config['trend'] * time_period)

        # Add seasonal component for relevant features
        seasonal_factor = 1.0
        if feature_type in ['demand', 'cost']:
            # Create a seasonal pattern with peak in summer (period 6-7) and trough in winter (period 0-1)
            seasonal_amplitude = 0.15  # 15% seasonal variation
            seasonal_factor = 1 + seasonal_amplitude * math.sin(2 * math.pi * (time_period - 3) / 12)

        # Add random variation
        random_factor = 1 + random.uniform(-config['max_change'], config['max_change'])

        return base_value * trend_factor * seasonal_factor * random_factor

    def generate_temporal_data(self):
        """Generate temporal data and graph snapshots for all time periods with dynamic attributes"""
        base_graph = self.G.copy()
        self.temporal_graphs[0] = base_graph


        for time_period in range(1,self.base_periods):
            current_date = BASE_DATE + timedelta(days=30 * time_period)
            self.timestamp += 1
            period_data = {'date': current_date}

            # Create a new graph snapshot for this period
            period_graph = base_graph.copy()

            # Update Business Group attributes
            bg_revenue = self._generate_temporal_value(self.business_group['revenue'], 'revenue', time_period)
            period_graph.nodes[self.business_group['id']]['revenue'] = bg_revenue
            changes = {'revenue': bg_revenue}
            self._log_node_operation("update",self.business_group['id'],"BUSINESS_GROUP",changes)
            period_data['business_group_revenue'] = bg_revenue

            # Update Product Family attributes
            for family in self.product_families:
                family_revenue = self._generate_temporal_value(family['revenue'], 'revenue', time_period)
                period_graph.nodes[family['id']]['revenue'] = family_revenue
                changes = {'revenue': family_revenue}
                self._log_node_operation("update",family['id'],"PRODUCT_FAMILY",changes)
                period_data[f"family_{family['id']}_revenue"] = family_revenue

            # Update Product Offering attributes
            for offering in self.product_offerings:
                offering_id = offering['id']
                # Update cost with seasonality
                new_cost = self._generate_temporal_value(offering['cost'], 'cost', time_period)
                period_graph.nodes[offering_id]['cost'] = new_cost

                # Update demand with seasonality
                new_demand = self._generate_temporal_value(offering['demand'], 'demand', time_period)
                period_graph.nodes[offering_id]['demand'] = new_demand

                changes = {'demand' : new_demand,'cost': new_cost}
                self._log_node_operation("update", offering_id, "PRODUCT_OFFERING", changes)

                period_data[f"offering_{offering_id}_cost"] = new_cost
                period_data[f"offering_{offering_id}_demand"] = new_demand

            # Update Warehouse attributes
            for warehouse_type, warehouses in self.warehouses.items():
                for warehouse in warehouses:
                    warehouse_id = warehouse['id']
                    # Update current capacity
                    new_capacity = self._generate_temporal_value(
                        warehouse['current_capacity'], 'capacity', time_period)

                    changes = {'capacity' : new_capacity}
                    self._log_node_operation("update", warehouse_id,"WAREHOUSE",changes)

                    period_graph.nodes[warehouse_id]['current_capacity'] = new_capacity
                    period_data[f"warehouse_{warehouse_id}_capacity"] = new_capacity

            # Update Supplier attributes
            for supplier in self.suppliers:
                supplier_id = supplier['id']
                new_reliability = self._generate_temporal_value(
                    supplier['reliability'], 'reliability', time_period)

                changes = {'reliability' : new_reliability}

                self._log_node_operation("update",supplier_id,"SUPPLIERS",changes)
                period_graph.nodes[supplier_id]['reliability'] = new_reliability
                period_data[f"supplier_{supplier_id}_reliability"] = new_reliability

            # Update Part attributes
            for part_type, parts in self.parts.items():
                for part in parts:
                    if part['valid_from'] <= current_date <= part['valid_till']:
                        part_id = part['id']
                        new_cost = self._generate_temporal_value(part['cost'], 'cost', time_period)

                        changes = {'cost' : new_cost}
                        self._log_node_operation("update",part_id,"PARTS", changes)

                        period_graph.nodes[part_id]['cost'] = new_cost
                        period_data[f"part_{part_id}_cost"] = new_cost

            # Update edge attributes
            for u, v, attrs in period_graph.edges(data=True):
                if 'transportation_cost' in attrs:
                    new_transport_cost = self._generate_temporal_value(attrs['transportation_cost'], 'transportation_cost', time_period)
                    changes = {'transportation_cost' : new_transport_cost}
                    self._log_edge_operation("update",u,v,changes,"SUPPLIERS_WAREHOUSE")

                    period_graph.edges[u, v]['transportation_cost'] = new_transport_cost
                    period_data[f"edge_{u}_{v}_transport_cost"] = new_transport_cost

                if 'inventory_level' in attrs:
                    new_inventory = self._generate_temporal_value(
                        attrs['inventory_level'], 'inventory', time_period)

                    changes = {'inventory_level' : new_inventory}
                    self._log_edge_operation("update",u,v,changes,"WAREHOUSE_PARTS")

                    period_graph.edges[u, v]['inventory_level'] = new_inventory
                    period_data[f"edge_{u}_{v}_inventory"] = new_inventory

            # Store both the complete graph snapshot and the period data
            self.temporal_graphs[time_period] = period_graph
            self.temporal_data[time_period] = period_data

    def _generate_part_validity(self):
        """Generate valid_from and valid_till dates for parts"""
        valid_from = BASE_DATE
        validity_months = random.randint(*PART_VALIDITY_RANGE)
        valid_till = valid_from + timedelta(days=30 * validity_months)
        return  valid_from,valid_till

    def _generate_suppliers(self):
        counter = 1
        for size_category, count in self.supplier_distribution.items():
            size_range = SUPPLIER_SIZES[size_category]['range']
            for _ in range(count):
                size_value = random.randint(*size_range)
                # Randomly assign part types this supplier can supply
                supplied_types = []
                if random.random() < 0.7:  # 70% chance to supply raw materials
                    supplied_types.extend(random.sample(PART_TYPES['raw'],
                                                        random.randint(1, len(PART_TYPES['raw']))))
                if random.random() < 0.3:  # 30% chance to supply subassemblies
                    supplied_types.extend(random.sample(PART_TYPES['subassembly'],
                                                        random.randint(1, len(PART_TYPES['subassembly']))))

                supplier_data = {
                    'id': f'S_{counter:03d}',
                    'name': f'Supplier_{counter}',
                    'location': random.choice(LOCATIONS),
                    'reliability': random.uniform(*RELIABILITY_RANGE),
                    'size': size_value,
                    'size_category': size_category,
                    'supplied_part_types': supplied_types
                }
                self.suppliers.append(supplier_data)

                self._log_node_operation("create", supplier_data['id'], "SUPPLIERS", supplier_data)
                self.G.add_node(supplier_data['id'], **supplier_data, node_type='supplier')

                counter += 1

    def _generate_business_hierarchy(self):
        """Generate business hierarchy including business group, product families, and offerings"""
        self.business_group = {
            'id': 'BG_001',
            'name': BUSINESS_GROUP,
            'description': f'{BUSINESS_GROUP} Business Unit',
            'revenue': random.uniform(*COST_RANGE)
        }

        # self.operations_log
        self._log_node_operation("create", self.business_group['id'], "BUSINESS_GROUP", self.business_group)

        self.G.add_node('BG_001', **self.business_group, node_type='business_group')

        for i, pf in enumerate(PRODUCT_FAMILIES, 1):
            pf_data = {
                'id': f'PF_{i:03d}',
                'name': pf,
                'revenue': random.uniform(*COST_RANGE)
            }
            self.product_families.append(pf_data)
            self._log_node_operation("create", pf_data['id'], "PRODUCT_FAMILY", pf_data)
            self.G.add_node(pf_data['id'], **pf_data, node_type='product_family')

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
                    self._log_node_operation("create", po_data['id'], "PRODUCT_OFFERING", po_data)
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
                self._log_node_operation("create",warehouse_data['id'],"WAREHOUSE",warehouse_data)
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
                self._log_node_operation("create",facility_data['id'],"FACILITY",facility_data)
                counter += 1

    def _generate_parts(self):
        counter = 1
        for p_type, count in self.parts_distribution.items():
            for _ in range(count):
                valid_from, valid_till = self._generate_part_validity()
                subtype = random.choice(PART_TYPES[p_type])
                part_data = {
                    'id': f'P_{counter:03d}',
                    'name': f'Part_{counter}',
                    'type': p_type,
                    'subtype': subtype,
                    'cost': random.uniform(*COST_RANGE),
                    'importance_factor': random.uniform(*IMPORTANCE_FACTOR_RANGE),
                    'valid_from': valid_from,
                    'valid_till': valid_till
                }
                copy_part_data = part_data.copy()
                copy_part_data['valid_from']  = copy_part_data['valid_from'].strftime('%Y-%m-%d')
                copy_part_data['valid_till'] = copy_part_data['valid_till'].strftime('%Y-%m-%d')
                self.parts[p_type].append(part_data)
                self.G.add_node(part_data['id'], **part_data, node_type='part')
                self._log_node_operation("create",part_data['id'],"PARTS",copy_part_data)
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

            # Connect to supplier warehouses for raw materials
            if any(t in PART_TYPES['raw'] for t in supplier['supplied_part_types']):
                possible_warehouses = self.warehouses['supplier']
                num_connections = min(max_connections, len(possible_warehouses))
                selected_warehouses = random.sample(possible_warehouses, num_connections)

                for warehouse in selected_warehouses:
                    edge_data = {
                        'transportation_cost': random.uniform(*TRANSPORTATION_COST_RANGE),
                        'lead_time': random.uniform(*TRANSPORTATION_TIME_RANGE)
                    }
                    self.G.add_edge(supplier['id'], warehouse['id'], **edge_data)
                    self._log_edge_operation("create",supplier['id'],warehouse['id'],edge_data,"SUPPLIERS_WAREHOUSE")

            # Connect to subassembly warehouses if supplier provides subassemblies
            if any(t in PART_TYPES['subassembly'] for t in supplier['supplied_part_types']):
                possible_warehouses = self.warehouses['subassembly']
                num_connections = min(max_connections, len(possible_warehouses))
                selected_warehouses = random.sample(possible_warehouses, num_connections)

                for warehouse in selected_warehouses:
                    edge_data = {
                        'transportation_cost': random.uniform(*TRANSPORTATION_COST_RANGE),
                        'lead_time': random.uniform(*TRANSPORTATION_TIME_RANGE)
                    }
                    self.G.add_edge(supplier['id'], warehouse['id'], **edge_data)
                    self._log_edge_operation("create", supplier['id'], warehouse['id'], edge_data,"SUPPLIERS_WAREHOUSE")

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
                self._log_edge_operation("create",warehouse['id'], part['id'],edge_data,"WAREHOUSE_PARTS")
                # Update warehouse current capacity
                self.G.nodes[warehouse['id']]['current_capacity'] = current_inventory
                changes = {'current_capacity': current_inventory}
                self._log_node_operation("update", warehouse['id'], "WAREHOUSE", changes)

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
                self._log_edge_operation("create", part['id'],facility['id'],edge_data,"PARTS_FACILITY")

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
                self._log_edge_operation("create",  facility['id'], part['id'],edge_data,"FACILITY_PARTS")

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
                self._log_edge_operation("create",  part['id'],facility['id'], edge_data,"PARTS_FACILITY")

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
                self._log_edge_operation("create",facility['id'], product['id'],edge_data,"FACILITY_PRODUCT_OFFERING")

                # Connect to LAM warehouse for storage
                for warehouse in self.warehouses['lam']:
                    edge_data = {
                        'inventory_level': random.randint(*INVENTORY_RANGE),
                        'storage_cost': random.uniform(*COST_RANGE)
                    }
                    self.G.add_edge(product['id'], warehouse['id'], **edge_data)
                    self._log_edge_operation("create", product['id'], warehouse['id'], edge_data,"PRODUCT_OFFERING_WAREHOUSE")

    def _connect_hierarchy(self):
        # Connect business group to product families
        for pf in self.product_families:
            self.G.add_edge('BG_001', pf['id'], type='hierarchy')
            self._log_edge_operation("create",'BG_001', pf['id'],{},"BUSINESS_GROUP_PROUDUCT_FAMILY")

        # Connect product families to their respective product offerings
        for pf in self.product_families:
            # Find all product offerings belonging to this family
            family_offerings = [
                po for po in self.product_offerings
                if po['name'] in PRODUCT_OFFERINGS[pf['name']]
            ]
            for po in family_offerings:
                self.G.add_edge(pf['id'], po['id'], type='hierarchy')
                self._log_edge_operation("create",pf['id'],po['id'],{},"PRODUCT_FAMILY_PRODUCT_OFFERING")

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
        """Return all generated data"""
        return self.data

    def get_temporal_data(self):
        """Return temporal data"""
        return self.temporal_data

    def get_graph_snapshot(self, time_period):
        """Return the complete graph snapshot for a specific time period"""
        return self.temporal_graphs.get(time_period)

    def get_all_temporal_graphs(self):
        """Return all temporal graph snapshots"""
        return self.temporal_graphs

    def get_node_distribution(self):
        """Return node distribution statistics"""
        return {
            'fixed_nodes': {
                'business_groups': self.FIXED_BUSINESS_GROUPS,
                'product_families': self.FIXED_PRODUCT_FAMILIES,
                'product_offerings': self.FIXED_PRODUCT_OFFERINGS
            },
            'variable_nodes': {
                'parts': self.parts_distribution,
                'suppliers': self.supplier_distribution,
                'warehouses': self.warehouse_distribution,
                'facilities': self.facility_distribution
            },
            'total_nodes': self.G.number_of_nodes()
        }

    def export_to_csv(self, export_dir='exports'):
        """Export all supply chain data with separate files for each node type and timestamp, including temporal attributes"""
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        # Export temporal data for each time period
        for period, graph in self.temporal_graphs.items():
            current_date = BASE_DATE + timedelta(days=30 * period)
            date_str = current_date.strftime('%Y%m%d')

            # Create period directory
            period_dir = f"{export_dir}/{date_str}"
            if not os.path.exists(period_dir):
                os.makedirs(period_dir)

            # Export Business Group with temporal revenue
            business_group_data = self.business_group.copy()
            if business_group_data['id'] in graph.nodes:
                business_group_data['revenue'] = graph.nodes[business_group_data['id']]['revenue']
                pd.DataFrame([business_group_data]).to_csv(
                    f"{period_dir}/business_group.csv", index=False)

            # Export Product Families with temporal revenue
            product_families_data = []
            for family in self.product_families:
                if family['id'] in graph.nodes:
                    family_data = family.copy()
                    family_data['revenue'] = graph.nodes[family['id']]['revenue']
                    product_families_data.append(family_data)
            if product_families_data:
                pd.DataFrame(product_families_data).to_csv(
                    f"{period_dir}/product_families.csv", index=False)

            # Export Product Offerings with temporal cost and demand
            product_offerings_data = []
            for offering in self.product_offerings:
                if offering['id'] in graph.nodes:
                    offering_data = offering.copy()
                    offering_node = graph.nodes[offering['id']]
                    offering_data.update({
                        'cost': offering_node['cost'],
                        'demand': offering_node['demand']
                    })
                    product_offerings_data.append(offering_data)
            if product_offerings_data:
                pd.DataFrame(product_offerings_data).to_csv(
                    f"{period_dir}/product_offerings.csv", index=False)

            # Export Suppliers with temporal reliability
            suppliers_data = []
            for supplier in self.suppliers:
                if supplier['id'] in graph.nodes:
                    supplier_data = supplier.copy()
                    supplier_node = graph.nodes[supplier['id']]
                    supplier_data['reliability'] = supplier_node['reliability']
                    suppliers_data.append(supplier_data)
            if suppliers_data:
                pd.DataFrame(suppliers_data).to_csv(
                    f"{period_dir}/suppliers.csv", index=False)

            # Export Warehouses with temporal current capacity
            warehouses_data = []
            for warehouse_type, warehouses in self.warehouses.items():
                for warehouse in warehouses:
                    if warehouse['id'] in graph.nodes:
                        warehouse_data = warehouse.copy()
                        warehouse_node = graph.nodes[warehouse['id']]
                        warehouse_data['current_capacity'] = warehouse_node['current_capacity']
                        warehouses_data.append(warehouse_data)
            if warehouses_data:
                pd.DataFrame(warehouses_data).to_csv(
                    f"{period_dir}/warehouses.csv", index=False)

            # Export Facilities (no temporal attributes currently)
            facilities_data = []
            for facility_type, facilities in self.facilities.items():
                for facility in facilities:
                    if facility['id'] in graph.nodes:
                        facilities_data.append(facility.copy())
            if facilities_data:
                pd.DataFrame(facilities_data).to_csv(
                    f"{period_dir}/facilities.csv", index=False)

            # Export Parts with temporal cost and validity period check
            parts_data = []
            for part_type, parts in self.parts.items():
                for part in parts:
                    if (part['valid_from'] <= current_date <= part['valid_till'] and
                            part['id'] in graph.nodes):
                        part_data = part.copy()
                        part_node = graph.nodes[part['id']]
                        part_data['cost'] = part_node['cost']
                        parts_data.append(part_data)
            if parts_data:
                pd.DataFrame(parts_data).to_csv(
                    f"{period_dir}/parts.csv", index=False)

            # Export edges with temporal attributes
            edges_data = []
            for u, v, data in graph.edges(data=True):
                # Only include edges where both nodes exist in the graph
                if u in graph.nodes and v in graph.nodes:
                    edge_data = {
                        'source_id': u,
                        'target_id': v,
                        'source_type': graph.nodes[u]['node_type'],
                        'target_type': graph.nodes[v]['node_type']
                    }

                    # Add temporal edge attributes
                    temporal_attributes = [
                        'transportation_cost', 'inventory_level', 'distance',
                        'lead_time', 'storage_cost', 'quantity', 'production_cost',
                        'product_cost'
                    ]

                    for attr in temporal_attributes:
                        if attr in data:
                            edge_data[attr] = data[attr]

                    edges_data.append(edge_data)

            if edges_data:
                pd.DataFrame(edges_data).to_csv(
                    f"{period_dir}/edges.csv", index=False)

            # Add metadata file to track node counts
            metadata = {
                'timestamp': date_str,
                'period': period,
                'total_nodes': len(graph.nodes),
                'total_edges': len(graph.edges),
                'suppliers_count': len([n for n, d in graph.nodes(data=True) if d.get('node_type') == 'supplier']),
                'warehouses_count': len([n for n, d in graph.nodes(data=True) if d.get('node_type') == 'warehouse']),
                'parts_count': len([n for n, d in graph.nodes(data=True) if d.get('node_type') == 'part'])
            }
            pd.DataFrame([metadata]).to_csv(f"{period_dir}/metadata.csv", index=False)

    def export_to_json(self, export_dir='exports_json', include_detailed_edges=True):
        """
        Export supply chain data to JSON format with comprehensive edge features

        Args:
            export_dir (str): Directory to export JSON files
            include_detailed_edges (bool): Flag to include detailed edge analysis
        """
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        # Export temporal data for each time period
        for period, graph in self.temporal_graphs.items():
            current_date = BASE_DATE + timedelta(days=30 * period)
            date_str = current_date.strftime('%Y%m%d')

            # Create period directory
            period_dir = f"{export_dir}/{date_str}"
            if not os.path.exists(period_dir):
                os.makedirs(period_dir)

            # Prepare comprehensive JSON structure
            supply_chain_data = {
                "timestamp": date_str,
                "period": period,
                "nodes": {},
                "edges": {
                    "connections": [],
                    "statistics": {
                        "total_edges": 0,
                        "edge_type_breakdown": {},
                        "connection_density": 0
                    },
                    "detailed_features": {}
                }
            }

            # Process nodes (same as previous implementation)
            for node_id, node_data in graph.nodes(data=True):
                node_type = node_data.get('node_type', 'unknown')

                node_info = node_data.copy()
                node_info['id'] = node_id

                if 'valid_from' in node_info and isinstance(node_info['valid_from'], datetime):
                    node_info['valid_from'] = node_info['valid_from'].strftime('%Y-%m-%d')
                if 'valid_till' in node_info and isinstance(node_info['valid_till'], datetime):
                    node_info['valid_till'] = node_info['valid_till'].strftime('%Y-%m-%d')

                if node_type not in supply_chain_data['nodes']:
                    supply_chain_data['nodes'][node_type] = []

                supply_chain_data['nodes'][node_type].append(node_info)

            # Enhanced Edge Processing
            edge_feature_mappings = {
                'suppliers_to_warehouses': ['transportation_cost', 'lead_time'],
                'warehouses_to_parts': ['inventory_level', 'storage_cost'],
                'parts_to_facilities': ['quantity', 'distance', 'transport_cost', 'lead_time'],
                'facilities_to_products': ['production_cost', 'lead_time', 'quantity'],
                'product_logistics': ['inventory_level', 'storage_cost']
            }

            # Process edges with detailed features
            for u, v, edge_data in graph.edges(data=True):
                source_type = graph.nodes[u].get('node_type', 'unknown')
                target_type = graph.nodes[v].get('node_type', 'unknown')

                # Determine edge category
                edge_category = f"{source_type}_to_{target_type}"

                # Prepare edge connection info
                edge_info = {
                    'source': u,
                    'target': v,
                    'source_type': source_type,
                    'target_type': target_type,
                    'connection_type': edge_category
                }

                # Add all edge attributes
                edge_info.update(edge_data)

                # Add to connections
                supply_chain_data['edges']['connections'].append(edge_info)

                # Update edge type breakdown
                supply_chain_data['edges']['statistics']['edge_type_breakdown'][edge_category] = \
                    supply_chain_data['edges']['statistics']['edge_type_breakdown'].get(edge_category, 0) + 1

                # Detailed edge feature tracking
                if include_detailed_edges:
                    for category, features in edge_feature_mappings.items():
                        if category not in supply_chain_data['edges']['detailed_features']:
                            supply_chain_data['edges']['detailed_features'][category] = {
                                'total_connections': 0,
                                'feature_summary': {}
                            }

                        if edge_category in category:
                            supply_chain_data['edges']['detailed_features'][category]['total_connections'] += 1

                            for feature in features:
                                if feature in edge_data:
                                    feature_values = supply_chain_data['edges']['detailed_features'][category][
                                        'feature_summary'].get(feature, [])
                                    feature_values.append(edge_data[feature])
                                    supply_chain_data['edges']['detailed_features'][category]['feature_summary'][
                                        feature] = feature_values

            # Calculate total edges and connection density
            supply_chain_data['edges']['statistics']['total_edges'] = len(graph.edges())
            total_possible_edges = len(graph.nodes()) * (len(graph.nodes()) - 1)
            supply_chain_data['edges']['statistics']['connection_density'] = \
                len(graph.edges()) / total_possible_edges if total_possible_edges > 0 else 0

            # Compute summary statistics for detailed features
            if include_detailed_edges:
                for category, details in supply_chain_data['edges']['detailed_features'].items():
                    for feature, values in details['feature_summary'].items():
                        if values:
                            details['feature_summary'][feature] = {
                                'min': min(values),
                                'max': max(values),
                                'average': sum(values) / len(values)
                            }

            # Write JSON file
            json_filename = f"{period_dir}/supply_chain_detailed.json"
            with open(json_filename, 'w') as f:
                json.dump(supply_chain_data, f, indent=2, default=str)

            print(f"Exported detailed JSON for period {period} to {json_filename}")

    def export_to_json_all_timestamps(self):
        """
        Export the supply chain graph data for all time periods

        Returns:
            dict: Comprehensive supply chain data across all timestamps
        """
        # Create a comprehensive export dictionary
        export_data = {
            "metadata": {
                "total_timestamps": len(self.temporal_graphs),
                "base_date": str(BASE_DATE),
                "total_nodes": len(self.G.nodes()),
                "total_edges": len(self.G.edges())
            },
            "timestamps": {}
        }

        # Export data for each timestamp
        for timestamp, graph in self.temporal_graphs.items():
            # Create timestamp-specific export
            current_date = BASE_DATE + timedelta(days=30 * timestamp)
            timestamp_export = {
                "directed": True,
                "multigraph": False,
                "graph": {
                    "date": str(current_date)
                },
                "node_types": {
                    "BusinessGroup": ["node_type", "name", "description", "revenue", "id"],
                    "ProductFamily": ["node_type", "name", "revenue", "id"],
                    "ProductOffering": ["node_type", "name", "cost", "demand", "id"],
                    "Supplier": ["node_type", "name", "location", "reliability", "size", "size_category",
                                 "supplied_part_types", "id"],
                    "Warehouse": ["node_type", "name", "type", "location", "size_category", "max_capacity",
                                  "current_capacity", "safety_stock", "max_parts", "id"],
                    "Facility": ["node_type", "name", "type", "location", "max_capacity", "operating_cost", "id"],
                    "Parts": ["node_type", "name", "type", "subtype", "cost", "importance_factor", "valid_from",
                              "valid_till", "id"]
                },
                "relationship_types": {
                    "SupplierToWarehouse": ["relationship_type", "transportation_cost", "lead_time", "source",
                                            "target"],
                    "WarehouseToParts": ["relationship_type", "inventory_level", "storage_cost", "source", "target"],
                    "PartsToFacility": ["relationship_type", "quantity", "distance", "transport_cost", "lead_time",
                                        "source", "target"],
                    "FacilityToParts": ["relationship_type", "production_cost", "lead_time", "quantity", "source",
                                        "target"],
                    "FacilityToProductOfferings": ["relationship_type", "product_cost", "lead_time", "quantity",
                                                   "source", "target"],
                    "HierarchicalRelationship": ["relationship_type", "source", "target"]
                },
                "node_values": {},
                "relationship_values": []
            }

            # Helper function to convert datetime to string
            def datetime_to_string(dt):
                return dt.strftime("%Y-%m-%d") if dt else None

            # Node type mapping
            node_type_mapping = {
                'business_group': 'BusinessGroup',
                'product_family': 'ProductFamily',
                'product_offering': 'ProductOffering',
                'supplier': 'Supplier',
                'warehouse': 'Warehouse',
                'facility': 'Facility',
                'part': 'Parts'
            }

            # Collect nodes for each type
            for node, data in graph.nodes(data=True):
                node_type = node_type_mapping.get(data.get('node_type'))
                if not node_type:
                    continue

                # Prepare node values based on node type
                node_values = timestamp_export['node_types'][node_type]
                node_data = []

                for attr in node_values:
                    if attr == 'node_type':
                        node_data.append(node_type)
                    elif attr == 'valid_from' or attr == 'valid_till':
                        node_data.append(datetime_to_string(data.get(attr)))
                    else:
                        node_data.append(data.get(attr, None))

                # Add to node values
                timestamp_export['node_values'].setdefault(node_type, []).append(node_data)

            # Collect relationship values
            for source, target, edge_data in graph.edges(data=True):
                source_node = graph.nodes[source]
                target_node = graph.nodes[target]

                # Determine relationship type
                rel_type = 'HierarchicalRelationship'
                rel_attrs = ['source', 'target']

                if source_node.get('node_type') == 'supplier' and target_node.get('node_type') == 'warehouse':
                    rel_type = 'SupplierToWarehouse'
                    rel_attrs = ['relationship_type', 'transportation_cost', 'lead_time', 'source', 'target']

                elif source_node.get('node_type') == 'warehouse' and target_node.get('node_type') == 'part':
                    rel_type = 'WarehouseToParts'
                    rel_attrs = ['relationship_type', 'inventory_level', 'storage_cost', 'source', 'target']

                elif source_node.get('node_type') == 'part' and target_node.get('node_type') == 'facility':
                    rel_type = 'PartsToFacility'
                    rel_attrs = ['relationship_type', 'quantity', 'distance', 'transport_cost', 'lead_time', 'source',
                                 'target']

                elif source_node.get('node_type') == 'facility' and target_node.get('node_type') == 'part':
                    rel_type = 'FacilityToParts'
                    rel_attrs = ['relationship_type', 'production_cost', 'lead_time', 'quantity', 'source', 'target']

                elif source_node.get('node_type') == 'facility' and target_node.get('node_type') == 'product_offering':
                    rel_type = 'FacilityToProductOfferings'
                    rel_attrs = ['relationship_type', 'product_cost', 'lead_time', 'quantity', 'source', 'target']

                # Prepare relationship data
                rel_data = []
                # print(" ________________________________________________________________")
                # print("The edge data is as follows :")
                #
                # print(edge_data)
                # print("================================")
                # rel_data.append(rel_type)
                for attr in rel_attrs:

                    if attr == 'source':
                        rel_data.append(source)
                    elif attr == 'target':
                        rel_data.append(target)
                    elif attr == 'relationship_type':
                        rel_data.append(rel_type)
                    else:
                        rel_data.append(edge_data.get(attr, None))

                timestamp_export['relationship_values'].append(rel_data)

            # Store this timestamp's export
            export_data['timestamps'][timestamp] = timestamp_export

        return export_data

    def save_export_to_file(self, directory='supply_chain_export'):
        """
        Save the full export to a directory with separate JSON files for each timestamp

        Args:
            directory (str): Output directory for the JSON exports
        """
        import json
        import os

        # Create the directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)

        # Get the full export data
        export_data = self.export_to_json_all_timestamps()

        # Save metadata file
        metadata_path = os.path.join(directory, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(export_data['metadata'], f, indent=2)

        # Save each timestamp in a separate file
        for timestamp, timestamp_data in export_data['timestamps'].items():
            # Create a filename based on the timestamp
            filename = f'timestamp_{timestamp}.json'
            filepath = os.path.join(directory, filename)

            # Write the timestamp-specific data
            with open(filepath, 'w') as f:
                json.dump(timestamp_data, f, indent=2)

        print(f"Export saved to directory: {directory}")
