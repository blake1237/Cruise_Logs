import streamlit as st
import sqlite3
import pandas as pd
import json
from datetime import datetime, date, time
import os
import numpy as np

# Database configuration
DB_PATH = os.path.expanduser("~/Github/Cruise_Logs/Cruise_Logs.db")



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
            'lwrad_old_sn', 'lwrad_new_sn', 'lwrad_condition', 'lwrad_details',
            'baro_old_sn', 'baro_new_sn', 'baro_condition', 'baro_details',
            'seacat_old_sn', 'seacat_new_sn', 'seacat_condition', 'seacat_details'
        ]

        # Add Tube Exchange columns
        tube_exchange_columns = [
            'tube_time', 'gmt', 'drift',
            'bat_logic', 'bat_transmit', 'file_name'
        ]

        # Add Met Obs JSON columns
        met_obs_columns = [
            'met_ship',
            'met_buoy'
        ]

        # rep_comments column is used for Description of Visit
        # (assuming rep_comments already exists in the table)
        description_columns = []

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

        for col in description_columns:
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
    """Migrate data from old column names to new ones"""
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

        # Migrate Met Obs individual columns to JSON format
        met_ship_cols = ['ship_date', 'ship_time', 'ship_wind_dir', 'ship_wind_spd',
                        'ship_air_temp', 'ship_sst', 'ship_ssc', 'ship_rh']
        met_buoy_cols = ['buoy_date', 'buoy_time', 'buoy_wind_dir', 'buoy_wind_spd',
                        'buoy_air_temp', 'buoy_sst', 'buoy_ssc', 'buoy_rh']

        # Check if old columns exist and new JSON columns exist
        if all(col in columns for col in met_ship_cols) and 'met_ship' in columns:
            cursor.execute("""
                SELECT id, ship_date, ship_time, ship_wind_dir, ship_wind_spd,
                       ship_air_temp, ship_sst, ship_ssc, ship_rh
                FROM repair_normalized
                WHERE met_ship IS NULL
                AND (ship_date IS NOT NULL OR ship_time IS NOT NULL OR
                     ship_wind_dir IS NOT NULL OR ship_wind_spd IS NOT NULL OR
                     ship_air_temp IS NOT NULL OR ship_sst IS NOT NULL OR
                     ship_ssc IS NOT NULL OR ship_rh IS NOT NULL)
            """)

            records = cursor.fetchall()
            for rec in records:
                met_ship_data = {}
                if rec[1]:  # ship_date
                    met_ship_data['date'] = f"{rec[1]}T00:00:00"
                if rec[2]:  # ship_time
                    time_str = str(rec[2])
                    if len(time_str) == 5:  # HH:MM format
                        time_str += ':00'
                    met_ship_data['time'] = time_str
                if rec[3] is not None:  # ship_wind_dir
                    try:
                        met_ship_data['wind_dir'] = float(rec[3])
                    except:
                        pass
                if rec[4] is not None:  # ship_wind_spd
                    try:
                        met_ship_data['wind_spd'] = float(rec[4])
                    except:
                        pass
                if rec[5] is not None:  # ship_air_temp
                    try:
                        met_ship_data['air_temp'] = float(rec[5])
                    except:
                        pass
                if rec[6] is not None:  # ship_sst
                    try:
                        met_ship_data['sst'] = float(rec[6])
                    except:
                        pass
                if rec[7] is not None:  # ship_ssc
                    try:
                        met_ship_data['ssc'] = float(rec[7])
                    except:
                        pass
                if rec[8] is not None:  # ship_rh
                    try:
                        met_ship_data['rh'] = float(rec[8])
                    except:
                        pass

                if met_ship_data:
                    cursor.execute("""
                        UPDATE repair_normalized
                        SET met_ship = ?
                        WHERE id = ?
                    """, (json.dumps(met_ship_data), rec[0]))

            conn.commit()
            print(f"Migrated {len(records)} records to met_ship JSON format")

        # Migrate buoy data
        if all(col in columns for col in met_buoy_cols) and 'met_buoy' in columns:
            cursor.execute("""
                SELECT id, buoy_date, buoy_time, buoy_wind_dir, buoy_wind_spd,
                       buoy_air_temp, buoy_sst, buoy_ssc, buoy_rh
                FROM repair_normalized
                WHERE met_buoy IS NULL
                AND (buoy_date IS NOT NULL OR buoy_time IS NOT NULL OR
                     buoy_wind_dir IS NOT NULL OR buoy_wind_spd IS NOT NULL OR
                     buoy_air_temp IS NOT NULL OR buoy_sst IS NOT NULL OR
                     buoy_ssc IS NOT NULL OR buoy_rh IS NOT NULL)
            """)

            records = cursor.fetchall()
            for rec in records:
                met_buoy_data = {}
                if rec[1]:  # buoy_date
                    met_buoy_data['date'] = f"{rec[1]}T00:00:00"
                if rec[2]:  # buoy_time
                    time_str = str(rec[2])
                    if len(time_str) == 5:  # HH:MM format
                        time_str += ':00'
                    met_buoy_data['time'] = time_str
                if rec[3] is not None:  # buoy_wind_dir
                    try:
                        met_buoy_data['wind_dir'] = float(rec[3])
                    except:
                        pass
                if rec[4] is not None:  # buoy_wind_spd
                    try:
                        met_buoy_data['wind_spd'] = float(rec[4])
                    except:
                        pass
                if rec[5] is not None:  # buoy_air_temp
                    try:
                        met_buoy_data['air_temp'] = float(rec[5])
                    except:
                        pass
                if rec[6] is not None:  # buoy_sst
                    try:
                        met_buoy_data['sst'] = float(rec[6])
                    except:
                        pass
                if rec[7] is not None:  # buoy_ssc
                    try:
                        met_buoy_data['ssc'] = float(rec[7])
                    except:
                        pass
                if rec[8] is not None:  # buoy_rh
                    try:
                        met_buoy_data['rh'] = float(rec[8])
                    except:
                        pass

                if met_buoy_data:
                    cursor.execute("""
                        UPDATE repair_normalized
                        SET met_buoy = ?
                        WHERE id = ?
                    """, (json.dumps(met_buoy_data), rec[0]))

            conn.commit()
            print(f"Migrated {len(records)} records to met_buoy JSON format")

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

            # Navigation and Mooring ID display
            if len(st.session_state.search_results) > 1:
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    if st.button("◀ Previous", disabled=st.session_state.current_record_index <= 0):
                        st.session_state.current_record_index -= 1
                        st.rerun()
                with col2:
                    current_record = st.session_state.search_results.iloc[st.session_state.current_record_index]
                    mooring_id = current_record.get('mooring_id', 'N/A')
                    st.markdown(f"<div style='text-align: center;'><span style='font-size: 24px; font-weight: bold; color: #1f77b4;'>Mooring ID: {mooring_id}</span><br><span style='font-size: 14px;'>Record {st.session_state.current_record_index + 1} of {len(st.session_state.search_results)}</span></div>", unsafe_allow_html=True)
                with col3:
                    if st.button("Next ▶", disabled=st.session_state.current_record_index >= len(st.session_state.search_results) - 1):
                        st.session_state.current_record_index += 1
                        st.rerun()
            elif len(st.session_state.search_results) == 1:
                # Display mooring ID even for single result
                current_record = st.session_state.search_results.iloc[0]
                mooring_id = current_record.get('mooring_id', 'N/A')
                st.markdown(f"<div style='text-align: center;'><span style='font-size: 24px; font-weight: bold; color: #1f77b4;'>Mooring ID: {mooring_id}</span><br><span style='font-size: 14px;'>1 Record Found</span></div>", unsafe_allow_html=True)

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
        default_lwrad_old_sn = ""
        default_lwrad_new_sn = ""
        default_lwrad_condition = ""
        default_lwrad_details = ""
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

        # Met Obs defaults - parse from JSON if available
        default_met_ship = {}
        default_met_buoy = {}

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

        # Description of Visit - default empty for new records
        default_description_of_visit = ""

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



            # Time fields - extract time portion only
            start_repair = rec.get('start_repair_time', '')



            if start_repair and 'T' in str(start_repair):
                # Format is like "1900-03-13T03:00:00"
                time_part = str(start_repair).split('T')[1]
                default_start_repair_time = time_part[:5] if time_part else ''  # Get HH:mm

            elif start_repair and ' ' in str(start_repair):
                default_start_repair_time = str(start_repair).split(' ')[1][:5]  # Get HH:mm

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



            # Helper function to clean serial numbers (remove .0 from floats)
            def clean_serial_number(value):
                """Remove unnecessary decimal points from serial numbers."""
                if value is None or value == '':
                    return ''
                str_value = str(value).strip()
                # If it looks like a float with .0, remove the decimal part
                if str_value.endswith('.0'):
                    return str_value[:-2]
                return str_value

            # Helper function to get serial number from nested JSON structure
            def get_sensor_sn(data, key):
                sensor_data = data.get(key.lower(), {})
                if isinstance(sensor_data, dict):
                    sn_value = sensor_data.get('sn', '')
                    # Handle NaN, null, None as empty string
                    if sn_value and str(sn_value).lower() not in ['nan', 'null', 'none']:
                        return clean_serial_number(str(sn_value))
                return ''

            # Helper function to get lost/condition status from nested JSON structure
            def get_sensor_condition(data, key):
                sensor_data = data.get(key.lower(), {})
                if isinstance(sensor_data, dict):
                    lost_value = sensor_data.get('lost', '')
                    # Handle null, None as empty string
                    if lost_value and str(lost_value).lower() not in ['null', 'none']:
                        return str(lost_value).strip()
                return ''

            # Sensor Exchange defaults - Prioritize individual columns over JSON fields
            default_tube_old_sn = clean_serial_number(rec.get('tube_old_sn', '')) if rec.get('tube_old_sn') else get_sensor_sn(lost_equipment, 'tube')
            default_tube_new_sn = clean_serial_number(rec.get('tube_new_sn', '')) if rec.get('tube_new_sn') else get_sensor_sn(replacement_equipment, 'tube')
            default_tube_condition = str(rec.get('tube_condition', '')) if rec.get('tube_condition') else get_sensor_condition(lost_equipment, 'tube')
            default_tube_details = str(rec.get('tube_details', '')) if rec.get('tube_details') else ''



            default_ptt_old_sn = clean_serial_number(rec.get('ptt_old_sn', '')) if rec.get('ptt_old_sn') else get_sensor_sn(lost_equipment, 'ptt')
            default_ptt_new_sn = clean_serial_number(rec.get('ptt_new_sn', '')) if rec.get('ptt_new_sn') else get_sensor_sn(replacement_equipment, 'ptt')
            default_ptt_condition = str(rec.get('ptt_condition', '')) if rec.get('ptt_condition') else get_sensor_condition(lost_equipment, 'ptt')
            default_ptt_details = str(rec.get('ptt_details', '')) if rec.get('ptt_details') else ''

            default_atrh_old_sn = clean_serial_number(rec.get('atrh_old_sn', '')) if rec.get('atrh_old_sn') else get_sensor_sn(lost_equipment, 'atrh')
            default_atrh_new_sn = clean_serial_number(rec.get('atrh_new_sn', '')) if rec.get('atrh_new_sn') else get_sensor_sn(replacement_equipment, 'atrh')
            default_atrh_condition = str(rec.get('atrh_condition', '')) if rec.get('atrh_condition') else get_sensor_condition(lost_equipment, 'atrh')
            default_atrh_details = str(rec.get('atrh_details', '')) if rec.get('atrh_details') else ''

            default_sst_old_sn = clean_serial_number(rec.get('sst_old_sn', '')) if rec.get('sst_old_sn') else get_sensor_sn(lost_equipment, 'sst')
            default_sst_new_sn = clean_serial_number(rec.get('sst_new_sn', '')) if rec.get('sst_new_sn') else get_sensor_sn(replacement_equipment, 'sst')
            default_sst_condition = str(rec.get('sst_condition', '')) if rec.get('sst_condition') else get_sensor_condition(lost_equipment, 'sst')
            default_sst_details = str(rec.get('sst_details', '')) if rec.get('sst_details') else ''

            default_wind_old_sn = clean_serial_number(rec.get('wind_old_sn', '')) if rec.get('wind_old_sn') else get_sensor_sn(lost_equipment, 'wind')
            default_wind_new_sn = clean_serial_number(rec.get('wind_new_sn', '')) if rec.get('wind_new_sn') else get_sensor_sn(replacement_equipment, 'wind')
            default_wind_condition = str(rec.get('wind_condition', '')) if rec.get('wind_condition') else get_sensor_condition(lost_equipment, 'wind')
            default_wind_details = str(rec.get('wind_details', '')) if rec.get('wind_details') else ''

            default_rain_old_sn = clean_serial_number(rec.get('rain_old_sn', '')) if rec.get('rain_old_sn') else get_sensor_sn(lost_equipment, 'rain')
            default_rain_new_sn = clean_serial_number(rec.get('rain_new_sn', '')) if rec.get('rain_new_sn') else get_sensor_sn(replacement_equipment, 'rain')



            default_rain_condition = str(rec.get('rain_condition', '')) if rec.get('rain_condition') else get_sensor_condition(lost_equipment, 'rain')
            default_rain_details = str(rec.get('rain_details', '')) if rec.get('rain_details') else ''

            default_swrad_old_sn = clean_serial_number(rec.get('swrad_old_sn', '')) if rec.get('swrad_old_sn') else (get_sensor_sn(lost_equipment, 'swrad') or get_sensor_sn(lost_equipment, 'sw_rad'))
            default_swrad_new_sn = clean_serial_number(rec.get('swrad_new_sn', '')) if rec.get('swrad_new_sn') else (get_sensor_sn(replacement_equipment, 'swrad') or get_sensor_sn(replacement_equipment, 'sw_rad'))
            default_swrad_condition = str(rec.get('swrad_condition', '')) if rec.get('swrad_condition') else (get_sensor_condition(lost_equipment, 'swrad') or get_sensor_condition(lost_equipment, 'sw_rad'))
            default_swrad_details = str(rec.get('swrad_details', '')) if rec.get('swrad_details') else ''

            default_lwrad_old_sn = clean_serial_number(rec.get('lwrad_old_sn', '')) if rec.get('lwrad_old_sn') else (get_sensor_sn(lost_equipment, 'lwrad') or get_sensor_sn(lost_equipment, 'lw_rad') or get_sensor_sn(lost_equipment, 'lwr_rad'))
            default_lwrad_new_sn = clean_serial_number(rec.get('lwrad_new_sn', '')) if rec.get('lwrad_new_sn') else (get_sensor_sn(replacement_equipment, 'lwrad') or get_sensor_sn(replacement_equipment, 'lw_rad') or get_sensor_sn(replacement_equipment, 'lwr_rad'))
            default_lwrad_condition = str(rec.get('lwrad_condition', '')) if rec.get('lwrad_condition') else (get_sensor_condition(lost_equipment, 'lwrad') or get_sensor_condition(lost_equipment, 'lw_rad') or get_sensor_condition(lost_equipment, 'lwr_rad'))
            default_lwrad_details = str(rec.get('lwrad_details', '')) if rec.get('lwrad_details') else ''

            default_baro_old_sn = clean_serial_number(rec.get('baro_old_sn', '')) if rec.get('baro_old_sn') else (get_sensor_sn(lost_equipment, 'baro') or get_sensor_sn(replacement_equipment, 'baro_press'))
            default_baro_new_sn = clean_serial_number(rec.get('baro_new_sn', '')) if rec.get('baro_new_sn') else (get_sensor_sn(replacement_equipment, 'baro') or get_sensor_sn(replacement_equipment, 'baro_press'))
            default_baro_condition = str(rec.get('baro_condition', '')) if rec.get('baro_condition') else (get_sensor_condition(lost_equipment, 'baro') or get_sensor_condition(lost_equipment, 'baro_press'))
            default_baro_details = str(rec.get('baro_details', '')) if rec.get('baro_details') else ''

            default_seacat_old_sn = clean_serial_number(rec.get('seacat_old_sn', '')) if rec.get('seacat_old_sn') else get_sensor_sn(lost_equipment, 'seacat')
            default_seacat_new_sn = clean_serial_number(rec.get('seacat_new_sn', '')) if rec.get('seacat_new_sn') else get_sensor_sn(replacement_equipment, 'seacat')
            default_seacat_condition = str(rec.get('seacat_condition', '')) if rec.get('seacat_condition') else get_sensor_condition(lost_equipment, 'seacat')
            default_seacat_details = str(rec.get('seacat_details', '')) if rec.get('seacat_details') else ''

            # Tube Exchange defaults
            default_tube_time = str(rec.get('tube_time', '')) if rec.get('tube_time') else ''
            default_gmt = str(rec.get('gmt', '')) if rec.get('gmt') else ''
            default_drift = str(rec.get('drift', '')) if rec.get('drift') else ''
            default_bat_logic = str(rec.get('bat_logic', '')) if rec.get('bat_logic') else ''
            default_bat_transmit = str(rec.get('bat_transmit', '')) if rec.get('bat_transmit') else ''
            default_file_name = str(rec.get('file_name', '')) if rec.get('file_name') else ''

            # Met Obs defaults - parse from JSON columns
            # Parse met_ship JSON
            default_met_ship = parse_json_field(rec.get('met_ship', '{}'))
            if default_met_ship:
                # Handle ship_date - JSON uses "Date" with capital D
                ship_date_str = default_met_ship.get('Date', '')
                if ship_date_str and ship_date_str not in ['', 'None', 'null']:
                    try:
                        default_ship_date = datetime.strptime(str(ship_date_str).split('T')[0], '%Y-%m-%d').date()
                    except:
                        default_ship_date = None
                else:
                    default_ship_date = None

                default_ship_time = str(default_met_ship.get('Time', ''))[:5] if default_met_ship.get('Time') else ''  # Format as HH:MM
                default_ship_wind_dir = str(default_met_ship.get('Wind Dir', '')) if default_met_ship.get('Wind Dir') is not None else ''
                default_ship_wind_spd = str(default_met_ship.get('Wind Spd', '')) if default_met_ship.get('Wind Spd') is not None else ''
                default_ship_air_temp = str(default_met_ship.get('Air Temp', '')) if default_met_ship.get('Air Temp') is not None else ''
                default_ship_sst = str(default_met_ship.get('SST', '')) if default_met_ship.get('SST') is not None else ''
                # Handle both uppercase 'SSC' and lowercase 'ssc'
                ssc_value = default_met_ship.get('SSC') if 'SSC' in default_met_ship else default_met_ship.get('ssc')
                default_ship_ssc = str(ssc_value) if ssc_value not in [None, ''] else ''
                default_ship_rh = str(default_met_ship.get('RH', '')) if default_met_ship.get('RH') is not None else ''
            else:
                default_ship_date = None
                default_ship_time = ""
                default_ship_wind_dir = ""
                default_ship_wind_spd = ""
                default_ship_air_temp = ""
                default_ship_sst = ""
                default_ship_ssc = ""
                default_ship_rh = ""

            # Parse met_buoy JSON
            default_met_buoy = parse_json_field(rec.get('met_buoy', '{}'))
            if default_met_buoy:
                # Handle buoy_date - JSON uses "Date" with capital D
                buoy_date_str = default_met_buoy.get('Date', '')
                if buoy_date_str and buoy_date_str not in ['', 'None', 'null']:
                    try:
                        default_buoy_date = datetime.strptime(str(buoy_date_str).split('T')[0], '%Y-%m-%d').date()
                    except:
                        default_buoy_date = None
                else:
                    default_buoy_date = None

                default_buoy_time = str(default_met_buoy.get('Time', ''))[:5] if default_met_buoy.get('Time') else ''  # Format as HH:MM
                default_buoy_wind_dir = str(default_met_buoy.get('Wind Dir', '')) if default_met_buoy.get('Wind Dir') is not None else ''
                default_buoy_wind_spd = str(default_met_buoy.get('Wind Spd', '')) if default_met_buoy.get('Wind Spd') is not None else ''
                default_buoy_air_temp = str(default_met_buoy.get('Air Temp', '')) if default_met_buoy.get('Air Temp') is not None else ''
                default_buoy_sst = str(default_met_buoy.get('SST', '')) if default_met_buoy.get('SST') is not None else ''
                # Handle both uppercase 'SSC' and lowercase 'ssc'
                ssc_value = default_met_buoy.get('SSC') if 'SSC' in default_met_buoy else default_met_buoy.get('ssc')
                default_buoy_ssc = str(ssc_value) if ssc_value not in [None, ''] else ''
                default_buoy_rh = str(default_met_buoy.get('RH', '')) if default_met_buoy.get('RH') is not None else ''
            else:
                default_buoy_date = None
                default_buoy_time = ""
                default_buoy_wind_dir = ""
                default_buoy_wind_spd = ""
                default_buoy_air_temp = ""
                default_buoy_sst = ""
                default_buoy_ssc = ""
                default_buoy_rh = ""

            # Description of Visit - now using rep_comments column
            default_description_of_visit = str(rec.get('rep_comments', '')) if rec.get('rep_comments') else ''

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
            default_lwrad_old_sn = ""
            default_lwrad_new_sn = ""
            default_lwrad_condition = ""
            default_lwrad_details = ""
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

            # Description of Visit - default empty for new records
            default_description_of_visit = ""

            record_id = None



    # Show the form in both modes
    if mode == "Add New" or mode == "Search/Edit":

        st.markdown("---")

        # Form sections
        with st.form("repair_form"):

            # Row 1: Site and Mooring ID
            col1, col2 = st.columns(2)
            with col1:
                if mode == "Add New":
                    # In Add New mode, use text input with autocomplete suggestions
                    site = st.text_input("Site", value=default_site, key="site",
                                       help="Enter site name (you can type a new site or select from existing)")
                    if available_sites:
                        st.caption(f"Existing sites: {', '.join(available_sites[:5])}{'...' if len(available_sites) > 5 else ''}")
                else:
                    # In Search/Edit mode, use dropdown with existing sites
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
                if mode == "Add New":
                    # In Add New mode, use text input with autocomplete suggestions
                    cruise = st.text_input("Cruise", value=default_cruise, key="cruise",
                                         help="Enter cruise name (you can type a new cruise or select from existing)")
                    if available_cruises:
                        st.caption(f"Existing cruises: {', '.join(available_cruises[:5])}{'...' if len(available_cruises) > 5 else ''}")
                else:
                    # In Search/Edit mode, use dropdown with existing cruises
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

            # LWR Rad row
            col_label, col_old, col_new, col_condition, col_details = st.columns([1.5, 2, 2, 2, 3])
            with col_label:
                st.markdown("LWR Rad")
            with col_old:
                lwrad_old_sn = st.text_input("LWR Rad Old S/N", value=default_lwrad_old_sn, key="lwrad_old_sn", label_visibility="collapsed")
            with col_new:
                lwrad_new_sn = st.text_input("LWR Rad New S/N", value=default_lwrad_new_sn, key="lwrad_new_sn", label_visibility="collapsed")
            with col_condition:
                lwrad_condition = st.selectbox("LWR Rad Condition", options=condition_options, index=condition_options.index(default_lwrad_condition) if default_lwrad_condition in condition_options else 0, key="lwrad_condition", label_visibility="collapsed")
            with col_details:
                lwrad_details = st.text_input("LWR Rad Details", value=default_lwrad_details, key="lwrad_details", label_visibility="collapsed")

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
                                              placeholder="Volts", help="Battery logic serial number",
                                              label_visibility="collapsed")
            with col2:
                st.markdown("Bat Transmit")
                bat_transmit = st.text_input("Bat Transmit", value=default_bat_transmit, key="bat_transmit",
                                                 placeholder="Volts", help="Battery transmit interval",
                                                 label_visibility="collapsed")
            with col3:
                st.markdown("Data Filename")
                file_name = st.text_input("Filename", value=default_file_name, key="file_name",
                                                 placeholder="e.g., TUBE_001.BIN", help="Downloaded data filename",
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
            st.markdown("### Description of Visit")

            description_of_visit = st.text_area(
                "Description of Visit",
                value=default_description_of_visit,
                height=625,  # Approximately 25 lines
                key="description_of_visit",
                label_visibility="collapsed",
                placeholder="Enter detailed description of the visit, repairs performed, observations, etc."
            )

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
                    'buoy_details': buoy_condition.strip() if buoy_condition else None,
                    'repair_fishing_vandalism': fishing_vandalism.strip() if fishing_vandalism else None,
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
                    'lwrad_old_sn': lwrad_old_sn.strip() if lwrad_old_sn else None,
                    'lwrad_new_sn': lwrad_new_sn.strip() if lwrad_new_sn else None,
                    'lwrad_condition': lwrad_condition.strip() if lwrad_condition else None,
                    'lwrad_details': lwrad_details.strip() if lwrad_details else None,
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
                    # Met Obs fields - will be set as JSON below
                    'met_ship': None,
                    'met_buoy': None,
                    # Description of Visit - stored in rep_comments column
                    'rep_comments': description_of_visit.strip() if description_of_visit else None,
                    'a2_rep_dep': None,
                    'a2_rep_rec': None,
                    'check_duplicates': None,
                }

                # Build met_ship JSON object - use proper capitalized keys to match existing data
                met_ship_data = {}
                if ship_date:
                    met_ship_data['Date'] = ship_date.strftime('%Y-%m-%dT00:00:00')
                if ship_time and ship_time.strip():
                    # Ensure time is in HH:MM:SS format
                    time_str = ship_time.strip()
                    if len(time_str) == 5:  # HH:MM format
                        time_str += ':00'
                    met_ship_data['Time'] = time_str
                if ship_wind_dir and ship_wind_dir.strip():
                    met_ship_data['Wind Dir'] = parse_float_safe(ship_wind_dir.strip())
                if ship_wind_spd and ship_wind_spd.strip():
                    met_ship_data['Wind Spd'] = parse_float_safe(ship_wind_spd.strip())
                if ship_air_temp and ship_air_temp.strip():
                    met_ship_data['Air Temp'] = parse_float_safe(ship_air_temp.strip())
                if ship_sst and ship_sst.strip():
                    met_ship_data['SST'] = parse_float_safe(ship_sst.strip())
                if ship_ssc and ship_ssc.strip():
                    met_ship_data['SSC'] = parse_float_safe(ship_ssc.strip())
                if ship_rh and ship_rh.strip():
                    met_ship_data['RH'] = parse_float_safe(ship_rh.strip())

                # Only set met_ship if there's data
                if met_ship_data:
                    repair_data['met_ship'] = json.dumps(met_ship_data)

                # Build met_buoy JSON object - use proper capitalized keys to match existing data
                met_buoy_data = {}
                if buoy_date:
                    met_buoy_data['Date'] = buoy_date.strftime('%Y-%m-%dT00:00:00')
                if buoy_time and buoy_time.strip():
                    # Ensure time is in HH:MM:SS format
                    time_str = buoy_time.strip()
                    if len(time_str) == 5:  # HH:MM format
                        time_str += ':00'
                    met_buoy_data['Time'] = time_str
                if buoy_wind_dir and buoy_wind_dir.strip():
                    met_buoy_data['Wind Dir'] = parse_float_safe(buoy_wind_dir.strip())
                if buoy_wind_spd and buoy_wind_spd.strip():
                    met_buoy_data['Wind Spd'] = parse_float_safe(buoy_wind_spd.strip())
                if buoy_air_temp and buoy_air_temp.strip():
                    met_buoy_data['Air Temp'] = parse_float_safe(buoy_air_temp.strip())
                if buoy_sst and buoy_sst.strip():
                    met_buoy_data['SST'] = parse_float_safe(buoy_sst.strip())
                if buoy_ssc and buoy_ssc.strip():
                    met_buoy_data['SSC'] = parse_float_safe(buoy_ssc.strip())
                if buoy_rh and buoy_rh.strip():
                    met_buoy_data['RH'] = parse_float_safe(buoy_rh.strip())

                # Only set met_buoy if there's data
                if met_buoy_data:
                    repair_data['met_buoy'] = json.dumps(met_buoy_data)

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
                if lwrad_old_sn and lwrad_old_sn.strip():
                    lost_equipment_dict['lwrad'] = {'sn': lwrad_old_sn.strip(), 'lost': lwrad_condition.strip() if lwrad_condition else None}
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
                if lwrad_new_sn and lwrad_new_sn.strip():
                    replacement_equipment_dict['lwrad'] = {'sn': lwrad_new_sn.strip()}
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
