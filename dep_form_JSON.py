import streamlit as st
import sqlite3
import pandas as pd
import json
from datetime import datetime, date, time
import os

# Database configuration
DB_PATH = os.path.expanduser("~/Apps/databases/Cruise_Logs.db")





def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn



def get_distinct_sites():
    """Get all distinct sites from the database."""
    conn = get_db_connection()
    try:
        query = "SELECT DISTINCT site FROM deployments_normalized WHERE site IS NOT NULL AND site != '' ORDER BY site"
        cursor = conn.cursor()
        cursor.execute(query)
        sites = [row[0] for row in cursor.fetchall()]
        return sites
    except Exception as e:
        print(f"Error fetching sites: {e}")
        return []
    finally:
        conn.close()

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

def get_spool_ev50(spool_sn):
    """Get the yes_flag (EV50) for a specific spool."""
    conn = get_db_connection()
    try:
        query = "SELECT yes_flag FROM spool_inventory WHERE serial_number = ?"
        cursor = conn.cursor()
        cursor.execute(query, [spool_sn])
        row = cursor.fetchone()
        if row:
            return row['yes_flag'] if row['yes_flag'] else ''
        return ''
    except Exception as e:
        print(f"Error getting EV50 flag: {e}")
        return ''
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

def find_release_in_deployments(release_sn):
    """Find where an acoustic release is used in deployments."""
    conn = get_db_connection()
    try:
        release_sn = str(release_sn).strip() if release_sn else ""

        if not release_sn:
            return []

        query = """
            SELECT id, mooringid, site, deployment_info, acoustic_releases, depth
            FROM deployments_normalized
            WHERE acoustic_releases IS NOT NULL
        """

        cursor = conn.cursor()
        cursor.execute(query)

        results = []
        for row in cursor.fetchall():
            try:
                # Parse the acoustic_releases JSON
                release_data = json.loads(row['acoustic_releases']) if row['acoustic_releases'] else {}

                # Parse deployment_info for date
                deployment_info = json.loads(row['deployment_info']) if row['deployment_info'] else {}
                dep_date = deployment_info.get('dep_date', '')

                # Check each release in the acoustic_releases data
                for release_key, release_info in release_data.items():
                    if isinstance(release_info, dict) and release_info.get('sn', '').strip().upper() == release_sn.upper():
                        results.append({
                            'mooringid': row['mooringid'],
                            'site': row['site'],
                            'dep_date': dep_date,
                            'depth': row['depth'],
                            'position': release_key.replace('_', ' '),
                            'type': release_info.get('type', ''),
                            'int_freq': release_info.get('int_freq', ''),
                            'reply_freq': release_info.get('reply_freq', ''),
                            'release': release_info.get('release', ''),
                            'disable': release_info.get('disable', ''),
                            'enable': release_info.get('enable', '')
                        })
            except json.JSONDecodeError:
                continue

        # Sort by date (most recent first)
        results.sort(key=lambda x: x['dep_date'], reverse=True)
        return results
    except Exception as e:
        print(f"Error finding release in deployments: {e}")
        return []
    finally:
        conn.close()

def get_all_release_serials():
    """Get all unique acoustic release serial numbers from deployments."""
    conn = get_db_connection()
    try:
        query = """
            SELECT acoustic_releases FROM deployments_normalized
            WHERE acoustic_releases IS NOT NULL
        """
        cursor = conn.cursor()
        cursor.execute(query)

        serials = set()
        for row in cursor.fetchall():
            try:
                release_data = json.loads(row[0]) if row[0] else {}
                for release_info in release_data.values():
                    if isinstance(release_info, dict) and release_info.get('sn'):
                        serials.add(release_info['sn'])
            except json.JSONDecodeError:
                continue

        return sorted(list(serials))
    except Exception as e:
        print(f"Error fetching release serials: {e}")
        return []
    finally:
        conn.close()

def search_releases_advanced(serial_pattern=None, type_pattern=None, int_freq=None, reply_freq=None):
    """Search acoustic releases based on multiple criteria."""
    conn = get_db_connection()
    try:
        query = """
            SELECT acoustic_releases FROM deployments_normalized
            WHERE acoustic_releases IS NOT NULL
        """
        cursor = conn.cursor()
        cursor.execute(query)

        results = []
        processed_serials = set()  # To avoid duplicates

        for row in cursor.fetchall():
            try:
                release_data = json.loads(row[0]) if row[0] else {}
                for release_key, release_info in release_data.items():
                    if isinstance(release_info, dict):
                        serial = release_info.get('sn', '')
                        type_val = release_info.get('type', '')
                        int_freq_val = release_info.get('int_freq', '')
                        reply_freq_val = release_info.get('reply_freq', '')

                        # Apply filters
                        if serial_pattern and serial_pattern.lower() not in serial.lower():
                            continue
                        if type_pattern and type_pattern.lower() not in type_val.lower():
                            continue
                        if int_freq and int_freq not in str(int_freq_val):
                            continue
                        if reply_freq and reply_freq not in str(reply_freq_val):
                            continue

                        # Avoid duplicates
                        if serial in processed_serials:
                            continue
                        processed_serials.add(serial)

                        results.append({
                            'serial': serial,
                            'type': type_val,
                            'int_freq': int_freq_val,
                            'reply_freq': reply_freq_val,
                            'release': release_info.get('release', ''),
                            'disable': release_info.get('disable', ''),
                            'enable': release_info.get('enable', ''),
                            'position': release_key.replace('_', ' ')
                        })
            except json.JSONDecodeError:
                continue

        return results
    except Exception as e:
        print(f"Error searching releases: {e}")
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

def load_deployment_data(deployment_id=None):
    """Load deployment data from database."""
    conn = get_db_connection()
    if deployment_id:
        query = "SELECT * FROM deployments_normalized WHERE id = ?"
        df = pd.read_sql_query(query, conn, params=[deployment_id])
    else:
        # Return empty dataframe with column names for new entry
        query = "SELECT * FROM deployments_normalized LIMIT 0"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def search_deployments(search_criteria):
    """Search deployments based on criteria."""
    conn = get_db_connection()

    # Build WHERE clause dynamically
    where_clauses = []
    params = []

    if search_criteria.get('site'):
        where_clauses.append("site LIKE ?")
        params.append(f"%{search_criteria['site']}%")

    if search_criteria.get('mooringid'):
        where_clauses.append("mooringid LIKE ?")
        params.append(f"%{search_criteria['mooringid']}%")

    if search_criteria.get('cruise'):
        where_clauses.append("cruise LIKE ?")
        params.append(f"%{search_criteria['cruise']}%")

    # Personnel search in JSON deployment_info
    if search_criteria.get('personnel'):
        where_clauses.append("deployment_info LIKE ?")
        params.append(f"%{search_criteria['personnel']}%")

    # Check if created_at column exists
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(deployments_normalized)")
    columns = [col[1] for col in cursor.fetchall()]

    # Choose ordering column based on what's available
    if 'created_at' in columns:
        order_by = "ORDER BY created_at DESC"
    elif 'updated_at' in columns:
        order_by = "ORDER BY updated_at DESC"
    elif 'id' in columns:
        order_by = "ORDER BY id DESC"
    else:
        order_by = ""

    # Construct query
    if where_clauses:
        query = f"SELECT * FROM deployments_normalized WHERE {' AND '.join(where_clauses)} {order_by}"
        df = pd.read_sql_query(query, conn, params=params, index_col=None, parse_dates=False)
    else:
        query = f"SELECT * FROM deployments_normalized {order_by} LIMIT 100"
        df = pd.read_sql_query(query, conn, index_col=None, parse_dates=False)

    conn.close()
    return df

def parse_json_field(json_str):
    """Safely parse JSON field, return empty dict if invalid."""
    try:
        return json.loads(json_str) if json_str else {}
    except (json.JSONDecodeError, TypeError):
        return {}

def update_deployment_data(deployment_id, form_data):
    """Update existing deployment data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Prepare data for update (table existence will be checked by SQL execution)

        # Prepare JSON data structures
        deployment_info = {
            'dep_date': form_data.get('dep_date', ''),
            'deployment_start_time': form_data.get('deployment_start_time', ''),
            'personnel': form_data.get('personnel', ''),
            'mooring_type': form_data.get('mooring_type', ''),
            'comments': form_data.get('deployment_comments', '')
        }

        met_sensors = {
            'atrh': {
                'type': form_data.get('atrh_type', ''),
                'serial': form_data.get('atrh_serial', '')
            },
            'rain': {
                'type': form_data.get('rain_type', ''),
                'serial': form_data.get('rain_serial', '')
            },
            'sw_radiation': {
                'type': form_data.get('sw_radiation_type', ''),
                'serial': form_data.get('sw_radiation_serial', '')
            },
            'lw_radiation': {
                'type': form_data.get('lw_radiation_type', ''),
                'serial': form_data.get('lw_radiation_serial', '')
            },
            'barometer': {
                'type': form_data.get('barometer_type', ''),
                'serial': form_data.get('barometer_serial', '')
            },
            'wind': {
                'type': form_data.get('wind_type', ''),
                'serial': form_data.get('wind_serial', '')
            }
        }

        hardware = {
            'buoy_sn': form_data.get('buoy_sn', ''),
            'insert': form_data.get('insert', ''),
            'anti_theft_cage': form_data.get('anti_theft_cage', ''),
            'fairing_depth': form_data.get('fairing_depth', ''),
            'teacup_handle': form_data.get('teacup_handle', ''),
            'tube_sn': form_data.get('tube_sn', ''),
            'ptt_hexid': form_data.get('ptt_hexid', ''),
            'time_zone': form_data.get('time_zone', ''),
            'software_ver': form_data.get('software_ver', '')
        }

        # Nylon spools
        nylon_spools = {}
        for i in range(1, 11):
            sn = form_data.get(f'spool_{i}_sn', '')
            if sn:  # Only include non-empty spools
                nylon_spools[f'spool_{i}'] = {
                    'sn': sn,
                    'length': form_data.get(f'spool_{i}_length', ''),
                    'ev50': form_data.get(f'spool_{i}_ev50', '')
                }

        # Nylon configuration
        nylon_config = {
            'nylon_below_release': form_data.get('nylon_below_release', ''),
            'wiresn': form_data.get('wire_sn', ''),
            'hardware_length': form_data.get('hardware_length', ''),
            'wire_ln': form_data.get('wire_length', ''),
            'projected_scope': form_data.get('projected_scope', ''),
            'wire_age': form_data.get('wire_dep_number', ''),
            'topsecsn': form_data.get('top_section_sn', ''),
            'top_sec_usage': form_data.get('top_section_usage', '')
        }

        # Subsurface sensors
        subsurface_sensors = []
        if 'subsurface_sensors' in form_data:
            for sensor in form_data['subsurface_sensors']:
                if any(sensor.get(key, '') for key in ['type', 'sn', 'depth']):  # Only include non-empty sensors
                    subsurface_sensors.append({
                        'depth': sensor.get('depth', ''),
                        'type': sensor.get('type', ''),
                        'address': sensor.get('address', ''),
                        'sn': sensor.get('sn', ''),
                        'time_in': sensor.get('time_in', ''),
                        'comments': sensor.get('comments', '')
                    })

        # Acoustic releases
        acoustic_releases = {}
        if form_data.get('release1_sn'):
            acoustic_releases['release_1'] = {
                'type': form_data.get('release1_type', ''),
                'sn': form_data.get('release1_sn', ''),
                'int_freq': form_data.get('release1_int_freq', ''),
                'reply_freq': form_data.get('release1_reply_freq', ''),
                'release': form_data.get('release1_release', ''),
                'disable': form_data.get('release1_disable', ''),
                'enable': form_data.get('release1_enable', '')
            }
        if form_data.get('release2_sn'):
            acoustic_releases['release_2'] = {
                'type': form_data.get('release2_type', ''),
                'sn': form_data.get('release2_sn', ''),
                'int_freq': form_data.get('release2_int_freq', ''),
                'reply_freq': form_data.get('release2_reply_freq', ''),
                'release': form_data.get('release2_release', ''),
                'disable': form_data.get('release2_disable', ''),
                'enable': form_data.get('release2_enable', '')
            }

        # Anchor drop data
        anchor_drop = {
            'date': form_data.get('anchor_date', ''),
            'time': form_data.get('anchor_time', ''),
            'latitude': form_data.get('anchor_latitude', ''),
            'longitude': form_data.get('anchor_longitude', ''),
            'tow_time': form_data.get('anchor_tow_time', ''),
            'tow_distance': form_data.get('anchor_tow_distance', ''),
            'total_time': form_data.get('anchor_total_time', ''),
            'weight': form_data.get('anchor_weight', '')
        }

        # Met observations
        met_obs = {
            'ship': {
                'date': form_data.get('ship_date', ''),
                'time': form_data.get('ship_time', ''),
                'wind_dir': form_data.get('ship_wind_dir', ''),
                'wind_spd': form_data.get('ship_wind_spd', ''),
                'air_temp': form_data.get('ship_air_temp', ''),
                'sst': form_data.get('ship_sst', ''),
                'ssc': form_data.get('ship_ssc', ''),
                'rh': form_data.get('ship_rh', '')
            },
            'buoy': {
                'date': form_data.get('buoy_date', ''),
                'time': form_data.get('buoy_time', ''),
                'wind_dir': form_data.get('buoy_wind_dir', ''),
                'wind_spd': form_data.get('buoy_wind_spd', ''),
                'air_temp': form_data.get('buoy_air_temp', ''),
                'sst': form_data.get('buoy_sst', ''),
                'ssc': form_data.get('buoy_ssc', ''),
                'rh': form_data.get('buoy_rh', '')
            }
        }

        # Flyby data
        flyby = {
            'buoy_latitude': form_data.get('flyby_buoy_latitude', ''),
            'buoy_longitude': form_data.get('flyby_buoy_longitude', ''),
            'anchor_latitude': form_data.get('flyby_anchor_latitude', ''),
            'anchor_longitude': form_data.get('flyby_anchor_longitude', ''),
            'uncorrected_depth': form_data.get('flyby_uncorrected_depth', ''),
            'depth_correction': form_data.get('flyby_depth_correction', ''),
            'transducer_depth': form_data.get('flyby_transducer_depth', ''),
            'corrected_depth': form_data.get('flyby_corrected_depth', ''),
            'final_scope': form_data.get('flyby_final_scope', '')
        }

        # Verify deployment exists before update
        cursor.execute("SELECT id FROM deployments_normalized WHERE id = ?", [deployment_id])
        if not cursor.fetchone():
            return False, f"Record with ID {deployment_id} not found in database."

        # Build UPDATE query
        query = """
            UPDATE deployments_normalized SET
                site = ?, mooringid = ?, cruise = ?,
                latitude = ?, longitude = ?, depth = ?,
                deployment_info = ?, met_sensors = ?, hardware = ?,
                nylon_spools = ?, nylon_config = ?, subsurface_sensors = ?,
                acoustic_releases = ?, anchor_drop = ?, met_obs = ?, flyby = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        values = [
            form_data.get('site', ''),
            form_data.get('mooringid', ''),
            form_data.get('cruise', ''),
            form_data.get('anchor_drp_lat', ''),  # Now buoy latitude from flyby
            form_data.get('anchor_drp_long', ''),  # Now buoy longitude from flyby
            form_data.get('depth', ''),
            json.dumps(deployment_info),
            json.dumps(met_sensors),
            json.dumps(hardware),
            json.dumps(nylon_spools),
            json.dumps(nylon_config),
            json.dumps(subsurface_sensors),
            json.dumps(acoustic_releases),
            json.dumps(anchor_drop),
            json.dumps(met_obs),
            json.dumps(flyby),
            deployment_id
        ]

        rows_affected = cursor.execute(query, values).rowcount
        if rows_affected == 0:
            conn.rollback()
            return False, f"No rows updated. Record with ID {deployment_id} may not exist."
        elif rows_affected > 1:
            conn.rollback()
            return False, f"Error: Multiple rows ({rows_affected}) would be affected. Update aborted."

        conn.commit()
        return True, {'id': deployment_id, 'dep_date': deployment_info.get('dep_date'), 'mooringid': form_data.get('mooringid')}

    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()

def save_deployment_data(form_data):
    """Save deployment data to database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Prepare JSON data structures (same as in update_deployment_data)
        deployment_info = {
            'dep_date': form_data.get('dep_date', ''),
            'deployment_start_time': form_data.get('deployment_start_time', ''),
            'personnel': form_data.get('personnel', ''),
            'mooring_type': form_data.get('mooring_type', ''),
            'comments': form_data.get('deployment_comments', '')
        }

        met_sensors = {
            'atrh': {
                'type': form_data.get('atrh_type', ''),
                'serial': form_data.get('atrh_serial', '')
            },
            'rain': {
                'type': form_data.get('rain_type', ''),
                'serial': form_data.get('rain_serial', '')
            },
            'sw_radiation': {
                'type': form_data.get('sw_radiation_type', ''),
                'serial': form_data.get('sw_radiation_serial', '')
            },
            'lw_radiation': {
                'type': form_data.get('lw_radiation_type', ''),
                'serial': form_data.get('lw_radiation_serial', '')
            },
            'barometer': {
                'type': form_data.get('barometer_type', ''),
                'serial': form_data.get('barometer_serial', '')
            },
            'wind': {
                'type': form_data.get('wind_type', ''),
                'serial': form_data.get('wind_serial', '')
            }
        }

        hardware = {
            'buoy_sn': form_data.get('buoy_sn', ''),
            'insert': form_data.get('insert', ''),
            'anti_theft_cage': form_data.get('anti_theft_cage', ''),
            'fairing_depth': form_data.get('fairing_depth', ''),
            'teacup_handle': form_data.get('teacup_handle', ''),
            'tube_sn': form_data.get('tube_sn', ''),
            'ptt_hexid': form_data.get('ptt_hexid', ''),
            'time_zone': form_data.get('time_zone', ''),
            'software_ver': form_data.get('software_ver', '')
        }

        # Nylon spools
        nylon_spools = {}
        for i in range(1, 11):
            sn = form_data.get(f'spool_{i}_sn', '')
            if sn:  # Only include non-empty spools
                nylon_spools[f'spool_{i}'] = {
                    'sn': sn,
                    'length': form_data.get(f'spool_{i}_length', ''),
                    'ev50': form_data.get(f'spool_{i}_ev50', '')
                }

        # Nylon configuration
        nylon_config = {
            'nylon_below_release': form_data.get('nylon_below_release', ''),
            'wiresn': form_data.get('wire_sn', ''),
            'hardware_length': form_data.get('hardware_length', ''),
            'wire_ln': form_data.get('wire_length', ''),
            'projected_scope': form_data.get('projected_scope', ''),
            'wire_age': form_data.get('wire_dep_number', ''),
            'topsecsn': form_data.get('top_section_sn', ''),
            'top_sec_usage': form_data.get('top_section_usage', '')
        }

        # Subsurface sensors
        subsurface_sensors = []
        if 'subsurface_sensors' in form_data:
            for sensor in form_data['subsurface_sensors']:
                if any(sensor.get(key, '') for key in ['type', 'sn', 'depth']):  # Only include non-empty sensors
                    subsurface_sensors.append({
                        'depth': sensor.get('depth', ''),
                        'type': sensor.get('type', ''),
                        'address': sensor.get('address', ''),
                        'sn': sensor.get('sn', ''),
                        'time_in': sensor.get('time_in', ''),
                        'comments': sensor.get('comments', '')
                    })

        # Acoustic releases
        acoustic_releases = {}
        if form_data.get('release1_sn'):
            acoustic_releases['release_1'] = {
                'type': form_data.get('release1_type', ''),
                'sn': form_data.get('release1_sn', ''),
                'int_freq': form_data.get('release1_int_freq', ''),
                'reply_freq': form_data.get('release1_reply_freq', ''),
                'release': form_data.get('release1_release', ''),
                'disable': form_data.get('release1_disable', ''),
                'enable': form_data.get('release1_enable', '')
            }
        if form_data.get('release2_sn'):
            acoustic_releases['release_2'] = {
                'type': form_data.get('release2_type', ''),
                'sn': form_data.get('release2_sn', ''),
                'int_freq': form_data.get('release2_int_freq', ''),
                'reply_freq': form_data.get('release2_reply_freq', ''),
                'release': form_data.get('release2_release', ''),
                'disable': form_data.get('release2_disable', ''),
                'enable': form_data.get('release2_enable', '')
            }

        # Anchor drop data
        anchor_drop = {
            'date': form_data.get('anchor_date', ''),
            'time': form_data.get('anchor_time', ''),
            'latitude': form_data.get('anchor_latitude', ''),
            'longitude': form_data.get('anchor_longitude', ''),
            'tow_time': form_data.get('anchor_tow_time', ''),
            'tow_distance': form_data.get('anchor_tow_distance', ''),
            'total_time': form_data.get('anchor_total_time', ''),
            'weight': form_data.get('anchor_weight', '')
        }

        # Met observations
        met_obs = {
            'ship': {
                'date': form_data.get('ship_date', ''),
                'time': form_data.get('ship_time', ''),
                'wind_dir': form_data.get('ship_wind_dir', ''),
                'wind_spd': form_data.get('ship_wind_spd', ''),
                'air_temp': form_data.get('ship_air_temp', ''),
                'sst': form_data.get('ship_sst', ''),
                'ssc': form_data.get('ship_ssc', ''),
                'rh': form_data.get('ship_rh', '')
            },
            'buoy': {
                'date': form_data.get('buoy_date', ''),
                'time': form_data.get('buoy_time', ''),
                'wind_dir': form_data.get('buoy_wind_dir', ''),
                'wind_spd': form_data.get('buoy_wind_spd', ''),
                'air_temp': form_data.get('buoy_air_temp', ''),
                'sst': form_data.get('buoy_sst', ''),
                'ssc': form_data.get('buoy_ssc', ''),
                'rh': form_data.get('buoy_rh', '')
            }
        }

        # Flyby data
        flyby = {
            'buoy_latitude': form_data.get('flyby_buoy_latitude', ''),
            'buoy_longitude': form_data.get('flyby_buoy_longitude', ''),
            'anchor_latitude': form_data.get('flyby_anchor_latitude', ''),
            'anchor_longitude': form_data.get('flyby_anchor_longitude', ''),
            'uncorrected_depth': form_data.get('flyby_uncorrected_depth', ''),
            'depth_correction': form_data.get('flyby_depth_correction', ''),
            'transducer_depth': form_data.get('flyby_transducer_depth', ''),
            'corrected_depth': form_data.get('flyby_corrected_depth', ''),
            'final_scope': form_data.get('flyby_final_scope', '')
        }

        # Build INSERT query
        query = """
            INSERT INTO deployments_normalized (
                site, mooringid, cruise, latitude, longitude, depth,
                deployment_info, met_sensors, hardware, nylon_spools,
                nylon_config, subsurface_sensors, acoustic_releases,
                anchor_drop, met_obs, flyby, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """

        values = [
            form_data.get('site', ''),
            form_data.get('mooringid', ''),
            form_data.get('cruise', ''),
            form_data.get('anchor_drp_lat', ''),  # Now buoy latitude from flyby
            form_data.get('anchor_drp_long', ''),  # Now buoy longitude from flyby
            form_data.get('depth', ''),
            json.dumps(deployment_info),
            json.dumps(met_sensors),
            json.dumps(hardware),
            json.dumps(nylon_spools),
            json.dumps(nylon_config),
            json.dumps(subsurface_sensors),
            json.dumps(acoustic_releases),
            json.dumps(anchor_drop),
            json.dumps(met_obs),
            json.dumps(flyby)
        ]

        cursor.execute(query, values)
        conn.commit()
        deployment_id = cursor.lastrowid
        return True, deployment_id

    except sqlite3.IntegrityError as e:
        conn.rollback()
        return False, f"Data integrity error: {str(e)}"
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()

def main():
    """Main Streamlit application function."""
    # Import datetime components at function level to ensure availability
    from datetime import datetime, date, time

    # Page configuration
    st.set_page_config(
        page_title="GTMBA Deployment Log (JSON)",
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
    st.title("GTMBA Deployment Log (JSON Normalized)")

    # Database table will be checked during first search operation

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
    if 'subsurface_sensors' not in st.session_state:
        st.session_state.subsurface_sensors = []
    if 'num_subsurface_sensors' not in st.session_state:
        st.session_state.num_subsurface_sensors = 15

    # Mode selection and debugging
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        mode = st.radio("Mode", ["Search/Edit", "Add New"], key="mode_selector")
        st.session_state.mode = mode

    with col3:
        # Debug dropdown
        debug_option = st.selectbox(
            "🐛 Debug Tools",
            ["None", "Show DB Info", "Show Session State", "Show Search Results", "Test DB Connection", "Show Form Data", "Show Subsurface Sensors", "Show Available Fields", "Show Field Mapping"],
            key="debug_selector"
        )

        # Handle debug actions
        if debug_option != "None":
            st.expander_debug = st.expander(f"Debug: {debug_option}", expanded=True)
            with st.expander_debug:
                if debug_option == "Show DB Info":
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM deployments_normalized")
                        count = cursor.fetchone()[0]
                        st.write(f"**Total records:** {count}")

                        cursor.execute("PRAGMA table_info(deployments_normalized)")
                        columns = cursor.fetchall()
                        st.write("**Table columns:**")
                        for col in columns:
                            st.write(f"- {col[1]} ({col[2]})")
                        conn.close()
                    except Exception as e:
                        st.error(f"Database error: {e}")

                elif debug_option == "Show Session State":
                    st.json(dict(st.session_state))

                elif debug_option == "Show Search Results":
                    if st.session_state.search_results is not None:
                        st.write(f"**Search results shape:** {st.session_state.search_results.shape}")
                        st.dataframe(st.session_state.search_results)
                    else:
                        st.write("No search results available")

                elif debug_option == "Test DB Connection":
                    try:
                        conn = get_db_connection()
                        st.success("✅ Database connection successful")
                        cursor = conn.cursor()
                        cursor.execute("SELECT site, mooringid, cruise FROM deployments_normalized LIMIT 5")
                        sample_data = cursor.fetchall()
                        st.write("**Sample records:**")
                        for row in sample_data:
                            st.write(f"- Site: {row[0]}, Mooring: {row[1]}, Cruise: {row[2]}")
                        conn.close()
                    except Exception as e:
                        st.error(f"❌ Database connection failed: {e}")

                elif debug_option == "Show Form Data":
                    if st.session_state.form_data:
                        st.json(st.session_state.form_data)
                    else:
                        st.write("No form data available")

                elif debug_option == "Show Subsurface Sensors":
                    if hasattr(st.session_state, 'subsurface_sensors') and st.session_state.subsurface_sensors:
                        st.write(f"**Found {len(st.session_state.subsurface_sensors)} subsurface sensors:**")
                        for i, sensor in enumerate(st.session_state.subsurface_sensors):
                            if any(sensor.values()):  # Only show sensors with data
                                st.write(f"**Sensor {i+1}:**")
                                st.json(sensor)
                    else:
                        st.write("No subsurface sensors in session state")

                    # Also show current selected deployment subsurface data
                    if st.session_state.selected_deployment:
                        subsurface_raw = st.session_state.selected_deployment.get('subsurface_sensors', '')
                        st.write("**Raw subsurface JSON from database:**")
                        st.code(subsurface_raw)

                        try:
                            parsed = parse_json_field(subsurface_raw)
                            st.write("**Parsed subsurface data:**")
                            st.json(parsed)
                        except Exception as e:
                            st.error(f"Error parsing: {e}")

                elif debug_option == "Show Available Fields":
                    if st.session_state.selected_deployment:
                        st.write("**All available fields from current record:**")

                        # Show core fields
                        st.write("**Core Fields:**")
                        core_fields = ['id', 'site', 'mooringid', 'cruise', 'latitude', 'longitude', 'depth']
                        for field in core_fields:
                            value = st.session_state.selected_deployment.get(field, 'N/A')
                            st.write(f"  • {field}: {value}")

                        # Show JSON fields and their parsed contents
                        json_fields = ['deployment_info', 'met_sensors', 'hardware', 'nylon_spools',
                                     'nylon_config', 'subsurface_sensors', 'acoustic_releases',
                                     'anchor_drop', 'met_obs', 'flyby']

                        for json_field in json_fields:
                            st.write(f"**{json_field.upper()} JSON Field:**")
                            raw_data = st.session_state.selected_deployment.get(json_field, '{}')

                            try:
                                parsed_data = parse_json_field(raw_data)
                                if isinstance(parsed_data, dict):
                                    if parsed_data:  # Not empty
                                        for key, value in parsed_data.items():
                                            st.write(f"  • {key}: {value}")
                                    else:
                                        st.write("  (empty)")
                                elif isinstance(parsed_data, list):
                                    st.write(f"  Array with {len(parsed_data)} items")
                                    for i, item in enumerate(parsed_data[:3]):  # Show first 3 items
                                        if isinstance(item, dict):
                                            st.write(f"    Item {i+1}: {list(item.keys())}")
                                        else:
                                            st.write(f"    Item {i+1}: {item}")
                                    if len(parsed_data) > 3:
                                        st.write(f"    ... and {len(parsed_data) - 3} more items")
                            except Exception as e:
                                st.error(f"  Error parsing {json_field}: {e}")
                                st.code(raw_data)
                    else:
                        st.write("No deployment selected. Please search and select a record first.")

                elif debug_option == "Show Field Mapping":
                    if st.session_state.selected_deployment:
                        st.write("**Field Mapping Analysis:**")

                        # Check nylon_config fields
                        st.write("**NYLON_CONFIG Fields:**")
                        nylon_config_raw = st.session_state.selected_deployment.get('nylon_config', '{}')
                        nylon_config = parse_json_field(nylon_config_raw)

                        expected_nylon_fields = {
                            'wire_sn': 'Wire S/N',
                            'wire_length': 'Wire Length',
                            'wire_ln': 'Wire Length (alt)',
                            'hardware_length': 'Hardware Length',
                            'nylon_below_release': 'Nylon Below Release',
                            'projected_scope': 'Projected Scope',
                            'wire_dep_number': 'Wire Deployment Number',
                            'top_section_sn': 'Top Section S/N',
                            'top_section_usage': 'Top Section Usage'
                        }

                        for field, description in expected_nylon_fields.items():
                            value = nylon_config.get(field, 'NOT FOUND')
                            status = "✅" if value != 'NOT FOUND' else "❌"
                            st.write(f"  {status} {description} ({field}): {value}")

                        st.write("\n**Available nylon_config keys:**")
                        if nylon_config:
                            for key in nylon_config.keys():
                                st.write(f"  • {key}")
                        else:
                            st.write("  (nylon_config is empty)")

                        # Check original flat table for wire length data
                        st.write("\n**Checking Original Database for Wire Length:**")
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            mooringid = st.session_state.selected_deployment.get('mooringid', '')
                            cursor.execute("SELECT wire_ln, wiresn FROM deployments WHERE mooringid = ?", (mooringid,))
                            original_data = cursor.fetchone()
                            if original_data:
                                st.write(f"  • wire_ln: {original_data[0]}")
                                st.write(f"  • wiresn: {original_data[1]}")
                            else:
                                st.write("  No original data found")
                            conn.close()
                        except Exception as e:
                            st.error(f"Error checking original data: {e}")
                    else:
                        st.write("No deployment selected. Please search and select a record first.")

        # Clear subsurface sensors when switching to Add New mode
        if mode == "Add New" and st.session_state.subsurface_sensors:
            st.session_state.subsurface_sensors = []

    # Sidebar with comprehensive spool and release lookup
    if mode in ["Add New", "Search/Edit"]:
        with st.sidebar:
            st.subheader("🔍 Nylon Spool Lookup")
            st.write("Look up spool information while entering data")

            # Tab selection for different search modes
            tab1, tab2, tab3 = st.tabs(["Quick Lookup", "Advanced Search", "Deployment History"])

            with tab1:
                lookup_sn = st.text_input("Enter Spool S/N:", key="sidebar_lookup_sn")
                lookup_button = st.button("Look Up", key="sidebar_lookup_button")

                if lookup_button and lookup_sn:
                    spool_info = get_spool_info(lookup_sn)
                    if spool_info:
                        st.success(f"✅ Found: {spool_info['serial']}")
                        st.write(f"**Length:** {spool_info['length']}m")
                        st.write(f"**Status:** {spool_info['status']}")
                        if spool_info['ev50']:
                            st.write(f"**EV50:** {spool_info['ev50']}")
                        if spool_info['notes']:
                            st.write(f"**Notes:** {spool_info['notes']}")
                        if spool_info['year'] != 'Unknown':
                            st.write(f"**Year:** {spool_info['year']}")
                    else:
                        st.error(f"❌ Spool {lookup_sn} not found")

                    # Also check deployments table
                    st.write("---")
                    st.write("**Deployment History:**")
                    deployments = find_spool_in_deployments(lookup_sn)
                    if deployments:
                        # Show deployment summary
                        depths = []
                        for d in deployments:
                            if d['depth']:
                                try:
                                    depth_val = float(d['depth'])
                                    depths.append(depth_val)
                                except (ValueError, TypeError):
                                    pass

                        if depths:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Deployments", len(deployments))
                                st.metric("Depth Range", f"{min(depths):.0f}-{max(depths):.0f}m")
                            with col2:
                                st.metric("Avg Depth", f"{sum(depths)/len(depths):.0f}m")
                                # Count deployments by depth range
                                shallow = len([d for d in depths if d < 1000])
                                deep = len([d for d in depths if d >= 1000])
                                st.metric("Shallow/Deep", f"{shallow}/{deep}")
                        else:
                            st.info(f"Found {len(deployments)} deployment(s) - no depth data")

                        st.write("**Recent Deployments:**")
                        for dep in deployments[:10]:  # Show more deployments
                            depth_str = f"{dep['depth']}m" if dep['depth'] else "N/A"
                            length_str = f"{dep['length']}m" if dep['length'] else "N/A"
                            st.write(f"• **{dep['mooringid']}**")
                            st.write(f"  - Date: {dep['dep_date']}")
                            st.write(f"  - Depth: {depth_str}")
                            st.write(f"  - Length Used: {length_str}")
                            st.write(f"  - Position: {dep['position']}")
                            if dep['site']:
                                st.write(f"  - Site: {dep['site']}")
                            st.write("")  # Add spacing between entries
                        if len(deployments) > 10:
                            st.write(f"... and {len(deployments) - 10} more deployments")
                    else:
                        st.write("No deployment history")

            with tab2:
                st.write("**Search by criteria:**")

                search_serial = st.text_input("S/N contains:", key="sidebar_search_serial")

                col1, col2 = st.columns(2)
                with col1:
                    min_length = st.number_input("Min Length:", min_value=0, max_value=1000, value=0, key="sidebar_min_length")
                with col2:
                    max_length = st.number_input("Max Length:", min_value=0, max_value=1000, value=1000, key="sidebar_max_length")

                status_options = ["All", "Active", "Retired", "Lost at Sea", "Sent Away", "Cut/Modified"]
                search_status = st.selectbox("Status:", options=status_options, key="sidebar_search_status")

                search_year = st.text_input("Year:", key="sidebar_search_year")
                search_ev50 = st.text_input("EV50:", key="sidebar_search_ev50")

                if st.button("Search", key="sidebar_advanced_search"):
                    results = search_spools_advanced(
                        serial_pattern=search_serial if search_serial else None,
                        min_length=min_length if min_length > 0 else None,
                        max_length=max_length if max_length < 1000 else None,
                        status=search_status if search_status != "All" else None,
                        year=search_year if search_year else None,
                        notes_pattern=None,
                        ev50=search_ev50 if search_ev50 else None
                    )

                    if results:
                        st.success(f"Found {len(results)} spool(s)")

                        # Show compact results in sidebar
                        for spool in results[:10]:  # Limit to 10 results
                            st.write(f"**{spool['serial']}** - {spool['length']}m")
                            if spool['ev50']:
                                st.write(f"  EV50: {spool['ev50']}")
                            if spool['status']:
                                st.write(f"  Status: {spool['status']}")

                            # Check deployment history for this spool
                            deps = find_spool_in_deployments(spool['serial'])
                            if deps:
                                st.write(f"  Deployed {len(deps)} time(s)")
                                latest = deps[0]  # Most recent deployment
                                st.write(f"  Last: {latest['mooringid']} @ {latest['depth']}m" if latest['depth'] else f"  Last: {latest['mooringid']}")

                            st.write("---")

                        if len(results) > 10:
                            st.write(f"... and {len(results) - 10} more results")
                    else:
                        st.warning("No spools found")

            with tab3:
                st.write("**View detailed deployment history**")

                # Dropdown to select spool
                all_spools = get_all_spool_serials()
                history_spool = st.selectbox(
                    "Select Spool S/N:",
                    options=[""] + all_spools,
                    key="sidebar_history_spool"
                )

                if st.button("View History", key="sidebar_view_history") and history_spool:
                    # Get spool info
                    spool_info = get_spool_info(history_spool)
                    if spool_info:
                        st.success(f"**{spool_info['serial']}**")
                        st.write(f"Length: {spool_info['length']}m")
                        st.write(f"Status: {spool_info['status']}")
                        if spool_info['ev50']:
                            st.write(f"EV50: {spool_info['ev50']}")
                        if spool_info['year'] != 'Unknown':
                            st.write(f"Year: {spool_info['year']}")

                        st.write("---")

                    # Get deployment history
                    deployments = find_spool_in_deployments(history_spool)
                    if deployments:
                        st.write(f"**Deployment History ({len(deployments)} total):**")

                        # Create a summary
                        depths = []
                        for d in deployments:
                            if d['depth']:
                                try:
                                    depth_val = float(d['depth'])
                                    depths.append(depth_val)
                                except (ValueError, TypeError):
                                    pass

                        if depths:
                            st.write(f"• Depth range: {min(depths):.0f}m - {max(depths):.0f}m")
                            st.write(f"• Average depth: {sum(depths)/len(depths):.0f}m")

                        st.write("\n**All Deployments:**")
                        for i, dep in enumerate(deployments, 1):
                            with st.expander(f"{i}. {dep['mooringid']} - {dep['dep_date']}"):
                                st.write(f"**Site:** {dep['site'] or 'N/A'}")
                                st.write(f"**Depth:** {dep['depth']}m" if dep['depth'] else "**Depth:** N/A")
                                st.write(f"**Length Used:** {dep['length']}m" if dep['length'] else "**Length Used:** N/A")
                                st.write(f"**Position:** {dep['position']}")
                                st.write(f"**Date:** {dep['dep_date']}")
                    else:
                        st.write("No deployment history found")

    # Acoustic Release Lookup Sidebar - Only show in Add New mode or Search/Edit mode
    if mode in ["Add New", "Search/Edit"]:
        with st.sidebar:
            st.markdown("---")  # Separator from spool lookup
            st.subheader("🔊 Acoustic Release Lookup")
            st.write("Look up acoustic release specifications")

            # Tab selection for different search modes
            release_tab1, release_tab2 = st.tabs(["Quick Lookup", "Advanced Search"])

            with release_tab1:
                release_lookup_sn = st.text_input("Enter Release S/N:", key="sidebar_release_lookup_sn")
                release_lookup_button = st.button("Look Up", key="sidebar_release_lookup_button")

                if release_lookup_button and release_lookup_sn:
                    deployments = find_release_in_deployments(release_lookup_sn)
                    if deployments:
                        st.success(f"✅ Found Release: {release_lookup_sn}")

                        # Get the most recent deployment info for this release
                        latest = deployments[0]

                        # Display release specifications
                        st.write("**Release Specifications:**")
                        st.write(f"**Type:** {latest['type'] or 'N/A'}")
                        st.write(f"**Int. Freq:** {latest['int_freq'] or 'N/A'}")
                        st.write(f"**Reply Freq:** {latest['reply_freq'] or 'N/A'}")

                        # Display release command codes
                        st.write(f"**Release:** {latest.get('release') or 'N/A'}")
                        st.write(f"**Disable:** {latest.get('disable') or 'N/A'}")
                        st.write(f"**Enable:** {latest.get('enable') or 'N/A'}")

                        st.write("---")
                        st.write(f"**Last Used:** {latest['mooringid']} ({latest['dep_date']})")
                        st.write(f"**Position:** {latest['position']}")
                        st.write(f"**Total Uses:** {len(deployments)}")
                    else:
                        st.info(f"Release {release_lookup_sn} not found")

            with release_tab2:
                st.write("**Search by criteria:**")

                search_release_serial = st.text_input("S/N contains:", key="sidebar_search_release_serial")
                search_release_type = st.text_input("Type contains:", key="sidebar_search_release_type")
                search_int_freq = st.text_input("Int. Freq contains:", key="sidebar_search_int_freq")
                search_reply_freq = st.text_input("Reply Freq contains:", key="sidebar_search_reply_freq")

                if st.button("Search", key="sidebar_release_advanced_search"):
                    results = search_releases_advanced(
                        serial_pattern=search_release_serial if search_release_serial else None,
                        type_pattern=search_release_type if search_release_type else None,
                        int_freq=search_int_freq if search_int_freq else None,
                        reply_freq=search_reply_freq if search_reply_freq else None
                    )

                    if results:
                        st.success(f"Found {len(results)} release(s)")

                        for release in results[:10]:
                            st.write(f"**S/N: {release['serial']}**")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"Type: {release['type'] or 'N/A'}")
                                st.write(f"Int. Freq: {release['int_freq'] or 'N/A'}")
                            with col2:
                                st.write(f"Reply Freq: {release['reply_freq'] or 'N/A'}")
                                st.write(f"Position: {release['position']}")

                            # Display release command codes
                            release_val = release.get('release', 'N/A') or 'N/A'
                            disable_val = release.get('disable', 'N/A') or 'N/A'
                            enable_val = release.get('enable', 'N/A') or 'N/A'

                            # Truncate long codes for display
                            if len(str(release_val)) > 15:
                                release_display = str(release_val)[:12] + "..."
                            else:
                                release_display = release_val

                            if len(str(disable_val)) > 15:
                                disable_display = str(disable_val)[:12] + "..."
                            else:
                                disable_display = disable_val

                            if len(str(enable_val)) > 15:
                                enable_display = str(enable_val)[:12] + "..."
                            else:
                                enable_display = enable_val

                            st.write(f"Release: {release_display} | Disable: {disable_display} | Enable: {enable_display}")

                            # Check how many times used
                            deps = find_release_in_deployments(release['serial'])
                            if deps:
                                st.write(f"Used {len(deps)} time(s)")
                            st.write("---")

                        if len(results) > 10:
                            st.write(f"... and {len(results) - 10} more results")
                    else:
                        st.warning("No releases found")

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
                search_mooringid = st.text_input("Mooring ID", key="search_mooringid")
            with col3:
                search_cruise = st.text_input("Cruise", key="search_cruise")

            search_submitted = st.form_submit_button("Search", use_container_width=True)

            if search_submitted:
                search_criteria = {}
                if search_site and search_site.strip():
                    search_criteria['site'] = search_site
                if search_mooringid:
                    search_criteria['mooringid'] = search_mooringid
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
                deployment_info = parse_json_field(current_record_dict.get('deployment_info', '{}'))

                # Display key info
                info_cols = st.columns(4)
                with info_cols[0]:
                    st.metric("Site", current_record_dict.get('site', 'N/A'))
                with info_cols[1]:
                    st.metric("Mooringid", current_record_dict.get('mooringid', 'N/A'))
                with info_cols[2]:
                    st.metric("Cruise", current_record_dict.get('cruise', 'N/A'))
                with info_cols[3]:
                    st.metric("Date", deployment_info.get('dep_date', 'N/A'))

    # Form for Add New or Edit
    if mode == "Add New":
        st.subheader("Add New Deployment")
    else:
        st.subheader("Edit Deployment")

    # Initialize form defaults
    if mode == "Search/Edit" and st.session_state.selected_deployment is not None:
        record = st.session_state.selected_deployment

        # Parse JSON fields
        deployment_info = parse_json_field(record.get('deployment_info', '{}'))
        met_sensors = parse_json_field(record.get('met_sensors', '{}'))
        hardware = parse_json_field(record.get('hardware', '{}'))
        nylon_spools = parse_json_field(record.get('nylon_spools', '{}'))
        nylon_config = parse_json_field(record.get('nylon_config', '{}'))
        subsurface_sensors = parse_json_field(record.get('subsurface_sensors', '[]'))
        acoustic_releases = parse_json_field(record.get('acoustic_releases', '{}'))
        anchor_drop = parse_json_field(record.get('anchor_drop', '{}'))
        met_obs = parse_json_field(record.get('met_obs', '{}'))
        flyby = parse_json_field(record.get('flyby', '{}'))

        # Set defaults from parsed JSON
        default_site = record.get('site', '')
        default_mooringid = record.get('mooringid', '')
        default_cruise = record.get('cruise', '')
        default_personnel = deployment_info.get('personnel', '')
        # Use buoy coordinates from flyby instead of anchor_drop
        default_lat = flyby.get('buoy_latitude', '')
        default_long = flyby.get('buoy_longitude', '')
        default_depth = record.get('depth', '')
        default_mooring_type = deployment_info.get('mooring_type', '')

        # Parse deployment date
        dep_date_str = deployment_info.get('dep_date', '')
        if dep_date_str:
            try:
                default_deployment_start_date = datetime.strptime(dep_date_str, '%m/%d/%Y').date()
            except:
                default_deployment_start_date = None
        else:
            default_deployment_start_date = None

        # Parse deployment time
        dep_time_str = deployment_info.get('deployment_start_time', '')
        if dep_time_str:
            try:
                parts = dep_time_str.strip().split(':')
                if len(parts) >= 2:
                    hour = int(parts[0])
                    minute = int(parts[1])
                    second = int(parts[2]) if len(parts) > 2 else 0
                    default_deployment_start_time = time(hour, minute, second)
                else:
                    default_deployment_start_time = None
            except:
                default_deployment_start_time = None
        else:
            default_deployment_start_time = None

        # Met sensors defaults
        atrh_sensor = met_sensors.get('atrh', {})
        default_atrh_type = atrh_sensor.get('type', '')
        default_atrh_serial = atrh_sensor.get('serial', '')

        rain_sensor = met_sensors.get('rain', {})
        default_rain_type = rain_sensor.get('type', '')
        default_rain_serial = rain_sensor.get('serial', '')

        sw_radiation_sensor = met_sensors.get('sw_radiation', {})
        default_sw_radiation_type = sw_radiation_sensor.get('type', '')
        default_sw_radiation_serial = sw_radiation_sensor.get('serial', '')

        lw_radiation_sensor = met_sensors.get('lw_radiation', {})
        default_lw_radiation_type = lw_radiation_sensor.get('type', '')
        default_lw_radiation_serial = lw_radiation_sensor.get('serial', '')

        barometer_sensor = met_sensors.get('barometer', {})
        default_barometer_type = barometer_sensor.get('type', '')
        default_barometer_serial = barometer_sensor.get('serial', '')

        wind_sensor = met_sensors.get('wind', {})
        default_wind_type = wind_sensor.get('type', '')
        default_wind_serial = wind_sensor.get('serial', '')

        # Hardware defaults
        default_buoy_sn = hardware.get('buoy_sn', '')
        default_insert = hardware.get('insert', '')
        default_anti_theft_cage = hardware.get('anti_theft_cage', '')
        default_fairing_depth = hardware.get('fairing_depth', '')
        default_teacup_handle = hardware.get('teacup_handle', '')
        default_tube_sn = hardware.get('tube_sn', '')
        default_ptt_hexid = hardware.get('ptt_hexid', '')
        default_time_zone = hardware.get('time_zone', '')
        default_software_ver = hardware.get('software_ver', '')

        # Nylon defaults
        default_nylon_below_release = nylon_config.get('nylon_below_release', '50')
        default_wire_sn = nylon_config.get('wiresn', '')
        default_hardware_length = nylon_config.get('hardware_length', '7')
        default_wire_length = nylon_config.get('wire_ln', '')
        default_projected_scope = nylon_config.get('projected_scope', '')
        default_wire_dep_number = nylon_config.get('wire_age', '')
        default_top_section_sn = nylon_config.get('topsecsn', '')
        default_top_section_usage = nylon_config.get('top_sec_usage', '')

        # Nylon spool defaults (10 spools)
        default_spool_sns = []
        default_spool_lengths = []
        default_spool_ev50s = []
        for i in range(1, 11):
            spool_data = nylon_spools.get(f'spool_{i}', {})
            default_spool_sns.append(spool_data.get('sn', ''))
            default_spool_lengths.append(spool_data.get('length', ''))
            default_spool_ev50s.append(spool_data.get('ev50', ''))

        # Acoustic release defaults
        release1_data = acoustic_releases.get('release_1', {})
        default_release1_type = release1_data.get('type', '')
        default_release1_sn = release1_data.get('sn', '')
        default_release1_int_freq = release1_data.get('int_freq', '')
        default_release1_reply_freq = release1_data.get('reply_freq', '')
        default_release1_release = release1_data.get('release', '')
        default_release1_disable = release1_data.get('disable', '')
        default_release1_enable = release1_data.get('enable', '')

        release2_data = acoustic_releases.get('release_2', {})
        default_release2_type = release2_data.get('type', '')
        default_release2_sn = release2_data.get('sn', '')
        default_release2_int_freq = release2_data.get('int_freq', '')
        default_release2_reply_freq = release2_data.get('reply_freq', '')
        default_release2_release = release2_data.get('release', '')
        default_release2_disable = release2_data.get('disable', '')
        default_release2_enable = release2_data.get('enable', '')

        # Anchor Drop defaults
        default_anchor_date = date.today()
        anchor_date_str = anchor_drop.get('date', '')
        if anchor_date_str:
            try:
                default_anchor_date = datetime.strptime(anchor_date_str, '%m/%d/%Y').date()
            except:
                default_anchor_date = date.today()

        default_anchor_time = anchor_drop.get('time', '')
        default_anchor_latitude = anchor_drop.get('latitude', '')
        default_anchor_longitude = anchor_drop.get('longitude', '')
        default_anchor_tow_time = anchor_drop.get('tow_time', '')
        default_anchor_tow_distance = anchor_drop.get('tow_distance', '')
        default_anchor_total_time = anchor_drop.get('total_time', '')
        default_anchor_weight = anchor_drop.get('weight', '')

        # Meteorological Observations defaults
        ship_met = met_obs.get('ship', {})
        default_ship_date = date.today()
        ship_date_str = ship_met.get('date', '')
        if ship_date_str:
            try:
                default_ship_date = datetime.strptime(ship_date_str, '%m/%d/%Y').date()
            except:
                default_ship_date = date.today()

        default_ship_time = ship_met.get('time', '')
        default_ship_wind_dir = ship_met.get('wind_dir', '')
        default_ship_wind_spd = ship_met.get('wind_spd', '')
        default_ship_air_temp = ship_met.get('air_temp', '')
        default_ship_sst = ship_met.get('sst', '')
        default_ship_ssc = ship_met.get('ssc', '')
        default_ship_rh = ship_met.get('rh', '')

        buoy_met = met_obs.get('buoy', {})
        default_buoy_date = date.today()
        buoy_date_str = buoy_met.get('date', '')
        if buoy_date_str:
            try:
                default_buoy_date = datetime.strptime(buoy_date_str, '%m/%d/%Y').date()
            except:
                default_buoy_date = date.today()

        default_buoy_time = buoy_met.get('time', '')
        default_buoy_wind_dir = buoy_met.get('wind_dir', '')
        default_buoy_wind_spd = buoy_met.get('wind_spd', '')
        default_buoy_air_temp = buoy_met.get('air_temp', '')
        default_buoy_sst = buoy_met.get('sst', '')
        default_buoy_ssc = buoy_met.get('ssc', '')
        default_buoy_rh = buoy_met.get('rh', '')

        default_deployment_comments = deployment_info.get('comments', '')

        # Flyby defaults
        default_flyby_buoy_latitude = flyby.get('buoy_latitude', '')
        default_flyby_buoy_longitude = flyby.get('buoy_longitude', '')
        default_flyby_anchor_latitude = flyby.get('anchor_latitude', '')
        default_flyby_anchor_longitude = flyby.get('anchor_longitude', '')
        default_flyby_uncorrected_depth = flyby.get('uncorrected_depth', '')
        default_flyby_depth_correction = flyby.get('depth_correction', '')
        default_flyby_transducer_depth = flyby.get('transducer_depth', '')
        default_flyby_corrected_depth = flyby.get('corrected_depth', '')
        default_flyby_final_scope = flyby.get('final_scope', '')

        # Initialize subsurface sensors from JSON data
        if isinstance(subsurface_sensors, list):
            st.session_state.subsurface_sensors = subsurface_sensors.copy()
            # Ensure we have at least 15 sensors
            while len(st.session_state.subsurface_sensors) < 15:
                st.session_state.subsurface_sensors.append({
                    'depth': '',
                    'type': '',
                    'address': '',
                    'sn': '',
                    'time_in': '',
                    'comments': ''
                })

    else:
        # Defaults for Add New mode
        default_site = ""
        default_mooringid = ""
        default_cruise = ""
        default_personnel = ""
        default_lat = ""
        default_long = ""
        default_depth = ""
        default_mooring_type = ""
        default_deployment_start_date = None
        default_deployment_start_time = None
        default_atrh_type = "Rotronics"
        default_atrh_serial = ""
        default_rain_type = "RMYoung"
        default_rain_serial = ""
        default_sw_radiation_type = "Eppley"
        default_sw_radiation_serial = ""
        default_lw_radiation_type = "Eppley"
        default_lw_radiation_serial = ""
        default_barometer_type = "PAROS"
        default_barometer_serial = ""
        default_wind_type = "RMYoung"
        default_wind_serial = ""
        default_buoy_sn = ""
        default_insert = ""
        default_anti_theft_cage = ""
        default_fairing_depth = ""
        default_teacup_handle = ""
        default_tube_sn = ""
        default_ptt_hexid = ""
        default_time_zone = ""
        default_software_ver = ""
        default_nylon_below_release = "50"
        default_wire_sn = ""
        default_hardware_length = "7"
        default_wire_length = ""
        default_projected_scope = ""
        default_wire_dep_number = ""
        default_top_section_sn = ""
        default_top_section_usage = ""

        # Nylon spool defaults (10 spools)
        default_spool_sns = [""] * 10
        default_spool_lengths = [""] * 10
        default_spool_ev50s = [""] * 10

        # Acoustic release defaults (empty for new records)
        default_release1_type = ""
        default_release1_sn = ""
        default_release1_int_freq = ""
        default_release1_reply_freq = ""
        default_release1_release = ""
        default_release1_disable = ""
        default_release1_enable = ""
        default_release2_type = ""
        default_release2_sn = ""
        default_release2_int_freq = ""
        default_release2_reply_freq = ""
        default_release2_release = ""
        default_release2_disable = ""
        default_release2_enable = ""

        # Anchor Drop defaults (empty for new records)
        default_anchor_date = date.today()
        default_anchor_time = ""
        default_anchor_latitude = ""
        default_anchor_longitude = ""
        default_anchor_tow_time = ""
        default_anchor_tow_distance = ""
        default_anchor_total_time = ""
        default_anchor_weight = ""

        # Meteorological Observations defaults
        default_ship_date = date.today()
        default_ship_time = ""
        default_ship_wind_dir = ""
        default_ship_wind_spd = ""
        default_ship_air_temp = ""
        default_ship_sst = ""
        default_ship_ssc = ""
        default_ship_rh = ""

        default_buoy_date = date.today()
        default_buoy_time = ""
        default_buoy_wind_dir = ""
        default_buoy_wind_spd = ""
        default_buoy_air_temp = ""
        default_buoy_sst = ""
        default_buoy_ssc = ""
        default_buoy_rh = ""

        default_deployment_comments = ""

        # Flyby defaults (empty for new records)
        default_flyby_buoy_latitude = ""
        default_flyby_buoy_longitude = ""
        default_flyby_anchor_latitude = ""
        default_flyby_anchor_longitude = ""
        default_flyby_uncorrected_depth = ""
        default_flyby_depth_correction = ""
        default_flyby_transducer_depth = ""
        default_flyby_corrected_depth = ""
        default_flyby_final_scope = ""

        # Initialize subsurface sensors with 15 empty rows for new deployments
        if mode == "Add New":
            st.session_state.subsurface_sensors = []
            for i in range(15):
                sensor = {
                    'depth': '1' if i == 0 else '',
                    'type': '',
                    'address': '',
                    'sn': '',
                    'time_in': '',
                    'comments': ''
                }
                st.session_state.subsurface_sensors.append(sensor)

    # Create the complete form
    with st.form("deployment_form"):
        # Deployment Start Date and Time - Highlighted and default to blank
        col_start_date, col_start_time = st.columns(2)
        with col_start_date:
            st.markdown('<span style="color:red; font-weight:bold;">Deployment Start Date *</span>', unsafe_allow_html=True)
            deployment_start_date = st.date_input(
                "Deployment Start Date",
                value=default_deployment_start_date,
                key="deployment_start_date",
                label_visibility="collapsed",
                min_value=date(1990, 1, 1),
                max_value=date(2050, 12, 31),
                format="MM/DD/YYYY"
            )
        with col_start_time:
            st.markdown('<span style="color:red; font-weight:bold;">Deployment Start Time (GMT) *</span>', unsafe_allow_html=True)
            deployment_start_time = st.time_input(
                "Deployment Start Time",
                value=default_deployment_start_time,
                key="deployment_start_time",
                label_visibility="collapsed",
                help="Enter time in GMT format"
            )

        # First row: Site and Mooring ID
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
            mooringid = st.text_input("Mooring ID", value=default_mooringid, key="mooringid")

        # Second row: Cruise
        col3, col4 = st.columns(2)
        with col3:
            cruise = st.text_input("Cruise", value=default_cruise, key="cruise")
        with col4:
            st.write("")  # Empty column

        # Third row: Personnel (full width)
        personnel = st.text_area("Personnel", value=default_personnel, height=100, key="personnel",
                               help="Enter the names of personnel involved in the deployment")

        # Fourth row: Buoy Latitude and Longitude (from flyby)
        col5, col6 = st.columns(2)
        with col5:
            anchor_drp_lat = st.text_input("Buoy Latitude", value=default_lat, key="anchor_drp_lat",
                                         help="Buoy position from flyby - Enter latitude in decimal degrees (e.g., 37.7749) or degrees decimal minutes (e.g., 37 46.5 N)")
        with col6:
            anchor_drp_long = st.text_input("Buoy Longitude", value=default_long, key="anchor_drp_long",
                                          help="Buoy position from flyby - Enter longitude in decimal degrees (e.g., -122.4194) or degrees decimal minutes (e.g., 122 25.3 W)")

        # Fifth row: Mooring Type and Depth
        col7, col8 = st.columns(2)
        with col7:
            mooring_options = ["", "taut", "slack"]
            # Handle case-insensitive matching for mooring type
            try:
                # Convert default to lowercase for comparison
                default_mooring_lower = default_mooring_type.lower()
                # Find matching index (case-insensitive)
                mooring_index = next((i for i, opt in enumerate(mooring_options)
                                     if opt.lower() == default_mooring_lower), 0)
            except (ValueError, AttributeError):
                mooring_index = 0
            mooring_type = st.selectbox("Mooring Type", options=mooring_options, index=mooring_index, key="mooring_type")
        with col8:
            depth = st.text_input("Depth", value=default_depth, key="depth", help="Enter depth in meters")

        # Hardware section
        st.markdown("---")
        st.subheader("Hardware")

        # First row: Buoy S/N and Insert?
        col1, col2 = st.columns(2)
        with col1:
            buoy_sn = st.text_input("Buoy S/N", value=default_buoy_sn, key="buoy_sn")
        with col2:
            insert_options = ["", "Yes", "No"]
            try:
                default_index = insert_options.index(default_insert)
            except ValueError:
                default_index = 0
            insert = st.selectbox("Insert?", options=insert_options, index=default_index, key="insert")

        # Second row: Anti-theft cage? and Fairing Depth
        col1, col2 = st.columns(2)
        with col1:
            cage_options = ["", "Yes", "No"]
            try:
                cage_index = cage_options.index(default_anti_theft_cage)
            except ValueError:
                cage_index = 0
            anti_theft_cage = st.selectbox("Anti-theft cage?", options=cage_options, index=cage_index, key="anti_theft_cage")
        with col2:
            fairing_depth = st.text_input("Fairing Depth:", value=default_fairing_depth, key="fairing_depth")

        # Third row: Teacup handle?
        col1, col2 = st.columns(2)
        with col1:
            handle_options = ["", "Yes", "No"]
            try:
                handle_index = handle_options.index(default_teacup_handle)
            except ValueError:
                handle_index = 0
            teacup_handle = st.selectbox("Teacup handle?", options=handle_options, index=handle_index, key="teacup_handle")
        with col2:
            st.write("")  # Empty column for alignment

        # Tube subsection
        st.write("**Tube**")

        # Fourth row: Tube S/N and PTT/Hexid
        col1, col2 = st.columns(2)
        with col1:
            tube_sn = st.text_input("Tube S/N", value=default_tube_sn, key="tube_sn")
        with col2:
            ptt_hexid = st.text_input("PTT/Hexid", value=default_ptt_hexid, key="ptt_hexid")

        # Fifth row: Time Zone and Software Ver.
        col1, col2 = st.columns(2)
        with col1:
            time_zone = st.text_input("Time Zone", value=default_time_zone, key="time_zone")
        with col2:
            software_ver = st.text_input("Software Ver.", value=default_software_ver, key="software_ver")

        # Met Sensors section
        st.markdown("---")
        st.subheader("Met Sensors")

        # Create table header
        col_header1, col_header2, col_header3 = st.columns([2, 2, 2])
        with col_header1:
            st.write("")  # Empty for sensor name column
        with col_header2:
            st.write("**Sensor Type**")
        with col_header3:
            st.write("**Serial No.**")

        # AT/RH
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            st.write("AT/RH")
        with col2:
            atrh_type = st.text_input("AT/RH Type", value=default_atrh_type, key="atrh_type", label_visibility="collapsed")
        with col3:
            atrh_serial = st.text_input("AT/RH Serial", value=default_atrh_serial, key="atrh_serial", label_visibility="collapsed")

        # Rain
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            st.write("Rain")
        with col2:
            rain_type = st.text_input("Rain Type", value=default_rain_type, key="rain_type", label_visibility="collapsed")
        with col3:
            rain_serial = st.text_input("Rain Serial", value=default_rain_serial, key="rain_serial", label_visibility="collapsed")

        # SW Radiation
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            st.write("SW Radiation")
        with col2:
            sw_radiation_type = st.text_input("SW Radiation Type", value=default_sw_radiation_type, key="sw_radiation_type", label_visibility="collapsed")
        with col3:
            sw_radiation_serial = st.text_input("SW Radiation Serial", value=default_sw_radiation_serial, key="sw_radiation_serial", label_visibility="collapsed")

        # LW Radiation
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            st.write("LW Radiation")
        with col2:
            lw_radiation_type = st.text_input("LW Radiation Type", value=default_lw_radiation_type, key="lw_radiation_type", label_visibility="collapsed")
        with col3:
            lw_radiation_serial = st.text_input("LW Radiation Serial", value=default_lw_radiation_serial, key="lw_radiation_serial", label_visibility="collapsed")

        # Barometer
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            st.write("Barometer")
        with col2:
            barometer_type = st.text_input("Barometer Type", value=default_barometer_type, key="barometer_type", label_visibility="collapsed")
        with col3:
            barometer_serial = st.text_input("Barometer Serial", value=default_barometer_serial, key="barometer_serial", label_visibility="collapsed")

        # Wind
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            st.write("Wind")
        with col2:
            wind_type = st.text_input("Wind Type", value=default_wind_type, key="wind_type", label_visibility="collapsed")
        with col3:
            wind_serial = st.text_input("Wind Serial", value=default_wind_serial, key="wind_serial", label_visibility="collapsed")

        # Subsurface Sensors section
        st.markdown("---")
        st.subheader("Subsurface Sensors")

        # Row sets control (each set = 15 rows)
        row_sets = st.number_input(
            "Number of row sets (15 rows per set)",
            min_value=1,
            max_value=3,
            value=max(1, (len(st.session_state.subsurface_sensors) + 14) // 15),
            step=1,
            key="subsurface_row_sets",
            help="Each set adds 15 rows. Use 1 for 15 rows, 2 for 30 rows, 3 for 45 rows."
        )

        num_sensors = row_sets * 15
        st.write(f"Total rows: {num_sensors}")

        # Update the subsurface_sensors list based on the number input
        current_count = len(st.session_state.subsurface_sensors)
        if num_sensors > current_count:
            # Add new empty sensors
            for _ in range(num_sensors - current_count):
                new_idx = len(st.session_state.subsurface_sensors)
                st.session_state.subsurface_sensors.append({
                    'depth': '1' if new_idx == 0 else '',
                    'type': '',
                    'address': '',
                    'sn': '',
                    'time_in': '',
                    'comments': ''
                })
        elif num_sensors < current_count:
            # Remove sensors from the end
            st.session_state.subsurface_sensors = st.session_state.subsurface_sensors[:num_sensors]

        if num_sensors > 0:
            # Create table header
            col_headers = st.columns([1, 2, 2, 1.5, 2, 2, 3])
            with col_headers[0]:
                st.write("**Row**")
            with col_headers[1]:
                st.write("**Depth**")
            with col_headers[2]:
                st.write("**Type**")
            with col_headers[3]:
                st.write("**Address**")
            with col_headers[4]:
                st.write("**S/N**")
            with col_headers[5]:
                st.write("**Time In (GMT)**")
            with col_headers[6]:
                st.write("**Comments**")

            # Display sensors
            for idx in range(num_sensors):
                if idx < len(st.session_state.subsurface_sensors):
                    sensor = st.session_state.subsurface_sensors[idx]
                else:
                    sensor = {
                        'depth': '',
                        'type': '',
                        'address': '',
                        'sn': '',
                        'time_in': '',
                        'comments': ''
                    }
                    st.session_state.subsurface_sensors.append(sensor)

                cols = st.columns([1, 2, 2, 1.5, 2, 2, 3])

                with cols[0]:
                    st.write(f"{idx + 1}")

                with cols[1]:
                    default_depth = sensor.get('depth', '')
                    if idx == 0 and not default_depth:
                        default_depth = "1"

                    sensor['depth'] = st.text_input(
                        f"Depth {idx}",
                        value=default_depth,
                        key=f"subsurface_depth_{idx}",
                        label_visibility="collapsed"
                    )

                with cols[2]:
                    sensor['type'] = st.text_input(
                        f"Type {idx}",
                        value=sensor.get('type', ''),
                        key=f"subsurface_type_{idx}",
                        label_visibility="collapsed"
                    )

                with cols[3]:
                    sensor['address'] = st.text_input(
                        f"Address {idx}",
                        value=sensor.get('address', ''),
                        key=f"subsurface_address_{idx}",
                        label_visibility="collapsed"
                    )

                with cols[4]:
                    sensor['sn'] = st.text_input(
                        f"S/N {idx}",
                        value=sensor.get('sn', ''),
                        key=f"subsurface_sn_{idx}",
                        label_visibility="collapsed"
                    )

                with cols[5]:
                    sensor['time_in'] = st.text_input(
                        f"Time In {idx}",
                        value=sensor.get('time_in', ''),
                        key=f"subsurface_time_in_{idx}",
                        label_visibility="collapsed",
                        placeholder="HH:MM (GMT)",
                        help="Enter time in GMT format"
                    )

                with cols[6]:
                    sensor['comments'] = st.text_input(
                        f"Comments {idx}",
                        value=sensor.get('comments', ''),
                        key=f"subsurface_comments_{idx}",
                        label_visibility="collapsed"
                    )

        # Nylon section
        st.markdown("---")
        st.subheader("Nylon")

        # First row: Nylon below release and Wire S/N
        col1, col2 = st.columns(2)
        with col1:
            nylon_below_release = st.text_input("Nylon below release", value=default_nylon_below_release, key="below_release")
        with col2:
            wire_sn = st.text_input("Wire S/N", value=default_wire_sn, key="wire_sn")

        # Second row: Hardware length and Wire Length
        col1, col2 = st.columns(2)
        with col1:
            hardware_length = st.text_input("Hardware length", value=default_hardware_length, key="hardware_ln")
        with col2:
            wire_length = st.text_input("Wire Length", value=default_wire_length, key="wire_length")

        # Third row: Projected Scope and Wire dep number
        col1, col2 = st.columns(2)
        with col1:
            projected_scope = st.text_input("Projected Scope", value=default_projected_scope, key="projected_scope")
        with col2:
            wire_dep_number = st.text_input("Wire dep number", value=default_wire_dep_number, key="wire_dep_number")

        # Fourth row: Top Section S/N and Top Section usage
        col1, col2 = st.columns(2)
        with col1:
            top_section_sn = st.text_input("Top Section S/N", value=default_top_section_sn, key="top_section_sn")
        with col2:
            top_section_usage = st.text_input("Top Section usage", value=default_top_section_usage, key="top_section_usage")

        # Nylon Spools section
        st.subheader("Nylon Spools")

        # Create table header
        col_headers = st.columns([1, 2, 1.5, 1.5])
        with col_headers[0]:
            st.write("**Spool #**")
        with col_headers[1]:
            st.write("**S/N**")
        with col_headers[2]:
            st.write("**Length**")
        with col_headers[3]:
            st.write("**EV50**")

        # Create 10 spool rows
        spool_sns = []
        spool_lengths = []
        spool_ev50s = []
        for i in range(10):
            cols = st.columns([1, 2, 1.5, 1.5])

            with cols[0]:
                st.write(f"{i + 1}")

            with cols[1]:
                sn_value = default_spool_sns[i]
                spool_sn = st.text_input(
                    f"Spool {i+1} S/N",
                    value=sn_value,
                    key=f"spool_{i+1}_sn",
                    label_visibility="collapsed"
                )
                spool_sns.append(spool_sn)

            with cols[2]:
                length_value = default_spool_lengths[i]
                spool_length = st.text_input(
                    f"Spool {i+1} Length",
                    value=length_value,
                    key=f"spool_{i+1}_length",
                    label_visibility="collapsed"
                )
                spool_lengths.append(spool_length)

            with cols[3]:
                # Get EV50 flag for this spool
                ev50_value = ""

                # Handle different modes
                if mode == "Add New":
                    # Use default value for Add New mode
                    ev50_value = default_spool_ev50s[i]
                    # If user entered a spool serial, look up its EV50 flag
                    if spool_sn:
                        lookup_ev50 = get_spool_ev50(spool_sn)
                        if lookup_ev50:
                            ev50_value = lookup_ev50
                else:  # Search/Edit mode
                    # First use the stored default value from the database
                    ev50_value = default_spool_ev50s[i]

                    # If we have a spool serial number (either from form input or database default),
                    # look it up to get the most current EV50 flag
                    spool_to_lookup = spool_sn or default_spool_sns[i]
                    if spool_to_lookup:
                        lookup_ev50 = get_spool_ev50(spool_to_lookup)
                        if lookup_ev50:
                            ev50_value = lookup_ev50

                spool_ev50 = st.text_input(
                    f"EV50 {i+1}",
                    value=ev50_value,
                    key=f"spool_{i+1}_ev50",
                    label_visibility="collapsed"
                )
                spool_ev50s.append(spool_ev50)

        # Add separator line
        st.markdown("---")

        # Summary rows
        summary_cols = st.columns([1, 2, 1.5, 1.5])

        # Total Nylon row
        with summary_cols[0]:
            st.write("")  # Empty for alignment
        with summary_cols[1]:
            st.write("**Total Nylon:**")
        with summary_cols[2]:
            # Calculate total nylon length
            total_nylon = 0
            for length in spool_lengths:
                if length:
                    try:
                        total_nylon += float(length)
                    except ValueError:
                        pass
            st.write(f"**{total_nylon:.1f}**")
        with summary_cols[3]:
            st.write("")  # Empty for alignment

        # Final Scope row
        final_scope_cols = st.columns([1, 2, 1.5, 1.5])
        with final_scope_cols[0]:
            st.write("")  # Empty for alignment
        with final_scope_cols[1]:
            st.write("**Final Scope:**")
        with final_scope_cols[2]:
            # Calculate final scope using current form values
            try:
                hardware_ln = float(hardware_length or 0)
                wire_ln = float(wire_length or 0)
                nylon_below = float(nylon_below_release or 0)
                depth_val = float(depth or 1)  # Avoid division by zero

                if depth_val > 0:
                    final_scope = (hardware_ln + wire_ln + nylon_below + total_nylon) / depth_val
                    st.write(f"**{final_scope:.3f}**")
                else:
                    st.write("**N/A** (depth = 0)")
            except (ValueError, TypeError):
                st.write("**N/A**")
        with final_scope_cols[3]:
            st.write("")  # Empty for alignment

        # Acoustic Releases section
        st.markdown("---")
        st.subheader("Acoustic Releases")

        # Create table header
        release_headers = st.columns([1, 1.5, 1.5, 1, 1, 1, 1, 1])
        with release_headers[0]:
            st.write("")  # Empty for row labels
        with release_headers[1]:
            st.write("**Type**")
        with release_headers[2]:
            st.write("**S/N**")
        with release_headers[3]:
            st.write("**Int. Freq.**")
        with release_headers[4]:
            st.write("**Reply Freq**")
        with release_headers[5]:
            st.write("**Release**")
        with release_headers[6]:
            st.write("**Disable**")
        with release_headers[7]:
            st.write("**Enable**")

        # Release 1
        release1_cols = st.columns([1, 1.5, 1.5, 1, 1, 1, 1, 1])
        with release1_cols[0]:
            st.write("**Release 1**")
        with release1_cols[1]:
            release1_type = st.text_input("Release 1 Type", value=default_release1_type, key="release1_type", label_visibility="collapsed")
        with release1_cols[2]:
            release1_sn = st.text_input("Release 1 S/N", value=default_release1_sn, key="release1_sn", label_visibility="collapsed")
        with release1_cols[3]:
            release1_int_freq = st.text_input("Release 1 Int Freq", value=default_release1_int_freq, key="release1_int_freq", label_visibility="collapsed")
        with release1_cols[4]:
            release1_reply_freq = st.text_input("Release 1 Reply Freq", value=default_release1_reply_freq, key="release1_reply_freq", label_visibility="collapsed")
        with release1_cols[5]:
            release1_release = st.text_input("Release 1 Release", value=default_release1_release, key="release1_release", label_visibility="collapsed")
        with release1_cols[6]:
            release1_disable = st.text_input("Release 1 Disable", value=default_release1_disable, key="release1_disable", label_visibility="collapsed")
        with release1_cols[7]:
            release1_enable = st.text_input("Release 1 Enable", value=default_release1_enable, key="release1_enable", label_visibility="collapsed")

        # Release 2
        release2_cols = st.columns([1, 1.5, 1.5, 1, 1, 1, 1, 1])
        with release2_cols[0]:
            st.write("**Release 2**")
        with release2_cols[1]:
            release2_type = st.text_input("Release 2 Type", value=default_release2_type, key="release2_type", label_visibility="collapsed")
        with release2_cols[2]:
            release2_sn = st.text_input("Release 2 S/N", value=default_release2_sn, key="release2_sn", label_visibility="collapsed")
        with release2_cols[3]:
            release2_int_freq = st.text_input("Release 2 Int Freq", value=default_release2_int_freq, key="release2_int_freq", label_visibility="collapsed")
        with release2_cols[4]:
            release2_reply_freq = st.text_input("Release 2 Reply Freq", value=default_release2_reply_freq, key="release2_reply_freq", label_visibility="collapsed")
        with release2_cols[5]:
            release2_release = st.text_input("Release 2 Release", value=default_release2_release, key="release2_release", label_visibility="collapsed")
        with release2_cols[6]:
            release2_disable = st.text_input("Release 2 Disable", value=default_release2_disable, key="release2_disable", label_visibility="collapsed")
        with release2_cols[7]:
            release2_enable = st.text_input("Release 2 Enable", value=default_release2_enable, key="release2_enable", label_visibility="collapsed")

        # Anchor Drop section
        st.markdown("---")
        st.subheader("Anchor Drop")

        # First row: Date and Time
        anchor_row1 = st.columns(2)
        with anchor_row1[0]:
            anchor_date = st.date_input("Date", value=default_anchor_date, key="anchor_date", format="MM/DD/YYYY")
        with anchor_row1[1]:
            anchor_time = st.text_input("Time", value=default_anchor_time, key="anchor_time")

        # Second row: Latitude and Longitude
        anchor_row2 = st.columns(2)
        with anchor_row2[0]:
            anchor_latitude = st.text_input("Latitude", value=default_anchor_latitude, key="anchor_latitude")
        with anchor_row2[1]:
            anchor_longitude = st.text_input("Longitude", value=default_anchor_longitude, key="anchor_longitude")

        # Third row: Tow Time and Tow Distance
        anchor_row3 = st.columns(2)
        with anchor_row3[0]:
            anchor_tow_time = st.text_input("Tow Time", value=default_anchor_tow_time, key="anchor_tow_time")
        with anchor_row3[1]:
            anchor_tow_distance = st.text_input("Tow Distance", value=default_anchor_tow_distance, key="anchor_tow_distance")

        # Fourth row: Total Time and Anchor Weight
        anchor_row4 = st.columns(2)
        with anchor_row4[0]:
            # Auto-calculate Total Time (read-only)
            from datetime import datetime, timedelta

            start_time_str = deployment_start_time.strftime('%H:%M:%S') if deployment_start_time else ""
            anchor_time_str = anchor_time

            def parse_time(tstr):
                for fmt in ("%H:%M:%S", "%H:%M"):
                    try:
                        return datetime.strptime(tstr, fmt).time()
                    except Exception:
                        continue
                return None

            start_time = parse_time(start_time_str)
            anchor_drop = parse_time(anchor_time_str)

            total_time_str = ""
            if start_time and anchor_drop:
                today = datetime.today()
                dt_start = datetime.combine(today, start_time)
                dt_anchor = datetime.combine(today, anchor_drop)
                if dt_anchor < dt_start:
                    dt_anchor += timedelta(days=1)  # handle overnight
                delta = dt_anchor - dt_start
                # Format as HH:MM:SS
                total_seconds = int(delta.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                total_time_str = f"{hours:02}:{minutes:02}:{seconds:02}"

            anchor_total_time = st.text_input(
                "Total Time",
                value=total_time_str,
                key="anchor_total_time",
                disabled=True,
                help="Automatically calculated as the difference between Deployment Start Time and Anchor Drop Time (GMT)"
            )
        with anchor_row4[1]:
            anchor_weight = st.text_input("Anchor Weight", value=default_anchor_weight, key="anchor_weight")

        # Flyby section
        st.markdown("---")
        st.subheader("Flyby")

        # Buoy row
        flyby_row1 = st.columns([1, 2, 2])
        with flyby_row1[0]:
            st.write("**Buoy**")
        with flyby_row1[1]:
            flyby_buoy_latitude = st.text_input("Buoy Latitude", value=default_flyby_buoy_latitude, key="flyby_buoy_latitude", placeholder="Latitude")
        with flyby_row1[2]:
            flyby_buoy_longitude = st.text_input("Buoy Longitude", value=default_flyby_buoy_longitude, key="flyby_buoy_longitude", placeholder="Longitude")

        # Anchor row
        flyby_row2 = st.columns([1, 2, 2])
        with flyby_row2[0]:
            st.write("**Anchor**")
        with flyby_row2[1]:
            flyby_anchor_latitude = st.text_input("Anchor Latitude", value=default_flyby_anchor_latitude, key="flyby_anchor_latitude", placeholder="Latitude")
        with flyby_row2[2]:
            flyby_anchor_longitude = st.text_input("Anchor Longitude", value=default_flyby_anchor_longitude, key="flyby_anchor_longitude", placeholder="Longitude")

        # Single field rows
        flyby_row3 = st.columns([2, 3])
        with flyby_row3[0]:
            st.write("**Uncorrected Depth**")
        with flyby_row3[1]:
            flyby_uncorrected_depth = st.text_input("Uncorrected Depth", value=default_flyby_uncorrected_depth, key="flyby_uncorrected_depth", label_visibility="collapsed")

        flyby_row4 = st.columns([2, 3])
        with flyby_row4[0]:
            st.write("**Depth Correction**")
        with flyby_row4[1]:
            flyby_depth_correction = st.text_input("Depth Correction", value=default_flyby_depth_correction, key="flyby_depth_correction", label_visibility="collapsed")

        flyby_row5 = st.columns([2, 3])
        with flyby_row5[0]:
            st.write("**Transducer Depth**")
        with flyby_row5[1]:
            flyby_transducer_depth = st.text_input("Transducer Depth", value=default_flyby_transducer_depth, key="flyby_transducer_depth", label_visibility="collapsed")

        # Corrected Depth and Final Scope row
        flyby_row6 = st.columns([1, 1.5, 1, 1.5])
        with flyby_row6[0]:
            st.write("**Corrected Depth**")
        with flyby_row6[1]:
            # Auto-calculate corrected depth: Uncorrected Depth + Depth Correction + Transducer Depth
            try:
                uncorr_val = float(flyby_uncorrected_depth) if flyby_uncorrected_depth else 0.0
            except Exception:
                uncorr_val = 0.0
            try:
                corr_val = float(flyby_depth_correction) if flyby_depth_correction else 0.0
            except Exception:
                corr_val = 0.0
            try:
                trans_val = float(flyby_transducer_depth) if flyby_transducer_depth else 0.0
            except Exception:
                trans_val = 0.0
            auto_corrected_depth = uncorr_val + corr_val + trans_val
            flyby_corrected_depth = st.text_input(
                "Corrected Depth",
                value=f"{auto_corrected_depth:.2f}" if (flyby_uncorrected_depth or flyby_depth_correction or flyby_transducer_depth) else "",
                key="flyby_corrected_depth",
                label_visibility="collapsed",
                disabled=True,
                help="Automatically calculated: Uncorrected Depth + Depth Correction + Transducer Depth"
            )
        with flyby_row6[2]:
            st.write("**Final Scope**")
        with flyby_row6[3]:
            # Mirror Final Scope from Nylon section (read-only)
            try:
                final_scope_val = final_scope
                final_scope_display = f"{final_scope_val:.3g}"
            except:
                final_scope_display = ""
            flyby_final_scope = st.text_input(
                "Final Scope",
                value=final_scope_display,
                key="flyby_final_scope",
                label_visibility="collapsed",
                disabled=True,
                help="Mirrors the Final Scope value from the Nylon section (3 significant digits)"
            )

        # Met Obs section
        st.markdown("---")
        st.subheader("Met Obs")

        # Create table header
        met_headers = st.columns([0.8, 1, 1, 1, 1.2, 1, 0.8, 0.8, 0.8])
        with met_headers[0]:
            st.write("")  # Empty for row labels
        with met_headers[1]:
            st.write("**Date**")
        with met_headers[2]:
            st.write("**Time**")
        with met_headers[3]:
            st.write("**Wind Dir**")
        with met_headers[4]:
            st.write("**Wind Spd (kts)**")
        with met_headers[5]:
            st.write("**Air Temp**")
        with met_headers[6]:
            st.write("**SST**")
        with met_headers[7]:
            st.write("**SSC**")
        with met_headers[8]:
            st.write("**RH**")

        # Ship row
        ship_cols = st.columns([0.8, 1, 1, 1, 1.2, 1, 0.8, 0.8, 0.8])
        with ship_cols[0]:
            st.write("**Ship**")
        with ship_cols[1]:
            ship_date = st.text_input(
                "Ship Date (MM/DD/YYYY)",
                value=default_ship_date.strftime("%m/%d/%Y") if (default_ship_date and hasattr(default_ship_date, "strftime")) else "",
                key="ship_date_text",
                label_visibility="collapsed",
                placeholder="MM/DD/YYYY"
            )
        with ship_cols[2]:
            ship_time = st.text_input("Ship Time", value=default_ship_time, key="ship_time", label_visibility="collapsed")
        with ship_cols[3]:
            ship_wind_dir = st.text_input("Ship Wind Dir", value=default_ship_wind_dir, key="ship_wind_dir", label_visibility="collapsed")
        with ship_cols[4]:
            ship_wind_spd = st.text_input("Ship Wind Spd", value=default_ship_wind_spd, key="ship_wind_spd", label_visibility="collapsed")
        with ship_cols[5]:
            ship_air_temp = st.text_input("Ship Air Temp", value=default_ship_air_temp, key="ship_air_temp", label_visibility="collapsed")
        with ship_cols[6]:
            ship_sst = st.text_input("Ship SST", value=default_ship_sst, key="ship_sst", label_visibility="collapsed")
        with ship_cols[7]:
            ship_ssc = st.text_input("Ship SSC", value=default_ship_ssc, key="ship_ssc", label_visibility="collapsed")
        with ship_cols[8]:
            ship_rh = st.text_input("Ship RH", value=default_ship_rh, key="ship_rh", label_visibility="collapsed")

        # Buoy row
        buoy_cols = st.columns([0.8, 1, 1, 1, 1.2, 1, 0.8, 0.8, 0.8])
        with buoy_cols[0]:
            st.write("**Buoy**")
        with buoy_cols[1]:
            buoy_date = st.text_input(
                "Buoy Date (MM/DD/YYYY)",
                value=default_buoy_date.strftime("%m/%d/%Y") if (default_buoy_date and hasattr(default_buoy_date, "strftime")) else "",
                key="buoy_date_text",
                label_visibility="collapsed",
                placeholder="MM/DD/YYYY"
            )
        with buoy_cols[2]:
            buoy_time = st.text_input("Buoy Time", value=default_buoy_time, key="buoy_time", label_visibility="collapsed")
        with buoy_cols[3]:
            buoy_wind_dir = st.text_input("Buoy Wind Dir", value=default_buoy_wind_dir, key="buoy_wind_dir", label_visibility="collapsed")
        with buoy_cols[4]:
            buoy_wind_spd = st.text_input("Buoy Wind Spd", value=default_buoy_wind_spd, key="buoy_wind_spd", label_visibility="collapsed")
        with buoy_cols[5]:
            buoy_air_temp = st.text_input("Buoy Air Temp", value=default_buoy_air_temp, key="buoy_air_temp", label_visibility="collapsed")
        with buoy_cols[6]:
            buoy_sst = st.text_input("Buoy SST", value=default_buoy_sst, key="buoy_sst", label_visibility="collapsed")
        with buoy_cols[7]:
            buoy_ssc = st.text_input("Buoy SSC", value=default_buoy_ssc, key="buoy_ssc", label_visibility="collapsed")
        with buoy_cols[8]:
            buoy_rh = st.text_input("Buoy RH", value=default_buoy_rh, key="buoy_rh", label_visibility="collapsed")

        # Deployment Comments section
        st.markdown("---")
        st.subheader("Deployment Comments")
        deployment_comments = st.text_area("Deployment Comments",
                                         value=default_deployment_comments,
                                         key="deployment_comments",
                                         height=500,  # Approximately 25 lines
                                         label_visibility="collapsed",
                                         help="Enter any additional comments about the deployment")

        # Submit button
        button_label = "Update Deployment" if mode == "Search/Edit" and st.session_state.selected_deployment is not None else "Save Deployment"
        submitted = st.form_submit_button(button_label, use_container_width=True)

        if submitted:
            # Collect all form data
            form_data = {
                'dep_date': deployment_start_date.strftime("%m/%d/%Y") if deployment_start_date else "",
                'deployment_start_time': deployment_start_time.strftime('%H:%M:%S') if deployment_start_time else "",
                'site': site,
                'mooringid': mooringid,
                'cruise': cruise,
                'personnel': personnel,
                'anchor_drp_lat': anchor_drp_lat,  # Buoy latitude from flyby
                'anchor_drp_long': anchor_drp_long,  # Buoy longitude from flyby
                'mooring_type': mooring_type,
                'depth': depth,
                'atrh_type': atrh_type,
                'atrh_serial': atrh_serial,
                'rain_type': rain_type,
                'rain_serial': rain_serial,
                'sw_radiation_type': sw_radiation_type,
                'sw_radiation_serial': sw_radiation_serial,
                'lw_radiation_type': lw_radiation_type,
                'lw_radiation_serial': lw_radiation_serial,
                'barometer_type': barometer_type,
                'barometer_serial': barometer_serial,
                'wind_type': wind_type,
                'wind_serial': wind_serial,
                'buoy_sn': buoy_sn,
                'insert': insert,
                'anti_theft_cage': anti_theft_cage,
                'fairing_depth': fairing_depth,
                'teacup_handle': teacup_handle,
                'tube_sn': tube_sn,
                'ptt_hexid': ptt_hexid,
                'time_zone': time_zone,
                'software_ver': software_ver,
                'nylon_below_release': nylon_below_release,
                'wire_sn': wire_sn,
                'hardware_length': hardware_length,
                'wire_length': wire_length,
                'projected_scope': projected_scope,
                'wire_dep_number': wire_dep_number,
                'top_section_sn': top_section_sn,
                'top_section_usage': top_section_usage,
                'subsurface_sensors': st.session_state.subsurface_sensors,
                # Acoustic releases
                'release1_type': release1_type,
                'release1_sn': release1_sn,
                'release1_int_freq': release1_int_freq,
                'release1_reply_freq': release1_reply_freq,
                'release1_release': release1_release,
                'release1_disable': release1_disable,
                'release1_enable': release1_enable,
                'release2_type': release2_type,
                'release2_sn': release2_sn,
                'release2_int_freq': release2_int_freq,
                'release2_reply_freq': release2_reply_freq,
                'release2_release': release2_release,
                'release2_disable': release2_disable,
                'release2_enable': release2_enable,
                # Anchor Drop data
                'anchor_date': anchor_date.strftime("%m/%d/%Y") if anchor_date else "",
                'anchor_time': anchor_time,
                'anchor_latitude': anchor_latitude,
                'anchor_longitude': anchor_longitude,
                'anchor_tow_time': anchor_tow_time,
                'anchor_tow_distance': anchor_tow_distance,
                'anchor_total_time': total_time_str,
                'anchor_weight': anchor_weight,
                # Meteorological Observations data
                'ship_date': ship_date if ship_date else "",
                'ship_time': ship_time,
                'ship_wind_dir': ship_wind_dir,
                'ship_wind_spd': ship_wind_spd,
                'ship_air_temp': ship_air_temp,
                'ship_sst': ship_sst,
                'ship_ssc': ship_ssc,
                'ship_rh': ship_rh,
                'buoy_date': buoy_date if buoy_date else "",
                'buoy_time': buoy_time,
                'buoy_wind_dir': buoy_wind_dir,
                'buoy_wind_spd': buoy_wind_spd,
                'buoy_air_temp': buoy_air_temp,
                'buoy_sst': buoy_sst,
                'buoy_ssc': buoy_ssc,
                'buoy_rh': buoy_rh,
                'deployment_comments': deployment_comments,
                # Flyby data
                'flyby_buoy_latitude': flyby_buoy_latitude,
                'flyby_buoy_longitude': flyby_buoy_longitude,
                'flyby_anchor_latitude': flyby_anchor_latitude,
                'flyby_anchor_longitude': flyby_anchor_longitude,
                'flyby_uncorrected_depth': flyby_uncorrected_depth,
                'flyby_depth_correction': flyby_depth_correction,
                'flyby_transducer_depth': flyby_transducer_depth,
                'flyby_corrected_depth': f"{auto_corrected_depth:.2f}" if (flyby_uncorrected_depth or flyby_depth_correction or flyby_transducer_depth) else "",
                'flyby_final_scope': final_scope_display,
            }

            # Add spool data to form_data
            for i in range(10):
                form_data[f'spool_{i+1}_sn'] = spool_sns[i]
                form_data[f'spool_{i+1}_length'] = spool_lengths[i]
                form_data[f'spool_{i+1}_ev50'] = spool_ev50s[i]

            # Validate required fields
            required_fields = {
                'Site': form_data.get('site'),
                'Mooringid': form_data.get('mooringid'),
                'Cruise': form_data.get('cruise'),
                'Deployment Start Date': deployment_start_date,
                'Deployment Start Time': deployment_start_time
            }

            missing_fields = [name for name, value in required_fields.items() if not value]

            if missing_fields:
                st.error(f"Please fill in required fields: {', '.join(missing_fields)}")
            else:
                # Function to parse degrees decimal minutes format
                def parse_coordinate(coord_str, is_latitude=True):
                    """Parse coordinate in various formats including degrees decimal minutes with NSEW."""
                    coord_str = coord_str.strip()

                    # Try to parse as simple decimal degrees first
                    try:
                        return float(coord_str)
                    except ValueError:
                        pass

                    # Try to parse degrees decimal minutes format (e.g., "37 46.5 N" or "122 25.3 W")
                    import re
                    pattern = r'^(\d+)\s+(\d+\.?\d*)\s*([NSEW])$'
                    match = re.match(pattern, coord_str, re.IGNORECASE)

                    if match:
                        degrees = float(match.group(1))
                        minutes = float(match.group(2))
                        direction = match.group(3).upper()

                        # Convert to decimal degrees
                        decimal_degrees = degrees + (minutes / 60)

                        # Apply sign based on direction
                        if direction in ['S', 'W']:
                            decimal_degrees = -decimal_degrees

                        return decimal_degrees

                    raise ValueError("Invalid coordinate format")

                # Validate latitude and longitude if provided
                lat_valid = True
                long_valid = True

                if form_data.get('anchor_drp_lat'):
                    try:
                        lat = parse_coordinate(form_data['anchor_drp_lat'], is_latitude=True)
                        if not -90 <= lat <= 90:
                            st.error("Latitude must be between -90 and 90 degrees")
                            lat_valid = False
                    except ValueError:
                        st.error("Latitude must be a valid number or in format: degrees minutes.decimal N/S (e.g., 37 46.5 N)")
                        lat_valid = False

                if form_data.get('anchor_drp_long'):
                    try:
                        lon = parse_coordinate(form_data['anchor_drp_long'], is_latitude=False)
                        if not -180 <= lon <= 180:
                            st.error("Longitude must be between -180 and 180 degrees")
                            long_valid = False
                    except ValueError:
                        st.error("Longitude must be a valid number or in format: degrees minutes.decimal E/W (e.g., 122 25.3 W)")
                        long_valid = False

                if lat_valid and long_valid:
                    # Store in session state
                    st.session_state.form_data.update(form_data)

                    # Save or update to database
                    if mode == "Search/Edit" and st.session_state.selected_deployment is not None:
                        deployment_id = st.session_state.selected_deployment.get('id')

                        if deployment_id is None:
                            st.error("Could not determine deployment ID for update. The 'id' field is missing from the selected record.")
                            st.stop()

                        success, result = update_deployment_data(deployment_id, form_data)
                        if success:
                            if isinstance(result, dict):
                                st.success(f"✅ Deployment updated successfully!")
                                st.info(f"Verified in database - dep_date is now: {result.get('dep_date', 'unknown')}")
                            else:
                                st.success(f"✅ Deployment updated successfully! (ID: {result})")

                            # Update the current record in session state with the new values
                            st.session_state.selected_deployment.update(form_data)

                            # Also update the search results if they exist
                            if st.session_state.search_results is not None and st.session_state.current_record_index is not None:
                                # Update the dataframe row with new values
                                for key, value in form_data.items():
                                    if key in st.session_state.search_results.columns and key != 'subsurface_sensors':
                                        st.session_state.search_results.at[st.session_state.current_record_index, key] = value

                            st.success("✅ Data updated and display refreshed!")
                            st.info("The form now shows the updated values. You can continue editing or search for another record.")

                            # Trigger a rerun to refresh the display
                            st.rerun()
                        else:
                            st.error(f"❌ Error updating deployment: {result}")
                    else:
                        # Save new record
                        success, result = save_deployment_data(form_data)
                        if success:
                            st.success(f"✅ Deployment saved successfully! (ID: {result})")
                            # Clear the form by rerunning
                            if st.button("Add Another Deployment"):
                                st.rerun()
                        else:
                            st.error(f"❌ Error saving deployment: {result}")

                    # Show the collected data
                    with st.expander("View Saved Data"):
                        st.json(form_data)



if __name__ == "__main__":
    main()
