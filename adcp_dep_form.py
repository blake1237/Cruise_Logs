import streamlit as st
import sqlite3
import pandas as pd
import json
from datetime import datetime, date, time
import os
import math

# Database configuration
DB_PATH = 'Cruise_Logs.db'

def get_spool_info(spool_sn):
    """Look up spool information from spool inventory table."""
    conn = get_db_connection()
    try:
        # Query spool inventory table
        query = """
            SELECT serial_number, length, status, notes, year, yes_flag
            FROM spool_inventory
            WHERE serial_number = ?
        """
        cursor = conn.cursor()
        cursor.execute(query, [spool_sn])
        row = cursor.fetchone()

        if row:
            return {
                'serial': row['serial_number'],
                'length': row['length'],
                'status': row['status'] if row['status'] else 'Active',
                'notes': row['notes'] if row['notes'] else '',
                'year': row['year'] if row['year'] else 'Unknown',
                'ev50': row['yes_flag'] if row['yes_flag'] else ''
            }
        return None
    except Exception as e:
        print(f"Error looking up spool: {e}")
        return None
    finally:
        conn.close()

def find_spool_in_deployments(spool_sn):
    """Find where a spool is used in deployments by checking both JSON and flat table columns."""
    conn = get_db_connection()
    try:
        # Trim and handle the spool serial number
        spool_sn = str(spool_sn).strip() if spool_sn else ""

        if not spool_sn:
            return []

        results = []

        # First check the JSON normalized table
        try:
            query_json = """
                SELECT id, mooringid, site, deployment_info, nylon_spools, depth
                FROM deployments_normalized
                WHERE nylon_spools IS NOT NULL
            """

            cursor = conn.cursor()
            cursor.execute(query_json)

            for row in cursor.fetchall():
                try:
                    # Parse the nylon_spools JSON
                    nylon_data = json.loads(row['nylon_spools']) if row['nylon_spools'] else {}

                    # Parse deployment_info for date
                    deployment_info = json.loads(row['deployment_info']) if row['deployment_info'] else {}
                    dep_date = deployment_info.get('dep_date', '')

                    # Check each spool in the nylon_spools data
                    for spool_key, spool_info in nylon_data.items():
                        if isinstance(spool_info, dict) and spool_info.get('sn', '').strip().upper() == spool_sn.upper():
                            results.append({
                                'mooringid': row['mooringid'],
                                'site': row['site'],
                                'dep_date': dep_date,
                                'depth': row['depth'],
                                'position': spool_key.replace('_', ' #').title(),
                                'length': spool_info.get('length', '')
                            })
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            print(f"Error checking JSON deployments: {e}")

        # Also check the original flat table for historical data
        try:
            query_flat = """
                SELECT mooringid, site, dep_date, corr_depth,
                    CASE
                        WHEN UPPER(nylon1sn) = UPPER(?) THEN 'Spool #1'
                        WHEN UPPER(nylon2sn) = UPPER(?) THEN 'Spool #2'
                        WHEN UPPER(nylon3sn) = UPPER(?) THEN 'Spool #3'
                        WHEN UPPER(nylon4sn) = UPPER(?) THEN 'Spool #4'
                        WHEN UPPER(nylon5sn) = UPPER(?) THEN 'Spool #5'
                        WHEN UPPER(nylon6sn) = UPPER(?) THEN 'Spool #6'
                        WHEN UPPER(nylon7sn) = UPPER(?) THEN 'Spool #7'
                        WHEN UPPER(nylon8sn) = UPPER(?) THEN 'Spool #8'
                        WHEN UPPER(nylon9sn) = UPPER(?) THEN 'Spool #9'
                        WHEN UPPER(nylon10sn) = UPPER(?) THEN 'Spool #10'
                    END as spool_position,
                    nylon1ln, nylon2ln, nylon3ln, nylon4ln, nylon5ln,
                    nylon6ln, nylon7ln, nylon8ln, nylon9ln, nylon10ln,
                    nylon1sn, nylon2sn, nylon3sn, nylon4sn, nylon5sn,
                    nylon6sn, nylon7sn, nylon8sn, nylon9sn, nylon10sn
                FROM deployments
                WHERE UPPER(nylon1sn) = UPPER(?)
                   OR UPPER(nylon2sn) = UPPER(?)
                   OR UPPER(nylon3sn) = UPPER(?)
                   OR UPPER(nylon4sn) = UPPER(?)
                   OR UPPER(nylon5sn) = UPPER(?)
                   OR UPPER(nylon6sn) = UPPER(?)
                   OR UPPER(nylon7sn) = UPPER(?)
                   OR UPPER(nylon8sn) = UPPER(?)
                   OR UPPER(nylon9sn) = UPPER(?)
                   OR UPPER(nylon10sn) = UPPER(?)
                ORDER BY dep_date DESC
            """

            # Execute with the spool_sn for all 20 parameters
            params = [spool_sn] * 20  # 10 for CASE statement, 10 for WHERE clause
            cursor.execute(query_flat, params)

            for row in cursor.fetchall():
                # Get the length from the corresponding length column
                spool_pos = row['spool_position']
                if spool_pos:
                    # Extract spool number from position string
                    spool_num = int(spool_pos.split('#')[1])
                    length = row[f'nylon{spool_num}ln']
                else:
                    length = None

                # Check if this deployment is already in results from JSON table
                existing = False
                for existing_result in results:
                    if (existing_result['mooringid'] == row['mooringid'] and
                        existing_result['dep_date'] == row['dep_date']):
                        existing = True
                        break

                if not existing:
                    results.append({
                        'mooringid': row['mooringid'],
                        'site': row['site'],
                        'dep_date': row['dep_date'],
                        'depth': row['corr_depth'],
                        'position': spool_pos,
                        'length': length
                    })
        except Exception as e:
            print(f"Error checking flat table deployments: {e}")

        # Sort by date (most recent first)
        results.sort(key=lambda x: x['dep_date'] or '', reverse=True)
        return results
    except Exception as e:
        print(f"Error finding spool in deployments: {e}")
        return []
    finally:
        conn.close()

def get_all_spool_serials():
    """Get all spool serial numbers from inventory for dropdown."""
    conn = get_db_connection()
    try:
        query = "SELECT DISTINCT serial_number FROM spool_inventory WHERE serial_number IS NOT NULL ORDER BY serial_number"
        cursor = conn.cursor()
        cursor.execute(query)
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching spool serials: {e}")
        return []
    finally:
        conn.close()

def search_spools_advanced(serial_pattern=None, min_length=None, max_length=None,
                          status=None, year=None, notes_pattern=None, ev50=None):
    """Search spools based on multiple criteria."""
    conn = get_db_connection()
    try:
        # Build query with filters
        query = "SELECT serial_number, length, status, notes, year, yes_flag FROM spool_inventory WHERE 1=1"
        params = []

        if serial_pattern:
            query += " AND serial_number LIKE ?"
            params.append(f"%{serial_pattern}%")

        if min_length is not None:
            query += " AND length >= ?"
            params.append(min_length)

        if max_length is not None:
            query += " AND length <= ?"
            params.append(max_length)

        if status:
            query += " AND status = ?"
            params.append(status)

        if year:
            query += " AND year = ?"
            params.append(year)

        if notes_pattern:
            query += " AND notes LIKE ?"
            params.append(f"%{notes_pattern}%")

        if ev50:
            query += " AND yes_flag = ?"
            params.append(ev50)

        query += " ORDER BY serial_number"

        cursor = conn.cursor()
        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            results.append({
                'serial': row['serial_number'],
                'length': row['length'],
                'status': row['status'],
                'notes': row['notes'],
                'year': row['year'],
                'ev50': row['yes_flag'] if row['yes_flag'] else ''
            })

        return results
    except Exception as e:
        print(f"Error searching spools: {e}")
        return []
    finally:
        conn.close()

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
            "anchor_drop_lat": form_data.get('anchor_drop_latitude', ''),
            "anchor_drop_long": form_data.get('anchor_drop_longitude', ''),
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
            "workboat_lat": form_data.get('flyby_latitude', ''),
            "workboat_lon": form_data.get('flyby_longitude', ''),
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
            "mtpr_turn_on": form_data.get('mtpr_turn_on_datetime', ''),
            "mtpr_on_ball_set_to_adcp_heads": form_data.get('measured_distance_mtpr', ''),
            "seacat_on": form_data.get('seacat_on', ''),
            "obsolete_argos_dep": form_data.get('argos_beacon_usage', ''),
            "total_kevlar_length": form_data.get('total_kevlar_length', ''),
            "historical_hardware_length": form_data.get('historical_hardware_length', ''),
            "deployment_problems": form_data.get('comments', '')
        }

        # SECTION 3: DEPTH INFORMATION
        depth_info = {
            "depth": form_data.get('depth', ''),
            "depth_source": form_data.get('depth_source', ''),
            "depth_correction": form_data.get('depth_correction', ''),
            "corrected_depth": form_data.get('corrected_depth', ''),
            "flyby_method": form_data.get('flyby_method', ''),
            "flyby_corrected_depth": form_data.get('flyby_corrected_depth', ''),
            "nylon_below_float_ball": form_data.get('nylon_below_float_ball', ''),
            "nylon_below_release": form_data.get('nylon_below_release', ''),
            "instrument_hardware_length": form_data.get('instrument_hardware_length', ''),
            "depth_correction": form_data.get('anchor_depth_correction', ''),
            "corrected_depth": form_data.get('anchor_corrected_depth', '')
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
            "line7_type": form_data.get('line7_type', ''),
            "actual_nylon_cut": form_data.get('actual_nylon_cut', '')
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
            "top_type": form_data.get('top_type', ''),
            "rel1_sn": form_data.get('rel1_sn', ''),
            "btm_type": form_data.get('btm_type', ''),
            "rel2_sn": form_data.get('rel2_sn', ''),
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
        initial_sidebar_state="auto"
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
    if 'copied_nylon_cut' not in st.session_state:
        st.session_state.copied_nylon_cut = None

    # Mode selection
    mode = st.radio("Mode", ["Search/Edit", "Add New"], key="mode_selector", horizontal=True)
    st.session_state.mode = mode

    # Sidebar - Tools for Add New mode (only in Add New mode)
    if mode == "Add New":
        with st.sidebar:
            st.markdown("## 🎯 Nylon Cut Calculator")
            st.markdown("**Target: ADCP Head at 300m**")
            st.markdown("---")

            # Helper function for sidebar calculations
            def safe_float_sidebar(value):
                try:
                    return float(value) if value and str(value).strip() else 0.0
                except (ValueError, TypeError):
                    return 0.0

            # Input fields for calculation
            st.markdown("### Site Information")
            sidebar_bottom_depth = st.number_input("Bottom Depth", value=4000.0, step=1.0, key="sidebar_bottom_depth")

            st.markdown("### Mooring Components")
            sidebar_total_length = st.number_input("Total Mooring Line Length", value=280.0, step=1.0, key="sidebar_total_length")
            sidebar_nylon_below_float = st.number_input("Nylon Below Float Ball", value=50.0, step=1.0, key="sidebar_nylon_below_float")
            sidebar_nylon_below_release = st.number_input("Nylon Below Release", value=50.0, step=1.0, key="sidebar_nylon_below_release")
            sidebar_instrument_hardware = st.number_input("Instrument Hardware Length", value=0.0, step=1.0, key="sidebar_instrument_hardware")

            st.markdown("---")
            st.markdown("### Target Depth")
            target_adcp_depth = st.number_input("Target ADCP Head Depth (below surface)", value=300.0, step=1.0, key="target_depth")

            # Calculate required nylon cut length
            # Distance from bottom to ADCP head position
            distance_from_bottom = sidebar_bottom_depth - target_adcp_depth
            # Required nylon cut = Distance from bottom - all other components
            required_nylon_cut_unscaled = distance_from_bottom - sidebar_total_length - sidebar_nylon_below_float - sidebar_nylon_below_release - sidebar_instrument_hardware
            required_nylon_cut = required_nylon_cut_unscaled * 0.94

            st.markdown("---")
            st.markdown("### 🎯 Result")
            if required_nylon_cut > 0:
                st.success(f"**Cut off {required_nylon_cut:.1f}m**")
            else:
                st.error(f"**Cut off {abs(required_nylon_cut):.1f}m (negative - need less hardware)**")

            # Show calculation details and total mooring length
            st.info(f"Distance from bottom to ADCP head: {distance_from_bottom:.1f}m")
            total_mooring_length = sidebar_total_length + sidebar_nylon_below_float + sidebar_nylon_below_release + sidebar_instrument_hardware + max(0, required_nylon_cut_unscaled)
            st.info(f"Total Mooring Length: {total_mooring_length:.1f}m")

            # Verify calculation
            actual_adcp_depth = sidebar_bottom_depth - total_mooring_length
            if abs(actual_adcp_depth - target_adcp_depth) < 0.1:
                st.success(f"✅ ADCP head will be at {actual_adcp_depth:.1f}m depth")
            else:
                st.warning(f"⚠️ ADCP head will actually be at {actual_adcp_depth:.1f}m depth")

            st.markdown("---")

            # Apply CSS to make button green
            st.markdown("""
            <style>
            button[kind="secondary"] {
                background-color: #28a745 !important;
                color: white !important;
                border-color: #28a745 !important;
            }
            button[kind="secondary"]:hover {
                background-color: #218838 !important;
                border-color: #218838 !important;
            }
            </style>
            """, unsafe_allow_html=True)

            if st.button("📋 Copy Required Nylon Cut Length to Main Form", key="copy_nylon_button"):
                st.session_state.copied_nylon_cut = required_nylon_cut
                st.success(f"✅ Copied {required_nylon_cut:.1f}m to main form!")
                st.rerun()

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

    # Create unique widget key suffix based on mode and record
    # This prevents session state from one record interfering with another
    if mode == "Search/Edit" and st.session_state.selected_deployment is not None:
        record = st.session_state.selected_deployment
        record_id = record.get('id')
        widget_key_suffix = f"_edit_{record_id}"
    else:
        widget_key_suffix = "_new"

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
        default_actual_nylon_cut = mooring_line_details.get('actual_nylon_cut', '')

        # Set depth and length defaults
        default_req_adcp_head_depth = deployment_details.get('intended_xducer_depth', '')
        default_bottom_depth = deployment_details.get('target_bottom_depth', '')
        default_nylon_below_float_ball = depth_info.get('nylon_below_float_ball') or "50"
        default_nylon_below_release = depth_info.get('nylon_below_release') or "50"
        default_instrument_hardware_length = deployment_details.get('instrument_hardware_length', '')

        # Release defaults for Search/Edit mode - use release_details variable directly
        default_top_release_type = release_details.get('top_type', '')
        default_top_release_sn = release_details.get('rel1_sn', '')
        default_top_release_int_freq = release_details.get('rel8_toprelsn_interrogate_freq', '')
        default_top_release_reply = release_details.get('rel8_toprelsn_reply_freq', '')
        default_top_release_release = release_details.get('rel8_toprelsn_cmd_1a_code_function_reply', '')
        default_top_release_disable = release_details.get('rel8_toprelsn_cmd_2b_code_function_reply', '')
        default_top_release_enable = release_details.get('rel8_toprelsn_cmd_3c_code_function_reply', '')
        default_top_release_new = release_details.get('top_rel_new', '')
        default_top_release_2nd_dep = release_details.get('top_rel_2nd', '')
        default_top_release_rebatteried = release_details.get('top_rel_rebatt', '')
        default_bottom_release_type = release_details.get('btm_type', '')
        default_bottom_release_sn = release_details.get('rel2_sn', '')
        default_bottom_release_int_freq = release_details.get('rel8_btmrelsn_interrogate_freq', '')
        default_bottom_release_reply = release_details.get('rel8_btmrelsn_reply_freq', '')
        default_bottom_release_release = release_details.get('rel8_btmrelsn_cmd_1a_code_function_reply', '')
        default_bottom_release_disable = release_details.get('rel8_btmrelsn_cmd_2b_code_function_reply', '')
        default_bottom_release_enable = release_details.get('rel8_btmrelsn_cmd_3c_code_function_reply', '')
        default_bottom_release_new = release_details.get('btm_rel_new', '')
        default_bottom_release_2nd_dep = release_details.get('btm_rel_2nd', '')
        default_bottom_release_rebatteried = release_details.get('btm_rel_rebatt', '')
        default_ball_release_type = ""  # Ball releases don't have type field
        default_ball_release_sn = ""  # Ball releases don't have S/N field
        default_ball_release_int_freq = release_details.get('rel8_ballrelsn_interrogate_freq', '')
        default_ball_release_reply = release_details.get('rel8_ballrelsn_reply_freq', '')
        default_ball_release_release = release_details.get('rel8_ballrelsn_cmd_1a_code_function_reply', '')
        default_ball_release_disable = release_details.get('rel8_ballrelsn_cmd_2b_code_function_reply', '')
        default_ball_release_enable = release_details.get('rel8_ballrelsn_cmd_3c_code_function_reply', '')

        # Anchor Drop defaults for Search/Edit mode
        default_anchor_drop_date = anchor_drop.get('anchor_drop_date', '')
        default_anchor_drop_time = anchor_drop.get('anchor_drop_time', '')
        default_anchor_drop_latitude = anchor_drop.get('anchor_drop_lat', '')
        default_anchor_drop_longitude = anchor_drop.get('anchor_drop_long', '')
        default_anchor_drop_depth = anchor_drop.get('anchor_drop_depth', '')
        default_anchor_weight = anchor_drop.get('anchor_weight', '')
        default_anchor_depth_correction = depth_info.get('depth_correction', '')
        default_anchor_corrected_depth = depth_info.get('corrected_depth', '')

        # Fly By defaults for Search/Edit mode - get from deployment_details workboat coordinates
        default_flyby_latitude = deployment_details.get('workboat_lat', '')
        default_flyby_longitude = deployment_details.get('workboat_lon', '')
        default_flyby_corrected_depth = depth_info.get('flyby_corrected_depth', '')
        default_flyby_method = depth_info.get('flyby_method', '')

        # Historical defaults for Search/Edit mode
        default_adcp_xducer_depth = deployment_details.get('actual_xducer_depth_calculated', '')
        default_measured_distance_mtpr = deployment_details.get('mtpr_on_ball_set_to_adcp_heads', '')
        default_mtpr_turn_on_datetime = deployment_details.get('mtpr_turn_on', '')
        default_argos_beacon_usage = deployment_details.get('obsolete_argos_dep', '')
        default_hardware_length = deployment_details.get('historical_hardware_length', '')
        default_kevlar_main_spool = deployment_details.get('kevlar_main_spool_length', '')
        default_additional_kevlar = deployment_details.get('additional_kevlar_length', '')
        default_total_kevlar_length = deployment_details.get('total_kevlar_length', '')
        default_ball_set_rel_lat = deployment_details.get('latitude', '')
        default_ball_set_rel_lon = deployment_details.get('longitude', '')
        default_comments = deployment_details.get('deployment_problems', '')

    else:
        # Defaults for Add New mode - initialize empty release_details
        release_details = {}
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
        default_actual_nylon_cut = ""

        # Set depth and length defaults for Add New
        default_req_adcp_head_depth = ""
        default_bottom_depth = ""
        default_nylon_below_float_ball = "50"
        default_nylon_below_release = "50"
        default_instrument_hardware_length = ""

        # Release defaults for Add New mode
        default_top_release_type = ""
        default_top_release_sn = ""
        default_top_release_int_freq = ""
        default_top_release_reply = ""
        default_top_release_release = ""
        default_top_release_disable = ""
        default_top_release_enable = ""
        default_top_release_new = ""
        default_top_release_2nd_dep = ""
        default_top_release_rebatteried = ""
        default_bottom_release_type = ""
        default_bottom_release_sn = ""
        default_bottom_release_int_freq = ""
        default_bottom_release_reply = ""
        default_bottom_release_release = ""
        default_bottom_release_disable = ""
        default_bottom_release_enable = ""
        default_bottom_release_new = ""
        default_bottom_release_2nd_dep = ""
        default_bottom_release_rebatteried = ""
        default_ball_release_type = ""  # Ball releases don't have type field
        default_ball_release_sn = ""  # Ball releases don't have S/N field
        default_ball_release_int_freq = ""
        default_ball_release_reply = ""
        default_ball_release_release = ""
        default_ball_release_disable = ""
        default_ball_release_enable = ""

        # Anchor Drop defaults for Add New mode
        default_anchor_drop_date = ""
        default_anchor_drop_time = ""
        default_anchor_drop_latitude = ""
        default_anchor_drop_longitude = ""
        default_anchor_drop_depth = ""
        default_anchor_weight = ""
        default_anchor_depth_correction = ""
        default_anchor_corrected_depth = ""

        # Fly By defaults for Add New mode
        default_flyby_latitude = ""
        default_flyby_longitude = ""
        default_flyby_corrected_depth = ""
        default_flyby_method = ""

        # Historical defaults for Add New mode
        default_adcp_xducer_depth = ""
        default_measured_distance_mtpr = ""
        default_mtpr_turn_on_datetime = ""
        default_argos_beacon_usage = ""
        default_hardware_length = ""
        default_kevlar_main_spool = ""
        default_additional_kevlar = ""
        default_total_kevlar_length = ""
        default_ball_set_rel_lat = ""
        default_ball_set_rel_lon = ""
        default_comments = ""

    # Create the form
    with st.form("deployment_form"):
        # SECTION 1: BASIC INFORMATION (heading hidden - self-explanatory)

        # Row 1: Site, Mooring ID
        col1, col2 = st.columns(2)
        with col1:
            site = st.text_input("Site", value=default_site, key=f"site{widget_key_suffix}")
        with col2:
            mooring_id = st.text_input("Mooring ID", value=default_mooring_id, key=f"mooring_id{widget_key_suffix}")

        # Row 2: Cruise, Anchor Date
        col1, col2 = st.columns(2)
        with col1:
            cruise = st.text_input("Cruise", value=default_cruise, key=f"cruise{widget_key_suffix}")
        with col2:
            anchor_date = st.date_input("Anchor Date", value=default_deployment_date, key=f"anchor_date{widget_key_suffix}", format="MM/DD/YYYY")

        # Row 3: Personnel (entire row)
        personnel = st.text_input("Personnel", value=default_personnel, key=f"personnel{widget_key_suffix}")

        # Row 4: Latitude, Longitude
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.text_input("Latitude", value=default_latitude, key=f"latitude{widget_key_suffix}")
        with col2:
            longitude = st.text_input("Longitude", value=default_longitude, key=f"longitude{widget_key_suffix}")

        # Row 5: Source of Location, Transducer Depth Calc
        col1, col2 = st.columns(2)
        with col1:
            location_source = st.text_input("Source of Location", value=default_location_source, key=f"location_source{widget_key_suffix}")
        with col2:
            actual_xducer_depth_calculated = st.text_input("Transducer Depth Calc", value=default_actual_xducer_depth_calculated, key=f"actual_xducer_depth_calculated{widget_key_suffix}")

        # Row 6: Corrected Depth, Deployment Start Date
        col1, col2 = st.columns(2)
        with col1:
            corrected_depth = st.text_input("Corrected Depth", value=default_corrected_depth, key=f"corrected_depth{widget_key_suffix}")
        with col2:
            deployment_start_date = st.date_input("Deployment Start Date", value=default_deployment_date, key=f"deployment_start_date{widget_key_suffix}", format="MM/DD/YYYY")

        # Row 7: Source of Depth, Start Time (GMT)
        col1, col2 = st.columns(2)
        with col1:
            depth_source = st.text_input("Source of Depth", value=default_depth_source, key=f"depth_source{widget_key_suffix}")
        with col2:
            start_time_gmt = st.time_input("Start Time (GMT)", value=default_deployment_time, key=f"start_time_gmt{widget_key_suffix}", step=60)

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
                iridium_checked = st.checkbox("Iridium", value=default_iridium_checked, key=f"iridium_checkbox{widget_key_suffix}")
            with col_sn:
                sat_beacon_sn = st.text_input("Satellite Beacon S/N", value=default_sat_beacon_sn, key=f"sat_beacon_sn{widget_key_suffix}", label_visibility="collapsed")
            with col_imei:
                sat_beacon_id = st.text_input("Satellite Beacon IMEI/PTT", value=default_sat_beacon_id, key=f"sat_beacon_id{widget_key_suffix}", label_visibility="collapsed")

            # RF Beacon row
            col_name, col_sn, col_imei = st.columns([2, 2, 2])
            with col_name:
                st.markdown("RF Beacon")
            with col_sn:
                rf_beacon_sn = st.text_input("RF Beacon S/N", value=default_rf_beacon_sn, key=f"rf_beacon_sn{widget_key_suffix}", label_visibility="collapsed")
            with col_imei:
                rf_beacon_id = st.text_input("RF Beacon IMEI/PTT", value=default_rf_beacon_id, placeholder="Ch/Freq: 70/165.525 MHz", key=f"rf_beacon_id{widget_key_suffix}", label_visibility="collapsed")

            # Flasher row
            col_name, col_sn, col_imei = st.columns([2, 2, 2])
            with col_name:
                st.markdown("Flasher")
            with col_sn:
                flasher_sn = st.text_input("Flasher S/N", value=default_flasher_sn, key=f"flasher_sn{widget_key_suffix}", label_visibility="collapsed")
            with col_imei:
                flasher_id = st.text_input("Flasher IMEI/PTT", value=default_flasher_id, placeholder="Pattern: 2 sec ON/4 sec OFF", key=f"flasher_id{widget_key_suffix}", label_visibility="collapsed")

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
                adcp_type = st.text_input("ADCP Type", value="ADCP", key=f"adcp_type{widget_key_suffix}", disabled=True, label_visibility="collapsed")
            with col_sn:
                adcp_sn = st.text_input("ADCP S/N", value=default_adcp_sn, key=f"adcp_sn{widget_key_suffix}", label_visibility="collapsed")
            with col_distance:
                adcp_distance = st.text_input("ADCP Distance", value="", placeholder="0", key=f"adcp_distance{widget_key_suffix}", disabled=True, label_visibility="collapsed")

            # P Sensor 1 row
            col_name, col_type, col_sn, col_distance = st.columns([1.5, 1.5, 1.5, 2])
            with col_name:
                st.markdown("P Sensor 1")
            with col_type:
                instr1_type = st.text_input("P Sensor 1 Type", value=default_instr1_type, key=f"instr1_type{widget_key_suffix}", label_visibility="collapsed")
            with col_sn:
                instr1_sn = st.text_input("P Sensor 1 S/N", value=default_instr1_sn, key=f"instr1_sn{widget_key_suffix}", label_visibility="collapsed")
            with col_distance:
                instr1_distance_from_adcp = st.text_input("P Sensor 1 Distance", value=default_instr1_distance_from_adcp, key=f"instr1_distance_from_adcp{widget_key_suffix}", label_visibility="collapsed")

            # P Sensor 2 row
            col_name, col_type, col_sn, col_distance = st.columns([1.5, 1.5, 1.5, 2])
            with col_name:
                st.markdown("P Sensor 2")
            with col_type:
                instr2_type = st.text_input("P Sensor 2 Type", value=default_instr2_type, key=f"instr2_type{widget_key_suffix}", label_visibility="collapsed")
            with col_sn:
                instr2_sn = st.text_input("P Sensor 2 S/N", value=default_instr2_sn, key=f"instr2_sn{widget_key_suffix}", label_visibility="collapsed")
            with col_distance:
                instr2_distance_from_adcp = st.text_input("P Sensor 2 Distance", value=default_instr2_distance_from_adcp, key=f"instr2_distance_from_adcp{widget_key_suffix}", label_visibility="collapsed")

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
                line1_sn = st.text_input("Line 1 S/N", value=default_line1_sn, key=f"line1_sn{widget_key_suffix}", label_visibility="collapsed")
            with col_length:
                line1_len = st.text_input("Line 1 Length", value=default_line1_len, key=f"line1_len{widget_key_suffix}", label_visibility="collapsed")
            with col_type:
                line1_type = st.text_input("Line 1 Type", value=default_line1_type, key=f"line1_type{widget_key_suffix}", label_visibility="collapsed")

            # Line 2
            col_num, col_sn, col_length, col_type = st.columns([1, 2, 2, 2])
            with col_num:
                st.markdown("2")
            with col_sn:
                line2_sn = st.text_input("Line 2 S/N", value=default_line2_sn, key=f"line2_sn{widget_key_suffix}", label_visibility="collapsed")
            with col_length:
                line2_len = st.text_input("Line 2 Length", value=default_line2_len, key=f"line2_len{widget_key_suffix}", label_visibility="collapsed")
            with col_type:
                line2_type = st.text_input("Line 2 Type", value=default_line2_type, key=f"line2_type{widget_key_suffix}", label_visibility="collapsed")

            # Line 3
            col_num, col_sn, col_length, col_type = st.columns([1, 2, 2, 2])
            with col_num:
                st.markdown("3")
            with col_sn:
                line3_sn = st.text_input("Line 3 S/N", value=default_line3_sn, key=f"line3_sn{widget_key_suffix}", label_visibility="collapsed")
            with col_length:
                line3_len = st.text_input("Line 3 Length", value=default_line3_len, key=f"line3_len{widget_key_suffix}", label_visibility="collapsed")
            with col_type:
                line3_type = st.text_input("Line 3 Type", value=default_line3_type, key=f"line3_type{widget_key_suffix}", label_visibility="collapsed")

            # Line 4
            col_num, col_sn, col_length, col_type = st.columns([1, 2, 2, 2])
            with col_num:
                st.markdown("4")
            with col_sn:
                line4_sn = st.text_input("Line 4 S/N", value=default_line4_sn, key=f"line4_sn{widget_key_suffix}", label_visibility="collapsed")
            with col_length:
                line4_len = st.text_input("Line 4 Length", value=default_line4_len, key=f"line4_len{widget_key_suffix}", label_visibility="collapsed")
            with col_type:
                line4_type = st.text_input("Line 4 Type", value=default_line4_type, key=f"line4_type{widget_key_suffix}", label_visibility="collapsed")

            # Line 5
            col_num, col_sn, col_length, col_type = st.columns([1, 2, 2, 2])
            with col_num:
                st.markdown("5")
            with col_sn:
                line5_sn = st.text_input("Line 5 S/N", value=default_line5_sn, key=f"line5_sn{widget_key_suffix}", label_visibility="collapsed")
            with col_length:
                line5_len = st.text_input("Line 5 Length", value=default_line5_len, key=f"line5_len{widget_key_suffix}", label_visibility="collapsed")
            with col_type:
                line5_type = st.text_input("Line 5 Type", value=default_line5_type, key=f"line5_type{widget_key_suffix}", label_visibility="collapsed")

            # Line 6
            col_num, col_sn, col_length, col_type = st.columns([1, 2, 2, 2])
            with col_num:
                st.markdown("6")
            with col_sn:
                line6_sn = st.text_input("Line 6 S/N", value=default_line6_sn, key=f"line6_sn{widget_key_suffix}", label_visibility="collapsed")
            with col_length:
                line6_len = st.text_input("Line 6 Length", value=default_line6_len, key=f"line6_len{widget_key_suffix}", label_visibility="collapsed")
            with col_type:
                line6_type = st.text_input("Line 6 Type", value=default_line6_type, key=f"line6_type{widget_key_suffix}", label_visibility="collapsed")

            # Line 7
            col_num, col_sn, col_length, col_type = st.columns([1, 2, 2, 2])
            with col_num:
                st.markdown("7")
            with col_sn:
                line7_sn = st.text_input("Line 7 S/N", value=default_line7_sn, key=f"line7_sn{widget_key_suffix}", label_visibility="collapsed")
            with col_length:
                line7_len = st.text_input("Line 7 Length", value=default_line7_len, key=f"line7_len{widget_key_suffix}", label_visibility="collapsed")
            with col_type:
                line7_type = st.text_input("Line 7 Type", value=default_line7_type, key=f"line7_type{widget_key_suffix}", label_visibility="collapsed")

            # Calculate total length
            def safe_float(value):
                try:
                    return float(value) if value and str(value).strip() else 0.0
                except (ValueError, TypeError):
                    return 0.0

            total_length = (safe_float(line1_len) + safe_float(line2_len) + safe_float(line3_len) +
                          safe_float(line4_len) + safe_float(line5_len) + safe_float(line6_len) +
                          safe_float(line7_len))

            # Total row
            st.markdown("---")
            st.markdown(f"**Total Length: {total_length:.1f}**")

        # MIDDLE: VERTICAL DIVIDER
        with col_divider2:
            st.markdown('<div style="border-left: 2px solid #e0e0e0; height: 400px; margin-left: 50%;"></div>', unsafe_allow_html=True)

        # RIGHT COLUMN: DEPTHS AND LENGTHS
        with col_right:
            st.markdown("## Depths and Lengths")

            # Req. ADCP Head Depth
            req_adcp_head_depth = st.text_input("Req. ADCP Head Depth", value=default_req_adcp_head_depth, key=f"req_adcp_head_depth{widget_key_suffix}")

            # Bottom Depth
            bottom_depth = st.text_input("Bottom Depth", value=default_bottom_depth, key=f"bottom_depth{widget_key_suffix}")

            # Nylon Below Float Ball
            nylon_below_float_ball = st.text_input("Nylon Below Float Ball", value=default_nylon_below_float_ball, key=f"nylon_below_float_ball{widget_key_suffix}")

            # Nylon Below Release
            nylon_below_release = st.text_input("Nylon Below Release", value=default_nylon_below_release, key=f"nylon_below_release{widget_key_suffix}")

            # Instrument and Hardware Length
            instrument_hardware_length = st.text_input("Instrument and Hardware Length", value=default_instrument_hardware_length, key=f"instrument_hardware_length{widget_key_suffix}")


        # Calculate summary values after all inputs are defined
        st.markdown("---")
        st.markdown("### Summary Calculations")

        # Helper function for safe float conversion
        def safe_float_calc(value):
            try:
                return float(value) if value and str(value).strip() else 0.0
            except (ValueError, TypeError):
                return 0.0

        # Calculated Nylon Cut Length (x.94)
        bottom_depth_val = safe_float_calc(bottom_depth)
        nylon_below_float_ball_val = safe_float_calc(nylon_below_float_ball)
        nylon_below_release_val = safe_float_calc(nylon_below_release)
        instrument_hardware_length_val = safe_float_calc(instrument_hardware_length)
        req_adcp_head_depth_val = safe_float_calc(req_adcp_head_depth)

        calculated_nylon_cut = (bottom_depth_val - total_length - nylon_below_float_ball_val - nylon_below_release_val - instrument_hardware_length_val - req_adcp_head_depth_val) * 0.94
        st.markdown(f"**Calculated Nylon Cut Length (x.94): {calculated_nylon_cut:.1f}**")

        # Actual Nylon Cut Length (above release) - editable field
        # Check if we have a copied value from sidebar
        nylon_cut_value = default_actual_nylon_cut
        if st.session_state.copied_nylon_cut is not None:
            nylon_cut_value = str(round(st.session_state.copied_nylon_cut, 1))
            # Clear the copied value after using it
            st.session_state.copied_nylon_cut = None

        actual_nylon_cut = st.text_input("**Actual Nylon Cut Length (above release)**", value=nylon_cut_value, key=f"actual_nylon_cut{widget_key_suffix}")

        # Total Mooring Length - calculated field
        actual_nylon_cut_val = safe_float_calc(actual_nylon_cut)
        total_mooring_length = total_length + nylon_below_float_ball_val + nylon_below_release_val + instrument_hardware_length_val + actual_nylon_cut_val
        st.markdown(f"**Total Mooring Length: {total_mooring_length:.1f}**")

        # Display Actual Xducer Depth
        if actual_xducer_depth_calculated:
            actual_xducer_depth_val = safe_float_calc(actual_xducer_depth_calculated)
            st.markdown(f"**Actual Xducer Depth: {actual_xducer_depth_val:.1f}m**")

        st.markdown("---")

        # Releases Section
        st.subheader("Releases")

        # Debug display (remove after testing)
        if mode == "Search/Edit" and st.session_state.selected_deployment:
            with st.expander("Debug: Release Details JSON"):
                st.json(release_details)

        # Create column headers
        col_labels = st.columns([1, 1, 1.5, 1, 1, 1, 1, 1, 1, 1.2, 1.2])
        col_labels[0].write("**Position**")
        col_labels[1].write("**Type**")
        col_labels[2].write("**S/N**")
        col_labels[3].write("**Int. Freq.**")
        col_labels[4].write("**Reply**")
        col_labels[5].write("**Release**")
        col_labels[6].write("**Disable**")
        col_labels[7].write("**Enable**")
        col_labels[8].write("**New**")
        col_labels[9].write("**2nd Dep**")
        col_labels[10].write("**Rebatteried?**")

        # Top Release Row
        col_top = st.columns([1, 1, 1.5, 1, 1, 1, 1, 1, 1, 1.2, 1.2])
        col_top[0].write("Top")
        top_type = col_top[1].text_input("Top Release Type", value=default_top_release_type, key=f"top_release_type{widget_key_suffix}", label_visibility="collapsed")
        top_sn = col_top[2].text_input("Top Release S/N", value=default_top_release_sn, key=f"top_release_sn{widget_key_suffix}", label_visibility="collapsed")
        top_int_freq = col_top[3].text_input("Top Release Int. Freq.", value=default_top_release_int_freq, key=f"top_release_int_freq{widget_key_suffix}", label_visibility="collapsed")
        top_reply = col_top[4].text_input("Top Release Reply", value=default_top_release_reply, key=f"top_release_reply{widget_key_suffix}", label_visibility="collapsed")
        top_release = col_top[5].text_input("Top Release Release", value=default_top_release_release, key=f"top_release_release{widget_key_suffix}", label_visibility="collapsed")
        top_disable = col_top[6].text_input("Top Release Disable", value=default_top_release_disable, key=f"top_release_disable{widget_key_suffix}", label_visibility="collapsed")
        top_enable = col_top[7].text_input("Top Release Enable", value=default_top_release_enable, key=f"top_release_enable{widget_key_suffix}", label_visibility="collapsed")
        top_new = col_top[8].selectbox("Top Release New", options=["", "Yes", "No"], index=0 if not default_top_release_new else (1 if default_top_release_new == "Yes" else 2), key=f"top_release_new{widget_key_suffix}", label_visibility="collapsed")
        top_2nd_dep = col_top[9].selectbox("Top Release 2nd Dep", options=["", "Yes", "No"], index=0 if not default_top_release_2nd_dep else (1 if default_top_release_2nd_dep == "Yes" else 2), key=f"top_release_2nd_dep{widget_key_suffix}", label_visibility="collapsed")
        top_rebatteried = col_top[10].selectbox("Top Release Rebatteried", options=["", "Yes", "No"], index=0 if not default_top_release_rebatteried else (1 if default_top_release_rebatteried == "Yes" else 2), key=f"top_release_rebatteried{widget_key_suffix}", label_visibility="collapsed")

        # Bottom Release Row
        col_bottom = st.columns([1, 1, 1.5, 1, 1, 1, 1, 1, 1, 1.2, 1.2])
        col_bottom[0].write("Bottom")
        bottom_type = col_bottom[1].text_input("Bottom Release Type", value=default_bottom_release_type, key=f"bottom_release_type{widget_key_suffix}", label_visibility="collapsed")
        bottom_sn = col_bottom[2].text_input("Bottom Release S/N", value=default_bottom_release_sn, key=f"bottom_release_sn{widget_key_suffix}", label_visibility="collapsed")
        bottom_int_freq = col_bottom[3].text_input("Bottom Release Int. Freq.", value=default_bottom_release_int_freq, key=f"bottom_release_int_freq{widget_key_suffix}", label_visibility="collapsed")
        bottom_reply = col_bottom[4].text_input("Bottom Release Reply", value=default_bottom_release_reply, key=f"bottom_release_reply{widget_key_suffix}", label_visibility="collapsed")
        bottom_release = col_bottom[5].text_input("Bottom Release Release", value=default_bottom_release_release, key=f"bottom_release_release{widget_key_suffix}", label_visibility="collapsed")
        bottom_disable = col_bottom[6].text_input("Bottom Release Disable", value=default_bottom_release_disable, key=f"bottom_release_disable{widget_key_suffix}", label_visibility="collapsed")
        bottom_enable = col_bottom[7].text_input("Bottom Release Enable", value=default_bottom_release_enable, key=f"bottom_release_enable{widget_key_suffix}", label_visibility="collapsed")
        bottom_new = col_bottom[8].selectbox("Bottom Release New", options=["", "Yes", "No"], index=0 if not default_bottom_release_new else (1 if default_bottom_release_new == "Yes" else 2), key=f"bottom_release_new{widget_key_suffix}", label_visibility="collapsed")
        bottom_2nd_dep = col_bottom[9].selectbox("Bottom Release 2nd Dep", options=["", "Yes", "No"], index=0 if not default_bottom_release_2nd_dep else (1 if default_bottom_release_2nd_dep == "Yes" else 2), key=f"bottom_release_2nd_dep{widget_key_suffix}", label_visibility="collapsed")
        bottom_rebatteried = col_bottom[10].selectbox("Bottom Release Rebatteried", options=["", "Yes", "No"], index=0 if not default_bottom_release_rebatteried else (1 if default_bottom_release_rebatteried == "Yes" else 2), key=f"bottom_release_rebatteried{widget_key_suffix}", label_visibility="collapsed")

        st.markdown("---")

        # Anchor Drop and Fly By Section
        main_col1, divider_col, main_col2 = st.columns([5, 0.5, 5])

        with main_col1:
            st.subheader("Anchor Drop")

            # Create compact 2-column layout within left column
            anchor_left, anchor_right = st.columns(2)

            with anchor_left:
                st.write("**Date**")
                anchor_drop_date = st.text_input("Anchor Drop Date", value=default_anchor_drop_date, key=f"anchor_drop_date{widget_key_suffix}", label_visibility="collapsed")

                st.write("**Latitude**")
                anchor_drop_latitude = st.text_input("Anchor Drop Latitude", value=default_anchor_drop_latitude, key=f"anchor_drop_latitude{widget_key_suffix}", label_visibility="collapsed")

                st.write("**Depth**")
                anchor_drop_depth = st.text_input("Anchor Drop Depth", value=default_anchor_drop_depth, key=f"anchor_drop_depth{widget_key_suffix}", label_visibility="collapsed")

                st.write("**Depth Correction**")
                anchor_depth_correction = st.text_input("Anchor Depth Correction", value=default_anchor_depth_correction, key=f"anchor_depth_correction{widget_key_suffix}", label_visibility="collapsed")

            with anchor_right:
                st.write("**Time**")
                anchor_drop_time = st.text_input("Anchor Drop Time", value=default_anchor_drop_time, key=f"anchor_drop_time{widget_key_suffix}", label_visibility="collapsed")

                st.write("**Longitude**")
                anchor_drop_longitude = st.text_input("Anchor Drop Longitude", value=default_anchor_drop_longitude, key=f"anchor_drop_longitude{widget_key_suffix}", label_visibility="collapsed")

                st.write("**Anchor Weight**")
                anchor_weight = st.text_input("Anchor Weight", value=default_anchor_weight, key=f"anchor_weight{widget_key_suffix}", label_visibility="collapsed")

                st.write("**Corrected Depth**")
                anchor_corrected_depth = st.text_input("Anchor Corrected Depth", value=default_anchor_corrected_depth, key=f"anchor_corrected_depth{widget_key_suffix}", label_visibility="collapsed")

        with divider_col:
            st.markdown("""
            <div style="height: 400px; border-left: 2px solid #e0e0e0; margin: 20px 0;"></div>
            """, unsafe_allow_html=True)

        with main_col2:
            st.subheader("Fly By")

            # Create 2-column layout for Fly By
            flyby_left, flyby_right = st.columns(2)

            with flyby_left:
                st.write("**Latitude**")
                flyby_latitude = st.text_input("Flyby Latitude", value=default_flyby_latitude, key=f"flyby_latitude{widget_key_suffix}", label_visibility="collapsed")

                st.write("**Corrected Depth**")
                flyby_corrected_depth = st.text_input("Flyby Corrected Depth", value=default_flyby_corrected_depth, key=f"flyby_corrected_depth{widget_key_suffix}", label_visibility="collapsed")

            with flyby_right:
                st.write("**Longitude**")
                flyby_longitude = st.text_input("Flyby Longitude", value=default_flyby_longitude, key=f"flyby_longitude{widget_key_suffix}", label_visibility="collapsed")

                st.write("**Method Used**")
                flyby_method_options = ["", "fatho", "triangulated"]
                flyby_method_index = 0
                if default_flyby_method in flyby_method_options:
                    flyby_method_index = flyby_method_options.index(default_flyby_method)
                flyby_method = st.selectbox("Flyby Method", options=flyby_method_options, index=flyby_method_index, key=f"flyby_method{widget_key_suffix}", label_visibility="collapsed")

        st.markdown("---")

        # Historical Section - Add styled container
        st.markdown("""
        <style>
        .historical-container {
            border: 1px solid rgba(128, 128, 128, 0.3);
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            background-color: rgba(128, 128, 128, 0.05);
        }

        /* Dark mode adjustments */
        @media (prefers-color-scheme: dark) {
            .historical-container {
                border: 1px solid rgba(255, 255, 255, 0.2);
                background-color: rgba(255, 255, 255, 0.03);
            }
        }

        /* Streamlit dark theme detection */
        .stApp[data-theme="dark"] .historical-container {
            border: 1px solid rgba(255, 255, 255, 0.2);
            background-color: rgba(255, 255, 255, 0.03);
        }
        </style>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="historical-container">', unsafe_allow_html=True)
            st.subheader("Historical")

        # Row 1: ADCP Xducer Depth
        hist_row1 = st.columns([3, 2])
        with hist_row1[0]:
            st.write("**ADCP Xducer Depth (obtained by ball-set MTPR)**")
        with hist_row1[1]:
            adcp_xducer_depth = st.text_input("ADCP Xducer Depth", value=default_adcp_xducer_depth, key=f"adcp_xducer_depth{widget_key_suffix}", label_visibility="collapsed")

        # Row 2: Measured Distance
        hist_row2 = st.columns([3, 2])
        with hist_row2[0]:
            st.write("**Measured Distance - MTPR On Ball Set To ADCP Head**")
        with hist_row2[1]:
            measured_distance_mtpr = st.text_input("Measured Distance MTPR", value=default_measured_distance_mtpr, key=f"measured_distance_mtpr{widget_key_suffix}", label_visibility="collapsed")

        # Row 3: MTPR Turn on Time and Date
        hist_row3 = st.columns([3, 2])
        with hist_row3[0]:
            st.write("**MTPR Turn on Time and Date**")
        with hist_row3[1]:
            mtpr_turn_on_datetime = st.text_input("MTPR Turn on Time and Date", value=default_mtpr_turn_on_datetime, key=f"mtpr_turn_on_datetime{widget_key_suffix}", label_visibility="collapsed")

        # Row 4: Argos Beacon Deployment Usage
        hist_row4 = st.columns([3, 2])
        with hist_row4[0]:
            st.write("**Argos Beacon Deployment Usage (before new battery)**")
        with hist_row4[1]:
            argos_usage_options = ["", "1st", "2nd", "3rd", "none"]
            argos_usage_index = 0
            if default_argos_beacon_usage in argos_usage_options:
                argos_usage_index = argos_usage_options.index(default_argos_beacon_usage)
            argos_beacon_usage = st.selectbox("Argos Beacon Usage", options=argos_usage_options, index=argos_usage_index, key=f"argos_beacon_usage{widget_key_suffix}", label_visibility="collapsed")

        # Row 5: Hardware Length
        hist_row5 = st.columns([3, 2])
        with hist_row5[0]:
            st.write("**Hardware Length**")
        with hist_row5[1]:
            hardware_length = st.text_input("Hardware Length", value=default_hardware_length, key=f"hardware_length{widget_key_suffix}", label_visibility="collapsed")

        # Row 6: Kevlar Main Spool
        hist_row6 = st.columns([3, 2])
        with hist_row6[0]:
            st.write("**Kevlar Main Spool (stretched length)**")
        with hist_row6[1]:
            kevlar_main_spool = st.text_input("Kevlar Main Spool", value=default_kevlar_main_spool, key=f"kevlar_main_spool{widget_key_suffix}", label_visibility="collapsed")

        # Row 7: Additional Kevlar
        hist_row7 = st.columns([3, 2])
        with hist_row7[0]:
            st.write("**Additional Kevlar (stretched length)**")
        with hist_row7[1]:
            additional_kevlar = st.text_input("Additional Kevlar", value=default_additional_kevlar, key=f"additional_kevlar{widget_key_suffix}", label_visibility="collapsed")

        # Row 8: Total Kevlar Length - calculated field
        hist_row8 = st.columns([3, 2])
        with hist_row8[0]:
            st.write("**Total Kevlar Length**")
        with hist_row8[1]:
            # Calculate total kevlar length
            kevlar_main_val = safe_float_calc(kevlar_main_spool)
            additional_kevlar_val = safe_float_calc(additional_kevlar)
            calculated_total_kevlar = kevlar_main_val + additional_kevlar_val

            # Show calculated value
            if calculated_total_kevlar > 0:
                total_kevlar_display = f"{calculated_total_kevlar:.1f}"
            else:
                total_kevlar_display = default_total_kevlar_length

            total_kevlar_length = st.text_input("Total Kevlar Length", value=total_kevlar_display, key=f"total_kevlar_length{widget_key_suffix}", label_visibility="collapsed", disabled=True)

        # Row 9: Ball set Release Coordinates
        hist_row9 = st.columns([1, 1])
        with hist_row9[0]:
            st.write("**Ball set Rel. Lat.**")
            ball_set_rel_lat = st.text_input("Ball set Rel. Lat.", value=default_ball_set_rel_lat, key=f"ball_set_rel_lat{widget_key_suffix}", label_visibility="collapsed")
        with hist_row9[1]:
            st.write("**Ball set Rel. Lon.**")
            ball_set_rel_lon = st.text_input("Ball set Rel. Lon.", value=default_ball_set_rel_lon, key=f"ball_set_rel_lon{widget_key_suffix}", label_visibility="collapsed")

        # Ball-Set Release subsection
        st.markdown("##### Ball-Set Release")

        # Create table-like header row
        ball_release_header = st.columns([1.5, 1.5, 1.5, 1.5])
        with ball_release_header[0]:
            st.write("**Type**")
        with ball_release_header[1]:
            st.write("**Int. Freq**")
        with ball_release_header[2]:
            st.write("**Reply**")
        with ball_release_header[3]:
            st.write("**Release**")

        # First data row
        ball_release_row1 = st.columns([1.5, 1.5, 1.5, 1.5])
        with ball_release_row1[0]:
            ball_release_type = st.text_input("Ball Release Type", value=default_ball_release_type, key=f"ball_release_type{widget_key_suffix}", label_visibility="collapsed", disabled=True, placeholder="N/A")
        with ball_release_row1[1]:
            ball_release_int_freq = st.text_input("Ball Release Int. Freq", value=default_ball_release_int_freq, key=f"ball_release_int_freq{widget_key_suffix}", label_visibility="collapsed")
        with ball_release_row1[2]:
            ball_release_reply = st.text_input("Ball Release Reply", value=default_ball_release_reply, key=f"ball_release_reply{widget_key_suffix}", label_visibility="collapsed")
        with ball_release_row1[3]:
            ball_release_release = st.text_input("Ball Release Release", value=default_ball_release_release, key=f"ball_release_release{widget_key_suffix}", label_visibility="collapsed")

        # Second data row
        ball_release_row2 = st.columns([1.5, 1.5, 1.5, 1.5])
        with ball_release_row2[0]:
            st.write("**S/N**")
        with ball_release_row2[1]:
            st.write("")  # Empty cell
        with ball_release_row2[2]:
            st.write("")  # Empty cell
        with ball_release_row2[3]:
            st.write("**Disable**")

        # Third data row
        ball_release_row3 = st.columns([1.5, 1.5, 1.5, 1.5])
        with ball_release_row3[0]:
            ball_release_sn = st.text_input("Ball Release S/N", value=default_ball_release_sn, key=f"ball_release_sn{widget_key_suffix}", label_visibility="collapsed", disabled=True, placeholder="N/A")
        with ball_release_row3[1]:
            st.write("")  # Empty cell
        with ball_release_row3[2]:
            st.write("")  # Empty cell
        with ball_release_row3[3]:
            ball_release_disable = st.text_input("Ball Release Disable", value=default_ball_release_disable, key=f"ball_release_disable{widget_key_suffix}", label_visibility="collapsed")

        # Fourth data row
        ball_release_row4 = st.columns([1.5, 1.5, 1.5, 1.5])
        with ball_release_row4[0]:
            st.write("")  # Empty cell
        with ball_release_row4[1]:
            st.write("")  # Empty cell
        with ball_release_row4[2]:
            st.write("")  # Empty cell
        with ball_release_row4[3]:
            st.write("**Enable**")

        # Fifth data row
        ball_release_row5 = st.columns([1.5, 1.5, 1.5, 1.5])
        with ball_release_row5[0]:
            st.write("")  # Empty cell
        with ball_release_row5[1]:
            st.write("")  # Empty cell
        with ball_release_row5[2]:
            st.write("")  # Empty cell
        with ball_release_row5[3]:
            ball_release_enable = st.text_input("Ball Release Enable", value=default_ball_release_enable, key=f"ball_release_enable{widget_key_suffix}", label_visibility="collapsed")

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Comments Section
        st.subheader("Comments")
        comments = st.text_area("Comments", value=default_comments, height=600, key=f"comments{widget_key_suffix}", label_visibility="collapsed")

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
                'actual_nylon_cut': actual_nylon_cut,
                'intended_xducer_depth': req_adcp_head_depth,
                'target_bottom_depth': bottom_depth,
                'nylon_below_float_ball': nylon_below_float_ball,
                'nylon_below_release': nylon_below_release,
                'instrument_hardware_length': instrument_hardware_length,
                'anchor_drop_date': anchor_drop_date,
                'anchor_drop_time': anchor_drop_time,
                'anchor_drop_latitude': anchor_drop_latitude,
                'anchor_drop_longitude': anchor_drop_longitude,
                'anchor_drop_depth': anchor_drop_depth,
                'anchor_weight': anchor_weight,
                'anchor_depth_correction': anchor_depth_correction,
                'anchor_corrected_depth': anchor_corrected_depth,
                'flyby_latitude': flyby_latitude,
                'flyby_longitude': flyby_longitude,
                'flyby_corrected_depth': flyby_corrected_depth,
                'flyby_method': flyby_method,
                'top_type': top_type,
                'rel1_sn': top_sn,
                'btm_type': bottom_type,
                'rel2_sn': bottom_sn,
                'top_rel_new': top_new,
                'top_rel_2nd': top_2nd_dep,
                'top_rel_rebatt': top_rebatteried,
                'btm_rel_new': bottom_new,
                'btm_rel_2nd': bottom_2nd_dep,
                'btm_rel_rebatt': bottom_rebatteried,
                'rel8_toprelsn_cmd_1a_code_function_reply': top_release,
                'rel8_toprelsn_cmd_2b_code_function_reply': top_disable,
                'rel8_toprelsn_cmd_3c_code_function_reply': top_enable,
                'rel8_toprelsn_interrogate_freq': top_int_freq,
                'rel8_toprelsn_reply_freq': top_reply,
                'rel8_btmrelsn_cmd_1a_code_function_reply': bottom_release,
                'rel8_btmrelsn_cmd_2b_code_function_reply': bottom_disable,
                'rel8_btmrelsn_cmd_3c_code_function_reply': bottom_enable,
                'rel8_btmrelsn_interrogate_freq': bottom_int_freq,
                'rel8_btmrelsn_reply_freq': bottom_reply,
                'rel8_ballrelsn_cmd_1a_code_function_reply': ball_release_release,
                'rel8_ballrelsn_cmd_2b_code_function_reply': ball_release_disable,
                'rel8_ballrelsn_cmd_3c_code_function_reply': ball_release_enable,
                'rel8_ballrelsn_interrogate_freq': ball_release_int_freq,
                'rel8_ballrelsn_reply_freq': ball_release_reply,
                'adcp_xducer_depth': adcp_xducer_depth,
                'measured_distance_mtpr': measured_distance_mtpr,
                'mtpr_turn_on_datetime': mtpr_turn_on_datetime,
                'argos_beacon_usage': argos_beacon_usage,
                'historical_hardware_length': hardware_length,
                'kevlar_main_spool': kevlar_main_spool,
                'additional_kevlar': additional_kevlar,
                'total_kevlar_length': total_kevlar_length,
                'latitude': ball_set_rel_lat,
                'longitude': ball_set_rel_lon,
                'comments': comments
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
