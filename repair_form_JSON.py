import streamlit as st
import sqlite3
import pandas as pd
import json
from datetime import datetime, date, time
import os
import numpy as np

# Database configuration
DB_PATH = os.path.expanduser("~/Apps/databases/Cruise_Logs.db")

def check_tube_data():
    """Diagnostic function to check tube data for specific moorings."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check RA092B specifically
    cursor.execute("""
        SELECT id, mooring_id, lost_equipment, replacement_equipment, equipment_status
        FROM repair_normalized
        WHERE mooring_id = 'RA092B'
    """)

    records = cursor.fetchall()
    print(f"\n=== Checking RA092B tube data ===")
    print(f"Found {len(records)} record(s) for RA092B\n")

    for rec in records:
        print(f"Record ID: {rec['id']}")
        print(f"Mooring: {rec['mooring_id']}")

        # Parse JSONs
        if rec['lost_equipment']:
            lost = json.loads(rec['lost_equipment'])
            print(f"Lost Equipment: {json.dumps(lost, indent=2)}")
            if 'tube' in lost:
                print(f"  ✓ Tube found in lost_equipment: {lost['tube']}")
            else:
                print(f"  ✗ Tube NOT in lost_equipment")

        if rec['replacement_equipment']:
            replacement = json.loads(rec['replacement_equipment'])
            print(f"Replacement Equipment: {json.dumps(replacement, indent=2)}")
            if 'tube' in replacement:
                print(f"  ✓ Tube found in replacement_equipment: {replacement['tube']}")
            else:
                print(f"  ✗ Tube NOT in replacement_equipment")

        if rec['equipment_status']:
            status = json.loads(rec['equipment_status'])
            print(f"Equipment Status: {json.dumps(status, indent=2)}")
            if 'tube' in status:
                print(f"  ✓ Tube found in equipment_status: {status['tube']}")
            else:
                print(f"  ✗ Tube NOT in equipment_status")

        print("-" * 50)

    # Now check the Excel file to see what values exist
    REPAIR_FILE = os.path.expanduser("~/Apps/databases/repair2.xlsx")
    if os.path.exists(REPAIR_FILE):
        print(f"\n=== Checking Excel file for RA092B ===")
        df = pd.read_excel(REPAIR_FILE)

        # Find RA092B rows
        ra092b_rows = df[df['MooringID'] == 'RA092B']

        if not ra092b_rows.empty:
            print(f"Found {len(ra092b_rows)} row(s) for RA092B in Excel\n")

            # Check tube-related columns
            tube_columns = ['Tube SN', 'TubeLost', 'NewTubeSN']

            for idx, row in ra092b_rows.iterrows():
                print(f"Excel row {idx + 2}:")
                for col in tube_columns:
                    if col in df.columns:
                        value = row[col]
                        is_nan = pd.isna(value)
                        print(f"  {col}: {repr(value)} (isna={is_nan})")
                    else:
                        print(f"  {col}: COLUMN NOT FOUND")
                print()
        else:
            print("RA092B not found in Excel file")

    conn.close()
    return

def build_equipment_json_fixed(row, equipment_type='lost'):
    """
    Build equipment JSON objects with proper handling of NaN and None values.

    Args:
        row: DataFrame row containing equipment data
        equipment_type: 'lost', 'replacement', or 'status'

    Returns:
        Dictionary containing equipment information
    """
    equipment = {}

    if equipment_type == 'lost':
        # Check each equipment type - include if ANY relevant field has data
        # Use pd.notna() to properly check for non-NaN values

        # ATRH
        if pd.notna(row.get('ATRH SN')) or pd.notna(row.get('ATRHlost')):
            equipment['atrh'] = {
                'sn': row.get('ATRH SN') if pd.notna(row.get('ATRH SN')) else None,
                'lost': row.get('ATRHlost') if pd.notna(row.get('ATRHlost')) else None
            }

        # Rain
        if pd.notna(row.get('Rain SN')) or pd.notna(row.get('RainLost')):
            equipment['rain'] = {
                'sn': row.get('Rain SN') if pd.notna(row.get('Rain SN')) else None,
                'lost': row.get('RainLost') if pd.notna(row.get('RainLost')) else None
            }

        # SST
        if pd.notna(row.get('SST SN')) or pd.notna(row.get('SSTlost')):
            equipment['sst'] = {
                'sn': row.get('SST SN') if pd.notna(row.get('SST SN')) else None,
                'lost': row.get('SSTlost') if pd.notna(row.get('SSTlost')) else None
            }

        # SW Rad
        if pd.notna(row.get('SW Rad SN')) or pd.notna(row.get('SWRadLost')):
            equipment['sw_rad'] = {
                'sn': row.get('SW Rad SN') if pd.notna(row.get('SW Rad SN')) else None,
                'lost': row.get('SWRadLost') if pd.notna(row.get('SWRadLost')) else None
            }

        # Tube - FIXED: properly check for tube data
        if pd.notna(row.get('Tube SN')) or pd.notna(row.get('TubeLost')):
            equipment['tube'] = {
                'sn': row.get('Tube SN') if pd.notna(row.get('Tube SN')) else None,
                'lost': row.get('TubeLost') if pd.notna(row.get('TubeLost')) else None
            }

        # Wind
        if pd.notna(row.get('Wind SN')) or pd.notna(row.get('WindLost')):
            equipment['wind'] = {
                'sn': row.get('Wind SN') if pd.notna(row.get('Wind SN')) else None,
                'lost': row.get('WindLost') if pd.notna(row.get('WindLost')) else None
            }

    elif equipment_type == 'replacement':
        # Check each replacement equipment field

        # ATRH
        if pd.notna(row.get('New ATRH SN')):
            equipment['atrh'] = {'sn': row.get('New ATRH SN')}

        # PTT
        if pd.notna(row.get('New PTT Id')):
            equipment['ptt'] = {'id': row.get('New PTT Id')}

        # Rain
        if pd.notna(row.get('New Rain SN')):
            equipment['rain'] = {'sn': row.get('New Rain SN')}

        # SST
        if pd.notna(row.get('New SST SN')):
            equipment['sst'] = {'sn': row.get('New SST SN')}

        # SW Rad
        if pd.notna(row.get('New SW Rad SN')):
            equipment['sw_rad'] = {'sn': row.get('New SW Rad SN')}

        # Wind
        if pd.notna(row.get('New WindSN')):
            equipment['wind'] = {'sn': row.get('New WindSN')}

        # Tube - FIXED: properly check for NewTubeSN
        if pd.notna(row.get('NewTubeSN')):
            equipment['tube'] = {'sn': row.get('NewTubeSN')}

    elif equipment_type == 'status':
        # Equipment status (kept for backward compatibility)

        # PTT
        if pd.notna(row.get('PTT ID')):
            equipment['ptt'] = {'id': row.get('PTT ID')}

        # Tube
        if pd.notna(row.get('Tube SN')) or pd.notna(row.get('TubeLost')):
            equipment['tube'] = {
                'sn': row.get('Tube SN') if pd.notna(row.get('Tube SN')) else None,
                'lost': row.get('TubeLost') if pd.notna(row.get('TubeLost')) else None
            }

        # Wind
        if pd.notna(row.get('Wind SN')) or pd.notna(row.get('WindLost')):
            equipment['wind'] = {
                'sn': row.get('Wind SN') if pd.notna(row.get('Wind SN')) else None,
                'lost': row.get('WindLost') if pd.notna(row.get('WindLost')) else None
            }

    return equipment if equipment else None


def test_ra092b_tube_import():
    """Test function to diagnose why RA092B tube data isn't importing correctly."""
    print("\n" + "="*60)
    print("TESTING RA092B TUBE DATA IMPORT ISSUE")
    print("="*60)

    # First check what's in the database
    check_tube_data()

    # Now let's test the equipment building logic
    print("\n=== Testing Equipment Building Logic ===")

    # Simulate a row with tube data
    test_row = {
        'Tube SN': '12345',
        'TubeLost': None,
        'NewTubeSN': '67890',
        'ATRH SN': None,
        'ATRHlost': None,
        'Rain SN': '1554',
        'RainLost': None,
        'SST SN': float('nan'),
        'SSTlost': None,
        'SW Rad SN': None,
        'SWRadLost': None,
        'Wind SN': float('nan'),
        'WindLost': None,
        'New ATRH SN': None,
        'New PTT Id': None,
        'New Rain SN': '1554',
        'New SST SN': float('nan'),
        'New SW Rad SN': None,
        'New WindSN': float('nan'),
        'PTT ID': None
    }

    # Convert to pandas Series to simulate DataFrame row
    import pandas as pd
    test_row_series = pd.Series(test_row)

    print("\nTest row data:")
    print(f"  Tube SN: {test_row_series.get('Tube SN')} (isna={pd.isna(test_row_series.get('Tube SN'))})")
    print(f"  NewTubeSN: {test_row_series.get('NewTubeSN')} (isna={pd.isna(test_row_series.get('NewTubeSN'))})")

    # Test with fixed function
    lost_eq = build_equipment_json_fixed(test_row_series, 'lost')
    replacement_eq = build_equipment_json_fixed(test_row_series, 'replacement')

    print("\nFixed function results:")
    print(f"Lost equipment: {json.dumps(lost_eq, indent=2)}")
    print(f"Replacement equipment: {json.dumps(replacement_eq, indent=2)}")

    # Test with problematic original logic
    print("\n=== Testing Original Logic (problematic) ===")

    # This simulates the original code's problem
    lost_equipment_orig = {}
    replacement_equipment_orig = {}

    # Original lost equipment logic (before fix)
    if test_row_series['Tube SN'] or test_row_series['TubeLost']:  # Problem: fails if TubeLost is None/NaN
        lost_equipment_orig['tube'] = {
            'sn': test_row_series['Tube SN'],
            'lost': test_row_series['TubeLost']
        }

    # Original replacement logic
    if test_row_series['NewTubeSN']:  # Problem: fails for falsy values
        replacement_equipment_orig['tube'] = {'sn': test_row_series['NewTubeSN']}

    print(f"Original lost equipment: {json.dumps(lost_equipment_orig, indent=2)}")
    print(f"Original replacement equipment: {json.dumps(replacement_equipment_orig, indent=2)}")

    print("\n" + "="*60)
    print("DIAGNOSIS:")
    print("The original code uses 'if row['NewTubeSN']:' which fails when:")
    print("  1. The value is NaN (evaluates to False)")
    print("  2. The value is None (evaluates to False)")
    print("  3. The value is 0 or empty string (evaluates to False)")
    print("\nThe fix is to use 'pd.notna(row.get('NewTubeSN'))' instead.")
    print("="*60)

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def check_database_table():
    """Check if the repair_normalized table exists and return its columns."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='repair_normalized'
        """)
        if not cursor.fetchone():
            conn.close()
            return False, []

        # Get column names
        cursor.execute("PRAGMA table_info(repair_normalized)")
        columns = [col[1] for col in cursor.fetchall()]
        conn.close()
        return True, columns
    except Exception as e:
        print(f"Database check error: {e}")
        return False, []


def ensure_columns_exist():
    """Ensure buoy_details and repair_fishing_vandalism columns exist in the table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if columns exist
        cursor.execute("PRAGMA table_info(repair_normalized)")
        existing_columns = [col[1] for col in cursor.fetchall()]

        # Add buoy_details column if it doesn't exist
        if 'buoy_details' not in existing_columns:
            cursor.execute("""
                ALTER TABLE repair_normalized
                ADD COLUMN buoy_details TEXT
            """)
            conn.commit()
            print("Added buoy_details column to repair_normalized table")

        # Add repair_fishing_vandalism column if it doesn't exist
        if 'repair_fishing_vandalism' not in existing_columns:
            cursor.execute("""
                ALTER TABLE repair_normalized
                ADD COLUMN repair_fishing_vandalism TEXT
            """)
            conn.commit()
            print("Added fishing_vandalism column to repair_normalized table")

        # Add all Sensor Exchange columns if they don't exist
        sensor_columns = [
            'tube_old_sn', 'tube_new_sn', 'tube_condition', 'tube_details',
            'ptt_old_sn', 'ptt_new_sn', 'ptt_condition', 'ptt_details',
            'atrh_old_sn', 'atrh_new_sn', 'atrh_condition', 'atrh_details',
            'sst_old_sn', 'sst_new_sn', 'sst_condition', 'sst_details',
            'wind_old_sn', 'wind_new_sn', 'wind_condition', 'wind_details',
            'rain_old_sn', 'rain_new_sn', 'rain_condition', 'rain_details',
            'swrad_old_sn', 'swrad_new_sn', 'swrad_condition', 'swrad_details',
            'baro_old_sn', 'baro_new_sn', 'baro_condition', 'baro_details',
            'seacat_old_sn', 'seacat_new_sn', 'seacat_condition', 'seacat_details'
        ]

        # Add Tube Exchange columns
        tube_exchange_columns = [
            'tube_time', 'gmt', 'drift',
            'bat_logic', 'bat_transmit', 'file_name'
        ]

        # Add Met Obs columns
        met_obs_columns = [
            'ship_date', 'ship_time', 'ship_wind_dir', 'ship_wind_spd',
            'ship_air_temp', 'ship_sst', 'ship_ssc', 'ship_rh',
            'buoy_date', 'buoy_time', 'buoy_wind_dir', 'buoy_wind_spd',
            'buoy_air_temp', 'buoy_sst', 'buoy_ssc', 'buoy_rh'
        ]

        for col in sensor_columns:
            if col not in existing_columns:
                cursor.execute(f"""
                    ALTER TABLE repair_normalized
                    ADD COLUMN {col} TEXT
                """)
                conn.commit()
                print(f"Added {col} column to repair_normalized table")

        for col in tube_exchange_columns:
            if col not in existing_columns:
                cursor.execute(f"""
                    ALTER TABLE repair_normalized
                    ADD COLUMN {col} TEXT
                """)
                conn.commit()
                print(f"Added {col} column to repair_normalized table")

        for col in met_obs_columns:
            if col not in existing_columns:
                cursor.execute(f"""
                    ALTER TABLE repair_normalized
                    ADD COLUMN {col} TEXT
                """)
                conn.commit()
                print(f"Added {col} column to repair_normalized table")

        conn.close()
        return True
    except Exception as e:
        print(f"Error ensuring columns exist: {e}")
        return False


def migrate_old_columns():
    """Migrate data from old column names to new column names if needed."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if both old and new columns exist
        cursor.execute("PRAGMA table_info(repair_normalized)")
        columns = [col[1] for col in cursor.fetchall()]

        # Migrate fishing_vandalism to repair_fishing_vandalism if both exist
        if 'fishing_vandalism' in columns and 'repair_fishing_vandalism' in columns:
            cursor.execute("""
                UPDATE repair_normalized
                SET repair_fishing_vandalism = fishing_vandalism
                WHERE repair_fishing_vandalism IS NULL
                AND fishing_vandalism IS NOT NULL
            """)
            conn.commit()
            print(f"Migrated {cursor.rowcount} records from fishing_vandalism to repair_fishing_vandalism")

        # Migrate buoy_condition to buoy_details if both exist
        if 'buoy_condition' in columns and 'buoy_details' in columns:
            cursor.execute("""
                UPDATE repair_normalized
                SET buoy_details = buoy_condition
                WHERE buoy_details IS NULL
                AND buoy_condition IS NOT NULL
            """)
            conn.commit()
            print(f"Migrated {cursor.rowcount} records from buoy_condition to buoy_details")

        conn.close()
        return True
    except Exception as e:
        print(f"Error migrating columns: {e}")
        return False


def get_distinct_sites():
    """Get all distinct sites from the database."""
    conn = get_db_connection()
    try:
        query = "SELECT DISTINCT site FROM repair_normalized WHERE site IS NOT NULL AND site != '' ORDER BY site"
        cursor = conn.cursor()
        cursor.execute(query)
        sites = [row[0] for row in cursor.fetchall()]
        return sites
    except Exception as e:
        print(f"Error fetching sites: {e}")
        return []
    finally:
        conn.close()


def get_distinct_cruises():
    """Get all distinct cruises from the database."""
    conn = get_db_connection()
    try:
        query = "SELECT DISTINCT cruise FROM repair_normalized WHERE cruise IS NOT NULL AND cruise != '' ORDER BY cruise"
        cursor = conn.cursor()
        cursor.execute(query)
        cruises = [row[0] for row in cursor.fetchall()]
        return cruises
    except Exception as e:
        print(f"Error fetching cruises: {e}")
        return []
    finally:
        conn.close()


def search_repairs(criteria):
    """Search for repair records based on given criteria."""
    conn = get_db_connection()
    try:
        base_query = "SELECT * FROM repair_normalized WHERE 1=1"
        params = []

        if 'site' in criteria and criteria['site']:
            base_query += " AND site = ?"
            params.append(criteria['site'])

        if 'mooring_id' in criteria and criteria['mooring_id']:
            base_query += " AND mooring_id LIKE ?"
            params.append(f"%{criteria['mooring_id']}%")

        if 'cruise' in criteria and criteria['cruise']:
            base_query += " AND cruise LIKE ?"
            params.append(f"%{criteria['cruise']}%")

        base_query += " ORDER BY repair_date DESC, id DESC"

        df = pd.read_sql_query(base_query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Error searching repairs: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def save_repair(repair_data, is_update=False, record_id=None):
    """Save or update a repair record."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if is_update and record_id:
            # Build UPDATE query
            fields = []
            values = []

            for key, value in repair_data.items():
                if key != 'id':
                    fields.append(f"{key} = ?")
                    values.append(value)

            values.append(record_id)
            query = f"UPDATE repair_normalized SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"

            cursor.execute(query, values)
            conn.commit()
            return True, "Repair record updated successfully!"
        else:
            # Build INSERT query
            fields = list(repair_data.keys())
            placeholders = ', '.join(['?' for _ in fields])
            field_names = ', '.join(fields)

            query = f"INSERT INTO repair_normalized ({field_names}) VALUES ({placeholders})"

            cursor.execute(query, list(repair_data.values()))
            conn.commit()
            return True, "Repair record saved successfully!"

    except Exception as e:
        conn.rollback()
        return False, f"Error saving repair record: {e}"
    finally:
        conn.close()


def delete_repair(record_id):
    """Delete a repair record."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM repair_normalized WHERE id = ?", [record_id])
        conn.commit()
        return True, "Repair record deleted successfully!"
    except Exception as e:
        conn.rollback()
        return False, f"Error deleting repair record: {e}"
    finally:
        conn.close()


def format_time_input(time_str):
    """Format time input to HH:mm format."""
    if not time_str:
        return ""

    # Remove any seconds if present
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) >= 2:
            hours = parts[0].strip().zfill(2)
            minutes = parts[1][:2].strip().zfill(2)
            return f"{hours}:{minutes}"

    return time_str


def parse_date_input(date_value):
    """Parse date input and return as string in YYYY-MM-DD format."""
    if date_value is None:
        return None
    if isinstance(date_value, date):
        return date_value.strftime('%Y-%m-%d')
    if isinstance(date_value, str):
        if date_value == '':
            return None
        return date_value
    return str(date_value)


def parse_datetime_input(date_value, time_str):
    """Combine date and time into a timestamp string."""
    if not date_value:
        return None

    date_str = parse_date_input(date_value)
    if not date_str:
        return None

    if time_str:
        formatted_time = format_time_input(time_str)
        if formatted_time:
            return f"{date_str} {formatted_time}:00"

    return f"{date_str} 00:00:00"


def parse_json_field(json_str):
    """Parse JSON field from database."""
    if json_str is None or json_str == '':
        return {}
    if isinstance(json_str, dict):
        return json_str
    try:
        return json.loads(json_str)
    except:
        return {}


def parse_float_safe(value):
    """Safely parse a float value."""
    if value is None or value == '' or (isinstance(value, float) and np.isnan(value)):
        return None
    try:
        return float(value)
    except:
        return None


def parse_int_safe(value):
    """Safely parse integer values"""
    if value is None or value == '' or pd.isna(value):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def main():
    # Page configuration
    st.set_page_config(
        page_title="Repair Log",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Ensure new columns exist in the database
    ensure_columns_exist()

    # Migrate any existing data from old column names to new ones
    migrate_old_columns()

    # Custom CSS for better form styling
    st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        color: #1f77b4;
        padding-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        margin-bottom: 2rem;
    }
    .stTextInput label {
        font-weight: 600;
        color: var(--text-color);
    }
    /* Style for table-like layout */
    .table-row {
        display: flex;
        margin-bottom: 1rem;
    }
    .table-cell {
        flex: 1;
        padding: 0 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Main title
    st.title("Repair Log")

    # Check database connection and table
    table_exists, columns = check_database_table()
    if not table_exists:
        st.error("⚠️ repair_normalized table not found in database!")
        st.info("Please ensure the repair_normalized table is created in your database.")
        return

    # Initialize session state
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'current_record_index' not in st.session_state:
        st.session_state.current_record_index = 0
    if 'mode' not in st.session_state:
        st.session_state.mode = "Search/Edit"
    if 'selected_repair' not in st.session_state:
        st.session_state.selected_repair = None

    # Mode selection
    col1, col2 = st.columns([1, 3])
    with col1:
        mode = st.radio("Mode", ["Search/Edit", "Add New"], key="mode_selector")
        st.session_state.mode = mode

    # Get list of sites and cruises for dropdowns
    available_sites = get_distinct_sites()
    available_cruises = get_distinct_cruises()

    # Search section
    if mode == "Search/Edit":
        st.subheader("Search Repairs")

        with st.form("search_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                # Use dropdown for Site search
                site_options = [""] + available_sites
                search_site = st.selectbox("Site", options=site_options, key="search_site")
            with col2:
                search_mooring_id = st.text_input("Mooring ID", key="search_mooring_id")
            with col3:
                cruise_options = [""] + available_cruises
                search_cruise = st.selectbox("Cruise", options=cruise_options, key="search_cruise")

            search_submitted = st.form_submit_button("Search", use_container_width=True)

            if search_submitted:
                search_criteria = {}
                if search_site and search_site.strip():
                    search_criteria['site'] = search_site
                if search_mooring_id:
                    search_criteria['mooring_id'] = search_mooring_id
                if search_cruise:
                    search_criteria['cruise'] = search_cruise

                # Perform search
                results = search_repairs(search_criteria)
                st.session_state.search_results = results
                st.session_state.current_record_index = 0

                if results.empty:
                    st.warning("No repairs found matching your criteria.")
                else:
                    st.success(f"Found {len(results)} repair(s)")

        # Display search results
        if st.session_state.search_results is not None and not st.session_state.search_results.empty:
            st.subheader("Search Results")

            # Navigation
            if len(st.session_state.search_results) > 1:
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    if st.button("◀ Previous", disabled=st.session_state.current_record_index <= 0):
                        st.session_state.current_record_index -= 1
                        st.rerun()
                with col2:
                    st.write(f"Record {st.session_state.current_record_index + 1} of {len(st.session_state.search_results)}")
                with col3:
                    if st.button("Next ▶", disabled=st.session_state.current_record_index >= len(st.session_state.search_results) - 1):
                        st.session_state.current_record_index += 1
                        st.rerun()

            # Get current record
            if len(st.session_state.search_results) > 0:
                current_record = st.session_state.search_results.iloc[st.session_state.current_record_index]

                # Convert Series to dict for easier access
                if hasattr(current_record, 'to_dict'):
                    current_record_dict = current_record.to_dict()
                else:
                    current_record_dict = dict(current_record)

                st.session_state.selected_repair = current_record_dict

    # Determine default values based on mode
    if mode == "Add New":
        # Clear defaults for new record
        default_site = ""
        default_mooring_id = ""
        default_cruise = ""
        default_personnel = ""
        default_repair_date = None
        default_argos_latitude = ""
        default_argos_longitude = ""
        default_start_repair_time = ""
        default_end_repair_time = ""
        default_swap_time = ""
        default_cruise_site = ""
        default_counter = ""
        default_actual_latitude = ""
        default_actual_longitude = ""
        default_depth = ""
        default_ctd_number = ""
        default_buoy_condition = ""
        default_fishing_vandalism = ""

        # Sensor Exchange defaults
        default_tube_old_sn = ""
        default_tube_new_sn = ""
        default_tube_condition = ""
        default_tube_details = ""
        default_ptt_old_sn = ""
        default_ptt_new_sn = ""
        default_ptt_condition = ""
        default_ptt_details = ""
        default_atrh_old_sn = ""
        default_atrh_new_sn = ""
        default_atrh_condition = ""
        default_atrh_details = ""
        default_sst_old_sn = ""
        default_sst_new_sn = ""
        default_sst_condition = ""
        default_sst_details = ""
        default_wind_old_sn = ""
        default_wind_new_sn = ""
        default_wind_condition = ""
        default_wind_details = ""
        default_rain_old_sn = ""
        default_rain_new_sn = ""
        default_rain_condition = ""
        default_rain_details = ""
        default_swrad_old_sn = ""
        default_swrad_new_sn = ""
        default_swrad_condition = ""
        default_swrad_details = ""
        default_baro_old_sn = ""
        default_baro_new_sn = ""
        default_baro_condition = ""
        default_baro_details = ""
        default_seacat_old_sn = ""
        default_seacat_new_sn = ""
        default_seacat_condition = ""
        default_seacat_details = ""

        # Tube Exchange defaults
        default_tube_time = ""
        default_gmt = ""
        default_drift = ""
        default_bat_logic = ""
        default_bat_transmit = ""
        default_file_name = ""

        # Met Obs defaults
        default_ship_date = None
        default_ship_time = ""
        default_ship_wind_dir = ""
        default_ship_wind_spd = ""
        default_ship_air_temp = ""
        default_ship_sst = ""
        default_ship_ssc = ""
        default_ship_rh = ""
        default_buoy_date = None
        default_buoy_time = ""
        default_buoy_wind_dir = ""
        default_buoy_wind_spd = ""
        default_buoy_air_temp = ""
        default_buoy_sst = ""
        default_buoy_ssc = ""
        default_buoy_rh = ""

        record_id = None
    else:
        # Use selected record for editing
        if st.session_state.selected_repair:
            rec = st.session_state.selected_repair
            default_site = rec.get('site', '') or ''
            default_mooring_id = rec.get('mooring_id', '') or ''
            default_cruise = rec.get('cruise', '') or ''
            default_personnel = rec.get('personnel', '') or ''
            default_cruise_site = rec.get('cruise_site', '') or ''
            default_counter = str(rec.get('counter', '')) if rec.get('counter') is not None else ''

            # Handle repair_date
            repair_date_str = rec.get('repair_date', '')
            if repair_date_str and repair_date_str not in ['', 'None', 'null']:
                try:
                    default_repair_date = datetime.strptime(str(repair_date_str), '%Y-%m-%d').date()
                except:
                    default_repair_date = None
            else:
                default_repair_date = None

            # Location data - now stored as strings in database
            lat_val = rec.get('argos_latitude', '')
            lon_val = rec.get('argos_longitude', '')

            # Use string values directly without any conversion
            default_argos_latitude = str(lat_val) if lat_val and not pd.isna(lat_val) else ''
            default_argos_longitude = str(lon_val) if lon_val and not pd.isna(lon_val) else ''

            # Debug: Print what we're getting from database
            if default_argos_latitude or default_argos_longitude:
                print(f"DEBUG: Retrieved lat='{lat_val}' (type: {type(lat_val)}), lon='{lon_val}' (type: {type(lon_val)})")
                print(f"DEBUG: Using defaults lat='{default_argos_latitude}', lon='{default_argos_longitude}'")

            # Time fields - extract time portion only
            start_repair = rec.get('start_repair_time', '')

            # Debug: Print what we're getting for times
            if start_repair:
                print(f"DEBUG: Retrieved start_repair_time='{start_repair}' (type: {type(start_repair)})")

            if start_repair and 'T' in str(start_repair):
                # Format is like "1900-03-13T03:00:00"
                time_part = str(start_repair).split('T')[1]
                default_start_repair_time = time_part[:5] if time_part else ''  # Get HH:mm
                print(f"DEBUG: Extracted start time: '{default_start_repair_time}'")
            elif start_repair and ' ' in str(start_repair):
                default_start_repair_time = str(start_repair).split(' ')[1][:5]  # Get HH:mm
                print(f"DEBUG: Extracted start time (space separator): '{default_start_repair_time}'")
            else:
                default_start_repair_time = ''

            end_repair = rec.get('end_repair_time', '')
            if end_repair and 'T' in str(end_repair):
                # Format is like "1900-03-13T03:00:00"
                time_part = str(end_repair).split('T')[1]
                default_end_repair_time = time_part[:5] if time_part else ''  # Get HH:mm
            elif end_repair and ' ' in str(end_repair):
                default_end_repair_time = str(end_repair).split(' ')[1][:5]  # Get HH:mm
            else:
                default_end_repair_time = ''

            swap = rec.get('swap_time', '')
            if swap and 'T' in str(swap):
                # Format is like "1900-03-13T03:00:00"
                time_part = str(swap).split('T')[1]
                default_swap_time = time_part[:5] if time_part else ''  # Get HH:mm
            elif swap and ' ' in str(swap):
                default_swap_time = str(swap).split(' ')[1][:5]  # Get HH:mm
            else:
                default_swap_time = ''

            # Actual Position fields
            default_actual_latitude = str(rec.get('actual_latitude', '')) if rec.get('actual_latitude') else ''
            default_actual_longitude = str(rec.get('actual_longitude', '')) if rec.get('actual_longitude') else ''
            default_depth = str(rec.get('depth', '')) if rec.get('depth') else ''
            default_ctd_number = str(rec.get('ctd_number', '')) if rec.get('ctd_number') else ''

            # Buoy Condition and Evidence fields
            # Check both old and new column names for backward compatibility
            default_buoy_condition = str(rec.get('buoy_condition', '')) if rec.get('buoy_condition') else ''
            if not default_buoy_condition and rec.get('buoy_details'):
                default_buoy_condition = str(rec.get('buoy_details', ''))

            default_fishing_vandalism = str(rec.get('fishing_vandalism', '')) if rec.get('fishing_vandalism') else ''
            if not default_fishing_vandalism and rec.get('repair_fishing_vandalism'):
                default_fishing_vandalism = str(rec.get('repair_fishing_vandalism', ''))

            # Parse lost_equipment JSON for Old S/N values
            lost_equipment = parse_json_field(rec.get('lost_equipment', '{}'))

            # Parse replacement_equipment JSON for New S/N values
            replacement_equipment = parse_json_field(rec.get('replacement_equipment', '{}'))

            # Debug output for replacement_equipment
            if rec.get('mooring_id') == 'RA092B':
                print(f"DEBUG RA092B: replacement_equipment raw = {rec.get('replacement_equipment')}")
                print(f"DEBUG RA092B: replacement_equipment parsed = {replacement_equipment}")
                if 'rain' in replacement_equipment:
                    print(f"DEBUG RA092B: rain data in replacement = {replacement_equipment['rain']}")

            # Helper function to get serial number from nested JSON structure
            def get_sensor_sn(data, key):
                sensor_data = data.get(key.lower(), {})
                if isinstance(sensor_data, dict):
                    sn_value = sensor_data.get('sn', '')
                    # Handle NaN, null, None as empty string
                    if sn_value and str(sn_value).lower() not in ['nan', 'null', 'none']:
                        return str(sn_value)
                return ''

            # Helper function to get lost/condition status from nested JSON structure
            def get_sensor_condition(data, key):
                sensor_data = data.get(key.lower(), {})
                if isinstance(sensor_data, dict):
                    lost_value = sensor_data.get('lost', '')
                    # Handle null, None as empty string
                    if lost_value and str(lost_value).lower() not in ['null', 'none']:
                        return str(lost_value)
                return ''

            # Sensor Exchange defaults - Old S/N from lost_equipment JSON, New S/N from replacement_equipment JSON
            default_tube_old_sn = get_sensor_sn(lost_equipment, 'tube')
            default_tube_new_sn = get_sensor_sn(replacement_equipment, 'tube') or (str(rec.get('tube_new_sn', '')) if rec.get('tube_new_sn') else '')
            default_tube_condition = get_sensor_condition(lost_equipment, 'tube') or (str(rec.get('tube_condition', '')) if rec.get('tube_condition') else '')
            default_tube_details = str(rec.get('tube_details', '')) if rec.get('tube_details') else ''

            default_ptt_old_sn = get_sensor_sn(lost_equipment, 'ptt')
            default_ptt_new_sn = get_sensor_sn(replacement_equipment, 'ptt') or (str(rec.get('ptt_new_sn', '')) if rec.get('ptt_new_sn') else '')
            default_ptt_condition = get_sensor_condition(lost_equipment, 'ptt') or (str(rec.get('ptt_condition', '')) if rec.get('ptt_condition') else '')
            default_ptt_details = str(rec.get('ptt_details', '')) if rec.get('ptt_details') else ''

            default_atrh_old_sn = get_sensor_sn(lost_equipment, 'atrh')
            default_atrh_new_sn = get_sensor_sn(replacement_equipment, 'atrh') or (str(rec.get('atrh_new_sn', '')) if rec.get('atrh_new_sn') else '')
            default_atrh_condition = get_sensor_condition(lost_equipment, 'atrh') or (str(rec.get('atrh_condition', '')) if rec.get('atrh_condition') else '')
            default_atrh_details = str(rec.get('atrh_details', '')) if rec.get('atrh_details') else ''

            default_sst_old_sn = get_sensor_sn(lost_equipment, 'sst')
            default_sst_new_sn = get_sensor_sn(replacement_equipment, 'sst') or (str(rec.get('sst_new_sn', '')) if rec.get('sst_new_sn') else '')
            default_sst_condition = get_sensor_condition(lost_equipment, 'sst') or (str(rec.get('sst_condition', '')) if rec.get('sst_condition') else '')
            default_sst_details = str(rec.get('sst_details', '')) if rec.get('sst_details') else ''

            default_wind_old_sn = get_sensor_sn(lost_equipment, 'wind')
            default_wind_new_sn = get_sensor_sn(replacement_equipment, 'wind') or (str(rec.get('wind_new_sn', '')) if rec.get('wind_new_sn') else '')
            default_wind_condition = get_sensor_condition(lost_equipment, 'wind') or (str(rec.get('wind_condition', '')) if rec.get('wind_condition') else '')
            default_wind_details = str(rec.get('wind_details', '')) if rec.get('wind_details') else ''

            default_rain_old_sn = get_sensor_sn(lost_equipment, 'rain')
            default_rain_new_sn = get_sensor_sn(replacement_equipment, 'rain') or (str(rec.get('rain_new_sn', '')) if rec.get('rain_new_sn') else '')

            # Debug for RA092B rain sensor
            if rec.get('mooring_id') == 'RA092B':
                print(f"DEBUG RA092B: rain_new_sn from replacement_equipment = {get_sensor_sn(replacement_equipment, 'rain')}")
                print(f"DEBUG RA092B: rain_new_sn from column = {rec.get('rain_new_sn')}")
                print(f"DEBUG RA092B: default_rain_new_sn final value = {default_rain_new_sn}")

            default_rain_condition = get_sensor_condition(lost_equipment, 'rain') or (str(rec.get('rain_condition', '')) if rec.get('rain_condition') else '')
            default_rain_details = str(rec.get('rain_details', '')) if rec.get('rain_details') else ''

            default_swrad_old_sn = get_sensor_sn(lost_equipment, 'swrad') or get_sensor_sn(lost_equipment, 'sw_rad')
            default_swrad_new_sn = get_sensor_sn(replacement_equipment, 'swrad') or get_sensor_sn(replacement_equipment, 'sw_rad') or (str(rec.get('swrad_new_sn', '')) if rec.get('swrad_new_sn') else '')
            default_swrad_condition = get_sensor_condition(lost_equipment, 'swrad') or get_sensor_condition(lost_equipment, 'sw_rad') or (str(rec.get('swrad_condition', '')) if rec.get('swrad_condition') else '')
            default_swrad_details = str(rec.get('swrad_details', '')) if rec.get('swrad_details') else ''

            default_baro_old_sn = get_sensor_sn(lost_equipment, 'baro') or get_sensor_sn(lost_equipment, 'baro_press')
            default_baro_new_sn = get_sensor_sn(replacement_equipment, 'baro') or get_sensor_sn(replacement_equipment, 'baro_press') or (str(rec.get('baro_new_sn', '')) if rec.get('baro_new_sn') else '')
            default_baro_condition = get_sensor_condition(lost_equipment, 'baro') or get_sensor_condition(lost_equipment, 'baro_press') or (str(rec.get('baro_condition', '')) if rec.get('baro_condition') else '')
            default_baro_details = str(rec.get('baro_details', '')) if rec.get('baro_details') else ''

            default_seacat_old_sn = get_sensor_sn(lost_equipment, 'seacat')
            default_seacat_new_sn = get_sensor_sn(replacement_equipment, 'seacat') or (str(rec.get('seacat_new_sn', '')) if rec.get('seacat_new_sn') else '')
            default_seacat_condition = get_sensor_condition(lost_equipment, 'seacat') or (str(rec.get('seacat_condition', '')) if rec.get('seacat_condition') else '')
            default_seacat_details = str(rec.get('seacat_details', '')) if rec.get('seacat_details') else ''

            # Tube Exchange defaults
            default_tube_time = str(rec.get('tube_time', '')) if rec.get('tube_time') else ''
            default_gmt = str(rec.get('gmt', '')) if rec.get('gmt') else ''
            default_drift = str(rec.get('drift', '')) if rec.get('drift') else ''
            default_bat_logic = str(rec.get('bat_logic', '')) if rec.get('bat_logic') else ''
            default_bat_transmit = str(rec.get('bat_transmit', '')) if rec.get('bat_transmit') else ''
            default_file_name = str(rec.get('file_name', '')) if rec.get('file_name') else ''

            # Met Obs defaults
            # Handle ship_date
            ship_date_str = rec.get('ship_date', '')
            if ship_date_str and ship_date_str not in ['', 'None', 'null']:
                try:
                    default_ship_date = datetime.strptime(str(ship_date_str), '%Y-%m-%d').date()
                except:
                    default_ship_date = None
            else:
                default_ship_date = None

            default_ship_time = str(rec.get('ship_time', '')) if rec.get('ship_time') else ''
            default_ship_wind_dir = str(rec.get('ship_wind_dir', '')) if rec.get('ship_wind_dir') else ''
            default_ship_wind_spd = str(rec.get('ship_wind_spd', '')) if rec.get('ship_wind_spd') else ''
            default_ship_air_temp = str(rec.get('ship_air_temp', '')) if rec.get('ship_air_temp') else ''
            default_ship_sst = str(rec.get('ship_sst', '')) if rec.get('ship_sst') else ''
            default_ship_ssc = str(rec.get('ship_ssc', '')) if rec.get('ship_ssc') else ''
            default_ship_rh = str(rec.get('ship_rh', '')) if rec.get('ship_rh') else ''

            # Handle buoy_date
            buoy_date_str = rec.get('buoy_date', '')
            if buoy_date_str and buoy_date_str not in ['', 'None', 'null']:
                try:
                    default_buoy_date = datetime.strptime(str(buoy_date_str), '%Y-%m-%d').date()
                except:
                    default_buoy_date = None
            else:
                default_buoy_date = None

            default_buoy_time = str(rec.get('buoy_time', '')) if rec.get('buoy_time') else ''
            default_buoy_wind_dir = str(rec.get('buoy_wind_dir', '')) if rec.get('buoy_wind_dir') else ''
            default_buoy_wind_spd = str(rec.get('buoy_wind_spd', '')) if rec.get('buoy_wind_spd') else ''
            default_buoy_air_temp = str(rec.get('buoy_air_temp', '')) if rec.get('buoy_air_temp') else ''
            default_buoy_sst = str(rec.get('buoy_sst', '')) if rec.get('buoy_sst') else ''
            default_buoy_ssc = str(rec.get('buoy_ssc', '')) if rec.get('buoy_ssc') else ''
            default_buoy_rh = str(rec.get('buoy_rh', '')) if rec.get('buoy_rh') else ''

            # Deployment/Recovery tracking


            record_id = rec.get('id')
        else:
            # No record selected
            default_site = ""
            default_mooring_id = ""
            default_cruise = ""
            default_personnel = ""
            default_repair_date = None
            default_argos_latitude = ""
            default_argos_longitude = ""
            default_start_repair_time = ""
            default_end_repair_time = ""
            default_swap_time = ""
            default_cruise_site = ""
            default_counter = ""
            default_actual_latitude = ""
            default_actual_longitude = ""
            default_depth = ""
            default_ctd_number = ""
            default_buoy_condition = ""
            default_fishing_vandalism = ""

            # Sensor Exchange defaults
            default_tube_old_sn = ""
            default_tube_new_sn = ""
            default_tube_condition = ""
            default_tube_details = ""
            default_ptt_old_sn = ""
            default_ptt_new_sn = ""
            default_ptt_condition = ""
            default_ptt_details = ""
            default_atrh_old_sn = ""
            default_atrh_new_sn = ""
            default_atrh_condition = ""
            default_atrh_details = ""
            default_sst_old_sn = ""
            default_sst_new_sn = ""
            default_sst_condition = ""
            default_sst_details = ""
            default_wind_old_sn = ""
            default_wind_new_sn = ""
            default_wind_condition = ""
            default_wind_details = ""
            default_rain_old_sn = ""
            default_rain_new_sn = ""
            default_rain_condition = ""
            default_rain_details = ""
            default_swrad_old_sn = ""
            default_swrad_new_sn = ""
            default_swrad_condition = ""
            default_swrad_details = ""
            default_baro_old_sn = ""
            default_baro_new_sn = ""
            default_baro_condition = ""
            default_baro_details = ""
            default_seacat_old_sn = ""
            default_seacat_new_sn = ""
            default_seacat_condition = ""
            default_seacat_details = ""

            # Tube Exchange defaults
            default_tube_time = ""
            default_gmt = ""
            default_drift = ""
            default_bat_logic = ""
            default_bat_transmit = ""
            default_file_name = ""

            # Met Obs defaults
            default_ship_date = None
            default_ship_time = ""
            default_ship_wind_dir = ""
            default_ship_wind_spd = ""
            default_ship_air_temp = ""
            default_ship_sst = ""
            default_ship_ssc = ""
            default_ship_rh = ""
            default_buoy_date = None
            default_buoy_time = ""
            default_buoy_wind_dir = ""
            default_buoy_wind_spd = ""
            default_buoy_air_temp = ""
            default_buoy_sst = ""
            default_buoy_ssc = ""
            default_buoy_rh = ""

            record_id = None

    # Debug section to show available columns
    with st.expander("🔧 Debug: Database Columns", expanded=False):
        if st.session_state.selected_repair:
            st.write("**Available columns in repair_normalized table:**")

            # Show the default values being used
            st.write("**Default values for form fields:**")
            debug_defaults = {
                'site': default_site,
                'mooring_id': default_mooring_id,
                'cruise': default_cruise,
                'personnel': default_personnel,
                'argos_latitude': default_argos_latitude,
                'argos_longitude': default_argos_longitude,
                'start_repair_time': default_start_repair_time,
                'end_repair_time': default_end_repair_time,
                'swap_time': default_swap_time,
                'repair_date': str(default_repair_date) if default_repair_date else 'None'
            }
            st.json(debug_defaults)

            # Get all columns and values
            debug_data = []
            for key, value in st.session_state.selected_repair.items():
                # Parse JSON fields for better display
                if key in ['lost_equipment', 'replacement_equipment', 'equipment_status']:
                    try:
                        if value and value != 'null' and value != '{}':
                            parsed = json.loads(value) if isinstance(value, str) else value
                            debug_data.append({
                                'Column': key,
                                'Value': json.dumps(parsed, indent=2) if parsed else 'Empty JSON'
                            })
                        else:
                            debug_data.append({'Column': key, 'Value': 'Empty JSON'})
                    except:
                        debug_data.append({'Column': key, 'Value': str(value)})
                else:
                    debug_data.append({'Column': key, 'Value': str(value) if value is not None else 'NULL'})

            # Display as DataFrame
            debug_df = pd.DataFrame(debug_data)
            st.dataframe(debug_df, use_container_width=True, height=400)

            # Show raw record as JSON
            if st.checkbox("Show raw record as JSON"):
                st.json(st.session_state.selected_repair)
        else:
            # Just show available columns from database
            table_exists, columns = check_database_table()
            if columns:
                st.write("**Columns in repair_normalized table:**")
                for i, col in enumerate(columns, 1):
                    st.write(f"{i}. {col}")
            else:
                st.warning("Could not retrieve column information")

    # Show the form in both modes
    if mode == "Add New" or mode == "Search/Edit":

        st.markdown("---")

        # Form sections
        with st.form("repair_form"):

            # Basic Information Section
            st.markdown("### Basic Information")

            # Row 1: Site and Mooring ID
            col1, col2 = st.columns(2)
            with col1:
                site_options = [""] + available_sites + ["Other (specify below)"]
                if default_site in site_options:
                    site_index = site_options.index(default_site)
                elif default_site and default_site not in site_options:
                    site_options.insert(1, default_site)
                    site_index = 1
                else:
                    site_index = 0

                site_selection = st.selectbox("Site", options=site_options, index=site_index, key="site_dropdown")

                if site_selection == "Other (specify below)":
                    site = st.text_input("Specify site", value="", key="site_custom")
                else:
                    site = site_selection

            with col2:
                mooring_id = st.text_input("Mooring ID", value=default_mooring_id, key="mooring_id")

            # Row 2: Cruise and Repair Date
            col3, col4 = st.columns(2)
            with col3:
                cruise_options = [""] + available_cruises + ["Other (specify below)"]
                if default_cruise in cruise_options:
                    cruise_index = cruise_options.index(default_cruise)
                elif default_cruise and default_cruise not in cruise_options:
                    cruise_options.insert(1, default_cruise)
                    cruise_index = 1
                else:
                    cruise_index = 0

                cruise_selection = st.selectbox("Cruise", options=cruise_options, index=cruise_index, key="cruise_dropdown")

                if cruise_selection == "Other (specify below)":
                    cruise = st.text_input("Specify cruise", value="", key="cruise_custom")
                else:
                    cruise = cruise_selection

            with col4:
                repair_date = st.date_input("Repair Date", value=default_repair_date, key="repair_date", format="YYYY-MM-DD")

            # Row 3: Personnel (full width)
            personnel = st.text_input("Personnel", value=default_personnel, key="personnel",
                                     help="Enter personnel names involved in the repair")

            # Row 4: Argos Latitude and Argos Longitude
            col5, col6 = st.columns(2)
            with col5:
                # Add placeholder text only for Add New mode
                lat_placeholder = "DD mm.mm N/S" if mode == "Add New" else ""
                argos_latitude = st.text_input("Argos Latitude", value=default_argos_latitude, key="argos_latitude",
                                              help="Enter latitude value", placeholder=lat_placeholder)

            with col6:
                # Add placeholder text only for Add New mode
                lon_placeholder = "DDD mm.mm E/W" if mode == "Add New" else ""
                argos_longitude = st.text_input("Argos Longitude", value=default_argos_longitude, key="argos_longitude",
                                               help="Enter longitude value", placeholder=lon_placeholder)

            # Row 5: Start Repair Time and End Repair Time
            col7, col8 = st.columns(2)
            with col7:
                start_repair_time = st.text_input("Start Repair Time", value=default_start_repair_time,
                                                 key="start_repair_time", placeholder="HH:mm")

            with col8:
                end_repair_time = st.text_input("End Repair Time", value=default_end_repair_time,
                                               key="end_repair_time", placeholder="HH:mm")

            # Row 6: Swap Time (full width)
            swap_time = st.text_input("Swap Time", value=default_swap_time, key="swap_time",
                                     placeholder="HH:mm", help="Time when equipment swap occurred")

            # Hidden fields that still need to be captured but not displayed in main form
            cruise_site = st.session_state.get('cruise_site_hidden', default_cruise_site)
            counter = st.session_state.get('counter_hidden', default_counter)

            st.markdown("---")
            st.markdown("### Actual Position")

            # Row 1: Actual Latitude and Actual Longitude
            col9, col10 = st.columns(2)
            with col9:
                actual_latitude = st.text_input("Latitude", value=default_actual_latitude, key="actual_latitude",
                                               help="Actual latitude position")

            with col10:
                actual_longitude = st.text_input("Longitude", value=default_actual_longitude, key="actual_longitude",
                                                help="Actual longitude position")

            # Row 2: Depth and CTD#
            col11, col12 = st.columns(2)
            with col11:
                depth = st.text_input("Depth", value=default_depth, key="depth",
                                    help="Depth measurement")

            with col12:
                ctd_number = st.text_input("CTD#", value=default_ctd_number, key="ctd_number",
                                         help="CTD number")

            # Buoy Condition text area (3 rows)
            buoy_condition = st.text_area("Buoy Condition",
                                         value=default_buoy_condition,
                                         key="buoy_condition",
                                         height=75,  # Approximately 3 rows
                                         help="Describe the condition of the buoy")

            # Evidence of Fishing or Vandalism text area (3 rows)
            fishing_vandalism = st.text_area("Evidence of Fishing or Vandalism",
                                            value=default_fishing_vandalism,
                                            key="fishing_vandalism",
                                            height=75,  # Approximately 3 rows
                                            help="Describe any evidence of fishing or vandalism")

            st.markdown("---")
            st.markdown("### Sensor Exchange")

            # Create header row
            col_label, col_old, col_new, col_condition, col_details = st.columns([1.5, 2, 2, 2, 3])
            with col_label:
                st.markdown("**Sensor**")
            with col_old:
                st.markdown("**Old S/N**")
            with col_new:
                st.markdown("**New S/N**")
            with col_condition:
                st.markdown("**Condition**")
            with col_details:
                st.markdown("**Details**")

            # Tube row
            col_label, col_old, col_new, col_condition, col_details = st.columns([1.5, 2, 2, 2, 3])
            with col_label:
                st.markdown("Tube")
            with col_old:
                tube_old_sn = st.text_input("Tube Old S/N", value=default_tube_old_sn, key="tube_old_sn", label_visibility="collapsed")
            with col_new:
                tube_new_sn = st.text_input("Tube New S/N", value=default_tube_new_sn, key="tube_new_sn", label_visibility="collapsed")
            with col_condition:
                condition_options = ["", "Lost", "Damaged", "Fouled"]
                tube_condition = st.selectbox("Tube Condition", options=condition_options, index=condition_options.index(default_tube_condition) if default_tube_condition in condition_options else 0, key="tube_condition", label_visibility="collapsed")
            with col_details:
                tube_details = st.text_input("Tube Details", value=default_tube_details, key="tube_details", label_visibility="collapsed")

            # PTT row
            col_label, col_old, col_new, col_condition, col_details = st.columns([1.5, 2, 2, 2, 3])
            with col_label:
                st.markdown("PTT")
            with col_old:
                ptt_old_sn = st.text_input("PTT Old S/N", value=default_ptt_old_sn, key="ptt_old_sn", label_visibility="collapsed")
            with col_new:
                ptt_new_sn = st.text_input("PTT New S/N", value=default_ptt_new_sn, key="ptt_new_sn", label_visibility="collapsed")
            with col_condition:
                ptt_condition = st.selectbox("PTT Condition", options=condition_options, index=condition_options.index(default_ptt_condition) if default_ptt_condition in condition_options else 0, key="ptt_condition", label_visibility="collapsed")
            with col_details:
                ptt_details = st.text_input("PTT Details", value=default_ptt_details, key="ptt_details", label_visibility="collapsed")

            # ATRH row
            col_label, col_old, col_new, col_condition, col_details = st.columns([1.5, 2, 2, 2, 3])
            with col_label:
                st.markdown("ATRH")
            with col_old:
                atrh_old_sn = st.text_input("ATRH Old S/N", value=default_atrh_old_sn, key="atrh_old_sn", label_visibility="collapsed")
            with col_new:
                atrh_new_sn = st.text_input("ATRH New S/N", value=default_atrh_new_sn, key="atrh_new_sn", label_visibility="collapsed")
            with col_condition:
                atrh_condition = st.selectbox("ATRH Condition", options=condition_options, index=condition_options.index(default_atrh_condition) if default_atrh_condition in condition_options else 0, key="atrh_condition", label_visibility="collapsed")
            with col_details:
                atrh_details = st.text_input("ATRH Details", value=default_atrh_details, key="atrh_details", label_visibility="collapsed")

            # SST row
            col_label, col_old, col_new, col_condition, col_details = st.columns([1.5, 2, 2, 2, 3])
            with col_label:
                st.markdown("SST")
            with col_old:
                sst_old_sn = st.text_input("SST Old S/N", value=default_sst_old_sn, key="sst_old_sn", label_visibility="collapsed")
            with col_new:
                sst_new_sn = st.text_input("SST New S/N", value=default_sst_new_sn, key="sst_new_sn", label_visibility="collapsed")
            with col_condition:
                sst_condition = st.selectbox("SST Condition", options=condition_options, index=condition_options.index(default_sst_condition) if default_sst_condition in condition_options else 0, key="sst_condition", label_visibility="collapsed")
            with col_details:
                sst_details = st.text_input("SST Details", value=default_sst_details, key="sst_details", label_visibility="collapsed")

            # Wind row
            col_label, col_old, col_new, col_condition, col_details = st.columns([1.5, 2, 2, 2, 3])
            with col_label:
                st.markdown("Wind")
            with col_old:
                wind_old_sn = st.text_input("Wind Old S/N", value=default_wind_old_sn, key="wind_old_sn", label_visibility="collapsed")
            with col_new:
                wind_new_sn = st.text_input("Wind New S/N", value=default_wind_new_sn, key="wind_new_sn", label_visibility="collapsed")
            with col_condition:
                wind_condition = st.selectbox("Wind Condition", options=condition_options, index=condition_options.index(default_wind_condition) if default_wind_condition in condition_options else 0, key="wind_condition", label_visibility="collapsed")
            with col_details:
                wind_details = st.text_input("Wind Details", value=default_wind_details, key="wind_details", label_visibility="collapsed")

            # Rain row
            col_label, col_old, col_new, col_condition, col_details = st.columns([1.5, 2, 2, 2, 3])
            with col_label:
                st.markdown("Rain")
            with col_old:
                rain_old_sn = st.text_input("Rain Old S/N", value=default_rain_old_sn, key="rain_old_sn", label_visibility="collapsed")
            with col_new:
                rain_new_sn = st.text_input("Rain New S/N", value=default_rain_new_sn, key="rain_new_sn", label_visibility="collapsed")
            with col_condition:
                rain_condition = st.selectbox("Rain Condition", options=condition_options, index=condition_options.index(default_rain_condition) if default_rain_condition in condition_options else 0, key="rain_condition", label_visibility="collapsed")
            with col_details:
                rain_details = st.text_input("Rain Details", value=default_rain_details, key="rain_details", label_visibility="collapsed")

            # SW Rad row
            col_label, col_old, col_new, col_condition, col_details = st.columns([1.5, 2, 2, 2, 3])
            with col_label:
                st.markdown("SW Rad")
            with col_old:
                swrad_old_sn = st.text_input("SW Rad Old S/N", value=default_swrad_old_sn, key="swrad_old_sn", label_visibility="collapsed")
            with col_new:
                swrad_new_sn = st.text_input("SW Rad New S/N", value=default_swrad_new_sn, key="swrad_new_sn", label_visibility="collapsed")
            with col_condition:
                swrad_condition = st.selectbox("SW Rad Condition", options=condition_options, index=condition_options.index(default_swrad_condition) if default_swrad_condition in condition_options else 0, key="swrad_condition", label_visibility="collapsed")
            with col_details:
                swrad_details = st.text_input("SW Rad Details", value=default_swrad_details, key="swrad_details", label_visibility="collapsed")

            # Baro Press row
            col_label, col_old, col_new, col_condition, col_details = st.columns([1.5, 2, 2, 2, 3])
            with col_label:
                st.markdown("Baro Press")
            with col_old:
                baro_old_sn = st.text_input("Baro Press Old S/N", value=default_baro_old_sn, key="baro_old_sn", label_visibility="collapsed")
            with col_new:
                baro_new_sn = st.text_input("Baro Press New S/N", value=default_baro_new_sn, key="baro_new_sn", label_visibility="collapsed")
            with col_condition:
                baro_condition = st.selectbox("Baro Press Condition", options=condition_options, index=condition_options.index(default_baro_condition) if default_baro_condition in condition_options else 0, key="baro_condition", label_visibility="collapsed")
            with col_details:
                baro_details = st.text_input("Baro Press Details", value=default_baro_details, key="baro_details", label_visibility="collapsed")

            # SeaCat row
            col_label, col_old, col_new, col_condition, col_details = st.columns([1.5, 2, 2, 2, 3])
            with col_label:
                st.markdown("SeaCat")
            with col_old:
                seacat_old_sn = st.text_input("SeaCat Old S/N", value=default_seacat_old_sn, key="seacat_old_sn", label_visibility="collapsed")
            with col_new:
                seacat_new_sn = st.text_input("SeaCat New S/N", value=default_seacat_new_sn, key="seacat_new_sn", label_visibility="collapsed")
            with col_condition:
                seacat_condition = st.selectbox("SeaCat Condition", options=condition_options, index=condition_options.index(default_seacat_condition) if default_seacat_condition in condition_options else 0, key="seacat_condition", label_visibility="collapsed")
            with col_details:
                seacat_details = st.text_input("SeaCat Details", value=default_seacat_details, key="seacat_details", label_visibility="collapsed")

            st.markdown("---")
            st.markdown("### Tube Exchange")

            # Create two rows for the Tube Exchange section
            # First row: "Tube Time" GMT Drift
            col1, col2, col3 = st.columns([2, 2, 2])
            with col1:
                st.markdown('Tube Time')
                tube_time = st.text_input("Tube Time", value=default_tube_time, key="tube_time",
                                         placeholder="HH:MM", help="Time from tube clock",
                                         label_visibility="collapsed")
            with col2:
                st.markdown("GMT")
                gmt = st.text_input("GMT", value=default_gmt, key="gmt",
                                        placeholder="HH:MM", help="Greenwich Mean Time",
                                        label_visibility="collapsed")
            with col3:
                st.markdown("Drift (minutes)")
                drift = st.text_input("Drift", value=default_drift, key="drift",
                                          placeholder="±MM", help="Time drift in minutes (+ fast, - slow)",
                                          label_visibility="collapsed")

            # Add spacing
            st.markdown("")

            # Second row: Old Tube - Logic Transmit Filename
            st.markdown("**Old Tube Data**")
            col1, col2, col3 = st.columns([2, 2, 2])
            with col1:
                st.markdown("Bat Logic")
                bat_logic = st.text_input("Bat Logic", value=default_bat_logic, key="bat_logic",
                                              placeholder="Serial number", help="Battery logic serial number",
                                              label_visibility="collapsed")
            with col2:
                st.markdown("Bat Transmit")
                bat_transmit = st.text_input("Bat Transmit", value=default_bat_transmit, key="bat_transmit",
                                                 placeholder="e.g., 90s", help="Battery transmit interval",
                                                 label_visibility="collapsed")
            with col3:
                st.markdown("Data Filename")
                file_name = st.text_input("Filename", value=default_file_name, key="file_name",
                                                 placeholder="e.g., TUBE_001.DAT", help="Downloaded data filename",
                                                 label_visibility="collapsed")

            st.markdown("---")
            st.markdown("### Met Obs")

            # Create header row
            col_label, col_date, col_time, col_wind_dir, col_wind_spd, col_air_temp, col_sst, col_ssc, col_rh = st.columns([1, 1.5, 1, 1, 1.5, 1, 1, 1, 1])
            with col_label:
                st.markdown("")
            with col_date:
                st.markdown("**Date**")
            with col_time:
                st.markdown("**Time**")
            with col_wind_dir:
                st.markdown("**Wind Dir**")
            with col_wind_spd:
                st.markdown("**Wind Spd(kts)**")
            with col_air_temp:
                st.markdown("**Air Temp**")
            with col_sst:
                st.markdown("**SST**")
            with col_ssc:
                st.markdown("**SSC**")
            with col_rh:
                st.markdown("**RH**")

            # Ship row
            col_label, col_date, col_time, col_wind_dir, col_wind_spd, col_air_temp, col_sst, col_ssc, col_rh = st.columns([1, 1.5, 1, 1, 1.5, 1, 1, 1, 1])
            with col_label:
                st.markdown("**Ship**")
            with col_date:
                ship_date = st.date_input("Ship Date", value=default_ship_date, key="ship_date", label_visibility="collapsed", format="MM/DD/YYYY")
            with col_time:
                ship_time = st.text_input("Ship Time", value=default_ship_time, key="ship_time", placeholder="HH:MM", label_visibility="collapsed")
            with col_wind_dir:
                ship_wind_dir = st.text_input("Ship Wind Dir", value=default_ship_wind_dir, key="ship_wind_dir", placeholder="deg", label_visibility="collapsed")
            with col_wind_spd:
                ship_wind_spd = st.text_input("Ship Wind Speed", value=default_ship_wind_spd, key="ship_wind_spd", placeholder="kts", label_visibility="collapsed")
            with col_air_temp:
                ship_air_temp = st.text_input("Ship Air Temp", value=default_ship_air_temp, key="ship_air_temp", placeholder="°C", label_visibility="collapsed")
            with col_sst:
                ship_sst = st.text_input("Ship SST", value=default_ship_sst, key="ship_sst", placeholder="°C", label_visibility="collapsed")
            with col_ssc:
                ship_ssc = st.text_input("Ship SSC", value=default_ship_ssc, key="ship_ssc", placeholder="psu", label_visibility="collapsed")
            with col_rh:
                ship_rh = st.text_input("Ship RH", value=default_ship_rh, key="ship_rh", placeholder="%", label_visibility="collapsed")

            # Buoy row
            col_label, col_date, col_time, col_wind_dir, col_wind_spd, col_air_temp, col_sst, col_ssc, col_rh = st.columns([1, 1.5, 1, 1, 1.5, 1, 1, 1, 1])
            with col_label:
                st.markdown("**Buoy**")
            with col_date:
                buoy_date = st.date_input("Buoy Date", value=default_buoy_date, key="buoy_date", label_visibility="collapsed", format="MM/DD/YYYY")
            with col_time:
                buoy_time = st.text_input("Buoy Time", value=default_buoy_time, key="buoy_time", placeholder="HH:MM", label_visibility="collapsed")
            with col_wind_dir:
                buoy_wind_dir = st.text_input("Buoy Wind Dir", value=default_buoy_wind_dir, key="buoy_wind_dir", placeholder="deg", label_visibility="collapsed")
            with col_wind_spd:
                buoy_wind_spd = st.text_input("Buoy Wind Speed", value=default_buoy_wind_spd, key="buoy_wind_spd", placeholder="kts", label_visibility="collapsed")
            with col_air_temp:
                buoy_air_temp = st.text_input("Buoy Air Temp", value=default_buoy_air_temp, key="buoy_air_temp", placeholder="°C", label_visibility="collapsed")
            with col_sst:
                buoy_sst = st.text_input("Buoy SST", value=default_buoy_sst, key="buoy_sst", placeholder="°C", label_visibility="collapsed")
            with col_ssc:
                buoy_ssc = st.text_input("Buoy SSC", value=default_buoy_ssc, key="buoy_ssc", placeholder="psu", label_visibility="collapsed")
            with col_rh:
                buoy_rh = st.text_input("Buoy RH", value=default_buoy_rh, key="buoy_rh", placeholder="%", label_visibility="collapsed")

            st.markdown("---")

            # Form submission
            col_submit1, col_submit2, col_submit3 = st.columns([1, 1, 1])
            with col_submit2:
                submitted = st.form_submit_button(
                    "Save Repair" if mode == "Add New" else "Update Repair",
                    use_container_width=True,
                    type="primary"
                )

            if submitted:
                # Prepare data for saving - store lat/lon as strings
                repair_data = {
                    'site': site,
                    'mooring_id': mooring_id,
                    'cruise': cruise,
                    'personnel': personnel,
                    'cruise_site': cruise_site,
                    'counter': parse_int_safe(counter),
                    'repair_date': parse_date_input(repair_date),
                    'argos_latitude': argos_latitude.strip() if argos_latitude else None,
                    'argos_longitude': argos_longitude.strip() if argos_longitude else None,
                    'start_repair_time': parse_datetime_input(repair_date, start_repair_time),
                    'end_repair_time': parse_datetime_input(repair_date, end_repair_time),
                    'swap_time': parse_datetime_input(repair_date, swap_time),
                    'actual_latitude': actual_latitude.strip() if actual_latitude else None,
                    'actual_longitude': actual_longitude.strip() if actual_longitude else None,
                    'depth': depth.strip() if depth else None,
                    'ctd_number': ctd_number.strip() if ctd_number else None,
                    'buoy_condition': buoy_condition.strip() if buoy_condition else None,
                    'fishing_vandalism': fishing_vandalism.strip() if fishing_vandalism else None,
                    # Sensor Exchange fields
                    'tube_old_sn': tube_old_sn.strip() if tube_old_sn else None,
                    'tube_new_sn': tube_new_sn.strip() if tube_new_sn else None,
                    'tube_condition': tube_condition.strip() if tube_condition else None,
                    'tube_details': tube_details.strip() if tube_details else None,
                    'ptt_old_sn': ptt_old_sn.strip() if ptt_old_sn else None,
                    'ptt_new_sn': ptt_new_sn.strip() if ptt_new_sn else None,
                    'ptt_condition': ptt_condition.strip() if ptt_condition else None,
                    'ptt_details': ptt_details.strip() if ptt_details else None,
                    'atrh_old_sn': atrh_old_sn.strip() if atrh_old_sn else None,
                    'atrh_new_sn': atrh_new_sn.strip() if atrh_new_sn else None,
                    'atrh_condition': atrh_condition.strip() if atrh_condition else None,
                    'atrh_details': atrh_details.strip() if atrh_details else None,
                    'sst_old_sn': sst_old_sn.strip() if sst_old_sn else None,
                    'sst_new_sn': sst_new_sn.strip() if sst_new_sn else None,
                    'sst_condition': sst_condition.strip() if sst_condition else None,
                    'sst_details': sst_details.strip() if sst_details else None,
                    'wind_old_sn': wind_old_sn.strip() if wind_old_sn else None,
                    'wind_new_sn': wind_new_sn.strip() if wind_new_sn else None,
                    'wind_condition': wind_condition.strip() if wind_condition else None,
                    'wind_details': wind_details.strip() if wind_details else None,
                    'rain_old_sn': rain_old_sn.strip() if rain_old_sn else None,
                    'rain_new_sn': rain_new_sn.strip() if rain_new_sn else None,
                    'rain_condition': rain_condition.strip() if rain_condition else None,
                    'rain_details': rain_details.strip() if rain_details else None,
                    'swrad_old_sn': swrad_old_sn.strip() if swrad_old_sn else None,
                    'swrad_new_sn': swrad_new_sn.strip() if swrad_new_sn else None,
                    'swrad_condition': swrad_condition.strip() if swrad_condition else None,
                    'swrad_details': swrad_details.strip() if swrad_details else None,
                    'baro_old_sn': baro_old_sn.strip() if baro_old_sn else None,
                    'baro_new_sn': baro_new_sn.strip() if baro_new_sn else None,
                    'baro_condition': baro_condition.strip() if baro_condition else None,
                    'baro_details': baro_details.strip() if baro_details else None,
                    'seacat_old_sn': seacat_old_sn.strip() if seacat_old_sn else None,
                    'seacat_new_sn': seacat_new_sn.strip() if seacat_new_sn else None,
                    'seacat_condition': seacat_condition.strip() if seacat_condition else None,
                    'seacat_details': seacat_details.strip() if seacat_details else None,
                    # Tube Exchange fields
                    'tube_time': tube_time.strip() if tube_time else None,
                    'gmt': gmt.strip() if gmt else None,
                    'drift': drift.strip() if drift else None,
                    'bat_logic': bat_logic.strip() if bat_logic else None,
                    'bat_transmit': bat_transmit.strip() if bat_transmit else None,
                    'file_name': file_name.strip() if file_name else None,
                    # Met Obs fields
                    'ship_date': parse_date_input(ship_date) if ship_date else None,
                    'ship_time': ship_time.strip() if ship_time else None,
                    'ship_wind_dir': ship_wind_dir.strip() if ship_wind_dir else None,
                    'ship_wind_spd': ship_wind_spd.strip() if ship_wind_spd else None,
                    'ship_air_temp': ship_air_temp.strip() if ship_air_temp else None,
                    'ship_sst': ship_sst.strip() if ship_sst else None,
                    'ship_ssc': ship_ssc.strip() if ship_ssc else None,
                    'ship_rh': ship_rh.strip() if ship_rh else None,
                    'buoy_date': parse_date_input(buoy_date) if buoy_date else None,
                    'buoy_time': buoy_time.strip() if buoy_time else None,
                    'buoy_wind_dir': buoy_wind_dir.strip() if buoy_wind_dir else None,
                    'buoy_wind_spd': buoy_wind_spd.strip() if buoy_wind_spd else None,
                    'buoy_air_temp': buoy_air_temp.strip() if buoy_air_temp else None,
                    'buoy_sst': buoy_sst.strip() if buoy_sst else None,
                    'buoy_ssc': buoy_ssc.strip() if buoy_ssc else None,
                    'buoy_rh': buoy_rh.strip() if buoy_rh else None,
                    'a2_rep_dep': None,
                    'a2_rep_rec': None,
                    'check_duplicates': None,
                }

                # Build lost_equipment JSON from Old S/N values with nested structure
                lost_equipment_dict = {}
                if tube_old_sn and tube_old_sn.strip():
                    lost_equipment_dict['tube'] = {'sn': tube_old_sn.strip(), 'lost': tube_condition.strip() if tube_condition else None}
                if ptt_old_sn and ptt_old_sn.strip():
                    lost_equipment_dict['ptt'] = {'sn': ptt_old_sn.strip(), 'lost': ptt_condition.strip() if ptt_condition else None}
                if atrh_old_sn and atrh_old_sn.strip():
                    lost_equipment_dict['atrh'] = {'sn': atrh_old_sn.strip(), 'lost': atrh_condition.strip() if atrh_condition else None}
                if sst_old_sn and sst_old_sn.strip():
                    lost_equipment_dict['sst'] = {'sn': sst_old_sn.strip(), 'lost': sst_condition.strip() if sst_condition else None}
                if wind_old_sn and wind_old_sn.strip():
                    lost_equipment_dict['wind'] = {'sn': wind_old_sn.strip(), 'lost': wind_condition.strip() if wind_condition else None}
                if rain_old_sn and rain_old_sn.strip():
                    lost_equipment_dict['rain'] = {'sn': rain_old_sn.strip(), 'lost': rain_condition.strip() if rain_condition else None}
                if swrad_old_sn and swrad_old_sn.strip():
                    lost_equipment_dict['swrad'] = {'sn': swrad_old_sn.strip(), 'lost': swrad_condition.strip() if swrad_condition else None}
                if baro_old_sn and baro_old_sn.strip():
                    lost_equipment_dict['baro'] = {'sn': baro_old_sn.strip(), 'lost': baro_condition.strip() if baro_condition else None}
                if seacat_old_sn and seacat_old_sn.strip():
                    lost_equipment_dict['seacat'] = {'sn': seacat_old_sn.strip(), 'lost': seacat_condition.strip() if seacat_condition else None}

                # Build replacement_equipment JSON from New S/N values with nested structure
                replacement_equipment_dict = {}
                if tube_new_sn and tube_new_sn.strip():
                    replacement_equipment_dict['tube'] = {'sn': tube_new_sn.strip()}
                if ptt_new_sn and ptt_new_sn.strip():
                    replacement_equipment_dict['ptt'] = {'sn': ptt_new_sn.strip()}
                if atrh_new_sn and atrh_new_sn.strip():
                    replacement_equipment_dict['atrh'] = {'sn': atrh_new_sn.strip()}
                if sst_new_sn and sst_new_sn.strip():
                    replacement_equipment_dict['sst'] = {'sn': sst_new_sn.strip()}
                if wind_new_sn and wind_new_sn.strip():
                    replacement_equipment_dict['wind'] = {'sn': wind_new_sn.strip()}
                if rain_new_sn and rain_new_sn.strip():
                    replacement_equipment_dict['rain'] = {'sn': rain_new_sn.strip()}
                if swrad_new_sn and swrad_new_sn.strip():
                    replacement_equipment_dict['swrad'] = {'sn': swrad_new_sn.strip()}
                if baro_new_sn and baro_new_sn.strip():
                    replacement_equipment_dict['baro'] = {'sn': baro_new_sn.strip()}
                if seacat_new_sn and seacat_new_sn.strip():
                    replacement_equipment_dict['seacat'] = {'sn': seacat_new_sn.strip()}

                # Add the JSON fields to repair_data
                repair_data['lost_equipment'] = json.dumps(lost_equipment_dict)
                repair_data['replacement_equipment'] = json.dumps(replacement_equipment_dict)
                repair_data['equipment_status'] = json.dumps({})

                # Save or update the record
                is_update = (mode == "Search/Edit" and record_id is not None)
                success, message = save_repair(repair_data, is_update=is_update, record_id=record_id)

                if success:
                    st.success(message)
                    if mode == "Add New":
                        # Clear form for next entry
                        st.session_state.form_data = {}
                        st.rerun()
                else:
                    st.error(message)


if __name__ == "__main__":
    main()
