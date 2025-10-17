import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import os

# Database configuration
DB_PATH = os.path.expanduser("~/Apps/databases/Cruise_Logs.db")

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

def update_cruise(cruise_id, data):
    """Update an existing cruise record"""
    conn = get_connection()
    cursor = conn.cursor()

    set_clause = ', '.join([f'"{k}" = ?' for k in data.keys()])
    values = list(data.values()) + [cruise_id]

    query = f"UPDATE Cruise_Info SET {set_clause} WHERE id = ?"
    cursor.execute(query, values)
    conn.commit()
    conn.close()

def delete_cruise(cruise_id):
    """Delete a cruise record"""
    # Ensure cruise_id is an integer
    cruise_id = int(cruise_id)

    conn = get_connection()
    cursor = conn.cursor()

    # First check if the record exists
    check_query = "SELECT COUNT(*) FROM Cruise_Info WHERE id = ?"
    cursor.execute(check_query, (cruise_id,))
    count_before = cursor.fetchone()[0]

    if count_before == 0:
        # Try alternative queries to debug
        cursor.execute("SELECT id FROM Cruise_Info WHERE id = ? OR id = ?", (cruise_id, str(cruise_id)))
        debug_result = cursor.fetchone()

        # Check all IDs in a range
        cursor.execute("SELECT id FROM Cruise_Info WHERE id BETWEEN ? AND ?", (cruise_id - 2, cruise_id + 2))
        nearby = cursor.fetchall()

        conn.close()
        return 0, f"Record not found. Debug: {debug_result}, Nearby IDs: {[n[0] for n in nearby]}"

    # Delete the record
    query = "DELETE FROM Cruise_Info WHERE id = ?"
    cursor.execute(query, (cruise_id,))
    deleted_count = cursor.rowcount

    conn.commit()

    # Verify deletion
    cursor.execute(check_query, (cruise_id,))
    count_after = cursor.fetchone()[0]

    conn.close()

    if count_after == 0:
        return deleted_count, "Success"
    else:
        return 0, f"Record still exists after deletion attempt (ID: {cruise_id})"

def get_unique_values(column):
    """Get unique values for a column (for dropdowns)"""
    conn = get_connection()
    query = f'SELECT DISTINCT "{column}" FROM Cruise_Info WHERE "{column}" IS NOT NULL ORDER BY "{column}"'
    result = pd.read_sql_query(query, conn)
    conn.close()
    return result[column].tolist()

def check_table_structure():
    """Check the structure of the Cruise_Info table"""
    conn = get_connection()
    cursor = conn.cursor()

    # Get table info
    cursor.execute("PRAGMA table_info(Cruise_Info)")
    columns = cursor.fetchall()

    # Get total record count
    cursor.execute("SELECT COUNT(*) FROM Cruise_Info")
    total_count = cursor.fetchone()[0]

    # Get sample of IDs
    cursor.execute("SELECT id FROM Cruise_Info LIMIT 10")
    sample_ids = cursor.fetchall()

    conn.close()

    return columns, total_count, sample_ids

def find_duplicates():
    """Find duplicate cruises based on Cruise + Ship + Beginning_Date"""
    conn = get_connection()
    query = """
    WITH DuplicateCruises AS (
        SELECT
            Cruise,
            Ship,
            Beginning_Date,
            COUNT(*) as duplicate_count
        FROM Cruise_Info
        GROUP BY Cruise, Ship, Beginning_Date
        HAVING COUNT(*) > 1
    )
    SELECT
        ci.*,
        dc.duplicate_count
    FROM Cruise_Info ci
    INNER JOIN DuplicateCruises dc
        ON ci.Cruise = dc.Cruise
        AND ci.Ship = dc.Ship
        AND ci.Beginning_Date = dc.Beginning_Date
    ORDER BY ci.Cruise, ci.Ship, ci.Beginning_Date, ci.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def delete_duplicates(ids_to_delete):
    """Delete specific cruise records by their IDs"""
    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ','.join('?' * len(ids_to_delete))
    query = f"DELETE FROM Cruise_Info WHERE id IN ({placeholders})"
    cursor.execute(query, ids_to_delete)

    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count, "Success"

# Main app
st.title("🚢 Cruise Information Management System")

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 View & Search", "➕ Add New Cruise", "✏️ Edit/Delete", "📈 Analytics", "🔍 Duplicates"])

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

# Tab 3: Edit/Delete
with tab3:
    st.header("Edit or Delete Cruise")

    # Get all cruises for selection
    df = get_cruise_data()

    # Show database structure info
    with st.expander("🔍 Debug: Database Structure"):
        columns, total_count, sample_ids = check_table_structure()

        st.write("**Table Structure:**")
        col_df = pd.DataFrame(columns, columns=['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk'])
        st.dataframe(col_df)

        st.write(f"**Total Records:** {total_count}")
        st.write(f"**Sample IDs:** {[id[0] for id in sample_ids]}")

        # Direct SQL test
        test_id = st.number_input("Test ID lookup:", min_value=1, value=373)
        if st.button("Test Direct SQL Query"):
            conn = get_connection()
            cursor = conn.cursor()

            # Test 1: Direct query
            cursor.execute("SELECT * FROM Cruise_Info WHERE id = ?", (test_id,))
            result = cursor.fetchone()
            if result:
                st.success(f"Found record with ID {test_id}: {result}")
            else:
                st.error(f"No record found with ID {test_id}")

            # Test 2: Check if ID exists at all
            cursor.execute("SELECT id FROM Cruise_Info WHERE id = ?", (test_id,))
            id_result = cursor.fetchone()
            st.write(f"ID query result: {id_result}")

            # Test 3: Find similar IDs
            cursor.execute("SELECT id FROM Cruise_Info WHERE id BETWEEN ? AND ? ORDER BY id", (test_id - 5, test_id + 5))
            nearby_ids = cursor.fetchall()
            st.write(f"IDs near {test_id}: {[id[0] for id in nearby_ids]}")

            conn.close()

    if not df.empty:

        # Create a selection column
        cruise_options = df.apply(lambda row: f"ID {row['id']}: {row['Cruise']} - {row['Ship']} ({row['Beginning Date']} to {row['Ending Date']})", axis=1)

        selected_cruise_index = st.selectbox(
            "Select a cruise to edit or delete",
            range(len(cruise_options)),
            format_func=lambda x: cruise_options.iloc[x]
        )

        selected_cruise = df.iloc[selected_cruise_index]
        cruise_id = selected_cruise['id']

        # Debug information
        # Debug information
        with st.expander("🐛 Debug: Selected Cruise"):
            st.info(f"Selected cruise ID: {cruise_id}, Type: {type(cruise_id)}")

            # Convert to different types and test
            st.write(f"As int: {int(cruise_id)}")
            st.write(f"As string: '{str(cruise_id)}'")

            # Check if ID exists in database
            conn = get_connection()
            cursor = conn.cursor()

            # Try different query methods
            cursor.execute("SELECT COUNT(*) FROM Cruise_Info WHERE id = ?", (cruise_id,))
            count1 = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM Cruise_Info WHERE id = ?", (int(cruise_id),))
            count2 = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM Cruise_Info WHERE id = {int(cruise_id)}")
            count3 = cursor.fetchone()[0]

            st.write(f"Query results - Direct param: {count1}, Int param: {count2}, String format: {count3}")

            cursor.execute("SELECT id, Cruise, Ship FROM Cruise_Info WHERE id = ?", (int(cruise_id),))
            db_check = cursor.fetchone()
            conn.close()

            if db_check:
                st.success(f"Found in DB - ID: {db_check[0]}, Cruise: {db_check[1]}, Ship: {db_check[2]}")
            else:
                st.error(f"ID {cruise_id} NOT found in database!")

        # Show current values
        st.subheader("Current Values")
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Cruise:** {selected_cruise['Cruise']}")
            st.write(f"**Ship:** {selected_cruise['Ship']}")
            st.write(f"**Lines:** {selected_cruise['Lines']}")
            st.write(f"**Personnel:** {selected_cruise['Personnel']}")
            st.write(f"**Leg:** {selected_cruise['Leg']}")

        with col2:
            st.write(f"**Beginning Date:** {selected_cruise['Beginning Date']}")
            st.write(f"**Ending Date:** {selected_cruise['Ending Date']}")
            st.write(f"**Port 1:** {selected_cruise['Port1']}")
            st.write(f"**Port 2:** {selected_cruise['Port2']}")
            st.write(f"**Port 3:** {selected_cruise['Port3']}")

        st.divider()

        # Edit form
        st.subheader("Edit Cruise")

        with st.form("edit_cruise_form"):
            col1, col2 = st.columns(2)

            with col1:
                cruise_name = st.text_input("Cruise Name*", value=selected_cruise['Cruise'])
                ship = st.text_input("Ship*", value=selected_cruise['Ship'])
                lines = st.text_input("Lines", value=selected_cruise['Lines'] if pd.notna(selected_cruise['Lines']) else "")
                personnel = st.text_input("Personnel", value=selected_cruise['Personnel'] if pd.notna(selected_cruise['Personnel']) else "")
                leg = st.number_input("Leg", min_value=0, value=int(selected_cruise['Leg']) if pd.notna(selected_cruise['Leg']) else 0, step=1)

            with col2:
                parsed_begin = parse_date(selected_cruise['Beginning Date'])
                parsed_end = parse_date(selected_cruise['Ending Date'])
                beginning_date = st.date_input("Beginning Date*", value=parsed_begin.date() if parsed_begin else date.today())
                ending_date = st.date_input("Ending Date*", value=parsed_end.date() if parsed_end else date.today())
                port1 = st.text_input("Port 1", value=selected_cruise['Port1'] if pd.notna(selected_cruise['Port1']) else "")
                port2 = st.text_input("Port 2", value=selected_cruise['Port2'] if pd.notna(selected_cruise['Port2']) else "")
                port3 = st.text_input("Port 3", value=selected_cruise['Port3'] if pd.notna(selected_cruise['Port3']) else "")

            update_btn = st.form_submit_button("Update Cruise", type="primary")

            if update_btn:
                if cruise_name and ship and beginning_date and ending_date:
                    if ending_date < beginning_date:
                        st.error("Ending date must be after beginning date!")
                    else:
                        # Prepare updated data
                        updated_cruise = {
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
                            update_cruise(cruise_id, updated_cruise)
                            st.success("✅ Cruise updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating cruise: {e}")
                else:
                    st.error("Please fill in all required fields!")

        # Delete section - outside the form
        st.divider()
        st.subheader("Delete Cruise")

        col1, col2 = st.columns([3, 1])
        with col1:
            confirm_delete = st.checkbox("I confirm I want to delete this cruise")
        with col2:
            if st.button("Delete Cruise", type="secondary", disabled=not confirm_delete):
                try:
                    # Show spinner during deletion
                    with st.spinner("Deleting cruise..."):
                        deleted_count, status = delete_cruise(cruise_id)

                    if deleted_count > 0 and status == "Success":
                        st.success(f"✅ Cruise deleted successfully! (ID: {cruise_id})")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to delete cruise. Status: {status}")
                        # Additional debugging info
                        st.info(f"Debug: Attempted to delete ID {cruise_id}, deleted count: {deleted_count}")
                except Exception as e:
                    st.error(f"Error deleting cruise: {str(e)}")
                    st.exception(e)
    else:
        st.info("No cruises available to edit or delete.")

# Tab 4: Analytics
with tab4:
    st.header("Cruise Analytics")

    df = get_cruise_data()

    if not df.empty:
        # Convert dates for analysis
        df['Beginning Date'] = df['Beginning Date'].apply(parse_date)
        df['Ending Date'] = df['Ending Date'].apply(parse_date)
        df['Duration'] = (df['Ending Date'] - df['Beginning Date']).dt.days + 1

        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Cruises", len(df))

        with col2:
            st.metric("Total Ships", df['Ship'].nunique())

        with col3:
            st.metric("Total Personnel", df['Personnel'].nunique())

        with col4:
            st.metric("Avg Duration (days)", f"{df['Duration'].mean():.1f}")

        st.divider()

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Cruises by Ship")
            ship_counts = df['Ship'].value_counts().head(10)
            st.bar_chart(ship_counts)

        with col2:
            st.subheader("Cruises by Line")
            line_counts = df['Lines'].value_counts().head(10)
            st.bar_chart(line_counts)

        st.divider()

        # Timeline view
        st.subheader("Cruise Timeline")

        # Prepare data for timeline
        timeline_df = df[['Cruise', 'Ship', 'Beginning Date', 'Ending Date']].copy()
        timeline_df = timeline_df.sort_values('Beginning Date')

        # Show recent cruises
        st.write("**Recent Cruises (Last 20)**")
        recent_cruises = timeline_df.tail(20)

        for _, cruise in recent_cruises.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{cruise['Cruise']}** - {cruise['Ship']}")
            with col2:
                st.write(f"{cruise['Beginning Date'].strftime('%b %d, %Y')} → {cruise['Ending Date'].strftime('%b %d, %Y')}")

        st.divider()

        # Port analysis
        st.subheader("Port Analysis")

        # Combine all ports
        all_ports = []
        for col in ['Port1', 'Port2', 'Port3']:
            ports = df[col].dropna().tolist()
            all_ports.extend(ports)

        if all_ports:
            port_counts = pd.Series(all_ports).value_counts().head(15)
            st.bar_chart(port_counts)
        else:
            st.info("No port data available.")

    else:
        st.info("No data available for analytics.")

# Tab 5: Duplicates
with tab5:
    st.header("Duplicate Management")
    st.markdown("Find and manage duplicate cruises based on **Cruise Name + Ship + Beginning Date**")

    # Find duplicates
    duplicates_df = find_duplicates()

    if not duplicates_df.empty:
        st.warning(f"⚠️ Found {len(duplicates_df)} records that are duplicates")

        # Group duplicates for display
        duplicate_groups = duplicates_df.groupby(['Cruise', 'Ship', 'Beginning_Date'])

        st.subheader("Duplicate Groups")

        for (cruise, ship, begin_date), group in duplicate_groups:
            with st.expander(f"🔸 {cruise} - {ship} ({begin_date}) - {len(group)} copies"):

                # Display group info
                st.write(f"**Found {len(group)} duplicate records for this cruise:**")

                # Show details of each duplicate
                for idx, row in group.iterrows():
                    col1, col2, col3, col4 = st.columns([1, 3, 3, 2])

                    with col1:
                        st.write(f"**ID: {row['id']}**")

                    with col2:
                        st.write(f"Personnel: {row['Personnel'] if pd.notna(row['Personnel']) else 'N/A'}")
                        st.write(f"Leg: {row['Leg'] if pd.notna(row['Leg']) else 'N/A'}")

                    with col3:
                        ports = []
                        if pd.notna(row['Port1']):
                            ports.append(row['Port1'])
                        if pd.notna(row['Port2']):
                            ports.append(row['Port2'])
                        if pd.notna(row['Port3']):
                            ports.append(row['Port3'])
                        st.write(f"Ports: {', '.join(ports) if ports else 'N/A'}")
                        st.write(f"Lines: {row['Lines'] if pd.notna(row['Lines']) else 'N/A'}")

                    with col4:
                        st.write(f"Created: {row['created_at']}")

                    st.divider()

                # Option to keep one and delete others
                st.markdown("**Choose action:**")

                col1, col2 = st.columns(2)
                with col1:
                    keep_id = st.selectbox(
                        "Keep this record:",
                        options=group['id'].tolist(),
                        format_func=lambda x: f"ID {x} - {group[group['id']==x]['Personnel'].iloc[0] if pd.notna(group[group['id']==x]['Personnel'].iloc[0]) else 'No Personnel'}",
                        key=f"keep_{cruise}_{ship}_{begin_date}"
                    )

                with col2:
                    if st.button(f"Delete all except ID {keep_id}", key=f"delete_{cruise}_{ship}_{begin_date}"):
                        ids_to_delete = group[group['id'] != keep_id]['id'].tolist()

                        if ids_to_delete:
                            deleted, status = delete_duplicates(ids_to_delete)
                            if deleted > 0:
                                st.success(f"✅ Deleted {deleted} duplicate records")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete duplicates. Status: {status}")

        st.divider()

        # Bulk operations
        st.subheader("Bulk Operations")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ Remove ALL duplicates (keep oldest by ID)", type="secondary"):
                if st.checkbox("I understand this will delete multiple records"):
                    # Get IDs to delete (all except minimum ID per group)
                    query = """
                    SELECT id FROM Cruise_Info
                    WHERE id NOT IN (
                        SELECT MIN(id)
                        FROM Cruise_Info
                        GROUP BY Cruise, Ship, Beginning_Date
                    )
                    AND (Cruise, Ship, Beginning_Date) IN (
                        SELECT Cruise, Ship, Beginning_Date
                        FROM Cruise_Info
                        GROUP BY Cruise, Ship, Beginning_Date
                        HAVING COUNT(*) > 1
                    )
                    """
                    conn = get_connection()
                    ids_to_delete = pd.read_sql_query(query, conn)['id'].tolist()
                    conn.close()

                    if ids_to_delete:
                        deleted, status = delete_duplicates(ids_to_delete)
                        if deleted > 0:
                            st.success(f"✅ Deleted {deleted} duplicate records")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete duplicates. Status: {status}")

        with col2:
            # Show summary statistics
            st.metric("Total Duplicate Records", len(duplicates_df))
            st.metric("Duplicate Groups", len(duplicate_groups))
            st.metric("Extra Copies", len(duplicates_df) - len(duplicate_groups))

    else:
        st.success("✅ No duplicates found! Your database is clean.")

        # Show summary
        conn = get_connection()
        total_records = pd.read_sql_query("SELECT COUNT(*) as count FROM Cruise_Info", conn)['count'][0]
        conn.close()

        st.metric("Total Records", total_records)

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
