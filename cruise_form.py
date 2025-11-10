import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import os

# Database configuration
DB_PATH = os.path.expanduser("~/Github/Cruise_Logs/Cruise_Logs.db")

# Page configuration
st.set_page_config(
    page_title="Cruise Information Management",
    page_icon="🚢",
    layout="wide"
)

# Database connection
def get_connection():
    """Create a database connection"""
    return sqlite3.connect(DB_PATH)

def parse_date(date_value):
    """Parse date from various formats"""
    if pd.isna(date_value) or date_value is None:
        return None

    # If already a datetime object
    if isinstance(date_value, (datetime, date)):
        return pd.to_datetime(date_value)

    # Try different formats
    formats = ['%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d', '%d/%m/%Y']
    for fmt in formats:
        try:
            return pd.to_datetime(date_value, format=fmt)
        except:
            continue

    # Last resort - let pandas infer
    try:
        return pd.to_datetime(date_value)
    except:
        return None

def get_cruise_data():
    """Get all cruise data"""
    conn = get_connection()
    query = """
    SELECT
        id,
        Beginning_Date as 'Beginning Date',
        Cruise,
        Ending_Date as 'Ending Date',
        Leg,
        Lines,
        Personnel,
        Port1,
        Port2,
        Port3,
        Ship
    FROM Cruise_Info
    ORDER BY Beginning_Date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    return df

def insert_cruise(data):
    """Insert a new cruise record"""
    conn = get_connection()
    cursor = conn.cursor()

    columns = ', '.join([f'"{k}"' for k in data.keys()])
    placeholders = ', '.join(['?' for _ in data])
    values = tuple(data.values())

    query = f"INSERT INTO Cruise_Info ({columns}) VALUES ({placeholders})"
    cursor.execute(query, values)
    conn.commit()
    conn.close()

def get_unique_values(column):
    """Get unique values for a column (for dropdowns)"""
    conn = get_connection()
    query = f'SELECT DISTINCT "{column}" FROM Cruise_Info WHERE "{column}" IS NOT NULL ORDER BY "{column}"'
    result = pd.read_sql_query(query, conn)
    conn.close()
    return result[column].tolist()

# Main app
st.title("🚢 Cruise Information Management System")

# Create tabs
tab1, tab2 = st.tabs(["📊 View & Search", "➕ Add New Cruise"])

# Tab 1: View & Search
with tab1:
    st.header("View and Search Cruises")

    # Search filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        search_cruise = st.text_input("Search by Cruise Name", "")

    with col2:
        ships = ["All"] + get_unique_values("Ship")
        selected_ship = st.selectbox("Filter by Ship", ships)

    with col3:
        lines = ["All"] + get_unique_values("Lines")
        selected_line = st.selectbox("Filter by Line", lines)

    with col4:
        search_personnel = st.text_input("Search Personnel", placeholder="e.g., Stratton")

    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=None)
    with col2:
        end_date = st.date_input("End Date", value=None)

    # Get and filter data
    df = get_cruise_data()

    # Apply filters
    if search_cruise:
        df = df[df['Cruise'].str.contains(search_cruise, case=False, na=False)]

    if selected_ship != "All":
        df = df[df['Ship'] == selected_ship]

    if selected_line != "All":
        df = df[df['Lines'] == selected_line]

    if search_personnel:
        df = df[df['Personnel'].str.contains(search_personnel, case=False, na=False)]

    if start_date:
        df['Beginning Date'] = df['Beginning Date'].apply(parse_date)
        df = df[df['Beginning Date'] >= pd.to_datetime(start_date)]

    if end_date:
        df['Ending Date'] = df['Ending Date'].apply(parse_date)
        df = df[df['Ending Date'] <= pd.to_datetime(end_date)]

    # Display results
    st.subheader(f"Found {len(df)} cruises")

    # Show data in a nice format
    if not df.empty:
        # Add a checkbox to show/hide ID column
        show_id = st.checkbox("Show ID column", value=False)

        if not show_id:
            display_df = df.drop('id', axis=1)
        else:
            display_df = df

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Beginning Date": st.column_config.DateColumn(
                    "Beginning Date",
                    format="MMM DD, YYYY"
                ),
                "Ending Date": st.column_config.DateColumn(
                    "Ending Date",
                    format="MMM DD, YYYY"
                ),
                "Leg": st.column_config.NumberColumn(
                    "Leg",
                    format="%d"
                )
            }
        )

        # Export option
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"cruise_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No cruises found matching your criteria.")

# Tab 2: Add New Cruise
with tab2:
    st.header("Add New Cruise")

    with st.form("add_cruise_form"):
        col1, col2 = st.columns(2)

        with col1:
            cruise_name = st.text_input("Cruise Name*", placeholder="Enter cruise name")
            ship = st.text_input("Ship*", placeholder="Enter ship name")
            lines = st.text_input("Lines", placeholder="Enter cruise line")
            personnel = st.text_input("Personnel", placeholder="Enter personnel")
            leg = st.number_input("Leg", min_value=0, value=0, step=1)

        with col2:
            beginning_date = st.date_input("Beginning Date*")
            ending_date = st.date_input("Ending Date*")
            port1 = st.text_input("Port 1", placeholder="First port")
            port2 = st.text_input("Port 2", placeholder="Second port")
            port3 = st.text_input("Port 3", placeholder="Third port")

        st.markdown("*Required fields")

        submitted = st.form_submit_button("Add Cruise", type="primary")

        if submitted:
            if cruise_name and ship and beginning_date and ending_date:
                # Validate dates
                if ending_date < beginning_date:
                    st.error("Ending date must be after beginning date!")
                else:
                    # Prepare data
                    new_cruise = {
                        "Cruise": cruise_name,
                        "Ship": ship,
                        "Lines": lines if lines else None,
                        "Personnel": personnel if personnel else None,
                        "Leg": leg if leg > 0 else None,
                        "Beginning_Date": beginning_date.strftime("%Y-%m-%d"),
                        "Ending_Date": ending_date.strftime("%Y-%m-%d"),
                        "Port1": port1 if port1 else None,
                        "Port2": port2 if port2 else None,
                        "Port3": port3 if port3 else None
                    }

                    try:
                        insert_cruise(new_cruise)
                        st.success("✅ Cruise added successfully!")
                        st.balloons()

                        # Clear form by rerunning
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding cruise: {e}")
            else:
                st.error("Please fill in all required fields!")

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        Cruise Information Management System v1.0 |
        Database: <code>~/Apps/databases/my_database.db</code>
    </div>
    """,
    unsafe_allow_html=True
)
