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
            SELECT id, mooring_id, cruise_info, anchor_drop, deployment_details,
                   depth_info, sensor_details, beacon_details, release_details, mooring_line_details
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
                'depth_info': row['depth_info'],
                'sensor_details': row['sensor_details'],
                'beacon_details': row['beacon_details'],
                'release_details': row['release_details'],
                'mooring_line_details': row['mooring_line_details']
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
            if isinstance(field_value, str):
                field_value = field_value.replace(': NaN', ': null').replace(':NaN', ':null')
            parsed = json.loads(field_value)
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
    """Save or update deployment record with all 107 columns."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # SECTION 1: ANCHOR DROP
        anchor_drop = {
            "anchor_drop_date": form_data.get('anchor_drop_date', ''),
            "anchor_drop_time": form_data.get('anchor_drop_time', ''),
            "anchor_drop_lat": form_data.get('anchor_drop_lat', ''),
            "anchor_drop_long": form_data.get('anchor_drop_long', ''),
            "anchor_drop_depth": form_data.get('anchor_drop_depth', ''),
            "anchor_weight": form_data.get('anchor_weight', '')
        }

        # SECTION 2-9: DEPLOYMENT DETAILS
        deployment_details = {
            "deployment_date": form_data.get('deployment_date', ''),
            "deployment_time": form_data.get('deployment_time', ''),
            "site_name": form_data.get('site_name', ''),
            "station": form_data.get('station', ''),
            "cruise": form_data.get('cruise', ''),
            "personnel": form_data.get('personnel', ''),
            "deployment_problems": form_data.get('deployment_problems', ''),
            "latitude": form_data.get('latitude', ''),
            "longitude": form_data.get('longitude', ''),
            "location_source": form_data.get('location_source', ''),
            "workboat_lat": form_data.get('workboat_lat', ''),
            "workboat_lon": form_data.get('workboat_lon', ''),
            "bottom_depth": form_data.get('bottom_depth', ''),
            "target_bottom_depth": form_data.get('target_bottom_depth', ''),
            "intended_xducer_depth": form_data.get('intended_xducer_depth', ''),
            "actual_xducer_depth_calculated": form_data.get('actual_xducer_depth_calculated', ''),
            "nylon_length": form_data.get('nylon_length', ''),
            "nylon_below_releases": form_data.get('nylon_below_releases', ''),
            "intended_nylon_cut_length": form_data.get('intended_nylon_cut_length', ''),
            "actual_nylon_cut_length": form_data.get('actual_nylon_cut_length', ''),
            "steel_length": form_data.get('steel_length', ''),
            "instrument_hardware_length": form_data.get('instrument_hardware_length', ''),
            "spool_id": form_data.get('spool_id', ''),
            "spool_length_used": form_data.get('spool_length_used', ''),
            "spool_type": form_data.get('spool_type', ''),
            "tau_line_length": form_data.get('tau_line_length', ''),
            "additional_kevlar_length": form_data.get('additional_kevlar_length', ''),
            "kevlar_main_spool_length": form_data.get('kevlar_main_spool_length', ''),
            "total_length": form_data.get('total_length', ''),
            "total_instruments": form_data.get('total_instruments', ''),
            "mooring_line_length": form_data.get('mooring_line_length', ''),
            "mtpr_turn_on": form_data.get('mtpr_turn_on', ''),
            "mtpr_on_ball_set_to_adcp_heads": form_data.get('mtpr_on_ball_set_to_adcp_heads', ''),
            "seacat_on": form_data.get('seacat_on', ''),
            "obsolete_argos_dep": form_data.get('obsolete_argos_dep', '')
        }

        # SECTION 3: DEPTH INFORMATION
        depth_info = {
            "depth": form_data.get('depth', ''),
            "depth_source": form_data.get('depth_source', ''),
            "depth_correction": form_data.get('depth_correction', ''),
            "corrected_depth": form_data.get('corrected_depth', ''),
            "flyby_method": form_data.get('flyby_method', ''),
            "flyby_corrected_depth": form_data.get('flyby_corrected_depth', ''),
            "req_adcp_head_depth": form_data.get('req_adcp_head_depth', ''),
            "bottom_depth": form_data.get('bottom_depth', ''),
            "nylon_below_float_ball": form_data.get('nylon_below_float_ball', ''),
            "nylon_below_release": form_data.get('nylon_below_release', ''),
            "instrument_hardware_length": form_data.get('instrument_hardware_length', '')
        }

        # SECTION 5: PRIMARY MOORING LINE & SECTION 6: SECONDARY MOORING LINES
        mooring_line_details = {
            "line1_sn": form_data.get('line1_sn', ''),
            "line1_len": form_data.get('line1_len', ''),
            "line1_type": form_data.get('line1_type', ''),
            "line2_sn": form_data.get('line2_sn', ''),
            "line2_len": form_data.get('line2_len', ''),
            "line2_type": form_data.get('line2_type', ''),
            "line3_sn": form_data.get('line3_sn', ''),
            "line3_len": form_data.get('line3_len', ''),
            "line3_type": form_data.get('line3_type', ''),
            "line4_sn": form_data.get('line4_sn', ''),
            "line4_len": form_data.get('line4_len', ''),
            "line4_type": form_data.get('line4_type', ''),
            "line5_sn": form_data.get('line5_sn', ''),
            "line5_len": form_data.get('line5_len', ''),
            "line5_type": form_data.get('line5_type', ''),
            "line6_sn": form_data.get('line6_sn', ''),
            "line6_len": form_data.get('line6_len', ''),
            "line6_type": form_data.get('line6_type', ''),
            "line7_sn": form_data.get('line7_sn', ''),
            "line7_len": form_data.get('line7_len', ''),
            "line7_type": form_data.get('line7_type', '')
        }

        # SECTION 10-17: SENSOR DETAILS
        sensor_details = {
            "adcp_sn": form_data.get('adcp_sn', ''),
            "adcp_distance": form_data.get('adcp_distance', ''),
            "flasher_sn": form_data.get('flasher_sn', ''),
            "flasher_id": form_data.get('flasher_id', ''),
            "instr1_type": form_data.get('instr1_type', ''),
            "instr1_sn": form_data.get('instr1_sn', ''),
            "instr1_distance_from_adcp": form_data.get('instr1_distance_from_adcp', ''),
            "instr2_type": form_data.get('instr2_type', ''),
            "instr2_sn": form_data.get('instr2_sn', ''),
            "instr2_distance_from_adcp": form_data.get('instr2_distance_from_adcp', ''),
            "top_sn": form_data.get('top_sn', ''),
            "top_type": form_data.get('top_type', ''),
            "btm_sn": form_data.get('btm_sn', ''),
            "btm_type": form_data.get('btm_type', ''),
            "ballset_rel_sn": form_data.get('ballset_rel_sn', ''),
            "ballset_rel_lat": form_data.get('ballset_rel_lat', ''),
            "ballset_rel_long": form_data.get('ballset_rel_long', ''),
            "ballset_type": form_data.get('ballset_type', ''),
            "instr1_sn": form_data.get('instr1_sn', ''),
            "instr1_type": form_data.get('instr1_type', ''),
            "instr1_distance_from_adcp": form_data.get('instr1_distance_from_adcp', ''),
            "instr2_sn": form_data.get('instr2_sn', ''),
            "instr2_type": form_data.get('instr2_type', ''),
            "instr2_distance_from_adcp": form_data.get('instr2_distance_from_adcp', ''),
            "instr3_sn": form_data.get('instr3_sn', ''),
            "instr3_type": form_data.get('instr3_type', ''),
            "instr3_distance_from_adcp": form_data.get('instr3_distance_from_adcp', ''),
            "instr4_sn": form_data.get('instr4_sn', ''),
            "instr4_type": form_data.get('instr4_type', ''),
            "instr4_distance_from_adcp": form_data.get('instr4_distance_from_adcp', '')
        }

        # SECTION 18: BEACON DETAILS
        beacon_details = {
            "rf_beacon_sn": form_data.get('rf_beacon_sn', ''),
            "rf_beacon_id": form_data.get('rf_beacon_id', ''),
            "sat_beacon_id": form_data.get('sat_beacon_id', ''),
            "sat_beacon_sn": form_data.get('sat_beacon_sn', ''),
            "sat_beacon_type": form_data.get('sat_beacon_type', '')
        }

        # SECTION 19-22: RELEASE DETAILS
        release_details = {
            "top_rel_new": form_data.get('top_rel_new', ''),
            "top_rel_2nd": form_data.get('top_rel_2nd', ''),
            "top_rel_rebatt": form_data.get('top_rel_rebatt', ''),
            "btm_rel_new": form_data.get('btm_rel_new', ''),
            "btm_rel_2nd": form_data.get('btm_rel_2nd', ''),
            "btm_rel_rebatt": form_data.get('btm_rel_rebatt', ''),
            "rel8_toprelsn_cmd_1a_code_function_reply": form_data.get('rel8_toprelsn_cmd_1a_code_function_reply', ''),
            "rel8_toprelsn_cmd_2b_code_function_reply": form_data.get('rel8_toprelsn_cmd_2b_code_function_reply', ''),
            "rel8_toprelsn_cmd_3c_code_function_reply": form_data.get('rel8_toprelsn_cmd_3c_code_function_reply', ''),
            "rel8_toprelsn_interrogate_freq": form_data.get('rel8_toprelsn_interrogate_freq', ''),
            "rel8_toprelsn_reply_freq": form_data.get('rel8_toprelsn_reply_freq', ''),
            "rel8_btmrelsn_cmd_1a_code_function_reply": form_data.get('rel8_btmrelsn_cmd_1a_code_function_reply', ''),
            "rel8_btmrelsn_cmd_2b_code_function_reply": form_data.get('rel8_btmrelsn_cmd_2b_code_function_reply', ''),
            "rel8_btmrelsn_cmd_3c_code_function_reply": form_data.get('rel8_btmrelsn_cmd_3c_code_function_reply', ''),
            "rel8_btmrelsn_interrogate_freq": form_data.get('rel8_btmrelsn_interrogate_freq', ''),
            "rel8_btmrelsn_reply_freq": form_data.get('rel8_btmrelsn_reply_freq', ''),
            "rel8_ballrelsn_cmd_1a_code_function_reply": form_data.get('rel8_ballrelsn_cmd_1a_code_function_reply', ''),
            "rel8_ballrelsn_cmd_2b_code_function_reply": form_data.get('rel8_ballrelsn_cmd_2b_code_function_reply', ''),
            "rel8_ballrelsn_cmd_3c_code_function_reply": form_data.get('rel8_ballrelsn_cmd_3c_code_function_reply', ''),
            "rel8_ballrelsn_interrogate_freq": form_data.get('rel8_ballrelsn_interrogate_freq', ''),
            "rel8_ballrelsn_reply_freq": form_data.get('rel8_ballrelsn_reply_freq', '')
        }

        # SECTION 23: CRUISE INFO
        cruise_info = {
            "cruise": form_data.get('cruise', ''),
            "site": form_data.get('site', '')
        }

        # Determine if insert or update
        mooring_id = form_data.get('mooring_id', '')

        if record_id and record_id > 0:
            # Update existing record
            query = """
                UPDATE adcp_dep
                SET mooring_id=?, cruise_info=?, anchor_drop=?, deployment_details=?,
                    depth_info=?, sensor_details=?, beacon_details=?, release_details=?, mooring_line_details=?
                WHERE id=?
            """
            cursor.execute(query, [
                mooring_id,
                json.dumps(cruise_info),
                json.dumps(anchor_drop),
                json.dumps(deployment_details),
                json.dumps(depth_info),
                json.dumps(sensor_details),
                json.dumps(beacon_details),
                json.dumps(release_details),
                json.dumps(mooring_line_details),
                record_id
            ])
        else:
            # Insert new record
            query = """
                INSERT INTO adcp_dep (mooring_id, cruise_info, anchor_drop, deployment_details,
                                      depth_info, sensor_details, beacon_details, release_details, mooring_line_details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, [
                mooring_id,
                json.dumps(cruise_info),
                json.dumps(anchor_drop),
                json.dumps(deployment_details),
                json.dumps(depth_info),
                json.dumps(sensor_details),
                json.dumps(beacon_details),
                json.dumps(release_details),
                json.dumps(mooring_line_details)
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
    h2 {
        color: #1f77b4;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .stTextInput label {
        font-weight: 600;
        color: var(--text-color);
    }
    /* Vertical divider between sections */
    .vertical-divider {
        border-right: 2px solid #e0e0e0;
        padding-right: 1rem;
        margin-right: 1rem;
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

                # Format anchor date for display
                anchor_date_str = anchor_drop.get('anchor_drop_date', 'N/A')
                if anchor_date_str and anchor_date_str != 'N/A':
                    try:
                        # Try to parse and reformat the date
                        for fmt in ["%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S"]:
                            try:
                                anchor_date_obj = datetime.strptime(anchor_date_str, fmt).date()
                                anchor_date_str = anchor_date_obj.strftime("%m/%d/%Y")
                                break
                            except ValueError:
                                continue
                    except Exception:
                        anchor_date_str = 'N/A'

                # Display key info
                info_cols = st.columns(4)
                with info_cols[0]:
                    st.metric("Site", cruise_info.get('site', 'N/A'))
                with info_cols[1]:
                    st.metric("Mooring ID", current_record_dict.get('mooring_id', 'N/A'))
                with info_cols[2]:
                    st.metric("Cruise", cruise_info.get('cruise', 'N/A'))
                with info_cols[3]:
                    st.metric("Anchor Date", anchor_date_str)

    # Form for Add New or Edit
    if mode == "Add New":
        st.subheader("Add New Deployment")
    else:
        st.subheader("Edit Deployment")

    # Initialize form defaults
    if mode == "Search/Edit" and st.session_state.selected_deployment is not None:
        record = st.session_state.selected_deployment

        # Parse all JSON fields
        cruise_info = parse_json_field(record.get('cruise_info', '{}'))
        anchor_drop = parse_json_field(record.get('anchor_drop', '{}'))
        deployment_details = parse_json_field(record.get('deployment_details', '{}'))
        depth_info = parse_json_field(record.get('depth_info', '{}'))
        sensor_details = parse_json_field(record.get('sensor_details', '{}'))
        beacon_details = parse_json_field(record.get('beacon_details', '{}'))
        release_details = parse_json_field(record.get('release_details', '{}'))
        mooring_line_details = parse_json_field(record.get('mooring_line_details', '{}'))

        # Set defaults from parsed JSON
        default_record_id = record.get('id')
        default_mooring_id = record.get('mooring_id', '')
        default_site = cruise_info.get('site', '')
        default_cruise = cruise_info.get('cruise', '')
        default_personnel = deployment_details.get('personnel', '')
        default_latitude = deployment_details.get('latitude', '')
        default_longitude = deployment_details.get('longitude', '')
        default_location_source = deployment_details.get('location_source', '')
        default_actual_xducer_depth_calculated = deployment_details.get('actual_xducer_depth_calculated', '')
        default_corrected_depth = depth_info.get('corrected_depth', '')

        # Parse dates and times - handle multiple formats
        deployment_date_str = deployment_details.get('deployment_date', '')
        default_deployment_date = date.today()
        if deployment_date_str:
            for fmt in ["%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S"]:
                try:
                    default_deployment_date = datetime.strptime(deployment_date_str, fmt).date()
                    break
                except ValueError:
                    continue

        deployment_time_str = deployment_details.get('deployment_time', '')
        default_deployment_time = time(12, 0)
        if deployment_time_str:
            for fmt in ["%H:%M", "%H:%M:%S"]:
                try:
                    default_deployment_time = datetime.strptime(deployment_time_str, fmt).time()
                    break
                except ValueError:
                    continue

        # Set default depth_source based on corrected_depth value
        depth_source_value = depth_info.get('depth_source', '')
        corrected_depth_value = depth_info.get('corrected_depth', '')

        # If depth_source is empty or the corrected_depth is 0.0, default to "Corrected Depth"
        try:
            if not depth_source_value or float(corrected_depth_value) == 0.0:
                default_depth_source = "Corrected Depth"
            else:
                default_depth_source = depth_source_value
        except (ValueError, TypeError):
            # If corrected_depth can't be converted to float, use the depth_source value
            default_depth_source = depth_source_value if depth_source_value else "Corrected Depth"

        # Set beacon defaults
        default_sat_beacon_sn = beacon_details.get('sat_beacon_sn', '')
        default_sat_beacon_id = beacon_details.get('sat_beacon_id', '')
        default_sat_beacon_type = beacon_details.get('sat_beacon_type', '')
        default_rf_beacon_sn = beacon_details.get('rf_beacon_sn', '')
        default_rf_beacon_id = beacon_details.get('rf_beacon_id', '')
        default_flasher_sn = sensor_details.get('flasher_sn', '')
        default_flasher_id = sensor_details.get('flasher_id', '')
        default_iridium_checked = default_sat_beacon_type == 'Iridium'

        # Set subsurface sensor defaults
        default_adcp_sn = sensor_details.get('adcp_sn', '')
        default_adcp_distance = sensor_details.get('adcp_distance', '')
        default_instr1_type = sensor_details.get('instr1_type', '')
        default_instr1_sn = sensor_details.get('instr1_sn', '')
        default_instr1_distance_from_adcp = sensor_details.get('instr1_distance_from_adcp', '')
        default_instr2_type = sensor_details.get('instr2_type', '')
        default_instr2_sn = sensor_details.get('instr2_sn', '')
        default_instr2_distance_from_adcp = sensor_details.get('instr2_distance_from_adcp', '')

        # Set mooring line defaults
        default_line1_sn = mooring_line_details.get('line1_sn', '')
        default_line1_len = mooring_line_details.get('line1_len', '')
        default_line1_type = mooring_line_details.get('line1_type', '')
        default_line2_sn = mooring_line_details.get('line2_sn', '')
        default_line2_len = mooring_line_details.get('line2_len', '')
        default_line2_type = mooring_line_details.get('line2_type', '')
        default_line3_sn = mooring_line_details.get('line3_sn', '')
        default_line3_len = mooring_line_details.get('line3_len', '')
        default_line3_type = mooring_line_details.get('line3_type', '')
        default_line4_sn = mooring_line_details.get('line4_sn', '')
        default_line4_len = mooring_line_details.get('line4_len', '')
        default_line4_type = mooring_line_details.get('line4_type', '')
        default_line5_sn = mooring_line_details.get('line5_sn', '')
        default_line5_len = mooring_line_details.get('line5_len', '')
        default_line5_type = mooring_line_details.get('line5_type', '')
        default_line6_sn = mooring_line_details.get('line6_sn', '')
        default_line6_len = mooring_line_details.get('line6_len', '')
        default_line6_type = mooring_line_details.get('line6_type', '')
        default_line7_sn = mooring_line_details.get('line7_sn', '')
        default_line7_len = mooring_line_details.get('line7_len', '')
        default_line7_type = mooring_line_details.get('line7_type', '')

        # Set depth and length defaults
        default_req_adcp_head_depth = depth_info.get('req_adcp_head_depth', '')
        default_bottom_depth = depth_info.get('bottom_depth', '')
        default_nylon_below_float_ball = depth_info.get('nylon_below_float_ball') or "50"
        default_nylon_below_release = depth_info.get('nylon_below_release') or "50"
        default_instrument_hardware_length = depth_info.get('instrument_hardware_length') or "12"

    else:
        # Defaults for Add New mode
        default_record_id = None
        default_mooring_id = ""
        default_site = ""
        default_cruise = ""
        default_personnel = ""
        default_latitude = ""
        default_longitude = ""
        default_location_source = ""
        default_actual_xducer_depth_calculated = ""
        default_corrected_depth = ""
        default_deployment_date = date.today()
        default_deployment_time = time(12, 0)
        default_depth_source = "Corrected Depth"
        default_sat_beacon_sn = ""
        default_sat_beacon_id = ""
        default_sat_beacon_type = ""
        default_rf_beacon_sn = ""
        default_rf_beacon_id = ""
        default_flasher_sn = ""
        default_flasher_id = ""
        default_iridium_checked = False

        # Subsurface sensor defaults for Add New
        default_adcp_sn = ""
        default_adcp_distance = ""
        default_instr1_type = ""
        default_instr1_sn = ""
        default_instr1_distance_from_adcp = ""
        default_instr2_type = ""
        default_instr2_sn = ""
        default_instr2_distance_from_adcp = ""

        # Mooring line defaults for Add New
        default_line1_sn = ""
        default_line1_len = ""
        default_line1_type = ""
        default_line2_sn = ""
        default_line2_len = ""
        default_line2_type = ""
        default_line3_sn = ""
        default_line3_len = ""
        default_line3_type = ""
        default_line4_sn = ""
        default_line4_len = ""
        default_line4_type = ""
        default_line5_sn = ""
        default_line5_len = ""
        default_line5_type = ""
        default_line6_sn = ""
        default_line6_len = ""
        default_line6_type = ""
        default_line7_sn = ""
        default_line7_len = ""
        default_line7_type = ""

        # Depth and length defaults for Add New
        default_req_adcp_head_depth = ""
        default_bottom_depth = ""
        default_nylon_below_float_ball = "50"
        default_nylon_below_release = "50"
        default_instrument_hardware_length = "12"

    # Create the form
    with st.form("deployment_form"):
        # SECTION 1: BASIC INFORMATION (heading hidden - self-explanatory)

        # Row 1: Site, Mooring ID
        col1, col2 = st.columns(2)
        with col1:
            site = st.text_input("Site", value=default_site, key="site")
        with col2:
            mooring_id = st.text_input("Mooring ID", value=default_mooring_id, key="mooring_id")

        # Row 2: Cruise, Anchor Date
        col1, col2 = st.columns(2)
        with col1:
            cruise = st.text_input("Cruise", value=default_cruise, key="cruise")
        with col2:
            anchor_date = st.date_input("Anchor Date", value=default_deployment_date, key="anchor_date", format="MM/DD/YYYY")

        # Row 3: Personnel (entire row)
        personnel = st.text_input("Personnel", value=default_personnel, key="personnel")

        # Row 4: Latitude, Longitude
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.text_input("Latitude", value=default_latitude, key="latitude")
        with col2:
            longitude = st.text_input("Longitude", value=default_longitude, key="longitude")

        # Row 5: Source of Location, Transducer Depth Calc
        col1, col2 = st.columns(2)
        with col1:
            location_source = st.text_input("Source of Location", value=default_location_source, key="location_source")
        with col2:
            actual_xducer_depth_calculated = st.text_input("Transducer Depth Calc", value=default_actual_xducer_depth_calculated, key="actual_xducer_depth_calculated")

        # Row 6: Corrected Depth, Deployment Start Date
        col1, col2 = st.columns(2)
        with col1:
            corrected_depth = st.text_input("Corrected Depth", value=default_corrected_depth, key="corrected_depth")
        with col2:
            deployment_start_date = st.date_input("Deployment Start Date", value=default_deployment_date, key="deployment_start_date", format="MM/DD/YYYY")

        # Row 7: Source of Depth, Start Time (GMT)
        col1, col2 = st.columns(2)
        with col1:
            depth_source = st.text_input("Source of Depth", value=default_depth_source, key="depth_source")
        with col2:
            start_time_gmt = st.time_input("Start Time (GMT)", value=default_deployment_time, key="start_time_gmt", step=60)

        st.markdown("---")

        # SECTIONS 2 & 3: BEACONS AND SUBSURFACE SENSORS (SIDE BY SIDE)
        col_beacons, col_divider, col_sensors = st.columns([5, 0.5, 5])

        # LEFT COLUMN: BEACONS
        with col_beacons:
            st.markdown("## Beacons")

            # Header row
            col_name, col_sn, col_imei = st.columns([2, 2, 2])
            with col_name:
                st.markdown("**Type**")
            with col_sn:
                st.markdown("**S/N**")
            with col_imei:
                st.markdown("**IMEI/PTT**")

            # Satellite Beacon row
            col_name, col_sn, col_imei = st.columns([2, 2, 2])
            with col_name:
                st.markdown("Satellite Beacon")
                iridium_checked = st.checkbox("Iridium", value=default_iridium_checked, key="iridium_checkbox")
            with col_sn:
                sat_beacon_sn = st.text_input("Satellite Beacon S/N", value=default_sat_beacon_sn, key="sat_beacon_sn", label_visibility="collapsed")
            with col_imei:
                sat_beacon_id = st.text_input("Satellite Beacon IMEI/PTT", value=default_sat_beacon_id, key="sat_beacon_id", label_visibility="collapsed")

            # RF Beacon row
            col_name, col_sn, col_imei = st.columns([2, 2, 2])
            with col_name:
                st.markdown("RF Beacon")
            with col_sn:
                rf_beacon_sn = st.text_input("RF Beacon S/N", value=default_rf_beacon_sn, key="rf_beacon_sn", label_visibility="collapsed")
            with col_imei:
                rf_beacon_id = st.text_input("RF Beacon IMEI/PTT", value=default_rf_beacon_id, placeholder="Ch/Freq: 70/165.525 MHz", key="rf_beacon_id", label_visibility="collapsed")

            # Flasher row
            col_name, col_sn, col_imei = st.columns([2, 2, 2])
            with col_name:
                st.markdown("Flasher")
            with col_sn:
                flasher_sn = st.text_input("Flasher S/N", value=default_flasher_sn, key="flasher_sn", label_visibility="collapsed")
            with col_imei:
                flasher_id = st.text_input("Flasher IMEI/PTT", value=default_flasher_id, placeholder="Pattern: 2 sec ON/4 sec OFF", key="flasher_id", label_visibility="collapsed")

        # MIDDLE: VERTICAL DIVIDER
        with col_divider:
            st.markdown('<div style="border-left: 2px solid #e0e0e0; height: 400px; margin-left: 50%;"></div>', unsafe_allow_html=True)

        # RIGHT COLUMN: SUBSURFACE SENSORS
        with col_sensors:
            st.markdown("## Subsurface Sensors")

            # Header row
            col_name, col_type, col_sn, col_distance = st.columns([1.5, 1.5, 1.5, 2])
            with col_name:
                st.markdown("**Sensor**")
            with col_type:
                st.markdown("**Inst. Type**")
            with col_sn:
                st.markdown("**S/N**")
            with col_distance:
                st.markdown("**Dist.(m) from Head**")

            # ADCP row
            col_name, col_type, col_sn, col_distance = st.columns([1.5, 1.5, 1.5, 2])
            with col_name:
                st.markdown("ADCP")
            with col_type:
                adcp_type = st.text_input("ADCP Type", value="ADCP", key="adcp_type", disabled=True, label_visibility="collapsed")
            with col_sn:
                adcp_sn = st.text_input("ADCP S/N", value=default_adcp_sn, key="adcp_sn", label_visibility="collapsed")
            with col_distance:
                adcp_distance = st.text_input("ADCP Distance", value="", placeholder="0", key="adcp_distance", disabled=True, label_visibility="collapsed")

            # P Sensor 1 row
            col_name, col_type, col_sn, col_distance = st.columns([1.5, 1.5, 1.5, 2])
            with col_name:
                st.markdown("P Sensor 1")
            with col_type:
                instr1_type = st.text_input("P Sensor 1 Type", value=default_instr1_type, key="instr1_type", label_visibility="collapsed")
            with col_sn:
                instr1_sn = st.text_input("P Sensor 1 S/N", value=default_instr1_sn, key="instr1_sn", label_visibility="collapsed")
            with col_distance:
                instr1_distance_from_adcp = st.text_input("P Sensor 1 Distance", value=default_instr1_distance_from_adcp, key="instr1_distance_from_adcp", label_visibility="collapsed")

            # P Sensor 2 row
            col_name, col_type, col_sn, col_distance = st.columns([1.5, 1.5, 1.5, 2])
            with col_name:
                st.markdown("P Sensor 2")
            with col_type:
                instr2_type = st.text_input("P Sensor 2 Type", value=default_instr2_type, key="instr2_type", label_visibility="collapsed")
            with col_sn:
                instr2_sn = st.text_input("P Sensor 2 S/N", value=default_instr2_sn, key="instr2_sn", label_visibility="collapsed")
            with col_distance:
                instr2_distance_from_adcp = st.text_input("P Sensor 2 Distance", value=default_instr2_distance_from_adcp, key="instr2_distance_from_adcp", label_visibility="collapsed")

        st.markdown("---")

        # SECTION 4: MOORING COMPONENTS (SIDE BY SIDE WITH DIVIDER)
        col_mooring, col_divider2, col_right = st.columns([5, 0.5, 5])

        # LEFT COLUMN: MOORING LINES
        with col_mooring:
            st.markdown("## Mooring Lines")

            # Header row
            col_num, col_sn, col_length, col_type = st.columns([1, 2, 2, 2])
            with col_num:
                st.markdown("**#**")
            with col_sn:
                st.markdown("**S/N**")
            with col_length:
                st.markdown("**Length**")
            with col_type:
                st.markdown("**Line Type**")

            # Line 1
            col_num, col_sn, col_length, col_type = st.columns([1, 2, 2, 2])
            with col_num:
                st.markdown("1")
            with col_sn:
                line1_sn = st.text_input("Line 1 S/N", value=default_line1_sn, key="line1_sn", label_visibility="collapsed")
            with col_length:
                line1_len = st.text_input("Line 1 Length", value=default_line1_len, key="line1_len", label_visibility="collapsed")
            with col_type:
                line1_type = st.text_input("Line 1 Type", value=default_line1_type, key="line1_type", label_visibility="collapsed")

            # Line 2
            col_num, col_sn, col_length, col_type = st.columns([1, 2, 2, 2])
            with col_num:
                st.markdown("2")
            with col_sn:
                line2_sn = st.text_input("Line 2 S/N", value=default_line2_sn, key="line2_sn", label_visibility="collapsed")
            with col_length:
                line2_len = st.text_input("Line 2 Length", value=default_line2_len, key="line2_len", label_visibility="collapsed")
            with col_type:
                line2_type = st.text_input("Line 2 Type", value=default_line2_type, key="line2_type", label_visibility="collapsed")

            # Line 3
            col_num, col_sn, col_length, col_type = st.columns([1, 2, 2, 2])
            with col_num:
                st.markdown("3")
            with col_sn:
                line3_sn = st.text_input("Line 3 S/N", value=default_line3_sn, key="line3_sn", label_visibility="collapsed")
            with col_length:
                line3_len = st.text_input("Line 3 Length", value=default_line3_len, key="line3_len", label_visibility="collapsed")
            with col_type:
                line3_type = st.text_input("Line 3 Type", value=default_line3_type, key="line3_type", label_visibility="collapsed")

            # Line 4
            col_num, col_sn, col_length, col_type = st.columns([1, 2, 2, 2])
            with col_num:
                st.markdown("4")
            with col_sn:
                line4_sn = st.text_input("Line 4 S/N", value=default_line4_sn, key="line4_sn", label_visibility="collapsed")
            with col_length:
                line4_len = st.text_input("Line 4 Length", value=default_line4_len, key="line4_len", label_visibility="collapsed")
            with col_type:
                line4_type = st.text_input("Line 4 Type", value=default_line4_type, key="line4_type", label_visibility="collapsed")

            # Line 5
            col_num, col_sn, col_length, col_type = st.columns([1, 2, 2, 2])
            with col_num:
                st.markdown("5")
            with col_sn:
                line5_sn = st.text_input("Line 5 S/N", value=default_line5_sn, key="line5_sn", label_visibility="collapsed")
            with col_length:
                line5_len = st.text_input("Line 5 Length", value=default_line5_len, key="line5_len", label_visibility="collapsed")
            with col_type:
                line5_type = st.text_input("Line 5 Type", value=default_line5_type, key="line5_type", label_visibility="collapsed")

            # Line 6
            col_num, col_sn, col_length, col_type = st.columns([1, 2, 2, 2])
            with col_num:
                st.markdown("6")
            with col_sn:
                line6_sn = st.text_input("Line 6 S/N", value=default_line6_sn, key="line6_sn", label_visibility="collapsed")
            with col_length:
                line6_len = st.text_input("Line 6 Length", value=default_line6_len, key="line6_len", label_visibility="collapsed")
            with col_type:
                line6_type = st.text_input("Line 6 Type", value=default_line6_type, key="line6_type", label_visibility="collapsed")

            # Line 7
            col_num, col_sn, col_length, col_type = st.columns([1, 2, 2, 2])
            with col_num:
                st.markdown("7")
            with col_sn:
                line7_sn = st.text_input("Line 7 S/N", value=default_line7_sn, key="line7_sn", label_visibility="collapsed")
            with col_length:
                line7_len = st.text_input("Line 7 Length", value=default_line7_len, key="line7_len", label_visibility="collapsed")
            with col_type:
                line7_type = st.text_input("Line 7 Type", value=default_line7_type, key="line7_type", label_visibility="collapsed")

        # MIDDLE: VERTICAL DIVIDER
        with col_divider2:
            st.markdown('<div style="border-left: 2px solid #e0e0e0; height: 400px; margin-left: 50%;"></div>', unsafe_allow_html=True)

        # RIGHT COLUMN: DEPTHS AND LENGTHS
        with col_right:
            st.markdown("## Depths and Lengths")

            # Req. ADCP Head Depth
            req_adcp_head_depth = st.text_input("Req. ADCP Head Depth", value=default_req_adcp_head_depth, key="req_adcp_head_depth")

            # Bottom Depth
            bottom_depth = st.text_input("Bottom Depth", value=default_bottom_depth, key="bottom_depth")

            # Nylon Below Float Ball
            nylon_below_float_ball = st.text_input("Nylon Below Float Ball", value=default_nylon_below_float_ball, key="nylon_below_float_ball")

            # Nylon Below Release
            nylon_below_release = st.text_input("Nylon Below Release", value=default_nylon_below_release, key="nylon_below_release")

            # Instrument and Hardware Length
            instrument_hardware_length = st.text_input("Instrument and Hardware Length", value=default_instrument_hardware_length, key="instrument_hardware_length")

        st.markdown("---")

        # Form submission buttons
        col_button, col_spacer = st.columns([1, 11])

        with col_button:
            if mode == "Search/Edit" and st.session_state.selected_deployment:
                submitted = st.form_submit_button("Update", use_container_width=True, type="primary")
            else:
                submitted = st.form_submit_button("Save", use_container_width=True, type="primary")

        if submitted:
            # Prepare form data
            form_data = {
                'mooring_id': mooring_id,
                'site': site,
                'cruise': cruise,
                'personnel': personnel,
                'anchor_date': anchor_date.strftime("%m/%d/%Y") if anchor_date else "",
                'deployment_start_date': deployment_start_date.strftime("%m/%d/%Y") if deployment_start_date else "",
                'start_time_gmt': start_time_gmt.strftime("%H:%M") if start_time_gmt else "",
                'latitude': latitude,
                'longitude': longitude,
                'location_source': location_source,
                'actual_xducer_depth_calculated': actual_xducer_depth_calculated,
                'corrected_depth': corrected_depth,
                'depth_source': depth_source,
                'sat_beacon_sn': sat_beacon_sn,
                'sat_beacon_id': sat_beacon_id,
                'rf_beacon_sn': rf_beacon_sn,
                'rf_beacon_id': rf_beacon_id,
                'flasher_sn': flasher_sn,
                'flasher_id': flasher_id,
                'sat_beacon_type': 'Iridium' if iridium_checked else '',
                'adcp_sn': adcp_sn,
                'adcp_distance': "0",
                'instr1_type': instr1_type,
                'instr1_sn': instr1_sn,
                'instr1_distance_from_adcp': instr1_distance_from_adcp,
                'instr2_type': instr2_type,
                'instr2_sn': instr2_sn,
                'instr2_distance_from_adcp': instr2_distance_from_adcp,
                'line1_sn': line1_sn,
                'line1_len': line1_len,
                'line1_type': line1_type,
                'line2_sn': line2_sn,
                'line2_len': line2_len,
                'line2_type': line2_type,
                'line3_sn': line3_sn,
                'line3_len': line3_len,
                'line3_type': line3_type,
                'line4_sn': line4_sn,
                'line4_len': line4_len,
                'line4_type': line4_type,
                'line5_sn': line5_sn,
                'line5_len': line5_len,
                'line5_type': line5_type,
                'line6_sn': line6_sn,
                'line6_len': line6_len,
                'line6_type': line6_type,
                'line7_sn': line7_sn,
                'line7_len': line7_len,
                'line7_type': line7_type,
                'req_adcp_head_depth': req_adcp_head_depth,
                'bottom_depth': bottom_depth,
                'nylon_below_float_ball': nylon_below_float_ball,
                'nylon_below_release': nylon_below_release,
                'instrument_hardware_length': instrument_hardware_length,
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

if __name__ == '__main__':
    main()
