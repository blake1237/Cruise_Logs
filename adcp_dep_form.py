import streamlit as st
import sqlite3
import pandas as pd
import json
from datetime import datetime, date, time
import os
import math

# Database configuration
DB_PATH = '/Users/lake/Github/Cruise_Logs/Cruise_Logs.db'

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def search_deployments(search_criteria):
    """Search for ADCP deployments based on criteria."""
    conn = get_db_connection()
    try:
        query = """
            SELECT id, mooring_id, cruise_info, anchor_drop, deployment_details, sensor_details, release_details
            FROM adcp_dep
            WHERE 1=1
        """
        params = []

        if search_criteria.get('site'):
            query += " AND cruise_info LIKE ?"
            params.append(f'%"site": "%{search_criteria["site"]}%"%')

        if search_criteria.get('mooring_id'):
            query += " AND mooring_id LIKE ?"
            params.append(f'%{search_criteria["mooring_id"]}%')

        if search_criteria.get('cruise'):
            query += " AND cruise_info LIKE ?"
            params.append(f'%"cruise": "%{search_criteria["cruise"]}%"%')

        query += " ORDER BY id DESC"

        cursor = conn.cursor()
        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            record = {
                'id': row['id'],
                'mooring_id': row['mooring_id'],
                'cruise_info': row['cruise_info'],
                'anchor_drop': row['anchor_drop'],
                'deployment_details': row['deployment_details'],
                'sensor_details': row['sensor_details'],
                'release_details': row['release_details']
            }
            results.append(record)

        return pd.DataFrame(results) if results else pd.DataFrame()
    except Exception as e:
        st.error(f"Error searching deployments: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_distinct_sites():
    """Get all distinct sites from the database."""
    conn = get_db_connection()
    try:
        query = """
            SELECT DISTINCT json_extract(cruise_info, '$.site') as site
            FROM adcp_dep
            WHERE json_extract(cruise_info, '$.site') IS NOT NULL
                AND json_extract(cruise_info, '$.site') != ''
            ORDER BY site
        """
        cursor = conn.cursor()
        cursor.execute(query)
        sites = [row[0] for row in cursor.fetchall()]
        return sites
    except Exception as e:
        print(f"Error fetching sites: {e}")
        return []
    finally:
        conn.close()

def parse_json_field(field_value):
    """Parse a JSON field, returning empty dict/list if invalid."""
    if field_value:
        try:
            # Replace NaN strings with null before parsing
            if isinstance(field_value, str):
                field_value = field_value.replace(': NaN', ': null').replace(':NaN', ':null')
            parsed = json.loads(field_value)
            # Clean any remaining NaN values from the parsed data
            return clean_nan_values(parsed)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}

def clean_nan_values(data):
    """Recursively clean NaN and None values from data structure, replacing with empty string."""
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if value is None:
                cleaned[key] = ''
            elif isinstance(value, float) and math.isnan(value):
                cleaned[key] = ''
            elif value == 'NaN' or value == 'nan':
                cleaned[key] = ''
            elif isinstance(value, (dict, list)):
                cleaned[key] = clean_nan_values(value)
            else:
                cleaned[key] = value
        return cleaned
    elif isinstance(data, list):
        cleaned = []
        for item in data:
            if item is None:
                cleaned.append('')
            elif isinstance(item, float) and math.isnan(item):
                cleaned.append('')
            elif item == 'NaN' or item == 'nan':
                cleaned.append('')
            elif isinstance(item, (dict, list)):
                cleaned.append(clean_nan_values(item))
            else:
                cleaned.append(item)
        return cleaned
    else:
        if data is None:
            return ''
        elif isinstance(data, float) and math.isnan(data):
            return ''
        elif data == 'NaN' or data == 'nan':
            return ''
        return data

def save_deployment(record_id, form_data):
    """Save or update deployment record."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Prepare JSON data structures
        cruise_info = {
            "cruise": form_data.get('cruise', ''),
            "site": form_data.get('site', '')
        }

        anchor_drop = {
            "anchor_drop_date": form_data.get('anchor_date', ''),
            "anchor_drop_time": form_data.get('start_time_gmt', ''),
            "anchor_drop_lat": form_data.get('latitude', ''),
            "anchor_drop_long": form_data.get('longitude', ''),
            "anchor_drop_depth": form_data.get('corrected_depth', ''),
            "anchor_weight": form_data.get('anchor_weight', '')
        }

        deployment_details = {
            "deployment_date": form_data.get('deploy_start_date', ''),
            "deployment_time": form_data.get('start_time_gmt', ''),
            "deployment_personnel": form_data.get('personnel', ''),
            "comments": form_data.get('comments', ''),
            "satellite_beacon": {
                "sn": form_data.get('sat_beacon_sn', ''),
                "imei_ptt": form_data.get('sat_beacon_imei', '')
            },
            "rf_beacon": {
                "sn": form_data.get('rf_beacon_sn', ''),
                "imei_ptt": form_data.get('rf_beacon_imei', '')
            },
            "flasher": {
                "sn": form_data.get('flasher_sn', ''),
                "imei_ptt": form_data.get('flasher_imei', '')
            }
        }

        sensor_details = {}
        release_details = {}

        if record_id and record_id > 0:
            # Update existing record
            query = """
                UPDATE adcp_dep
                SET mooring_id=?, cruise_info=?, anchor_drop=?, deployment_details=?, sensor_details=?, release_details=?
                WHERE id=?
            """
            cursor.execute(query, [
                form_data.get('mooring_id', ''),
                json.dumps(cruise_info),
                json.dumps(anchor_drop),
                json.dumps(deployment_details),
                json.dumps(sensor_details),
                json.dumps(release_details),
                record_id
            ])
        else:
            # Insert new record
            query = """
                INSERT INTO adcp_dep (mooring_id, cruise_info, anchor_drop, deployment_details, sensor_details, release_details)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, [
                form_data.get('mooring_id', ''),
                json.dumps(cruise_info),
                json.dumps(anchor_drop),
                json.dumps(deployment_details),
                json.dumps(sensor_details),
                json.dumps(release_details)
            ])
            record_id = cursor.lastrowid

        conn.commit()
        return True, record_id
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def delete_deployment(record_id, password):
    """Delete a deployment record with password verification."""
    if password != "fidelio":
        return False, "Incorrect password"

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM adcp_dep WHERE id=?", [record_id])
        conn.commit()
        return True, "Record deleted successfully"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def main():
    """Main Streamlit application function."""

    # Page configuration
    st.set_page_config(
        page_title="Subsurface ADCP Deployment Log",
        page_icon="🌊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

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
    </style>
    """, unsafe_allow_html=True)

    # Main title
    st.title("Subsurface ADCP Deployment Log")

    # Initialize session state
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'current_record_index' not in st.session_state:
        st.session_state.current_record_index = 0
    if 'mode' not in st.session_state:
        st.session_state.mode = "Search/Edit"
    if 'selected_deployment' not in st.session_state:
        st.session_state.selected_deployment = None

    # Mode selection
    mode = st.radio("Mode", ["Search/Edit", "Add New"], key="mode_selector", horizontal=True)
    st.session_state.mode = mode

    # Get list of sites for dropdown
    available_sites = get_distinct_sites()

    # Search section
    if mode == "Search/Edit":
        st.subheader("Search Deployments")

        with st.form("search_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                site_options = [""] + available_sites
                search_site = st.selectbox("Site", options=site_options, key="search_site")
            with col2:
                search_mooring_id = st.text_input("Mooring ID", key="search_mooring_id")
            with col3:
                search_cruise = st.text_input("Cruise", key="search_cruise")

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
                results = search_deployments(search_criteria)
                st.session_state.search_results = results
                st.session_state.current_record_index = 0

                if results.empty:
                    st.warning("No deployments found matching your criteria.")
                else:
                    st.success(f"Found {len(results)} deployment(s)")

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
                current_record_dict = current_record.to_dict() if hasattr(current_record, 'to_dict') else dict(current_record)
                st.session_state.selected_deployment = current_record_dict

                # Parse JSON fields for display
                cruise_info = parse_json_field(current_record_dict.get('cruise_info', '{}'))
                anchor_drop = parse_json_field(current_record_dict.get('anchor_drop', '{}'))

                # Display key info
                info_cols = st.columns(4)
                with info_cols[0]:
                    st.metric("Site", cruise_info.get('site', 'N/A'))
                with info_cols[1]:
                    st.metric("Mooring ID", current_record_dict.get('mooring_id', 'N/A'))
                with info_cols[2]:
                    st.metric("Cruise", cruise_info.get('cruise', 'N/A'))
                with info_cols[3]:
                    st.metric("Anchor Date", anchor_drop.get('anchor_drop_date', 'N/A'))

    # Form for Add New or Edit
    if mode == "Add New":
        st.subheader("Add New Deployment")
    else:
        st.subheader("Edit Deployment")

    # Initialize form defaults
    if mode == "Search/Edit" and st.session_state.selected_deployment is not None:
        record = st.session_state.selected_deployment

        # Parse JSON fields
        cruise_info = parse_json_field(record.get('cruise_info', '{}'))
        anchor_drop = parse_json_field(record.get('anchor_drop', '{}'))
        deployment_details = parse_json_field(record.get('deployment_details', '{}'))

        # Set defaults from parsed JSON
        default_record_id = record.get('id')
        default_mooring_id = record.get('mooring_id', '')
        default_site = cruise_info.get('site', '')
        default_cruise = cruise_info.get('cruise', '')
        default_personnel = deployment_details.get('deployment_personnel', '')

        # Parse anchor drop date
        anchor_date_str = anchor_drop.get('anchor_drop_date', '')
        if anchor_date_str:
            try:
                # Handle datetime format
                if ' ' in anchor_date_str:
                    default_anchor_date = datetime.strptime(anchor_date_str.split(' ')[0], '%Y-%m-%d').date()
                else:
                    default_anchor_date = datetime.strptime(anchor_date_str, '%Y-%m-%d').date()
            except:
                default_anchor_date = None
        else:
            default_anchor_date = None

        # Use deployment date if available, otherwise use anchor date
        deploy_date_str = deployment_details.get('deployment_date', '')
        if deploy_date_str:
            try:
                default_deploy_start_date = datetime.strptime(deploy_date_str, '%Y-%m-%d').date()
            except:
                default_deploy_start_date = default_anchor_date
        else:
            default_deploy_start_date = default_anchor_date

        # Parse time
        start_time_str = anchor_drop.get('anchor_drop_time', '') or deployment_details.get('deployment_time', '')
        if start_time_str:
            try:
                default_start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
            except:
                try:
                    default_start_time = datetime.strptime(start_time_str, '%H:%M').time()
                except:
                    default_start_time = None
        else:
            default_start_time = None

        # Other defaults
        default_latitude = anchor_drop.get('anchor_drop_lat', '')
        default_longitude = anchor_drop.get('anchor_drop_long', '')
        default_source_location = ''  # Not in current structure
        default_corrected_depth = str(anchor_drop.get('anchor_drop_depth', ''))
        default_source_depth = ''  # Not in current structure
        default_transducer_depth_calc = ''  # Not in current structure
        default_anchor_weight = str(anchor_drop.get('anchor_weight', ''))

        # Comments from deployment details
        default_comments = deployment_details.get('comments', '')

        # Instrumentation defaults from sensor_details
        sat_beacon = deployment_details.get('satellite_beacon', {})
        default_sat_beacon_sn = sat_beacon.get('sn', '') if sat_beacon else ''
        default_sat_beacon_imei = sat_beacon.get('imei_ptt', '') if sat_beacon else ''

        rf_beacon = deployment_details.get('rf_beacon', {})
        default_rf_beacon_sn = rf_beacon.get('sn', '') if rf_beacon else ''
        default_rf_beacon_imei = rf_beacon.get('imei_ptt', '') if rf_beacon else ''

        flasher = deployment_details.get('flasher', {})
        default_flasher_sn = flasher.get('sn', '') if flasher else ''
        default_flasher_imei = flasher.get('imei_ptt', '') if flasher else ''
    else:
        # Defaults for Add New mode
        default_record_id = None
        default_mooring_id = ""
        default_site = ""
        default_cruise = ""
        default_personnel = ""
        default_anchor_date = None
        default_deploy_start_date = None
        default_start_time = None
        default_latitude = ""
        default_longitude = ""
        default_source_location = ""
        default_corrected_depth = ""
        default_source_depth = ""
        default_transducer_depth_calc = ""
        default_anchor_weight = ""
        default_comments = ""
        default_sat_beacon_sn = ""
        default_sat_beacon_imei = ""
        default_rf_beacon_sn = ""
        default_rf_beacon_imei = ""
        default_flasher_sn = ""
        default_flasher_imei = ""

    # Create the complete form
    with st.form("deployment_form"):
        # Basic Information Section
        st.markdown("### 📋 Basic Information")

        col1, col2 = st.columns(2)

        with col1:
            mooring_id = st.text_input("Mooring ID", value=default_mooring_id, key="mooring_id")
            site = st.text_input("Site", value=default_site, key="site")
            cruise = st.text_input("Cruise", value=default_cruise, key="cruise")
            latitude = st.text_input("Anchor Drop Latitude", value=default_latitude, key="latitude", help="Format: degrees minutes.decimal direction (e.g., '0 2.106 N')")
            corrected_depth = st.text_input("Anchor Drop Depth (m)", value=default_corrected_depth, key="corrected_depth")
            anchor_weight = st.text_input("Anchor Weight (lbs)", value=default_anchor_weight, key="anchor_weight")

        with col2:
            anchor_date = st.date_input("Anchor Drop Date", value=default_anchor_date, key="anchor_date", format="MM/DD/YYYY")
            deploy_start_date = st.date_input("Deployment Date", value=default_deploy_start_date, key="deploy_start_date", format="MM/DD/YYYY")
            start_time_gmt = st.time_input("Anchor Drop Time (GMT)", value=default_start_time, key="start_time_gmt")
            longitude = st.text_input("Anchor Drop Longitude", value=default_longitude, key="longitude", help="Format: degrees minutes.decimal direction (e.g., '82 57.047 E')")
            personnel = st.text_input("Personnel", value=default_personnel, key="personnel")

        st.markdown("---")

        # Instrumentation Section
        st.markdown("### 📡 Instrumentation")

        # Create table headers
        col_header0, col_header1, col_header2 = st.columns([1.5, 1.5, 1.5])
        with col_header0:
            st.markdown("**Instrument**")
        with col_header1:
            st.markdown("**S/N**")
        with col_header2:
            st.markdown("**IMEI or PTT**")

        # Satellite Beacon row
        col_sat_name, col_sat_sn, col_sat_imei = st.columns([1.5, 1.5, 1.5])
        with col_sat_name:
            st.markdown("Satellite Beacon")
        with col_sat_sn:
            sat_beacon_sn = st.text_input("Satellite Beacon S/N", value=default_sat_beacon_sn, key="sat_beacon_sn", label_visibility="collapsed")
        with col_sat_imei:
            sat_beacon_imei = st.text_input("Satellite Beacon IMEI/PTT", value=default_sat_beacon_imei, key="sat_beacon_imei", label_visibility="collapsed")

        # RF Beacon row
        col_rf_name, col_rf_sn, col_rf_imei = st.columns([1.5, 1.5, 1.5])
        with col_rf_name:
            st.markdown("RF Beacon")
        with col_rf_sn:
            rf_beacon_sn = st.text_input("RF Beacon S/N", value=default_rf_beacon_sn, key="rf_beacon_sn", label_visibility="collapsed")
        with col_rf_imei:
            rf_beacon_imei = st.text_input("RF Beacon IMEI/PTT", value=default_rf_beacon_imei, key="rf_beacon_imei", label_visibility="collapsed")

        # Flasher row
        col_flasher_name, col_flasher_sn, col_flasher_imei = st.columns([1.5, 1.5, 1.5])
        with col_flasher_name:
            st.markdown("Flasher")
        with col_flasher_sn:
            flasher_sn = st.text_input("Flasher S/N", value=default_flasher_sn, key="flasher_sn", label_visibility="collapsed")
        with col_flasher_imei:
            flasher_imei = st.text_input("Flasher IMEI/PTT", value=default_flasher_imei, key="flasher_imei", label_visibility="collapsed")

        st.markdown("---")

        # Comments Section
        st.markdown("### 💬 Comments")
        comments = st.text_area("Comments", height=150, value=default_comments, key="comments")

        st.markdown("---")

        # Form submission buttons
        col_save, col_delete, col_spacer = st.columns([1, 2, 7])

        with col_save:
            submitted = st.form_submit_button("Save", use_container_width=True, type="primary")

        with col_delete:
            if mode == "Search/Edit" and st.session_state.selected_deployment:
                delete_password = st.text_input("Delete Password", type="password", key="delete_password")
                delete_button = st.form_submit_button("Delete Record", use_container_width=True, type="secondary")
            else:
                delete_button = False

        if submitted:
            # Prepare form data
            form_data = {
                'mooring_id': mooring_id,
                'site': site,
                'cruise': cruise,
                'personnel': personnel,
                'anchor_date': str(anchor_date) if anchor_date else "",
                'deploy_start_date': str(deploy_start_date) if deploy_start_date else "",
                'start_time_gmt': str(start_time_gmt) if start_time_gmt else "",
                'latitude': latitude,
                'longitude': longitude,
                'corrected_depth': corrected_depth,
                'anchor_weight': anchor_weight,
                'comments': comments,
                'sat_beacon_sn': sat_beacon_sn,
                'sat_beacon_imei': sat_beacon_imei,
                'rf_beacon_sn': rf_beacon_sn,
                'rf_beacon_imei': rf_beacon_imei,
                'flasher_sn': flasher_sn,
                'flasher_imei': flasher_imei
            }

            # Save record
            success, result = save_deployment(default_record_id, form_data)

            if success:
                if mode == "Add New":
                    st.success(f"✅ New deployment saved successfully! Record ID: {result}")
                else:
                    st.success("✅ Deployment updated successfully!")

                # Clear search results to refresh
                st.session_state.search_results = None
                st.session_state.selected_deployment = None
            else:
                st.error(f"❌ Error saving deployment: {result}")

        if delete_button:
            if delete_password:
                success, message = delete_deployment(default_record_id, delete_password)
                if success:
                    st.success(f"✅ {message}")
                    st.session_state.search_results = None
                    st.session_state.selected_deployment = None
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.warning("Please enter the delete password")

if __name__ == '__main__':
    main()
