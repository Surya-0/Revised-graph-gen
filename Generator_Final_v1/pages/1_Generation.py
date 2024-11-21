        
import streamlit as st
import pandas as pd
import os
import requests
from data_generator import SupplyChainGenerator
import time
import plotly.express as px
from datetime import datetime


def initialize_session_state():
    if 'generator' not in st.session_state:
        st.session_state.generator = None
    if 'current_period' not in st.session_state:
        st.session_state.current_period = 0


def export_data(generator, export_dir):
    try:
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        generator.export_to_csv(export_dir)
        # generator.save_export_to_file()
        return True, f"Data successfully exported to {export_dir}"
    except Exception as e:
        return False, f"Error exporting data: {str(e)}"


def export_to_server(generator, url):
    try:
        export_list = generator.return_operation()
        # for i in range(20):
        # print(export_list[i])
        for i in range(0,len(export_list),2000):
            requests.post(f"{url}/schema/live/update/bulk", json=export_list[i:i+2000])
            time.sleep(0.5)
            # st.write("Batch",i," has been sent to the server")
            # print()
        return True, f"Data successfully exported to Server"
    except Exception as e:
        return False, f"Error exporting data: {str(e)}"


def main():
    st.title("Supply Chain Data Generation and Simulation")
    url = "https://bug-hardy-obviously.ngrok-free.app"
    initialize_session_state()

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        total_nodes = st.number_input(
            "Total Variable Nodes",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100
        )
        base_periods = st.number_input(
            "Base Time Periods",
            min_value=1,
            max_value=24,
            value=12,
            step=1
        )
        version = st.text_input("Enter the version")

    # Main area tabs
    tab1, tab2 = st.tabs(["Generate Data", "Simulation Control"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Generate New Supply Chain"):
                with st.spinner("Generating supply chain data..."):
                    st.session_state.generator = SupplyChainGenerator(
                        total_variable_nodes=total_nodes,
                        base_periods=base_periods,
                        version=version
                    )
                    st.session_state.generator.generate_data()
                    st.success("✅ Initial data generation complete!")

        with col2:
            if st.session_state.generator is not None:
                export_dir = st.text_input(
                    "Export Directory",
                    value="exports",
                    help="Specify the directory where CSV files will be saved"
                )

                col3,col4 = st.columns(2)
                with col3:
                        if st.button("Export to CSV"):
                            with st.spinner("Exporting data to CSV..."):
                                success, message = export_data(st.session_state.generator, export_dir)
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)

                with col4:

                    if st.button("Export to server"):
                        with st.spinner("Exporting data to Server..."):
                            success, message = export_to_server(st.session_state.generator, url)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)

    with tab2:
        if st.session_state.generator is not None:
            col1, col2 = st.columns(2)

            with col1:
                if st.button("Regenerate All Periods"):
                    st.session_state.generator.regenerate_all_periods()
                    st.success("✅ Data regenerated!")

            with col2:
                additional_periods = st.number_input(
                    "Number of Additional Periods",
                    min_value=1,
                    max_value=12,
                    value=1
                )
                if st.button("Simulate Additional Periods"):
                    new_periods = st.session_state.generator.simulate_multiple_periods(
                        additional_periods)
                    st.success(f"✅ Generated {len(new_periods)} new periods!")

            # Export section for simulation tab
            st.subheader("Export Simulation Data")
            col3, col4 = st.columns(2)

            with col3:
                export_dir = st.text_input(
                    "Export Directory (Simulation)",
                    value=f"exports",
                    help="Specify the directory where simulation CSV files will be saved"
                )

            with col4:
                if st.button("Export Simulation to CSV"):
                    with st.spinner("Exporting simulation data to CSV..."):
                        success, message = export_data(st.session_state.generator, export_dir)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)


        else:
            st.info("Please generate initial supply chain data first.")


if __name__ == "__main__":
    main()

