# app.py
import sys
import streamlit as st
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import streamlit.components.v1 as components
from data_generator import SupplyChainGenerator
from Supply_chain_manager import SupplyChainManager
from graph_analyzer import SupplyChainAnalyzer
from config import *
import time
import pickle



# Set page config
st.set_page_config(
    page_title="Supply Chain Management",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem;
        border: none;
        border-radius: 4px;
    }
    .stSelectbox {
        margin-bottom: 1rem;
    }
    .stPlotlyChart {
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


class SupplyChainApp:
    def __init__(self):
        if 'generator' not in st.session_state:
            st.session_state.generator = None
        if 'manager' not in st.session_state:
            st.session_state.manager = None
        if 'page' not in st.session_state:
            st.session_state.page = 'Overview'
        if 'complexity_data' not in st.session_state:
            st.session_state.complexity_data = []

    def run(self):
        st.sidebar.title('📊 Supply Chain Management')
        pages = {
            'Overview': self.overview_page,
            'Graph Generation': self.generation_page,
            'Node Management': self.node_management_page,
            'Graph Details': self.graph_details_page,
            'Graph Visualization': self.enhanced_visualization_page,
            'Complexity Analysis': self.complexity_analysis_page,
        }

        st.session_state.page = st.sidebar.selectbox('Navigation', list(pages.keys()))
        pages[st.session_state.page]()

    def overview_page(self):
        st.title("Supply Chain Overview")
        st.markdown("""
        This application provides a comprehensive view of our supply chain network. 
        The diagram below shows the hierarchical structure of our supply chain.
        """)

        # Mermaid diagram
        mermaid_diagram = """
        graph TD
            subgraph "Level 5: Business Units"
                BU[Business Unit]
            end

            subgraph "Level 4: Final Products"
                P1[Final Product 1]
                P2[Final Product 2]
            end

            subgraph "Level 3: Assembly & Storage"
                LW[Lam Warehouse]
                LF[Lam Factory/Facility]
            end

            subgraph "Level 2: Sub-Assemblies"
                SA1[Sub-Assembly 1]
                SA2[Sub-Assembly 2]
                SAW[Sub-Assembly Warehouse]
                EF[External Facility]
            end

            subgraph "Level 1: Raw Materials & Parts"
                S1[Supplier 1]
                S2[Supplier 2]
                SW[Supplier Warehouse]
                RP1[Raw Part 1]
                RP2[Raw Part 2]
            end

            S1 --> SW
            S2 --> SW
            SW --> RP1
            SW --> RP2
            RP1 --> EF
            RP2 --> EF

            EF --> SA1
            EF --> SA2
            SA1 --> SAW
            SA2 --> SAW

            SAW --> LF
            LF --> LW

            LW --> P1
            LW --> P2

            P1 --> BU
            P2 --> BU

            classDef businessUnit fill:#4B0082,stroke:#333,stroke-width:2px,color:#FFFFFF
            classDef product fill:#1E90FF,stroke:#333,stroke-width:2px,color:#FFFFFF
            classDef warehouse fill:#228B22,stroke:#333,stroke-width:1px,color:#FFFFFF
            classDef facility fill:#B8860B,stroke:#333,stroke-width:1px,color:#FFFFFF
            classDef supplier fill:#8B0000,stroke:#333,stroke-width:1px,color:#FFFFFF
            classDef parts fill:#4682B4,stroke:#333,stroke-width:1px,color:#FFFFFF

            class BU businessUnit
            class P1,P2 product
            class LW,SAW,SW warehouse
            class LF,EF facility
            class S1,S2 supplier
            class RP1,RP2,SA1,SA2 parts
        """

        # Display mermaid diagram using HTML component
        components.html(
            f"""
            <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
            <script>mermaid.initialize({{startOnLoad:true}});</script>
            <div class="mermaid">
                {mermaid_diagram}
            </div>
            """,
            height=1300,
        )

    def generation_page(self):
        st.title("Generate Supply Chain Network")

        with st.form("generate_network"):
            total_nodes = st.slider("Total number of variable nodes", 100, 10000, 1000)
            submitted = st.form_submit_button("Generate Network")

            if submitted:
                with st.spinner("Generating supply chain network..."):
                    st.session_state.generator = SupplyChainGenerator(total_nodes)
                    st.session_state.generator.generate_data()
                    st.session_state.manager = SupplyChainManager(st.session_state.generator)
                    st.success("Network generated successfully!")

                    # Display network statistics
                    stats = st.session_state.generator.get_node_distribution()

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Fixed Nodes")
                        for k, v in stats['fixed_nodes'].items():
                            st.metric(k.replace('_', ' ').title(), v)

                    with col2:
                        st.subheader("Variable Nodes")
                        for k, v in stats['variable_nodes'].items():
                            if isinstance(v, dict):
                                st.write(f"**{k.title()}**")
                                for sub_k, sub_v in v.items():
                                    st.metric(f"{sub_k}", sub_v)
                            else:
                                st.metric(k.title(), v)

    def node_management_page(self):
        st.title("Node Management")

        if not st.session_state.manager:
            st.warning("Please generate a network first!")
            return

        node_type = st.selectbox("Select node type to add",
                                 ["Supplier", "Warehouse", "Facility", "Part"])

        if node_type == "Supplier":
            with st.form("add_supplier"):
                st.subheader("Add New Supplier")
                name = st.text_input("Name")
                location = st.selectbox("Location", LOCATIONS)
                reliability = st.slider("Reliability", 0.6, 0.99, 0.8)
                size = st.slider("Size", 100, 1000, 500)

                if st.form_submit_button("Add Supplier"):
                    new_id = st.session_state.manager.add_supplier(
                        name=name,
                        location=location,
                        reliability=reliability,
                        size=size
                    )
                    st.success(f"Added supplier with ID: {new_id}")

        elif node_type == "Warehouse":
            with st.form("add_warehouse"):
                st.subheader("Add New Warehouse")
                name = st.text_input("Name")
                w_type = st.selectbox("Type", WAREHOUSE_TYPES)
                location = st.selectbox("Location", LOCATIONS)
                max_capacity = st.slider("Max Capacity", 1000, 10000, 5000)

                if st.form_submit_button("Add Warehouse"):
                    new_id = st.session_state.manager.add_warehouse(
                        name=name,
                        warehouse_type=w_type,
                        location=location,
                        max_capacity=max_capacity
                    )
                    st.success(f"Added warehouse with ID: {new_id}")



    def enhanced_visualization_page(self):
        st.title("Supply Chain Visualization")

        if not st.session_state.manager:
            st.warning("Please generate a network first!")
            return

        # Create network visualization using Plotly
        G = st.session_state.manager.G
        pos = nx.spring_layout(G, k=1 / np.sqrt(len(G.nodes())), iterations=50)



        # Create edges trace
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edges_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')

        # Create nodes trace
        node_x = []
        node_y = []
        node_text = []
        node_color = []

        color_map = {
            'supplier': '#8B0000',
            'warehouse': '#228B22',
            'facility': '#B8860B',
            'part': '#4682B4',
            'product_offering': '#1E90FF',
            'product_family': '#4B0082',
            'business_group': '#4B0082'
        }

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_type = G.nodes[node].get('node_type', 'unknown')
            node_text.append(f"ID: {node}<br>Type: {node_type}")
            node_color.append(color_map.get(node_type, '#000000'))

        nodes_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                color=node_color,
                size=10,
                line_width=2))

        # Create the figure
        fig = go.Figure(data=[edges_trace, nodes_trace],
                        layout=go.Layout(
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=20, l=5, r=5, t=40),
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                        )

        st.plotly_chart(fig, use_container_width=True)

    import sys

    def complexity_analysis_page(self):
        st.title("Complexity Analysis")

        # Node sizes for analysis
        node_sizes = [100, 200, 500, 1000,1500, 2000,2500,5000,7500,10000]

        if st.button("Run Complexity Analysis"):
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, size in enumerate(node_sizes):
                status_text.text(f"Analyzing network with {size} nodes...")

                # Measure generation time
                start_time = time.time()
                generator = SupplyChainGenerator(size)
                generator.generate_data()
                end_time = time.time()

                generation_time = end_time - start_time
                memory_usage = sys.getsizeof(generator.G)  # Measure memory usage

                results.append({
                    'nodes': size,
                    'time': generation_time,
                    'memory': memory_usage,
                    'edges': len(generator.G.edges())
                })

                progress_bar.progress((i + 1) / len(node_sizes))

            status_text.text("Analysis complete!")
            st.session_state.complexity_data = results

            # Create visualization of results
            self.plot_complexity_results(results)

    def plot_complexity_results(self, results):
        # Convert results to DataFrame
        df = pd.DataFrame(results)

        # Create time complexity plot
        fig1 = px.line(df, x='nodes', y='time',
                       title='Time Complexity Analysis',
                       labels={'nodes': 'Number of Nodes', 'time': 'Generation Time (seconds)'})
        st.plotly_chart(fig1)

        # Create space complexity plot (using memory usage)
        fig2 = px.line(df, x='nodes', y='memory',
                       title='Space Complexity Analysis',
                       labels={'nodes': 'Number of Nodes', 'memory': 'Memory Usage (bytes)'})
        st.plotly_chart(fig2)


        # Nodes vs edges
        fig3 = px.line(df, x='nodes', y='edges',
                       title='Graph Size Analysis',
                       labels={'nodes': 'Number of Nodes', 'edges': 'Number of Edges'})
        st.plotly_chart(fig3)

        # Display results table
        st.subheader("Detailed Results")
        st.dataframe(df.round(3))

        # Calculate and display complexity class approximation
        times = df['time'].values
        nodes = df['nodes'].values

        # Calculate growth rate
        growth_rate = np.polyfit(np.log(nodes), np.log(times), 1)[0]

        st.subheader("Complexity Analysis")
        st.write(f"Approximate Time Complexity: O(n^{growth_rate:.2f})")

        # Provide interpretation
        if growth_rate <= 1.2:
            complexity_class = "Linear (O(n))"
        elif growth_rate <= 2.2:
            complexity_class = "Quadratic (O(n²))"
        elif growth_rate <= 3.2:
            complexity_class = "Cubic (O(n³))"
        else:
            complexity_class = "Higher-order polynomial"

        st.write(f"Estimated Complexity Class: {complexity_class}")
    def graph_details_page(self):
        st.title("Graph Details")

        if not st.session_state.manager:
            st.warning("Please generate a network first!")
            return

        # Create columns for different metrics
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Basic Graph Metrics")
            G = st.session_state.manager.G
            metrics = {
                "Total Nodes": G.number_of_nodes(),
                "Total Edges": G.number_of_edges(),
                "Average Degree": np.mean([d for n, d in G.degree()]),
                "Graph Density": nx.density(G)
            }

            for metric, value in metrics.items():
                st.metric(metric, f"{value:.2f}" if isinstance(value, float) else value)

        with col2:
            st.subheader("Node Type Distribution")
            node_types = {}
            for node, data in G.nodes(data=True):
                node_type = data.get('node_type', 'unknown')
                node_types[node_type] = node_types.get(node_type, 0) + 1

            # Create a DataFrame for better display
            df = pd.DataFrame(list(node_types.items()), columns=['Node Type', 'Count'])
            st.dataframe(df)

        # Add export functionality
        st.subheader("Export Graph Data")
        if st.button("Export to CSV"):
            try:
                export_path = "exports"
                st.session_state.manager.export_to_csv(export_path)
                st.success(f"Data exported successfully to {export_path} directory!")
            except Exception as e:
                st.error(f"Error exporting data: {str(e)}")

            # Add save to pickle functionality
        st.subheader("Save Graph Object")
        if st.button("Save to Pickle"):
            try:
                with open("graph_object.pkl", "wb") as f:
                    pickle.dump(G, f)
                st.success("Graph object saved to graph_object.pkl")
            except Exception as e:
                st.error(f"Error saving graph object: {str(e)}")

        # Display detailed analysis plots
        st.subheader("Graph Analysis")

        # Create tabs for different plots
        plot_tab1, plot_tab2, plot_tab3 = st.tabs(["Node Distribution", "Degree Distribution", "Connection Analysis"])

        analyzer = SupplyChainAnalyzer(G)

        with plot_tab1:
            st.subheader("Node Type Distribution")
            fig1 = plt.figure(figsize=(10, 6))
            analyzer.plot_node_distribution()
            st.pyplot(fig1)

        with plot_tab2:
            st.subheader("Node Degree Distribution")
            fig2 = plt.figure(figsize=(10, 6))
            analyzer.plot_degree_distribution()
            st.pyplot(fig2)

        with plot_tab3:
            st.subheader("Supplier Connections")
            fig3 = plt.figure(figsize=(12, 6))
            analyzer.plot_supplier_connections()
            st.pyplot(fig3)




if __name__ == "__main__":
    app = SupplyChainApp()
    app.run()