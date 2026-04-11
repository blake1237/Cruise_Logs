#!/usr/bin/env python
"""
Streamlit app to search the release inventory by serial number
"""

import streamlit as st
import sqlite3
import pandas as pd
from config import DB_PATH

# Set page config
st.set_page_config(page_title="Release Inventory Search", layout="wide")

# Title
st.title("Acoustic Release Inventory Search")

# Database connection
@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

conn = get_connection()

# Search interface
st.subheader("Search by Serial Number")

search_term = st.text_input("Enter Instrument Serial Number:", "")

# Search button
if st.button("Search") or search_term:
    if search_term:
        # Query the database
        query = """
        SELECT * FROM release_inventory
        WHERE System_Serial_Num LIKE ?
        ORDER BY System_Serial_Num
        """

        try:
            df = pd.read_sql_query(query, conn, params=(f"%{search_term}%",))

            if len(df) > 0:
                st.success(f"Found {len(df)} result(s)")

                # Display results
                for idx, row in df.iterrows():
                    with st.expander(f"Serial #: {row['System_Serial_Num']} - {row['Type_Model']}"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write("**Basic Information:**")
                            st.write(f"Equipment ID: {row['Equipment_ID']}")
                            st.write(f"Serial Number: {row['System_Serial_Num']}")
                            st.write(f"Type/Model: {row['Type_Model']}")
                            st.write(f"Status: {row['Status']}")
                            st.write(f"Mechanism: {row['Mechanism']}")
                            st.write(f"Transponder: {row['Transponder']}")

                            st.write("\n**Dates:**")
                            st.write(f"Purchase Date: {row['Purchase_Date']}")
                            st.write(f"Battery Date: {row['Battery_Date']}")
                            st.write(f"Battery Life: {row['Battery_Life_yrs']} yrs")
                            st.write(f"Retired Date: {row['Retired_Date']}")

                        with col2:
                            st.write("**Technical Specs:**")
                            st.write(f"Interrogate Freq: {row['Interrogate_Freq_khz']} kHz")
                            st.write(f"Reply Freq: {row['Reply_Freq_kHz']} kHz")
                            st.write(f"Operational Depth: {row['Operational_Depth_m']} m")
                            st.write(f"Release Load: {row['Release_Load']}")
                            st.write(f"Enable/Disable: {row['Enable_Disable']}")

                            st.write("\n**Commands:**")
                            st.write(f"CMD 1 (Release): {row['CMD_1___Release_Code']}")
                            st.write(f"CMD 2 (Disable): {row['CMD_2___Disable_A_plus_B']}")
                            st.write(f"CMD 3 (Enable A): {row['CMD_3___Enable_A']}")
                            st.write(f"CMD 4 (Enable B): {row['CMD_4___Enable_B']}")

                        # Additional info
                        if pd.notna(row['Additional_Notes']):
                            st.write("**Additional Notes:**")
                            st.write(row['Additional_Notes'])

                        if pd.notna(row['PMEL___EDD_Comments']):
                            st.write("**PMEL/EDD Comments:**")
                            st.write(row['PMEL___EDD_Comments'])

                        # Show all data in expandable section
                        with st.expander("View All Fields"):
                            st.write(row.to_dict())
            else:
                st.warning("No results found for that serial number")
        except Exception as e:
            st.error(f"Error querying database: {e}")
    else:
        st.info("Please enter a serial number to search")

# Show all records option
st.markdown("---")
if st.checkbox("Show All Inventory"):
    try:
        df_all = pd.read_sql_query(
            "SELECT Equipment_ID, System_Serial_Num, Type_Model, Status, Mechanism, Transponder FROM release_inventory ORDER BY System_Serial_Num",
            conn
        )
        st.dataframe(df_all, use_container_width=True)
        st.info(f"Total inventory items: {len(df_all)}")
    except Exception as e:
        st.error(f"Error loading inventory: {e}")
