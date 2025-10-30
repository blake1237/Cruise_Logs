import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, time
import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Database configuration
DB_PATH = os.path.expanduser("~/Apps/databases/Cruise_Logs.db")

if not os.path.exists(DB_PATH):
    print(f"WARNING: Database file not found at {DB_PATH}")

def check_database_table():
    """Check if recoveries_normalized table exists and get column info."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='recoveries_normalized'
        """)
        if not cursor.fetchone():
            return False, []

        # Get column names
        cursor.execute("PRAGMA table_info(recoveries_normalized)")
        columns = [row[1] for row in cursor.fetchall()]
        return True, columns
    except Exception as e:
        return False, []
    finally:
        conn.close()

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def format_wind_direction_nautical(wind_dir):
    """
    Format wind direction to nautical format (3 digits, e.g., '009' for 9.0 degrees).
    Returns empty string if input is invalid.
    """
    if wind_dir is None or wind_dir == '':
        return ''
    try:
        # Convert to float first to handle various input formats
        dir_float = float(wind_dir)
        # Ensure it's within 0-360 range
        if 0 <= dir_float <= 360:
            # Format as 3-digit string with leading zeros
            return f"{int(dir_float):03d}"
        else:
            return str(wind_dir)  # Return as-is if out of range
    except (ValueError, TypeError):
        return str(wind_dir) if wind_dir else ''

def parse_wind_direction_from_nautical(nautical_dir):
    """
    Parse nautical format wind direction back to numeric string.
    E.g., '009' -> '9', '045' -> '45', '270' -> '270'
    """
    if nautical_dir is None or nautical_dir == '':
        return ''
    try:
        # Remove leading zeros and convert to string
        return str(int(nautical_dir))
    except (ValueError, TypeError):
        return str(nautical_dir) if nautical_dir else ''

def clean_serial_number(sn):
    """
    Clean serial number to remove decimal points if it's a whole number.
    E.g., '11153.0' -> '11153', 'D196' -> 'D196'
    """
    if sn is None or sn == '':
        return ''

    sn_str = str(sn)

    # Check if it looks like a float with .0
    if '.' in sn_str:
        try:
            # Try to convert to float then int
            num = float(sn_str)
            if num.is_integer():
                return str(int(num))
        except (ValueError, TypeError):
            pass

    return sn_str

def format_clock_error_to_mmss(mmss_value):
    """
    Format database MMSS value to MM:SS display format.
    Database stores as integer where 240 means 2:40, not 240 seconds.
    E.g., 240 -> '2:40', -30 -> '-0:30', 1005 -> '10:05'
    """
    if mmss_value is None or mmss_value == '':
        return ''

    try:
        # Convert to integer
        value = int(float(str(mmss_value)))

        # Handle negative values
        sign = '-' if value < 0 else ''
        value = abs(value)

        # Extract minutes and seconds from MMSS format
        # For values < 100, treat as seconds only (e.g., 30 -> 0:30)
        # For values >= 100, split as MMSS (e.g., 240 -> 2:40, 1005 -> 10:05)
        if value < 100:
            minutes = 0
            secs = value
        else:
            # Last two digits are seconds, rest are minutes
            minutes = value // 100
            secs = value % 100

        return f"{sign}{minutes}:{secs:02d}"
    except (ValueError, TypeError):
        # If conversion fails, return as-is
        return str(mmss_value) if mmss_value else ''

def parse_clock_error_from_mmss(mmss):
    """
    Parse MM:SS format back to database MMSS integer format.
    E.g., '2:40' -> 240, '-0:30' -> -30, '10:05' -> 1005
    """
    if mmss is None or mmss == '':
        return ''

    mmss_str = str(mmss)

    # Check if it's already in MMSS format (just a number without colon)
    try:
        if ':' not in mmss_str:
            # Already in database format, return as-is
            return str(int(float(mmss_str)))
    except (ValueError, TypeError):
        pass

    # Parse MM:SS format
    try:
        # Handle negative values
        sign = 1
        if mmss_str.startswith('-'):
            sign = -1
            mmss_str = mmss_str[1:]

        # Split minutes and seconds
        parts = mmss_str.split(':')
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = int(parts[1])
            # Convert to MMSS format (e.g., 2:40 -> 240, 10:05 -> 1005)
            mmss_value = sign * (minutes * 100 + seconds)
            return str(mmss_value)
        else:
            return mmss_str
    except (ValueError, TypeError):
        return mmss_str

def export_record_to_xml(record_data):
    """
    Convert a recovery record to XML format

    Args:
        record_data: Dictionary containing the recovery record data

    Returns:
        str: Pretty-formatted XML string
    """
    # Create root element
    root = ET.Element("recovery_record")

    # Add timestamp
    export_time = ET.SubElement(root, "export_timestamp")
    export_time.text = datetime.now().isoformat()

    # Group related fields
    # Basic Information
    basic_info = ET.SubElement(root, "basic_information")
    for field in ['site', 'mooringid', 'cruise', 'mooring_status', 'mooring_type', 'personnel']:
        if field in record_data and record_data[field]:
            elem = ET.SubElement(basic_info, field)
            elem.text = str(record_data[field])

    # Location Information
    location_info = ET.SubElement(root, "location_information")
    for field in ['argos_latitude', 'argos_longitude', 'release_latitude', 'release_longitude']:
        if field in record_data and record_data[field]:
            elem = ET.SubElement(location_info, field)
            elem.text = str(record_data[field])

    # Time Information
    time_info = ET.SubElement(root, "time_information")
    for field in ['touch_time', 'fire_time', 'fire_date', 'release_fire_date', 'relfiredate', 'rec_date', 'recovery_date', 'date']:
        if field in record_data and record_data[field]:
            elem = ET.SubElement(time_info, field)
            elem.text = str(record_data[field])

    # Surface Instrument Information
    surface_inst = ET.SubElement(root, "surface_instruments")
    for field in ['buoy_sn', 'buoy_type', 'buoy_hull_color', 'buoy_data_complete', 'buoy_vdata_complete']:
        if field in record_data and record_data[field]:
            elem = ET.SubElement(surface_inst, field)
            elem.text = str(record_data[field])

    # Subsurface Instruments
    if 'subsurface_instruments' in record_data:
        try:
            import json
            subsurface_data = record_data['subsurface_instruments']
            if isinstance(subsurface_data, str):
                subsurface_data = json.loads(subsurface_data)

            subsurface_elem = ET.SubElement(root, "subsurface_instruments")
            if isinstance(subsurface_data, list):
                for idx, inst in enumerate(subsurface_data):
                    inst_elem = ET.SubElement(subsurface_elem, f"instrument_{idx}")
                    for key, value in inst.items():
                        if value:
                            field_elem = ET.SubElement(inst_elem, key)
                            field_elem.text = str(value)
        except:
            pass

    # Nylon Information
    nylon_info = ET.SubElement(root, "nylon_recovered")
    for i in range(10):
        nylon_item = {}
        for field in ['spool', 'sn', 'length', 'condition']:
            key = f'nylon_{field}_{i}'
            if key in record_data and record_data[key]:
                nylon_item[field] = record_data[key]

        if nylon_item:
            nylon_elem = ET.SubElement(nylon_info, f"nylon_{i}")
            for key, value in nylon_item.items():
                elem = ET.SubElement(nylon_elem, key)
                elem.text = str(value)

    # Hardware Information
    hardware_info = ET.SubElement(root, "hardware")
    for field in ['buoy_hardware_sn', 'buoy_hardware_condition', 'buoy_top_section_sn',
                  'buoy_glass_balls', 'wire_hardware_sn', 'wire_hardware_condition',
                  'wire_top_section_sn', 'wire_glass_balls']:
        if field in record_data and record_data[field]:
            elem = ET.SubElement(hardware_info, field)
            elem.text = str(record_data[field])

    # Tube Information
    tube_info = ET.SubElement(root, "tube_information")
    for field in ['battery_logic', 'battery_transmit', 'tube_date', 'tube_actual_time',
                  'tube_inst_time', 'tube_clock_error']:
        if field in record_data and record_data[field]:
            elem = ET.SubElement(tube_info, field)
            elem.text = str(record_data[field])

    # Release Information
    release_info = ET.SubElement(root, "release_information")
    for field in ['rel_type_1', 'rel_sn_1', 'rel_1_rec', 'rel_type_2', 'rel_sn_2', 'rel_2_rec',
                  'release1_release', 'release1_disable', 'release1_enable',
                  'release2_release', 'release2_disable', 'release2_enable', 'release_comments']:
        if field in record_data and record_data[field]:
            elem = ET.SubElement(release_info, field)
            elem.text = str(record_data[field])

    # Subsurface Clock Errors
    if 'subsurface_clock_errors' in record_data:
        try:
            import json
            clock_error_data = record_data['subsurface_clock_errors']
            if isinstance(clock_error_data, str):
                clock_error_data = json.loads(clock_error_data)

            clock_errors_elem = ET.SubElement(root, "subsurface_clock_errors")
            if isinstance(clock_error_data, list):
                for idx, error in enumerate(clock_error_data):
                    error_elem = ET.SubElement(clock_errors_elem, f"clock_error_{idx}")
                    for key, value in error.items():
                        if value:
                            field_elem = ET.SubElement(error_elem, key)
                            field_elem.text = str(value)
        except:
            pass

    # Pretty print the XML
    xml_str = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")

    # Remove extra blank lines
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    return '\n'.join(lines)

def calculate_clock_error(actual_time, instrument_time):
    """
    Calculate clock error as actual_time - inst_time.
    Returns the result in M:SS format.

    Args:
        actual_time: Time string in HH:mm:ss format
        inst_time: Time string in HH:mm:ss format

    Returns:
        String in M:SS format, or empty string if calculation fails
    """
    if not actual_time or not inst_time:
        return ''

    try:
        from datetime import datetime, timedelta

        # Parse times - use a dummy date for calculation
        actual = datetime.strptime(f"2000-01-01 {actual_time}", "%Y-%m-%d %H:%M:%S")
        inst = datetime.strptime(f"2000-01-01 {inst_time}", "%Y-%m-%d %H:%M:%S")

        # Calculate difference in seconds
        diff = actual - inst
        total_seconds = int(diff.total_seconds())

        # Handle negative values
        sign = ''
        if total_seconds < 0:
            sign = '-'
            total_seconds = abs(total_seconds)

        # Convert to minutes and seconds
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        return f"{sign}{minutes}:{seconds:02d}"
    except:
        return ''

def get_distinct_sites():
    """Get all distinct sites from the database."""
    conn = get_db_connection()
    try:
        query = "SELECT DISTINCT site FROM recoveries_normalized WHERE site IS NOT NULL AND site != '' ORDER BY site"
        cursor = conn.cursor()
        cursor.execute(query)
        sites = [row[0] for row in cursor.fetchall()]
        return sites
    except Exception as e:
        print(f"Error fetching sites: {e}")
        return []
    finally:
        conn.close()

def search_recoveries(search_criteria):
    """Search recoveries based on criteria."""
    conn = get_db_connection()

    # Build WHERE clause dynamically
    where_clauses = []
    params = []

    if search_criteria.get('site'):
        where_clauses.append("site LIKE ?")
        params.append(f"%{search_criteria['site']}%")

    if search_criteria.get('mooringid'):
        where_clauses.append("mooring_id LIKE ?")
        params.append(f"%{search_criteria['mooringid']}%")

    if search_criteria.get('cruise'):
        where_clauses.append("cruise LIKE ?")
        params.append(f"%{search_criteria['cruise']}%")

    # Personnel search (simplified for normalized table)
    if search_criteria.get('personnel'):
        personnel_val = f"%{search_criteria['personnel']}%"
        where_clauses.append("personnel LIKE ?")
        params.append(personnel_val)

    # Construct query - sort by mooring_id descending to show most recent moorings first
    if where_clauses:
        query = f"SELECT * FROM recoveries_normalized WHERE {' AND '.join(where_clauses)} ORDER BY mooring_id DESC"
        df = pd.read_sql_query(query, conn, params=params, index_col=None, parse_dates=False)
    else:
        query = "SELECT * FROM recoveries_normalized ORDER BY mooring_id DESC LIMIT 100"
        df = pd.read_sql_query(query, conn, index_col=None, parse_dates=False)

    conn.close()

    # Get date column info for string conversion
    table_exists, available_columns = check_database_table()
    date_column = None
    possible_date_columns = ['release_fire_date', 'relfiredate', 'rec_date', 'recovery_date', 'date']
    for col in possible_date_columns:
        if col in available_columns:
            date_column = col
            break

    # Ensure date column is properly converted to string
    if date_column and date_column in df.columns:
        df[date_column] = df[date_column].fillna('').astype(str).replace('None', '').replace('nan', '').replace('<NA>', '')

    # Ensure id column exists
    if 'id' not in df.columns:
        print(f"WARNING: 'id' column not found in query results. Available columns: {list(df.columns)[:10]}")

    return df

def update_recovery_data(recovery_id, form_data):
    """Update existing recovery data."""
    import json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if table exists
        table_exists, available_columns = check_database_table()
        if not table_exists:
            return False, "Recoveries_normalized table not found."

        # Map form fields to database columns (flexible mapping)
        db_data = {}

        # Basic fields - try multiple possible column names
        basic_field_mappings = {
            'site': ['site'],
            'mooringid': ['mooring_id', 'mooringid'],
            'cruise': ['cruise'],
            'mooring_status': ['statuspriortodeparture'],
            'mooring_type': ['mooring_type'],
            'personnel': ['personnel'],
            'touch_time': ['touch_time'],
        }

        # Release Info fields - try multiple possible column names
        release_info_mappings = {
            'release_latitude': ['relfirelat'],
            'release_longitude': ['relfirelong'],
            'fire_time': ['relfiretime'],
            'fire_date': ['relfiredate'],
            'time_on_deck': ['relon_decktime'],
            'date_on_deck': ['dateondeck'],
        }

        # Met Sensors fields - try multiple possible column names
        met_sensors_mappings = {
            'tube_sn': ['tubesn'],
            'tube_condition': ['tube_condition'],
            'tube_details': ['tube_details'],
            'ptt_hexid_sn': ['ptt_id'],
            'ptt_hexid_condition': ['ptt_hexid_condition'],
            'ptt_hexid_details': ['ptt_hexid_details'],
            'at_rh_sn': ['atrh_sn'],
            'at_rh_condition': ['at_rh_condition', 'atrh_condition'],
            'at_rh_details': ['at_rh_details'],
            'wind_sn': ['windsn'],
            'wind_condition': ['wind_condition'],
            'wind_details': ['wind_details'],
            'rain_gauge_sn': ['rain_sn'],
            'rain_gauge_condition': ['rain_gauge_condition', 'rain_condition'],
            'rain_gauge_details': ['rain_gauge_details'],
            'sw_radiation_sn': ['swrad_sn'],
            'sw_radiation_condition': ['sw_radiation_condition', 'swrad_condition'],
            'sw_radiation_details': ['sw_radiation_details'],
            'lw_radiation_sn': ['lwrad_sn'],
            'lw_radiation_condition': ['lw_radiation_condition', 'lwrad_condition'],
            'lw_radiation_details': ['lw_radiation_details'],
            'barometer_sn': ['baro_sn'],
            'barometer_condition': ['barometer_condition', 'baro_condition'],
            'barometer_details': ['barometer_details'],
            'seacat_sn': ['seacat_sn'],
            'seacat_condition': ['seacat_condition'],
            'seacat_details': ['seacat_details'],
        }

        # Argos fields - try multiple possible column names
        argos_mappings = {
            'argos_latitude': ['argoslat'],
            'argos_longitude': ['argoslong'],
        }

        # Met Obs fields - data is stored as JSON in ship_met_data and buoy_met_data columns
        # We'll handle this differently in the form loading section
        met_obs_mappings = {
            'ship_date': ['ship_met_data'],
            'buoy_date': ['buoy_met_data'],
            'ship_time': ['ship_met_data'],
            'buoy_time': ['buoy_met_data'],
            'ship_wind_dir': ['ship_met_data'],
            'buoy_wind_dir': ['buoy_met_data'],
            'ship_wind_spd': ['ship_met_data'],
            'buoy_wind_spd': ['buoy_met_data'],
            'ship_air_temp': ['ship_met_data'],
            'buoy_air_temp': ['buoy_met_data'],
            'ship_sst': ['ship_met_data'],
            'buoy_sst': ['buoy_met_data'],
            'ship_ssc': ['ship_met_data'],
            'buoy_ssc': ['buoy_met_data'],
            'ship_rh': ['ship_met_data'],
            'buoy_rh': ['buoy_met_data'],
            'fishing_vandalism': ['fishing_or_vandalism'],
        }

        # Combine all mappings
        all_mappings = {**basic_field_mappings, **release_info_mappings, **met_sensors_mappings, **argos_mappings, **met_obs_mappings}

        # Handle basic fields (non-Met Obs)
        for form_field, possible_db_fields in basic_field_mappings.items():
            value = form_data.get(form_field, '')
            if value:  # Only add if there's a value
                for db_field in possible_db_fields:
                    if db_field in available_columns:
                        db_data[db_field] = value
                        break

        # Handle release info fields
        for form_field, possible_db_fields in release_info_mappings.items():
            value = form_data.get(form_field, '')
            if value:  # Only add if there's a value
                for db_field in possible_db_fields:
                    if db_field in available_columns:
                        db_data[db_field] = value
                        break

        # Handle met sensors fields (special JSON handling for condition fields)

        # Handle S/N fields (simple text)
        sn_fields = ['tube_sn', 'ptt_hexid_sn', 'at_rh_sn', 'wind_sn', 'rain_gauge_sn', 'sw_radiation_sn', 'lw_radiation_sn', 'barometer_sn', 'seacat_sn']
        for form_field in sn_fields:
            if form_field in met_sensors_mappings:
                value = form_data.get(form_field, '')
                if value:
                    for db_field in met_sensors_mappings[form_field]:
                        if db_field in available_columns:
                            db_data[db_field] = value
                            break

        # Handle condition/details fields (JSON format)
        sensor_types = ['tube', 'ptt_hexid', 'at_rh', 'wind', 'rain_gauge', 'sw_radiation', 'lw_radiation', 'barometer', 'seacat']
        for sensor_type in sensor_types:
            condition_field = f"{sensor_type}_condition"
            details_field = f"{sensor_type}_details"

            condition_value = form_data.get(condition_field, '')
            details_value = form_data.get(details_field, '')

            # Create JSON object if we have condition or details
            if condition_value or details_value:
                json_data = {
                    "condition": condition_value,
                    "details": details_value,
                    "picture": None
                }

                # Find the database column for this condition field
                if condition_field in met_sensors_mappings:
                    for db_field in met_sensors_mappings[condition_field]:
                        if db_field in available_columns:
                            db_data[db_field] = json.dumps(json_data)
                            break

        # Handle argos fields
        for form_field, possible_db_fields in argos_mappings.items():
            value = form_data.get(form_field, '')
            if value:  # Only add if there's a value
                for db_field in possible_db_fields:
                    if db_field in available_columns:
                        db_data[db_field] = value
                        break

        # Handle Met Obs fields (JSON structure)
        ship_met_data = {}
        buoy_met_data = {}

        # Collect ship met obs data
        if form_data.get('ship_date'): ship_met_data['date'] = form_data['ship_date']
        if form_data.get('ship_time'): ship_met_data['time'] = form_data['ship_time']
        if form_data.get('ship_wind_dir'):
            # Parse from nautical format before saving
            ship_met_data['wind_direction'] = parse_wind_direction_from_nautical(form_data['ship_wind_dir'])
        if form_data.get('ship_wind_spd'): ship_met_data['wind_speed'] = form_data['ship_wind_spd']
        if form_data.get('ship_air_temp'): ship_met_data['air_temp'] = form_data['ship_air_temp']
        if form_data.get('ship_sst'): ship_met_data['sea_surface_temp'] = form_data['ship_sst']
        if form_data.get('ship_ssc'): ship_met_data['ssc'] = form_data['ship_ssc']
        if form_data.get('ship_rh'): ship_met_data['relative_humidity'] = form_data['ship_rh']

        # Collect buoy met obs data
        if form_data.get('buoy_date'): buoy_met_data['date'] = form_data['buoy_date']
        if form_data.get('buoy_time'): buoy_met_data['time'] = form_data['buoy_time']
        if form_data.get('buoy_wind_dir'):
            # Parse from nautical format before saving
            buoy_met_data['wind_direction'] = parse_wind_direction_from_nautical(form_data['buoy_wind_dir'])
        if form_data.get('buoy_wind_spd'): buoy_met_data['wind_speed'] = form_data['buoy_wind_spd']
        if form_data.get('buoy_air_temp'): buoy_met_data['air_temp'] = form_data['buoy_air_temp']
        if form_data.get('buoy_sst'): buoy_met_data['sea_surface_temp'] = form_data['buoy_sst']
        if form_data.get('buoy_ssc'): buoy_met_data['ssc'] = form_data['buoy_ssc']
        if form_data.get('buoy_rh'): buoy_met_data['relative_humidity'] = form_data['buoy_rh']

        # Add JSON data to database fields if columns exist and data is present
        import json
        if ship_met_data and 'ship_met_data' in available_columns:
            db_data['ship_met_data'] = json.dumps(ship_met_data)
        if buoy_met_data and 'buoy_met_data' in available_columns:
            db_data['buoy_met_data'] = json.dumps(buoy_met_data)

        # Handle Fishing/Vandalism Evidence
        fishing_vandalism_value = form_data.get('fishing_vandalism', '')
        if fishing_vandalism_value:
            for db_field in ['fishing_or_vandalism']:
                if db_field in available_columns:
                    db_data[db_field] = fishing_vandalism_value
                    break

        # Handle Nylon Recovered (simplified table format)
        nylon_spools = []
        for i in range(10):  # Support up to 10 spools
            spool = form_data.get(f'nylon_spool_{i}')
            sn = form_data.get(f'nylon_sn_{i}')
            length = form_data.get(f'nylon_length_{i}')
            condition = form_data.get(f'nylon_condition_{i}')

            if any([spool, sn, length, condition]):
                nylon_spools.append({
                    'line_number': int(spool) if spool and spool.isdigit() else spool,
                    'serial_number': sn,
                    'length': float(length) if length and length.replace('.', '', 1).isdigit() else length,
                    'comments': condition if condition else None
                })

        if nylon_spools:
            if 'nylon_lines' in available_columns:
                db_data['nylon_lines'] = json.dumps(nylon_spools)

        # Handle Hardware - save to individual columns
        if 'buoy_sn' in available_columns and form_data.get('buoy_hardware_sn'):
            db_data['buoy_sn'] = form_data.get('buoy_hardware_sn', '')
        if 'buoy_condition' in available_columns and form_data.get('buoy_hardware_condition'):
            db_data['buoy_condition'] = form_data.get('buoy_hardware_condition', '')
        if 'top_section_sn' in available_columns and form_data.get('buoy_top_section_sn'):
            db_data['top_section_sn'] = form_data.get('buoy_top_section_sn', '')
        if 'glassballs' in available_columns and form_data.get('buoy_glass_balls'):
            try:
                # Try to save as integer if possible
                db_data['glassballs'] = int(form_data.get('buoy_glass_balls', 0))
            except (ValueError, TypeError):
                db_data['glassballs'] = form_data.get('buoy_glass_balls', '')
        if 'wiresn' in available_columns and form_data.get('wire_hardware_sn'):
            db_data['wiresn'] = form_data.get('wire_hardware_sn', '')
        if 'wirecond' in available_columns and form_data.get('wire_hardware_condition'):
            db_data['wirecond'] = form_data.get('wire_hardware_condition', '')

        # Handle Tube fields - save to individual columns
        if 'batlogic' in available_columns and form_data.get('battery_logic'):
            db_data['batlogic'] = form_data.get('battery_logic', '')
        if 'battransmit' in available_columns and form_data.get('battery_transmit'):
            db_data['battransmit'] = form_data.get('battery_transmit', '')
        if 'batdate' in available_columns and form_data.get('tube_date'):
            db_data['batdate'] = form_data.get('tube_date', '')
        if 'gmt_tube' in available_columns and form_data.get('tube_actual_time'):
            db_data['gmt_tube'] = form_data.get('tube_actual_time', '')
        # Note: tube_inst_time also maps to gmt_tube but we already set it with actual_time
        # Since both should be the same, we'll use actual_time as the primary source
        if 'clk_err_tube' in available_columns and form_data.get('tube_clock_error'):
            db_data['clk_err_tube'] = parse_clock_error_from_mmss(form_data.get('tube_clock_error', ''))

        # Handle Subsurface Instruments
        subsurface_instruments = form_data.get('subsurface_instruments', [])
        if subsurface_instruments:
            # Store subsurface_instruments JSON with address included
            for db_field in ['subsurface_instruments']:
                if db_field in available_columns:
                    db_data[db_field] = json.dumps(subsurface_instruments)
                    break

            # Also extract and save instrument_addresses separately if the column exists
            if 'instrument_addresses' in available_columns:
                instrument_addresses = []
                for inst in subsurface_instruments:
                    if inst.get('address'):  # Only include if address is not empty
                        instrument_addresses.append({
                            'position': inst.get('position', 0),
                            'address': inst.get('address', '')
                        })
                # Only save if there are actual addresses
                if instrument_addresses:
                    db_data['instrument_addresses'] = json.dumps(instrument_addresses)
                else:
                    db_data['instrument_addresses'] = None

        # Handle Subsurface Clock Errors - store as JSON in instrument_timing column
        subsurface_clock_errors = form_data.get('subsurface_clock_errors', [])
        if subsurface_clock_errors:
            # Convert to database format
            timing_data = []
            battery_data = []
            for sce in subsurface_clock_errors:
                # Keep times in HH:mm:ss format (no decimal seconds)
                actual_time = sce.get('actual_time', '')
                if actual_time and ':' in actual_time and actual_time.count(':') == 1:
                    actual_time = f"{actual_time}:00"
                # If already has HH:mm:ss format, keep it as is

                inst_time = sce.get('inst_time', '')
                if inst_time and ':' in inst_time and inst_time.count(':') == 1:
                    inst_time = f"{inst_time}:00"
                # If already has HH:mm:ss format, keep it as is

                timing_data.append({
                    'position': sce.get('position', 0),
                    'gmt_time': actual_time,
                    'instrument_time': inst_time,
                    'clock_error': sce.get('clock_error', ''),
                    'sensor_type': sce.get('sensor_type', ''),
                    'serial_number': sce.get('serial_number', '')
                })

                # Also collect battery voltage data if present
                if sce.get('battery_voltage'):
                    battery_data.append({
                        'position': sce.get('position', 0),
                        'voltage': sce.get('battery_voltage', '')
                    })

            if 'instrument_timing' in available_columns:
                db_data['instrument_timing'] = json.dumps(timing_data)

            if battery_data and 'battery_voltages' in available_columns:
                db_data['battery_voltages'] = json.dumps(battery_data)

            # Handle fname JSON column for filenames
            fname_data = []
            for sce in subsurface_clock_errors:
                if sce.get('filename'):
                    fname_data.append({
                        'position': sce.get('position', 0),
                        'value': sce.get('filename', '')
                    })

            if fname_data and 'fname' in available_columns:
                db_data['fname'] = json.dumps(fname_data)

            # Handle numofrec JSON column for number of records
            numofrec_data = []
            for sce in subsurface_clock_errors:
                if sce.get('number_of_records'):
                    numofrec_data.append({
                        'position': sce.get('position', 0),
                        'value': sce.get('number_of_records', '')
                    })

            if numofrec_data and 'numofrec' in available_columns:
                db_data['numofrec'] = json.dumps(numofrec_data)

            # Handle errcom JSON column for comments
            errcom_data = []
            for sce in subsurface_clock_errors:
                if sce.get('comments'):
                    errcom_data.append({
                        'position': sce.get('position', 0),  # Use 0-based position directly
                        'value': sce.get('comments', '')
                    })

            if errcom_data and 'errcom' in available_columns:
                db_data['errcom'] = json.dumps(errcom_data)

        # Handle Release Commands JSON
        release_commands = []

        # Add Release 1 commands if values exist
        if form_data.get('release1_release'):
            release_commands.append({
                "command_field": "rel8_relsn1::cmd_1/a_code_function_reply",
                "response": float(form_data['release1_release']) if form_data['release1_release'].replace('.', '').replace('-', '').isdigit() else form_data['release1_release']
            })
        if form_data.get('release1_disable'):
            release_commands.append({
                "command_field": "rel8_relsn1::cmd_2/b_code_function_reply",
                "response": float(form_data['release1_disable']) if form_data['release1_disable'].replace('.', '').replace('-', '').isdigit() else form_data['release1_disable']
            })
        if form_data.get('release1_enable'):
            release_commands.append({
                "command_field": "rel8_relsn1::cmd_3/c_code_function_reply",
                "response": float(form_data['release1_enable']) if form_data['release1_enable'].replace('.', '').replace('-', '').isdigit() else form_data['release1_enable']
            })

        # Add Release 2 commands if values exist
        if form_data.get('release2_release'):
            release_commands.append({
                "command_field": "rel8_relsn2::cmd_1/a_code_function_reply",
                "response": float(form_data['release2_release']) if form_data['release2_release'].replace('.', '').replace('-', '').isdigit() else form_data['release2_release']
            })
        if form_data.get('release2_disable'):
            release_commands.append({
                "command_field": "rel8_relsn2::cmd_2/b_code_function_reply",
                "response": float(form_data['release2_disable']) if form_data['release2_disable'].replace('.', '').replace('-', '').isdigit() else form_data['release2_disable']
            })
        if form_data.get('release2_enable'):
            release_commands.append({
                "command_field": "rel8_relsn2::cmd_3/c_code_function_reply",
                "response": float(form_data['release2_enable']) if form_data['release2_enable'].replace('.', '').replace('-', '').isdigit() else form_data['release2_enable']
            })

        # Add release commands JSON to database if column exists and commands exist
        if release_commands and 'release_commands' in available_columns:
            db_data['release_commands'] = json.dumps(release_commands)

        # Handle release information fields
        release_info_fields = {
            'rel_type_1': ['rel_type_1'],
            'rel_sn_1': ['rel_sn_1'],
            'rel_1_rec': ['rel_1_rec'],
            'rel_type_2': ['rel_type_2'],
            'rel_sn_2': ['rel_sn_2'],
            'rel_2_rec': ['rel_2_rec'],
            'release_comments': ['release_comments']
        }

        for form_field, possible_db_fields in release_info_fields.items():
            value = form_data.get(form_field, '')
            if value:
                for db_field in possible_db_fields:
                    if db_field in available_columns:
                        db_data[db_field] = value
                        break

        if not db_data:
            return False, "No matching columns found in database"

        # Validate recovery_id before proceeding
        if recovery_id is None or str(recovery_id).strip() == '':
            return False, "Invalid recovery ID provided. Cannot update."

        # Find the actual date column name that exists
        date_col = 'id'  # fallback
        for col in ['release_fire_date', 'relfiredate', 'rec_date', 'recovery_date', 'date']:
            if col in available_columns:
                date_col = col
                break

        # Verify recovery exists before update
        cursor.execute(f"SELECT id, {date_col}, mooring_id FROM recoveries_normalized WHERE id = ?", [recovery_id])
        before_update = cursor.fetchone()

        if not before_update:
            # Try converting to int if it's a string
            try:
                recovery_id_int = int(recovery_id)
                cursor.execute(f"SELECT id, {date_col}, mooring_id FROM recoveries_normalized WHERE id = ?", [recovery_id_int])
                before_update = cursor.fetchone()
                if before_update:
                    recovery_id = recovery_id_int
            except (ValueError, TypeError):
                pass

        if not before_update:
            conn.rollback()
            return False, f"Record with ID {recovery_id} not found in database. Update aborted to prevent data corruption."

        # Build UPDATE query with explicit ID check
        set_clauses = [f'"{k}" = ?' for k in db_data.keys()]
        query = f'UPDATE recoveries_normalized SET {", ".join(set_clauses)} WHERE id = ? AND id IS NOT NULL'

        values = list(db_data.values()) + [recovery_id]

        # Execute with explicit error handling
        try:
            rows_affected = cursor.execute(query, values).rowcount
            if rows_affected == 0:
                conn.rollback()
                return False, f"No rows updated. Record with ID {recovery_id} may not exist."
            elif rows_affected > 1:
                conn.rollback()
                return False, f"Error: Multiple rows ({rows_affected}) would be affected. Update aborted to prevent data corruption."
            conn.commit()
        except Exception as update_error:
            conn.rollback()
            return False, f"Database update failed: {update_error}"

        # Verify with same connection first
        cursor.execute(f"SELECT id, mooring_id, {date_col}, site, cruise FROM recoveries_normalized WHERE id = ?", [recovery_id])
        result = cursor.fetchone()

        # Now close and verify with new connection
        conn.close()

        # Verify with a completely new connection
        verify_conn = sqlite3.connect(DB_PATH)
        verify_cursor = verify_conn.cursor()
        verify_cursor.execute(f"SELECT id, mooring_id, {date_col}, site, cruise FROM recoveries_normalized WHERE id = ?", [recovery_id])
        fresh_result = verify_cursor.fetchone()

        if fresh_result:
            verify_conn.close()
            return True, {'id': recovery_id, date_col: fresh_result[2], 'mooring_id': fresh_result[1]}
        else:
            verify_conn.close()
            return False, "Update may have failed - could not verify in database"
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()

def save_recovery_data(form_data):
    """Save recovery data to database."""
    import json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if table exists
        table_exists, available_columns = check_database_table()
        if not table_exists:
            return False, "Recoveries_normalized table not found. Please ensure the table is created first."

        # Map form fields to database columns (flexible mapping)
        db_data = {}

        # Basic fields - try multiple possible column names
        basic_field_mappings = {
            'site': ['site'],
            'mooringid': ['mooring_id', 'mooringid'],
            'cruise': ['cruise'],
            'mooring_status': ['statuspriortodeparture'],
            'mooring_type': ['mooring_type'],
            'personnel': ['personnel'],
            'touch_time': ['touch_time'],
        }

        # Release Info fields - try multiple possible column names
        release_info_mappings = {
            'release_latitude': ['relfirelat'],
            'release_longitude': ['relfirelong'],
            'fire_time': ['relfiretime'],
            'fire_date': ['relfiredate'],
            'time_on_deck': ['relon_decktime'],
            'date_on_deck': ['dateondeck'],
        }

        # Met Sensors fields - try multiple possible column names
        met_sensors_mappings = {
            'tube_sn': ['tubesn'],
            'tube_condition': ['tube_condition'],
            'tube_details': ['tube_details'],
            'ptt_hexid_sn': ['ptt_id'],
            'ptt_hexid_condition': ['ptt_hexid_condition'],
            'ptt_hexid_details': ['ptt_hexid_details'],
            'at_rh_sn': ['atrh_sn'],
            'at_rh_condition': ['at_rh_condition', 'atrh_condition'],
            'at_rh_details': ['at_rh_details'],
            'wind_sn': ['windsn'],
            'wind_condition': ['wind_condition'],
            'wind_details': ['wind_details'],
            'rain_gauge_sn': ['rain_sn'],
            'rain_gauge_condition': ['rain_gauge_condition', 'rain_condition'],
            'rain_gauge_details': ['rain_gauge_details'],
            'sw_radiation_sn': ['swrad_sn'],
            'sw_radiation_condition': ['sw_radiation_condition', 'swrad_condition'],
            'sw_radiation_details': ['sw_radiation_details'],
            'lw_radiation_sn': ['lwrad_sn'],
            'lw_radiation_condition': ['lw_radiation_condition', 'lwrad_condition'],
            'lw_radiation_details': ['lw_radiation_details'],
            'barometer_sn': ['baro_sn'],
            'barometer_condition': ['barometer_condition', 'baro_condition'],
            'barometer_details': ['barometer_details'],
            'seacat_sn': ['seacat_sn'],
            'seacat_condition': ['seacat_condition'],
            'seacat_details': ['seacat_details'],
        }

        # Argos fields - try multiple possible column names
        argos_mappings = {
            'argos_latitude': ['argoslat'],
            'argos_longitude': ['argoslong'],
        }

        # Met Obs fields - data is stored as JSON in ship_met_data and buoy_met_data columns
        # We'll handle this differently in the form loading section
        met_obs_mappings = {
            'ship_date': ['ship_met_data'],
            'buoy_date': ['buoy_met_data'],
            'ship_time': ['ship_met_data'],
            'buoy_time': ['buoy_met_data'],
            'ship_wind_dir': ['ship_met_data'],
            'buoy_wind_dir': ['buoy_met_data'],
            'ship_wind_spd': ['ship_met_data'],
            'buoy_wind_spd': ['buoy_met_data'],
            'ship_air_temp': ['ship_met_data'],
            'buoy_air_temp': ['buoy_met_data'],
            'ship_sst': ['ship_met_data'],
            'buoy_sst': ['buoy_met_data'],
            'ship_ssc': ['ship_met_data'],
            'buoy_ssc': ['buoy_met_data'],
            'ship_rh': ['ship_met_data'],
            'buoy_rh': ['buoy_met_data'],
            'fishing_vandalism': ['fishing_or_vandalism'],
        }

        # Combine all mappings
        all_mappings = {**basic_field_mappings, **release_info_mappings, **met_sensors_mappings, **argos_mappings, **met_obs_mappings}

        # Handle basic fields (non-Met Obs)
        for form_field, possible_db_fields in basic_field_mappings.items():
            value = form_data.get(form_field, '')
            if value:  # Only add if there's a value
                for db_field in possible_db_fields:
                    if db_field in available_columns:
                        db_data[db_field] = value
                        break

        # Handle release info fields
        for form_field, possible_db_fields in release_info_mappings.items():
            value = form_data.get(form_field, '')
            if value:  # Only add if there's a value
                for db_field in possible_db_fields:
                    if db_field in available_columns:
                        db_data[db_field] = value
                        break

        # Handle met sensors fields (special JSON handling for condition fields)
        # Handle S/N fields (simple text)
        sn_fields = ['tube_sn', 'ptt_hexid_sn', 'at_rh_sn', 'wind_sn', 'rain_gauge_sn', 'sw_radiation_sn', 'lw_radiation_sn', 'barometer_sn', 'seacat_sn']
        for form_field in sn_fields:
            if form_field in met_sensors_mappings:
                value = form_data.get(form_field, '')
                if value:
                    for db_field in met_sensors_mappings[form_field]:
                        if db_field in available_columns:
                            db_data[db_field] = value
                            break

        # Handle condition/details fields (JSON format)
        sensor_types = ['tube', 'ptt_hexid', 'at_rh', 'wind', 'rain_gauge', 'sw_radiation', 'lw_radiation', 'barometer', 'seacat']
        for sensor_type in sensor_types:
            condition_field = f"{sensor_type}_condition"
            details_field = f"{sensor_type}_details"

            condition_value = form_data.get(condition_field, '')
            details_value = form_data.get(details_field, '')

            # Create JSON object if we have condition or details
            if condition_value or details_value:
                json_data = {
                    "condition": condition_value,
                    "details": details_value,
                    "picture": None
                }

                # Find the database column for this condition field
                if condition_field in met_sensors_mappings:
                    for db_field in met_sensors_mappings[condition_field]:
                        if db_field in available_columns:
                            db_data[db_field] = json.dumps(json_data)
                            break

        # Handle argos fields
        for form_field, possible_db_fields in argos_mappings.items():
            value = form_data.get(form_field, '')
            if value:  # Only add if there's a value
                for db_field in possible_db_fields:
                    if db_field in available_columns:
                        db_data[db_field] = value
                        break

        # Handle Met Obs fields (JSON structure)
        ship_met_data = {}
        buoy_met_data = {}

        # Collect ship met obs data
        if form_data.get('ship_date'): ship_met_data['date'] = form_data['ship_date']
        if form_data.get('ship_time'): ship_met_data['time'] = form_data['ship_time']
        if form_data.get('ship_wind_dir'):
            # Parse from nautical format before saving
            ship_met_data['wind_direction'] = parse_wind_direction_from_nautical(form_data['ship_wind_dir'])
        if form_data.get('ship_wind_spd'): ship_met_data['wind_speed'] = form_data['ship_wind_spd']
        if form_data.get('ship_air_temp'): ship_met_data['air_temp'] = form_data['ship_air_temp']
        if form_data.get('ship_sst'): ship_met_data['sea_surface_temp'] = form_data['ship_sst']
        if form_data.get('ship_ssc'): ship_met_data['ssc'] = form_data['ship_ssc']
        if form_data.get('ship_rh'): ship_met_data['relative_humidity'] = form_data['ship_rh']

        # Collect buoy met obs data
        if form_data.get('buoy_date'): buoy_met_data['date'] = form_data['buoy_date']
        if form_data.get('buoy_time'): buoy_met_data['time'] = form_data['buoy_time']
        if form_data.get('buoy_wind_dir'):
            # Parse from nautical format before saving
            buoy_met_data['wind_direction'] = parse_wind_direction_from_nautical(form_data['buoy_wind_dir'])
        if form_data.get('buoy_wind_spd'): buoy_met_data['wind_speed'] = form_data['buoy_wind_spd']
        if form_data.get('buoy_air_temp'): buoy_met_data['air_temp'] = form_data['buoy_air_temp']
        if form_data.get('buoy_sst'): buoy_met_data['sea_surface_temp'] = form_data['buoy_sst']
        if form_data.get('buoy_ssc'): buoy_met_data['ssc'] = form_data['buoy_ssc']
        if form_data.get('buoy_rh'): buoy_met_data['relative_humidity'] = form_data['buoy_rh']

        # Add JSON data to database fields if columns exist and data is present
        import json
        if ship_met_data and 'ship_met_data' in available_columns:
            db_data['ship_met_data'] = json.dumps(ship_met_data)
        if buoy_met_data and 'buoy_met_data' in available_columns:
            db_data['buoy_met_data'] = json.dumps(buoy_met_data)

        # Handle Fishing/Vandalism Evidence
        fishing_vandalism_value = form_data.get('fishing_vandalism', '')
        if fishing_vandalism_value:
            for db_field in ['fishing_or_vandalism']:
                if db_field in available_columns:
                    db_data[db_field] = fishing_vandalism_value
                    break

        # Handle Nylon Recovered (simplified table format)
        nylon_spools = []
        for i in range(10):  # Support up to 10 spools
            spool = form_data.get(f'nylon_spool_{i}')
            sn = form_data.get(f'nylon_sn_{i}')
            length = form_data.get(f'nylon_length_{i}')
            condition = form_data.get(f'nylon_condition_{i}')

            if any([spool, sn, length, condition]):
                nylon_spools.append({
                    'line_number': int(spool) if spool and spool.isdigit() else spool,
                    'serial_number': sn,
                    'length': float(length) if length and length.replace('.', '', 1).isdigit() else length,
                    'comments': condition if condition else None
                })

        if nylon_spools:
            if 'nylon_lines' in available_columns:
                db_data['nylon_lines'] = json.dumps(nylon_spools)

        # Handle Hardware - save to individual columns
        if 'buoy_sn' in available_columns and form_data.get('buoy_hardware_sn'):
            db_data['buoy_sn'] = form_data.get('buoy_hardware_sn', '')
        if 'buoy_condition' in available_columns and form_data.get('buoy_hardware_condition'):
            db_data['buoy_condition'] = form_data.get('buoy_hardware_condition', '')
        if 'top_section_sn' in available_columns and form_data.get('buoy_top_section_sn'):
            db_data['top_section_sn'] = form_data.get('buoy_top_section_sn', '')
        if 'glassballs' in available_columns and form_data.get('buoy_glass_balls'):
            try:
                # Try to save as integer if possible
                db_data['glassballs'] = int(form_data.get('buoy_glass_balls', 0))
            except (ValueError, TypeError):
                db_data['glassballs'] = form_data.get('buoy_glass_balls', '')
        if 'wiresn' in available_columns and form_data.get('wire_hardware_sn'):
            db_data['wiresn'] = form_data.get('wire_hardware_sn', '')
        if 'wirecond' in available_columns and form_data.get('wire_hardware_condition'):
            db_data['wirecond'] = form_data.get('wire_hardware_condition', '')

        # Handle Tube fields - save to individual columns
        if 'batlogic' in available_columns and form_data.get('battery_logic'):
            db_data['batlogic'] = form_data.get('battery_logic', '')
        if 'battransmit' in available_columns and form_data.get('battery_transmit'):
            db_data['battransmit'] = form_data.get('battery_transmit', '')
        if 'batdate' in available_columns and form_data.get('tube_date'):
            db_data['batdate'] = form_data.get('tube_date', '')
        if 'gmt_tube' in available_columns and form_data.get('tube_actual_time'):
            db_data['gmt_tube'] = form_data.get('tube_actual_time', '')
        # Note: tube_inst_time also maps to gmt_tube but we already set it with actual_time
        # Since both should be the same, we'll use actual_time as the primary source
        if 'clk_err_tube' in available_columns and form_data.get('tube_clock_error'):
            db_data['clk_err_tube'] = parse_clock_error_from_mmss(form_data.get('tube_clock_error', ''))

        # Handle Subsurface Instruments
        subsurface_instruments = form_data.get('subsurface_instruments', [])
        if subsurface_instruments:
            # Store subsurface_instruments JSON with address included
            for db_field in ['subsurface_instruments']:
                if db_field in available_columns:
                    db_data[db_field] = json.dumps(subsurface_instruments)
                    break

            # Also extract and save instrument_addresses separately if the column exists
            if 'instrument_addresses' in available_columns:
                instrument_addresses = []
                for inst in subsurface_instruments:
                    if inst.get('address'):  # Only include if address is not empty
                        instrument_addresses.append({
                            'position': inst.get('position', 0),
                            'address': inst.get('address', '')
                        })
                # Only save if there are actual addresses
                if instrument_addresses:
                    db_data['instrument_addresses'] = json.dumps(instrument_addresses)
                else:
                    db_data['instrument_addresses'] = None

        # Handle Subsurface Clock Errors - store as JSON in instrument_timing column
        subsurface_clock_errors = form_data.get('subsurface_clock_errors', [])
        if subsurface_clock_errors:
            # Convert to database format
            timing_data = []
            battery_data = []
            for sce in subsurface_clock_errors:
                # Keep times in HH:mm:ss format (no decimal seconds)
                actual_time = sce.get('actual_time', '')
                if actual_time and ':' in actual_time and actual_time.count(':') == 1:
                    actual_time = f"{actual_time}:00"
                # If already has HH:mm:ss format, keep it as is

                inst_time = sce.get('inst_time', '')
                if inst_time and ':' in inst_time and inst_time.count(':') == 1:
                    inst_time = f"{inst_time}:00"
                # If already has HH:mm:ss format, keep it as is

                timing_data.append({
                    'position': sce.get('position', 0),
                    'gmt_time': actual_time,
                    'instrument_time': inst_time,
                    'clock_error': sce.get('clock_error', ''),
                    'sensor_type': sce.get('sensor_type', ''),
                    'serial_number': sce.get('serial_number', '')
                })

                # Also collect battery voltage data if present
                if sce.get('battery_voltage'):
                    battery_data.append({
                        'position': sce.get('position', 0),
                        'voltage': sce.get('battery_voltage', '')
                    })

            if 'instrument_timing' in available_columns:
                db_data['instrument_timing'] = json.dumps(timing_data)

            if battery_data and 'battery_voltages' in available_columns:
                db_data['battery_voltages'] = json.dumps(battery_data)

            # Handle fname JSON column for filenames
            fname_data = []
            for sce in subsurface_clock_errors:
                if sce.get('filename'):
                    fname_data.append({
                        'position': sce.get('position', 0),
                        'value': sce.get('filename', '')
                    })

            if fname_data and 'fname' in available_columns:
                db_data['fname'] = json.dumps(fname_data)

            # Handle numofrec JSON column for number of records
            numofrec_data = []
            for sce in subsurface_clock_errors:
                if sce.get('number_of_records'):
                    numofrec_data.append({
                        'position': sce.get('position', 0),
                        'value': sce.get('number_of_records', '')
                    })

            if numofrec_data and 'numofrec' in available_columns:
                db_data['numofrec'] = json.dumps(numofrec_data)

            # Handle errcom JSON column for comments
            errcom_data = []
            for sce in subsurface_clock_errors:
                if sce.get('comments'):
                    errcom_data.append({
                        'position': sce.get('position', 0),  # Use 0-based position directly
                        'value': sce.get('comments', '')
                    })

            if errcom_data and 'errcom' in available_columns:
                db_data['errcom'] = json.dumps(errcom_data)

        # Handle Release Commands JSON
        release_commands = []

        # Add Release 1 commands if values exist
        if form_data.get('release1_release'):
            release_commands.append({
                "command_field": "rel8_relsn1::cmd_1/a_code_function_reply",
                "response": float(form_data['release1_release']) if form_data['release1_release'].replace('.', '').replace('-', '').isdigit() else form_data['release1_release']
            })
        if form_data.get('release1_disable'):
            release_commands.append({
                "command_field": "rel8_relsn1::cmd_2/b_code_function_reply",
                "response": float(form_data['release1_disable']) if form_data['release1_disable'].replace('.', '').replace('-', '').isdigit() else form_data['release1_disable']
            })
        if form_data.get('release1_enable'):
            release_commands.append({
                "command_field": "rel8_relsn1::cmd_3/c_code_function_reply",
                "response": float(form_data['release1_enable']) if form_data['release1_enable'].replace('.', '').replace('-', '').isdigit() else form_data['release1_enable']
            })

        # Add Release 2 commands if values exist
        if form_data.get('release2_release'):
            release_commands.append({
                "command_field": "rel8_relsn2::cmd_1/a_code_function_reply",
                "response": float(form_data['release2_release']) if form_data['release2_release'].replace('.', '').replace('-', '').isdigit() else form_data['release2_release']
            })
        if form_data.get('release2_disable'):
            release_commands.append({
                "command_field": "rel8_relsn2::cmd_2/b_code_function_reply",
                "response": float(form_data['release2_disable']) if form_data['release2_disable'].replace('.', '').replace('-', '').isdigit() else form_data['release2_disable']
            })
        if form_data.get('release2_enable'):
            release_commands.append({
                "command_field": "rel8_relsn2::cmd_3/c_code_function_reply",
                "response": float(form_data['release2_enable']) if form_data['release2_enable'].replace('.', '').replace('-', '').isdigit() else form_data['release2_enable']
            })

        # Add release commands JSON to database if column exists and commands exist
        if release_commands and 'release_commands' in available_columns:
            db_data['release_commands'] = json.dumps(release_commands)

        # Handle release information fields
        release_info_fields = {
            'rel_type_1': ['rel_type_1'],
            'rel_sn_1': ['rel_sn_1'],
            'rel_1_rec': ['rel_1_rec'],
            'rel_type_2': ['rel_type_2'],
            'rel_sn_2': ['rel_sn_2'],
            'rel_2_rec': ['rel_2_rec'],
            'release_comments': ['release_comments']
        }

        for form_field, possible_db_fields in release_info_fields.items():
            value = form_data.get(form_field, '')
            if value:
                for db_field in possible_db_fields:
                    if db_field in available_columns:
                        db_data[db_field] = value
                        break

        if not db_data:
            return False, "No matching columns found in database"

        # Build INSERT query dynamically
        columns = ', '.join([f'"{k}"' for k in db_data.keys()])
        placeholders = ', '.join(['?' for _ in db_data])

        query = f'INSERT INTO recoveries_normalized ({columns}) VALUES ({placeholders})'
        cursor.execute(query, list(db_data.values()))

        conn.commit()
        recovery_id = cursor.lastrowid
        return True, recovery_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        return False, f"Data integrity error: {str(e)}"
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()

def main():
    # Page configuration
    st.set_page_config(
        page_title="GTMBA Recovery Log (Normalized)",
        page_icon="⚓",
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
    st.title("GTMBA Recovery Log (Normalized)")

    # Check database connection and table
    table_exists, columns = check_database_table()
    if not table_exists:
        st.error("⚠️ Recoveries_normalized table not found in database!")
        st.info("Please ensure the recoveries_normalized table is created in your database.")
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
    if 'selected_recovery' not in st.session_state:
        st.session_state.selected_recovery = None

    # Mode selection
    col1, col2 = st.columns([1, 3])
    with col1:
        mode = st.radio("Mode", ["Search/Edit", "Add New"], key="mode_selector")
        st.session_state.mode = mode

    # Get list of sites for dropdown
    available_sites = get_distinct_sites()

    # Search section
    if mode == "Search/Edit":
        st.subheader("Search Recoveries")

        with st.form("search_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                # Use dropdown for Site search
                site_options = [""] + available_sites
                search_site = st.selectbox("Site", options=site_options, key="search_site")
                st.caption("Tip: After selecting a site, click the 'Search' button to submit your query.")
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
                results = search_recoveries(search_criteria)
                st.session_state.search_results = results
                st.session_state.current_record_index = 0

                if results.empty:
                    st.warning("No recoveries found matching your criteria.")
                else:
                    st.success(f"Found {len(results)} recovery(ies)")

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
            if len(st.session_state.search_results) == 0:
                st.session_state.selected_recovery = None
            else:
                # Get the row as a dictionary
                current_record = st.session_state.search_results.iloc[st.session_state.current_record_index]

                # Convert Series to dict for easier access
                if hasattr(current_record, 'to_dict'):
                    current_record_dict = current_record.to_dict()
                else:
                    current_record_dict = dict(current_record)

                # Handle date column - find which one exists
                table_exists, available_columns = check_database_table()
                rec_date_key = None
                possible_date_columns = ['release_fire_date', 'relfiredate', 'rec_date', 'recovery_date', 'date']
                for col in possible_date_columns:
                    if col in current_record_dict:
                        rec_date_key = col
                        break

                if rec_date_key and rec_date_key in current_record_dict:
                    rec_date_val = current_record_dict[rec_date_key]
                    if rec_date_val is None or str(rec_date_val).lower() in ['nan', 'none', '']:
                        current_record_dict[rec_date_key] = ''
                    else:
                        current_record_dict[rec_date_key] = str(rec_date_val)

                st.session_state.selected_recovery = current_record_dict



            # Add export button at the top
            export_cols = st.columns([3, 1])
            with export_cols[1]:
                if st.button("📄 Export to XML", key="top_export", use_container_width=True):
                    try:
                        xml_content = export_record_to_xml(current_record_dict)
                        # Generate filename
                        site = current_record_dict.get('site', 'unknown')
                        mooring_id = current_record_dict.get('mooring_id', current_record_dict.get('mooringid', 'unknown'))
                        cruise = current_record_dict.get('cruise', 'unknown')
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"recovery_{site}_{mooring_id}_{cruise}_{timestamp}.xml"

                        # Create download button
                        st.download_button(
                            label="⬇️ Download XML",
                            data=xml_content,
                            file_name=filename,
                            mime="application/xml",
                            key="top_download_xml"
                        )
                        st.success("✅ XML export ready for download!")
                    except Exception as e:
                        st.error(f"❌ Error generating XML: {str(e)}")

            # Display key info
            info_cols = st.columns(4)
            with info_cols[0]:
                st.metric("Site", current_record_dict.get('site', 'N/A'))
            with info_cols[1]:
                st.metric("Mooring ID", current_record_dict.get('mooring_id', 'N/A'))
            with info_cols[2]:
                st.metric("Cruise", current_record_dict.get('cruise', 'N/A'))
            with info_cols[3]:
                # Find the actual date column name that exists
                rec_date_display = 'N/A'
                for col in ['release_fire_date', 'relfiredate', 'rec_date', 'recovery_date', 'date']:
                    if col in current_record_dict:
                        rec_date_display = current_record_dict.get(col, 'N/A')
                        break
                # Clean up display value
                if rec_date_display and rec_date_display != 'N/A':
                    rec_date_display = str(rec_date_display).replace('None', '').replace('nan', '').replace('<NA>', '')
                st.metric("Release Fire Date", rec_date_display if rec_date_display else 'N/A')

    # Create the form
    if mode == "Add New":
        st.subheader("Add New Recovery")
    else:
        st.subheader("Edit Recovery")

    with st.form("recovery_form"):
        # Initialize form values
        if mode == "Search/Edit" and st.session_state.selected_recovery is not None:
            record = st.session_state.selected_recovery

            default_site = record.get('site', '')
            default_mooringid = record.get('mooring_id', '')
            default_cruise = record.get('cruise', '')

            # Release Info defaults
            default_release_latitude = record.get('relfirelat', '')
            default_release_longitude = record.get('relfirelong', '')

            # Format fire time to HH:mm
            fire_time_raw = record.get('relfiretime', '')
            if fire_time_raw and ':' in str(fire_time_raw):
                try:
                    # Split and take only hours and minutes
                    time_parts = str(fire_time_raw).split(':')
                    default_fire_time = f"{time_parts[0]}:{time_parts[1]}"
                except:
                    default_fire_time = fire_time_raw
            else:
                default_fire_time = fire_time_raw

            # Format fire date to MM/DD/YYYY
            fire_date_raw = record.get('relfiredate', '')
            if fire_date_raw:
                try:
                    # Parse the date and format as MM/DD/YYYY
                    parsed_date = pd.to_datetime(fire_date_raw, errors='coerce')
                    if not pd.isna(parsed_date):
                        default_fire_date = parsed_date.strftime("%m/%d/%Y")
                    else:
                        default_fire_date = fire_date_raw
                except:
                    default_fire_date = fire_date_raw
            else:
                default_fire_date = fire_date_raw

            # Format time on deck to HH:mm
            time_on_deck_raw = record.get('relon_decktime', '')
            if time_on_deck_raw and ':' in str(time_on_deck_raw):
                try:
                    # Split and take only hours and minutes
                    time_parts = str(time_on_deck_raw).split(':')
                    default_time_on_deck = f"{time_parts[0]}:{time_parts[1]}"
                except:
                    default_time_on_deck = time_on_deck_raw
            else:
                default_time_on_deck = time_on_deck_raw

            # Format date on deck to MM/DD/YYYY
            date_on_deck_raw = record.get('dateondeck', '')
            if date_on_deck_raw:
                try:
                    # Parse the date and format as MM/DD/YYYY
                    parsed_date = pd.to_datetime(date_on_deck_raw, errors='coerce')
                    if not pd.isna(parsed_date):
                        default_date_on_deck = parsed_date.strftime("%m/%d/%Y")
                    else:
                        default_date_on_deck = date_on_deck_raw
                except:
                    default_date_on_deck = date_on_deck_raw
            else:
                default_date_on_deck = date_on_deck_raw

            # Met Sensors defaults
            import json

            default_tube_sn = clean_serial_number(record.get('tubesn', ''))
            # Parse tube_condition JSON
            tube_condition_json = record.get('tube_condition', '')
            if tube_condition_json:
                try:
                    tube_data = json.loads(tube_condition_json) if isinstance(tube_condition_json, str) else tube_condition_json
                    default_tube_condition = tube_data.get('condition', '') if isinstance(tube_data, dict) else ''
                    default_tube_details = tube_data.get('details', '') if isinstance(tube_data, dict) else ''
                except:
                    default_tube_condition = ''
                    default_tube_details = ''
            else:
                default_tube_condition = ''
                default_tube_details = ''

            default_ptt_hexid_sn = clean_serial_number(record.get('ptt_id', ''))
            # PTT/Hexid condition should match tube condition since PTT is inside the tube
            default_ptt_hexid_condition = default_tube_condition
            default_ptt_hexid_details = default_tube_details

            default_at_rh_sn = clean_serial_number(record.get('atrh_sn', ''))
            # Parse at_rh_condition JSON (check both possible column names)
            at_rh_condition_json = record.get('at_rh_condition', '') or record.get('atrh_condition', '')
            if at_rh_condition_json:
                try:
                    at_rh_data = json.loads(at_rh_condition_json) if isinstance(at_rh_condition_json, str) else at_rh_condition_json
                    default_at_rh_condition = at_rh_data.get('condition', '') if isinstance(at_rh_data, dict) else ''
                    default_at_rh_details = at_rh_data.get('details', '') if isinstance(at_rh_data, dict) else ''
                except:
                    default_at_rh_condition = ''
                    default_at_rh_details = ''
            else:
                default_at_rh_condition = ''
                default_at_rh_details = ''

            default_wind_sn = clean_serial_number(record.get('windsn', ''))
            # Parse wind_condition JSON
            wind_condition_json = record.get('wind_condition', '')
            if wind_condition_json:
                try:
                    wind_data = json.loads(wind_condition_json) if isinstance(wind_condition_json, str) else wind_condition_json
                    default_wind_condition = wind_data.get('condition', '') if isinstance(wind_data, dict) else ''
                    default_wind_details = wind_data.get('details', '') if isinstance(wind_data, dict) else ''
                except:
                    default_wind_condition = ''
                    default_wind_details = ''
            else:
                default_wind_condition = ''
                default_wind_details = ''

            default_rain_gauge_sn = clean_serial_number(record.get('rain_sn', ''))
            # Parse rain_gauge_condition JSON (check both possible column names)
            rain_condition_json = record.get('rain_gauge_condition', '') or record.get('rain_condition', '')
            if rain_condition_json:
                try:
                    rain_data = json.loads(rain_condition_json) if isinstance(rain_condition_json, str) else rain_condition_json
                    default_rain_gauge_condition = rain_data.get('condition', '') if isinstance(rain_data, dict) else ''
                    default_rain_gauge_details = rain_data.get('details', '') if isinstance(rain_data, dict) else ''
                except:
                    default_rain_gauge_condition = ''
                    default_rain_gauge_details = ''
            else:
                default_rain_gauge_condition = ''
                default_rain_gauge_details = ''

            default_sw_radiation_sn = clean_serial_number(record.get('swrad_sn', ''))
            # Parse sw_radiation_condition JSON (check both possible column names)
            sw_condition_json = record.get('sw_radiation_condition', '') or record.get('swrad_condition', '')
            if sw_condition_json:
                try:
                    sw_data = json.loads(sw_condition_json) if isinstance(sw_condition_json, str) else sw_condition_json
                    default_sw_radiation_condition = sw_data.get('condition', '') if isinstance(sw_data, dict) else ''
                    default_sw_radiation_details = sw_data.get('details', '') if isinstance(sw_data, dict) else ''
                except:
                    default_sw_radiation_condition = ''
                    default_sw_radiation_details = ''
            else:
                default_sw_radiation_condition = ''
                default_sw_radiation_details = ''

            default_lw_radiation_sn = clean_serial_number(record.get('lwrad_sn', ''))
            # Parse lw_radiation_condition JSON (check both possible column names)
            lw_condition_json = record.get('lw_radiation_condition', '') or record.get('lwrad_condition', '')
            if lw_condition_json:
                try:
                    lw_data = json.loads(lw_condition_json) if isinstance(lw_condition_json, str) else lw_condition_json
                    default_lw_radiation_condition = lw_data.get('condition', '') if isinstance(lw_data, dict) else ''
                    default_lw_radiation_details = lw_data.get('details', '') if isinstance(lw_data, dict) else ''
                except:
                    default_lw_radiation_condition = ''
                    default_lw_radiation_details = ''
            else:
                default_lw_radiation_condition = ''
                default_lw_radiation_details = ''

            default_barometer_sn = clean_serial_number(record.get('baro_sn', ''))
            # Parse barometer_condition JSON (check both possible column names)
            barometer_condition_json = record.get('barometer_condition', '') or record.get('baro_condition', '')
            if barometer_condition_json:
                try:
                    barometer_data = json.loads(barometer_condition_json) if isinstance(barometer_condition_json, str) else barometer_condition_json
                    default_barometer_condition = barometer_data.get('condition', '') if isinstance(barometer_data, dict) else ''
                    default_barometer_details = barometer_data.get('details', '') if isinstance(barometer_data, dict) else ''
                except:
                    default_barometer_condition = ''
                    default_barometer_details = ''
            else:
                default_barometer_condition = ''
                default_barometer_details = ''

            default_seacat_sn = clean_serial_number(record.get('seacat_sn', ''))
            # Parse seacat_condition JSON
            seacat_condition_json = record.get('seacat_condition', '')
            if seacat_condition_json:
                try:
                    seacat_data = json.loads(seacat_condition_json) if isinstance(seacat_condition_json, str) else seacat_condition_json
                    default_seacat_condition = seacat_data.get('condition', '') if isinstance(seacat_data, dict) else ''
                    default_seacat_details = seacat_data.get('details', '') if isinstance(seacat_data, dict) else ''
                except:
                    default_seacat_condition = ''
                    default_seacat_details = ''
            else:
                default_seacat_condition = ''
                default_seacat_details = ''

            # Argos Latitude defaults
            default_argos_latitude = record.get('argoslat', '')

            # Argos Longitude defaults
            default_argos_longitude = record.get('argoslong', '')

            default_mooring_status = record.get('statuspriortodeparture', '')
            default_mooring_type = str(record.get('mooring_type', ''))
            default_personnel = record.get('personnel', '')

            # Format touch_time to HH:mm only (remove seconds if present)
            touch_time_raw = record.get('touch_time', '')
            if touch_time_raw:
                touch_time_str = str(touch_time_raw)
                # Handle various time formats
                if ':' in touch_time_str:
                    # Split by colon and take only hours and minutes
                    time_parts = touch_time_str.split(':')
                    if len(time_parts) >= 2:
                        # Extract hours and minutes, ignoring seconds
                        hours = time_parts[0].strip().zfill(2)
                        # Remove any decimal seconds from minutes part
                        minutes = time_parts[1][:2].strip().zfill(2)
                        default_touch_time = f"{hours}:{minutes}"
                    else:
                        default_touch_time = touch_time_str
                elif '.' in touch_time_str:
                    # Handle decimal format (e.g., 13.5 for 13:30)
                    try:
                        time_float = float(touch_time_str)
                        hours = int(time_float)
                        minutes = int((time_float - hours) * 60)
                        default_touch_time = f"{hours:02d}:{minutes:02d}"
                    except ValueError:
                        default_touch_time = touch_time_str
                else:
                    default_touch_time = touch_time_str
            else:
                default_touch_time = ''

            # Met Obs - Ship observations (parse JSON from ship_met_data column)
            ship_date_str = ''
            ship_met_json = None

            # Parse ship_met_data JSON
            if 'ship_met_data' in record and record['ship_met_data']:
                try:
                    import json
                    ship_met_json = json.loads(record['ship_met_data']) if isinstance(record['ship_met_data'], str) else record['ship_met_data']
                    if isinstance(ship_met_json, dict):
                        ship_date_str = ship_met_json.get('date', '')
                except:
                    pass

            if ship_date_str:
                try:
                    default_ship_date = pd.to_datetime(ship_date_str, errors='coerce').date()
                    if pd.isna(default_ship_date):
                        default_ship_date = None
                except:
                    default_ship_date = None
            else:
                default_ship_date = None

            # Ship time - format to HH:mm
            ship_time_raw = ''
            if ship_met_json and isinstance(ship_met_json, dict):
                ship_time_raw = str(ship_met_json.get('time', '') or '')

            if ship_time_raw and ':' in ship_time_raw:
                try:
                    # Split and take only hours and minutes
                    time_parts = ship_time_raw.split(':')
                    default_ship_time = f"{time_parts[0]}:{time_parts[1]}"
                except:
                    default_ship_time = ship_time_raw
            else:
                default_ship_time = ship_time_raw

            # Ship wind direction (format to nautical)
            default_ship_wind_dir = ''
            if ship_met_json and isinstance(ship_met_json, dict):
                wind_dir_value = str(ship_met_json.get('wind_direction', '') or '')
                default_ship_wind_dir = format_wind_direction_nautical(wind_dir_value)

            # Ship wind speed
            default_ship_wind_spd = ''
            if ship_met_json and isinstance(ship_met_json, dict):
                default_ship_wind_spd = str(ship_met_json.get('wind_speed', '') or '')

            # Ship air temp
            default_ship_air_temp = ''
            if ship_met_json and isinstance(ship_met_json, dict):
                default_ship_air_temp = str(ship_met_json.get('air_temp', '') or '')

            # Ship SST
            default_ship_sst = ''
            if ship_met_json and isinstance(ship_met_json, dict):
                default_ship_sst = str(ship_met_json.get('sea_surface_temp', '') or '')

            # Ship SSC
            default_ship_ssc = ''
            if ship_met_json and isinstance(ship_met_json, dict):
                default_ship_ssc = str(ship_met_json.get('ssc', '') or '')

            # Ship RH
            default_ship_rh = ''
            if ship_met_json and isinstance(ship_met_json, dict):
                default_ship_rh = str(ship_met_json.get('relative_humidity', '') or '')

            # Met Obs - Buoy observations (parse JSON from buoy_met_data column)
            buoy_date_str = ''
            buoy_met_json = None

            # Parse buoy_met_data JSON
            if 'buoy_met_data' in record and record['buoy_met_data']:
                try:
                    import json
                    buoy_met_json = json.loads(record['buoy_met_data']) if isinstance(record['buoy_met_data'], str) else record['buoy_met_data']
                    if isinstance(buoy_met_json, dict):
                        buoy_date_str = buoy_met_json.get('date', '')
                except:
                    pass
            if buoy_date_str:
                try:
                    default_buoy_date = pd.to_datetime(buoy_date_str, errors='coerce').date()
                    if pd.isna(default_buoy_date):
                        default_buoy_date = None
                except:
                    default_buoy_date = None
            else:
                default_buoy_date = None

            # Buoy time - format to HH:mm
            buoy_time_raw = ''
            if buoy_met_json and isinstance(buoy_met_json, dict):
                buoy_time_raw = str(buoy_met_json.get('time', '') or '')

            if buoy_time_raw and ':' in buoy_time_raw:
                try:
                    # Split and take only hours and minutes
                    time_parts = buoy_time_raw.split(':')
                    default_buoy_time = f"{time_parts[0]}:{time_parts[1]}"
                except:
                    default_buoy_time = buoy_time_raw
            else:
                default_buoy_time = buoy_time_raw

            # Buoy wind direction (format to nautical)
            default_buoy_wind_dir = ''
            if buoy_met_json and isinstance(buoy_met_json, dict):
                wind_dir_value = str(buoy_met_json.get('wind_direction', '') or '')
                default_buoy_wind_dir = format_wind_direction_nautical(wind_dir_value)

            # Buoy wind speed
            default_buoy_wind_spd = ''
            if buoy_met_json and isinstance(buoy_met_json, dict):
                default_buoy_wind_spd = str(buoy_met_json.get('wind_speed', '') or '')

            # Buoy air temp
            default_buoy_air_temp = ''
            if buoy_met_json and isinstance(buoy_met_json, dict):
                default_buoy_air_temp = str(buoy_met_json.get('air_temp', '') or '')

            # Buoy SST
            default_buoy_sst = ''
            if buoy_met_json and isinstance(buoy_met_json, dict):
                default_buoy_sst = str(buoy_met_json.get('sea_surface_temp', '') or '')

            # Buoy SSC
            default_buoy_ssc = ''
            if buoy_met_json and isinstance(buoy_met_json, dict):
                default_buoy_ssc = str(buoy_met_json.get('ssc', '') or '')

            # Buoy RH
            default_buoy_rh = ''
            if buoy_met_json and isinstance(buoy_met_json, dict):
                default_buoy_rh = str(buoy_met_json.get('relative_humidity', '') or '')

            # Release Information defaults
            default_rel_type_1 = record.get('rel_type_1', '')
            default_rel_sn_1 = clean_serial_number(record.get('rel_sn_1', ''))
            default_rel_1_rec = record.get('rel_1_rec', '')
            default_rel_type_2 = record.get('rel_type_2', '')
            default_rel_sn_2 = clean_serial_number(record.get('rel_sn_2', ''))
            default_rel_2_rec = record.get('rel_2_rec', '')

            # Parse release_commands JSON for Release, Disable, Enable values
            release_commands_json = record.get('release_commands', '')
            default_release1_release = ''
            default_release1_disable = ''
            default_release1_enable = ''
            default_release2_release = ''
            default_release2_disable = ''
            default_release2_enable = ''

            if release_commands_json:
                try:
                    release_commands = json.loads(release_commands_json) if isinstance(release_commands_json, str) else release_commands_json
                    if isinstance(release_commands, list):
                        for command in release_commands:
                            if isinstance(command, dict) and 'command_field' in command and 'response' in command:
                                cmd_field = command['command_field']
                                response = str(command['response'])

                                # Parse command fields for Release 1
                                if 'relsn1' in cmd_field.lower():
                                    if 'release' in cmd_field.lower() or 'cmd_1' in cmd_field.lower():
                                        default_release1_release = response
                                    elif 'disable' in cmd_field.lower() or 'cmd_2' in cmd_field.lower():
                                        default_release1_disable = response
                                    elif 'enable' in cmd_field.lower() or 'cmd_3' in cmd_field.lower():
                                        default_release1_enable = response

                                # Parse command fields for Release 2
                                elif 'relsn2' in cmd_field.lower():
                                    if 'release' in cmd_field.lower() or 'cmd_1' in cmd_field.lower():
                                        default_release2_release = response
                                    elif 'disable' in cmd_field.lower() or 'cmd_2' in cmd_field.lower():
                                        default_release2_disable = response
                                    elif 'enable' in cmd_field.lower() or 'cmd_3' in cmd_field.lower():
                                        default_release2_enable = response
                except:
                    pass

            # Release Comments defaults
            default_release_comments = record.get('release_comments', '')

            # Fishing/Vandalism Evidence defaults
            default_fishing_vandalism = record.get('fishing_or_vandalism', '')

            # Nylon Recovered defaults (from nylon_lines column)
            nylon_lines_raw = record.get('nylon_lines', '')
            default_nylon_spools = []
            if nylon_lines_raw:
                try:
                    import json
                    nylon_data = json.loads(nylon_lines_raw) if isinstance(nylon_lines_raw, str) else nylon_lines_raw
                    if isinstance(nylon_data, list):
                        # Map from the database structure to our form structure
                        for item in nylon_data:
                            line_num = item.get('line_number', '')
                            length_val = item.get('length', '')
                            default_nylon_spools.append({
                                'spool': '' if pd.isna(line_num) else str(line_num) if line_num else '',
                                'sn': clean_serial_number(item.get('serial_number', '')),
                                'length': '' if pd.isna(length_val) else str(length_val) if length_val else '',
                                'condition': item.get('comments', '') or ''
                            })
                except (json.JSONDecodeError, TypeError):
                    default_nylon_spools = []

            # Hardware defaults - read from individual columns
            default_buoy_hardware_sn = clean_serial_number(record.get('buoy_sn', ''))
            default_buoy_hardware_condition = record.get('buoy_condition', '')
            default_buoy_top_section_sn = clean_serial_number(record.get('top_section_sn', ''))
            glass_balls_val = record.get('glassballs', '')
            default_buoy_glass_balls = '' if pd.isna(glass_balls_val) else str(glass_balls_val) if glass_balls_val else ''
            default_wire_hardware_sn = clean_serial_number(record.get('wiresn', ''))
            default_wire_hardware_condition = record.get('wirecond', '')

            # Subsurface Sensors defaults - MUST be parsed first before instrument_timing
            subsurface_instruments_raw = record.get('subsurface_instruments', '')

            # Get instrument_addresses field to determine if addresses should be shown
            instrument_addresses_raw = record.get('instrument_addresses', '')
            instrument_addresses_data = []
            if instrument_addresses_raw:
                try:
                    import json
                    instrument_addresses_data = json.loads(instrument_addresses_raw) if isinstance(instrument_addresses_raw, str) else instrument_addresses_raw
                except (json.JSONDecodeError, TypeError):
                    instrument_addresses_data = []

            # Parse subsurface instruments JSON
            if subsurface_instruments_raw:
                try:
                    import json
                    default_subsurface_instruments = json.loads(subsurface_instruments_raw) if isinstance(subsurface_instruments_raw, str) else subsurface_instruments_raw

                    # Build a map of positions to addresses from instrument_addresses
                    address_map = {}
                    if instrument_addresses_data and isinstance(instrument_addresses_data, list):
                        for addr_entry in instrument_addresses_data:
                            if isinstance(addr_entry, dict) and 'position' in addr_entry and 'address' in addr_entry:
                                address_map[addr_entry['position']] = addr_entry['address']

                    # Format timeout values to HH:mm only and clean serial numbers
                    for idx, instrument in enumerate(default_subsurface_instruments):
                        if 'serial_number' in instrument:
                            instrument['serial_number'] = clean_serial_number(instrument['serial_number'])
                        # Clear address for Sontek instruments (including typos like "Sonteck")
                        inst_type_value = instrument.get('instrument_type') or ''
                        if 'sontek' in inst_type_value.lower() or 'sonteck' in inst_type_value.lower():
                            instrument['address'] = ''
                        if 'timeout' in instrument and instrument['timeout']:
                            timeout_str = str(instrument['timeout'])
                            if ':' in timeout_str:
                                # Split and take only hours and minutes
                                time_parts = timeout_str.split(':')
                                if len(time_parts) >= 2:
                                    instrument['timeout'] = f"{time_parts[0]}:{time_parts[1]}"

                        # Set address based on instrument_addresses data if it exists
                        # If instrument_addresses is NULL/empty, addresses should be empty
                        if instrument_addresses_data and address_map:
                            # Use address from instrument_addresses based on position
                            position = instrument.get('position', idx)
                            instrument['address'] = address_map.get(position, '')
                        else:
                            # No instrument_addresses data, so clear all addresses
                            instrument['address'] = ''
                except (json.JSONDecodeError, TypeError):
                    default_subsurface_instruments = []
            else:
                default_subsurface_instruments = []

            # Tube defaults - read from database columns
            # Debug: Log what we're reading from the record
            raw_batlogic = record.get('batlogic')
            raw_battransmit = record.get('battransmit')
            raw_batdate = record.get('batdate')
            raw_gmt_tube = record.get('gmt_tube')
            raw_clk_err_tube = record.get('clk_err_tube')

            # Convert None to empty string for form fields
            default_battery_logic = raw_batlogic if raw_batlogic is not None else ''
            default_battery_transmit = raw_battransmit if raw_battransmit is not None else ''

            # Format tube date as YYYY-MM-DD
            default_tube_date = ''
            if raw_batdate is not None and raw_batdate != '':
                # Convert to string and extract just the date part
                date_str = str(raw_batdate)
                # Handle various date formats
                if 'T' in date_str:  # Handle datetime string with T separator
                    default_tube_date = date_str.split('T')[0]
                elif ' ' in date_str:  # Handle datetime string with space separator (YYYY-MM-DD HH:MM:SS)
                    default_tube_date = date_str.split(' ')[0]
                else:
                    # Already just a date, use as-is
                    default_tube_date = date_str

            # Format tube actual time as HH:mm:ss (remove decimal seconds)
            default_tube_actual_time = ''
            if raw_gmt_tube is not None and raw_gmt_tube != '':
                time_str = str(raw_gmt_tube)
                if '.' in time_str:  # Remove decimal seconds
                    time_str = time_str.split('.')[0]
                if ':' in time_str:
                    time_parts = time_str.split(':')
                    if len(time_parts) >= 3:
                        default_tube_actual_time = f"{time_parts[0]}:{time_parts[1]}:{time_parts[2]}"
                    elif len(time_parts) == 2:
                        default_tube_actual_time = f"{time_parts[0]}:{time_parts[1]}:00"
                else:
                    default_tube_actual_time = time_str

            default_tube_inst_time = ''  # Will be set from instrument_timing if available
            default_tube_clock_error = format_clock_error_to_mmss(raw_clk_err_tube) if raw_clk_err_tube is not None else ''

            # Get instrument_timing data
            instrument_timing_raw = record.get('instrument_timing', '')

            # Also check instrument_timing for tube entry
            if instrument_timing_raw:
                try:
                    import json
                    timing_data = json.loads(instrument_timing_raw) if isinstance(instrument_timing_raw, str) else instrument_timing_raw
                    if isinstance(timing_data, list):
                        for item in timing_data:
                            if item.get('position') == 'tube':
                                # Found tube timing entry
                                tube_inst_time = item.get('instrument_time', '')
                                if tube_inst_time:
                                    time_str = str(tube_inst_time)
                                    if '.' in time_str:  # Remove decimal seconds
                                        time_str = time_str.split('.')[0]
                                    if ':' in time_str:
                                        time_parts = time_str.split(':')
                                        if len(time_parts) >= 3:
                                            default_tube_inst_time = f"{time_parts[0]}:{time_parts[1]}:{time_parts[2]}"
                                        elif len(time_parts) == 2:
                                            default_tube_inst_time = f"{time_parts[0]}:{time_parts[1]}:00"
                                    else:
                                        default_tube_inst_time = time_str

                                # Update clock error from this entry if available
                                tube_clk_err = item.get('clock_error', '')
                                if tube_clk_err:
                                    default_tube_clock_error = format_clock_error_to_mmss(tube_clk_err)
                                break
                except:
                    pass

            # Parse battery voltages JSON first
            battery_voltages_raw = record.get('battery_voltages', '')
            battery_voltages_dict = {}
            if battery_voltages_raw:
                try:
                    import json
                    battery_data = json.loads(battery_voltages_raw) if isinstance(battery_voltages_raw, str) else battery_voltages_raw
                    if isinstance(battery_data, list):
                        # Create a dictionary mapping position to voltage
                        for item in battery_data:
                            position = item.get('position')
                            voltage = item.get('voltage')
                            if position is not None:
                                # Convert position to int for consistent keys
                                try:
                                    position_key = int(position)
                                except (ValueError, TypeError):
                                    position_key = position
                                battery_voltages_dict[position_key] = voltage
                except (json.JSONDecodeError, TypeError):
                    battery_voltages_dict = {}

            # Parse fname JSON column for filenames
            fname_dict = {}
            fname_raw = record.get('fname', '')
            if fname_raw:
                try:
                    import json
                    fname_data = json.loads(fname_raw) if isinstance(fname_raw, str) else fname_raw
                    if isinstance(fname_data, list):
                        for item in fname_data:
                            position = item.get('position')
                            if position is not None:
                                # Convert position to int for consistent keys
                                try:
                                    position_key = int(position)
                                except (ValueError, TypeError):
                                    position_key = position
                                fname_dict[position_key] = item.get('value', '')
                except (json.JSONDecodeError, TypeError):
                    fname_dict = {}

            # Parse numofrec JSON column for number of records
            numofrec_dict = {}
            numofrec_raw = record.get('numofrec', '')
            if numofrec_raw:
                try:
                    import json
                    numofrec_data = json.loads(numofrec_raw) if isinstance(numofrec_raw, str) else numofrec_raw
                    if isinstance(numofrec_data, list):
                        for item in numofrec_data:
                            position = item.get('position')
                            if position is not None:
                                # Convert position to int for consistent keys
                                try:
                                    position_key = int(position)
                                except (ValueError, TypeError):
                                    position_key = position
                                numofrec_dict[position_key] = str(item.get('value', ''))
                except (json.JSONDecodeError, TypeError):
                    numofrec_dict = {}

            # Parse errcom JSON for comments
            errcom_dict = {}
            errcom_raw = current_record_dict.get('errcom')
            if errcom_raw:
                try:
                    import json
                    errcom_data = json.loads(errcom_raw) if isinstance(errcom_raw, str) else errcom_raw
                    if isinstance(errcom_data, list):
                        for item in errcom_data:
                            position = item.get('position')
                            try:
                                position_idx = int(position) if position is not None else None
                                if position_idx is not None:
                                    # Use position directly as array index (both are 0-based)
                                    errcom_dict[position_idx] = item.get('value', '')
                            except (ValueError, TypeError):
                                continue
                except (json.JSONDecodeError, TypeError):
                    errcom_dict = {}

            # Subsurface Clock Errors defaults - parse from instrument_timing JSON column
            # Build an array that matches indices with subsurface_instruments
            default_subsurface_clock_errors = [None] * 45  # Initialize with None for all possible positions

            # First, pre-populate with sensor info from subsurface_instruments
            # This ensures every instrument shows up in clock errors, even if no timing data exists
            if default_subsurface_instruments:
                for idx, instrument in enumerate(default_subsurface_instruments):
                    if idx < 45 and instrument:
                        # Pre-populate with instrument info but empty timing data
                        default_subsurface_clock_errors[idx] = {
                            'sensor_type': instrument.get('instrument_type', ''),
                            'serial_number': clean_serial_number(instrument.get('serial_number', '')),
                            'actual_time': '',
                            'inst_time': '',
                            'clock_error': '',
                            'filename': '',
                            'battery_voltage': '',
                            'number_of_records': '',
                            'comments': errcom_dict.get(idx, '')  # Add comment from errcom if available
                        }

            # Now overlay with actual timing data if it exists
            if instrument_timing_raw:
                try:
                    import json
                    timing_data = json.loads(instrument_timing_raw) if isinstance(instrument_timing_raw, str) else instrument_timing_raw
                    if isinstance(timing_data, list):
                        # Convert from database format to display format
                        for item in timing_data:
                            if item.get('position') != 'tube':  # Skip tube entry, it's handled separately
                                position = item.get('position')

                                # Convert position to int for array indexing
                                try:
                                    position_idx = int(position) if position is not None else None
                                except (ValueError, TypeError):
                                    continue  # Skip items with invalid positions

                                if position_idx is None or position_idx < 0 or position_idx >= 45:
                                    continue  # Skip out-of-range positions

                                # Get corresponding instrument info from same index
                                sensor_type = ''
                                sensor_sn = ''
                                if default_subsurface_instruments and position_idx < len(default_subsurface_instruments):
                                    instrument = default_subsurface_instruments[position_idx]
                                    if instrument:  # Check if instrument exists at this index
                                        sensor_type = instrument.get('instrument_type', '')
                                        sensor_sn = clean_serial_number(instrument.get('serial_number', ''))

                                # Get battery voltage for this position
                                battery_voltage = battery_voltages_dict.get(position_idx, '')

                                # Get filename for this position from fname JSON
                                filename = fname_dict.get(position_idx, '')

                                # Get number of records for this position from numofrec JSON
                                number_of_records = numofrec_dict.get(position_idx, '')

                                # Format times to HH:mm:ss
                                gmt_time = item.get('gmt_time', '')
                                if gmt_time and ':' in gmt_time:
                                    time_parts = gmt_time.split('.')  # Remove decimal seconds first
                                    time_base = time_parts[0] if time_parts else gmt_time
                                    time_components = time_base.split(':')
                                    if len(time_components) >= 3:
                                        gmt_time = f"{time_components[0]}:{time_components[1]}:{time_components[2]}"
                                    elif len(time_components) == 2:
                                        gmt_time = f"{time_components[0]}:{time_components[1]}:00"

                                inst_time = item.get('instrument_time', '')
                                if inst_time and ':' in inst_time:
                                    time_parts = inst_time.split('.')  # Remove decimal seconds first
                                    time_base = time_parts[0] if time_parts else inst_time
                                    time_components = time_base.split(':')
                                    if len(time_components) >= 3:
                                        inst_time = f"{time_components[0]}:{time_components[1]}:{time_components[2]}"
                                    elif len(time_components) == 2:
                                        inst_time = f"{time_components[0]}:{time_components[1]}:00"

                                # Extract sensor type and serial number from timing data if not found in instruments
                                if not sensor_type and 'sensor_type' in item:
                                    sensor_type = item.get('sensor_type', '')
                                if not sensor_sn and 'serial_number' in item:
                                    sensor_sn = clean_serial_number(item.get('serial_number', ''))

                                # Update the entry at the correct index (overlaying pre-populated data)
                                default_subsurface_clock_errors[position_idx] = {
                                    'sensor_type': sensor_type,
                                    'serial_number': sensor_sn,
                                    'actual_time': gmt_time,
                                    'inst_time': inst_time,
                                    'clock_error': format_clock_error_to_mmss(item.get('clock_error', '')),
                                    'filename': filename,
                                    'battery_voltage': str(battery_voltage) if battery_voltage else '',
                                    'number_of_records': number_of_records,
                                    'comments': errcom_dict.get(position_idx, '')
                                }
                except (json.JSONDecodeError, TypeError):
                    pass  # Keep the pre-populated data if parsing fails

            # Finally, add any comments that weren't already added (for positions without timing data)
            for idx, comment in errcom_dict.items():
                if idx < 45 and comment:
                    if default_subsurface_clock_errors[idx] is None:
                        # Create a minimal entry if nothing exists at this position
                        default_subsurface_clock_errors[idx] = {
                            'sensor_type': '',
                            'serial_number': '',
                            'actual_time': '',
                            'inst_time': '',
                            'clock_error': '',
                            'filename': '',
                            'battery_voltage': '',
                            'number_of_records': '',
                            'comments': comment
                        }
                    elif not default_subsurface_clock_errors[idx].get('comments'):
                        # Add comment if the entry exists but has no comment yet
                        default_subsurface_clock_errors[idx]['comments'] = comment
        else:
            # Default values for new records
            default_site = ""
            default_mooringid = ""
            default_cruise = ""
            default_release_latitude = ""
            default_release_longitude = ""
            default_fire_time = ""
            default_fire_date = ""
            default_time_on_deck = ""
            default_date_on_deck = ""
            default_argos_latitude = ""
            default_argos_longitude = ""
            default_mooring_status = ""
            default_mooring_type = ""
            default_personnel = ""
            default_touch_time = ""

            # Met Sensors defaults for new records
            default_tube_sn = ""
            default_tube_condition = ""
            default_tube_details = ""
            default_ptt_hexid_sn = ""
            default_ptt_hexid_condition = ""
            default_ptt_hexid_details = ""
            default_at_rh_sn = ""
            default_at_rh_condition = ""
            default_at_rh_details = ""
            default_wind_sn = ""
            default_wind_condition = ""
            default_wind_details = ""
            default_rain_gauge_sn = ""
            default_rain_gauge_condition = ""
            default_rain_gauge_details = ""
            default_sw_radiation_sn = ""
            default_sw_radiation_condition = ""
            default_sw_radiation_details = ""
            default_lw_radiation_sn = ""
            default_lw_radiation_condition = ""
            default_lw_radiation_details = ""
            default_barometer_sn = ""
            default_barometer_condition = ""
            default_barometer_details = ""
            default_seacat_sn = ""
            default_seacat_condition = ""
            default_seacat_details = ""

            # Met Obs defaults for new records
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

            # Release Information defaults for new records
            default_rel_type_1 = ""
            default_rel_sn_1 = ""
            default_rel_1_rec = ""
            default_rel_type_2 = ""
            default_rel_sn_2 = ""
            default_rel_2_rec = ""
            default_release1_release = ""
            default_release1_disable = ""
            default_release1_enable = ""
            default_release2_release = ""
            default_release2_disable = ""
            default_release2_enable = ""
            default_release_comments = ""

            # Fishing/Vandalism Evidence defaults for new records
            default_fishing_vandalism = ""

            # Nylon Recovered defaults for new records
            default_nylon_spools = []

            # Hardware defaults for new records
            default_buoy_hardware_sn = ''
            default_buoy_hardware_condition = ''
            default_buoy_top_section_sn = ''
            default_buoy_glass_balls = ''
            default_wire_hardware_sn = ''
            default_wire_hardware_condition = ''

            # Tube defaults for new records
            default_battery_logic = ""
            default_battery_transmit = ""
            default_tube_date = ""
            default_tube_actual_time = ""
            default_tube_inst_time = ""
            default_tube_clock_error = ""

            # Subsurface Clock Errors defaults for new records
            default_subsurface_clock_errors = [None] * 45  # Initialize array with None

            # Subsurface Sensors defaults for new records
            default_subsurface_instruments = []

        # Basic Information Section
        st.markdown("### Basic Information")
        st.markdown("*Fields marked with * are required*")

        # First row: Site and Mooring ID
        col1, col2 = st.columns(2)
        with col1:
            # Add "Other" option to allow custom entries
            site_options = [""] + available_sites + ["Other (specify below)"]

            # Check if the default site is in the list
            if default_site in site_options:
                site_index = site_options.index(default_site)
            elif default_site and default_site not in site_options:
                # If there's a default site not in the list, add it
                site_options.insert(1, default_site)
                site_index = 1
            else:
                site_index = 0

            site_selection = st.selectbox("Site",
                                        options=site_options,
                                        index=site_index,
                                        key="site_dropdown")

            # If "Other" is selected, show a text input
            if site_selection == "Other (specify below)":
                site = st.text_input("Specify site",
                                   value="",
                                   key="site_custom")
            else:
                site = site_selection
        with col2:
            mooringid = st.text_input("Mooring ID *", value=default_mooringid, key="mooringid", placeholder="XX-###X (Ex. PM794A)")

        # Second row: Cruise and Mooring Type
        col3, col4 = st.columns(2)
        with col3:
            cruise = st.text_input("Cruise *", value=default_cruise, key="cruise")
        with col4:
            mooring_options = ["", "taught", "slack"]
            default_mooring_value = default_mooring_type if 'default_mooring_type' in locals() else ""
            try:
                mooring_index = mooring_options.index(default_mooring_value)
            except ValueError:
                mooring_index = 0
            mooring_type = st.selectbox("Mooring Type",
                                       options=mooring_options,
                                       index=mooring_index,
                                       key="mooring_type")

        # Third row: Argos Latitude and Argos Longitude
        col5, col6 = st.columns(2)
        with col5:
            argos_latitude = st.text_input(
                "Argos Latitude",
                value=default_argos_latitude,
                key="argos_latitude",
                help="Argos latitude coordinates"
            )
        with col6:
            argos_longitude = st.text_input(
                "Argos Longitude",
                value=default_argos_longitude,
                key="argos_longitude",
                help="Argos longitude coordinates"
            )

        # Fourth row: Mooring Status (full width)
        mooring_status = st.text_area("Mooring Status",
                               value=default_mooring_status,
                               height=100,
                               key="mooring_status",
                               help="Enter the status of the mooring prior to departure")

        # Personnel field
        personnel = st.text_input("Personnel",
                                 value=default_personnel,
                                 help="Enter the personnel involved in the recovery")

        # Touch Time field (half width with note)
        col_touch1, col_touch2 = st.columns(2)
        with col_touch1:
            st.markdown('<span style="font-weight:bold;">Touch Time (HH:mm)</span>', unsafe_allow_html=True)
            touch_time = st.text_input("Touch Time",
                                    value=default_touch_time,
                                    key="touch_time",
                                    label_visibility="collapsed",
                                    placeholder="HH:mm",
                                    help="Enter time in HH:mm format (24-hour). Record the time when the mooring was first touched or contacted")
            # Format touch_time to ensure HH:mm format when saving
            if touch_time and ':' in touch_time:
                time_parts = touch_time.split(':')
                if len(time_parts) >= 2:
                    # Ensure proper HH:mm format, removing any seconds
                    hours = time_parts[0].strip().zfill(2)
                    minutes = time_parts[1][:2].strip().zfill(2)
                    touch_time = f"{hours}:{minutes}"
        with col_touch2:
            st.markdown('<span style="color:red; font-style:italic; margin-top:1.5rem; display:block;">First time anything was done to the buoy</span>', unsafe_allow_html=True)

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
            ship_time = st.text_input("Ship Time", value=default_ship_time, key="ship_time", label_visibility="collapsed", placeholder="HH:mm")
        with ship_cols[3]:
            ship_wind_dir = st.text_input("Ship Wind Dir", value=default_ship_wind_dir, key="ship_wind_dir", label_visibility="collapsed", placeholder="000-360")
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
            buoy_time = st.text_input("Buoy Time", value=default_buoy_time, key="buoy_time", label_visibility="collapsed", placeholder="HH:mm")
        with buoy_cols[3]:
            buoy_wind_dir = st.text_input("Buoy Wind Dir", value=default_buoy_wind_dir, key="buoy_wind_dir", label_visibility="collapsed", placeholder="000-360")
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

        # Release Info section
        st.markdown("---")
        st.subheader("Release Info")

        # First row: Release Latitude and Longitude
        col_rel1, col_rel2 = st.columns(2)
        with col_rel1:
            release_latitude = st.text_input("Latitude", value=default_release_latitude, key="release_latitude")
        with col_rel2:
            release_longitude = st.text_input("Longitude", value=default_release_longitude, key="release_longitude")

        # Second row: Fire Time and Fire Date
        col_fire1, col_fire2 = st.columns(2)
        with col_fire1:
            fire_time = st.text_input("Fire Time", value=default_fire_time, key="fire_time", placeholder="HH:mm")
        with col_fire2:
            fire_date = st.text_input("Fire Date", value=default_fire_date, key="fire_date", placeholder="MM/DD/YYYY")

        # Third row: Time on Deck and Date on Deck
        col_deck1, col_deck2 = st.columns(2)
        with col_deck1:
            time_on_deck = st.text_input("Time on Deck", value=default_time_on_deck, key="time_on_deck", placeholder="HH:mm")
        with col_deck2:
            date_on_deck = st.text_input("Date on Deck", value=default_date_on_deck, key="date_on_deck", placeholder="MM/DD/YYYY")

        # Create table header
        release_headers = st.columns([1.0, 0.8, 1.0, 0.8, 0.8, 0.8, 0.8])
        with release_headers[0]:
            st.write("")  # Empty for row labels
        with release_headers[1]:
            st.write("**Type**")
        with release_headers[2]:
            st.write("**S/N**")
        with release_headers[3]:
            st.write("**Recovered?**")
        with release_headers[4]:
            st.write("**Release**")
        with release_headers[5]:
            st.write("**Disable**")
        with release_headers[6]:
            st.write("**Enable**")

        # Release 1 row
        release1_cols = st.columns([1.0, 0.8, 1.0, 0.8, 0.8, 0.8, 0.8])
        with release1_cols[0]:
            st.write("**Release 1**")
        with release1_cols[1]:
            rel_type_1 = st.text_input("Release 1 Type", value=default_rel_type_1, key="rel_type_1", label_visibility="collapsed")
        with release1_cols[2]:
            rel_sn_1 = st.text_input("Release 1 S/N", value=default_rel_sn_1, key="rel_sn_1", label_visibility="collapsed")
        with release1_cols[3]:
            recovered_options = ["", "Yes", "No"]
            rel_1_rec_index = 0
            if default_rel_1_rec and default_rel_1_rec in recovered_options:
                rel_1_rec_index = recovered_options.index(default_rel_1_rec)
            rel_1_rec = st.selectbox("Release 1 Recovered", options=recovered_options, index=rel_1_rec_index, key="rel_1_rec", label_visibility="collapsed")
        with release1_cols[4]:
            release1_release = st.text_input("Release 1 Release", value=default_release1_release, key="release1_release", label_visibility="collapsed")
        with release1_cols[5]:
            release1_disable = st.text_input("Release 1 Disable", value=default_release1_disable, key="release1_disable", label_visibility="collapsed")
        with release1_cols[6]:
            release1_enable = st.text_input("Release 1 Enable", value=default_release1_enable, key="release1_enable", label_visibility="collapsed")

        # Release 2 row
        release2_cols = st.columns([1.0, 0.8, 1.0, 0.8, 0.8, 0.8, 0.8])
        with release2_cols[0]:
            st.write("**Release 2**")
        with release2_cols[1]:
            rel_type_2 = st.text_input("Release 2 Type", value=default_rel_type_2, key="rel_type_2", label_visibility="collapsed")
        with release2_cols[2]:
            rel_sn_2 = st.text_input("Release 2 S/N", value=default_rel_sn_2, key="rel_sn_2", label_visibility="collapsed")
        with release2_cols[3]:
            rel_2_rec_index = 0
            if default_rel_2_rec and default_rel_2_rec in recovered_options:
                rel_2_rec_index = recovered_options.index(default_rel_2_rec)
            rel_2_rec = st.selectbox("Release 2 Recovered", options=recovered_options, index=rel_2_rec_index, key="rel_2_rec", label_visibility="collapsed")
        with release2_cols[4]:
            release2_release = st.text_input("Release 2 Release", value=default_release2_release, key="release2_release", label_visibility="collapsed")
        with release2_cols[5]:
            release2_disable = st.text_input("Release 2 Disable", value=default_release2_disable, key="release2_disable", label_visibility="collapsed")
        with release2_cols[6]:
            release2_enable = st.text_input("Release 2 Enable", value=default_release2_enable, key="release2_enable", label_visibility="collapsed")

        # Release Problems/Comments
        st.markdown("#### Release Problems/Comments")
        release_comments = st.text_area(
            "Release Problems/Comments",
            value=default_release_comments,
            height=100,
            key="release_comments",
            label_visibility="collapsed",
            help="Enter any problems or comments regarding the releases"
        )

        # Met Sensors section
        st.markdown("---")
        st.subheader("Met Sensors")

        # Create table header
        sensor_headers = st.columns([1.2, 0.8, 0.8, 1.2])
        with sensor_headers[0]:
            st.write("**Sensor**")
        with sensor_headers[1]:
            st.write("**S/N**")
        with sensor_headers[2]:
            st.write("**Condition**")
        with sensor_headers[3]:
            st.write("**Details**")

        # Tube row
        tube_cols = st.columns([1.2, 0.8, 0.8, 1.2])
        with tube_cols[0]:
            st.write("Tube")
        with tube_cols[1]:
            tube_sn = st.text_input("Tube S/N", value=default_tube_sn, key="tube_sn", label_visibility="collapsed")
        with tube_cols[2]:
            condition_options = ["", "OK", "Lost", "Damaged", "Fouled"]
            # Default to blank if no S/N, otherwise default to "OK"
            if tube_sn:
                tube_condition_index = 1  # Default to "OK" when there's a S/N
                if default_tube_condition:
                    # Case-insensitive matching
                    for i, option in enumerate(condition_options):
                        if option.lower() == default_tube_condition.lower():
                            tube_condition_index = i
                            break
            else:
                tube_condition_index = 0  # Default to blank when no S/N
            tube_condition = st.selectbox("Tube Condition", options=condition_options, index=tube_condition_index, key="tube_condition", label_visibility="collapsed")
        with tube_cols[3]:
            tube_details = st.text_input("Tube Details", value=default_tube_details, key="tube_details", label_visibility="collapsed")

        # PTT/Hexid row
        ptt_cols = st.columns([1.2, 0.8, 0.8, 1.2])
        with ptt_cols[0]:
            st.write("PTT/Hexid")
        with ptt_cols[1]:
            ptt_hexid_sn = st.text_input("PTT/Hexid S/N", value=default_ptt_hexid_sn, key="ptt_hexid_sn", label_visibility="collapsed")
        with ptt_cols[2]:
            # Default to blank if no S/N, otherwise default to "OK"
            if ptt_hexid_sn:
                ptt_condition_index = 1  # Default to "OK" when there's a S/N
                if default_ptt_hexid_condition:
                    # Case-insensitive matching
                    for i, option in enumerate(condition_options):
                        if option.lower() == default_ptt_hexid_condition.lower():
                            ptt_condition_index = i
                            break
            else:
                ptt_condition_index = 0  # Default to blank when no S/N
            ptt_hexid_condition = st.selectbox("PTT/Hexid Condition", options=condition_options, index=ptt_condition_index, key="ptt_hexid_condition", label_visibility="collapsed")
        with ptt_cols[3]:
            ptt_hexid_details = st.text_input("PTT/Hexid Details", value=default_ptt_hexid_details, key="ptt_hexid_details", label_visibility="collapsed")

        # AT/RH row
        at_rh_cols = st.columns([1.2, 0.8, 0.8, 1.2])
        with at_rh_cols[0]:
            st.write("AT/RH")
        with at_rh_cols[1]:
            at_rh_sn = st.text_input("AT/RH S/N", value=default_at_rh_sn, key="at_rh_sn", label_visibility="collapsed")
        with at_rh_cols[2]:
            # Default to blank if no S/N, otherwise default to "OK"
            if at_rh_sn:
                at_rh_condition_index = 1  # Default to "OK" when there's a S/N
                if default_at_rh_condition:
                    # Case-insensitive matching
                    for i, option in enumerate(condition_options):
                        if option.lower() == default_at_rh_condition.lower():
                            at_rh_condition_index = i
                            break
            else:
                at_rh_condition_index = 0  # Default to blank when no S/N
            at_rh_condition = st.selectbox("AT/RH Condition", options=condition_options, index=at_rh_condition_index, key="at_rh_condition", label_visibility="collapsed")
        with at_rh_cols[3]:
            at_rh_details = st.text_input("AT/RH Details", value=default_at_rh_details, key="at_rh_details", label_visibility="collapsed")

        # Wind row
        wind_cols = st.columns([1.2, 0.8, 0.8, 1.2])
        with wind_cols[0]:
            st.write("Wind")
        with wind_cols[1]:
            wind_sn = st.text_input("Wind S/N", value=default_wind_sn, key="wind_sn", label_visibility="collapsed")
        with wind_cols[2]:
            # Default to blank if no S/N, otherwise default to "OK"
            if wind_sn:
                wind_condition_index = 1  # Default to "OK" when there's a S/N
                if default_wind_condition:
                    # Case-insensitive matching
                    for i, option in enumerate(condition_options):
                        if option.lower() == default_wind_condition.lower():
                            wind_condition_index = i
                            break
            else:
                wind_condition_index = 0  # Default to blank when no S/N
            wind_condition = st.selectbox("Wind Condition", options=condition_options, index=wind_condition_index, key="wind_condition", label_visibility="collapsed")
        with wind_cols[3]:
            wind_details = st.text_input("Wind Details", value=default_wind_details, key="wind_details", label_visibility="collapsed")

        # Rain Gauge row
        rain_cols = st.columns([1.2, 0.8, 0.8, 1.2])
        with rain_cols[0]:
            st.write("Rain Gauge")
        with rain_cols[1]:
            rain_gauge_sn = st.text_input("Rain Gauge S/N", value=default_rain_gauge_sn, key="rain_gauge_sn", label_visibility="collapsed")
        with rain_cols[2]:
            # Default to blank if no S/N, otherwise default to "OK"
            if rain_gauge_sn:
                rain_condition_index = 1  # Default to "OK" when there's a S/N
                if default_rain_gauge_condition:
                    # Case-insensitive matching
                    for i, option in enumerate(condition_options):
                        if option.lower() == default_rain_gauge_condition.lower():
                            rain_condition_index = i
                            break
            else:
                rain_condition_index = 0  # Default to blank when no S/N
            rain_gauge_condition = st.selectbox("Rain Gauge Condition", options=condition_options, index=rain_condition_index, key="rain_gauge_condition", label_visibility="collapsed")
        with rain_cols[3]:
            rain_gauge_details = st.text_input("Rain Gauge Details", value=default_rain_gauge_details, key="rain_gauge_details", label_visibility="collapsed")

        # SW Radiation row
        sw_cols = st.columns([1.2, 0.8, 0.8, 1.2])
        with sw_cols[0]:
            st.write("SW Radiation")
        with sw_cols[1]:
            sw_radiation_sn = st.text_input("SW Radiation S/N", value=default_sw_radiation_sn, key="sw_radiation_sn", label_visibility="collapsed")
        with sw_cols[2]:
            # Default to blank if no S/N, otherwise default to "OK"
            if sw_radiation_sn:
                sw_condition_index = 1  # Default to "OK" when there's a S/N
                if default_sw_radiation_condition:
                    # Case-insensitive matching
                    for i, option in enumerate(condition_options):
                        if option.lower() == default_sw_radiation_condition.lower():
                            sw_condition_index = i
                            break
            else:
                sw_condition_index = 0  # Default to blank when no S/N
            sw_radiation_condition = st.selectbox("SW Radiation Condition", options=condition_options, index=sw_condition_index, key="sw_radiation_condition", label_visibility="collapsed")
        with sw_cols[3]:
            sw_radiation_details = st.text_input("SW Radiation Details", value=default_sw_radiation_details, key="sw_radiation_details", label_visibility="collapsed")

        # LW Radiation row
        lw_cols = st.columns([1.2, 0.8, 0.8, 1.2])
        with lw_cols[0]:
            st.write("LW Radiation")
        with lw_cols[1]:
            lw_radiation_sn = st.text_input("LW Radiation S/N", value=default_lw_radiation_sn, key="lw_radiation_sn", label_visibility="collapsed")
        with lw_cols[2]:
            # Default to blank if no S/N, otherwise default to "OK"
            if lw_radiation_sn:
                lw_condition_index = 1  # Default to "OK" when there's a S/N
                if default_lw_radiation_condition:
                    # Case-insensitive matching
                    for i, option in enumerate(condition_options):
                        if option.lower() == default_lw_radiation_condition.lower():
                            lw_condition_index = i
                            break
            else:
                lw_condition_index = 0  # Default to blank when no S/N
            lw_radiation_condition = st.selectbox("LW Radiation Condition", options=condition_options, index=lw_condition_index, key="lw_radiation_condition", label_visibility="collapsed")
        with lw_cols[3]:
            lw_radiation_details = st.text_input("LW Radiation Details", value=default_lw_radiation_details, key="lw_radiation_details", label_visibility="collapsed")

        # Barometer row
        barometer_cols = st.columns([1.2, 0.8, 0.8, 1.2])
        with barometer_cols[0]:
            st.write("Barometer")
        with barometer_cols[1]:
            barometer_sn = st.text_input("Barometer S/N", value=default_barometer_sn, key="barometer_sn", label_visibility="collapsed")
        with barometer_cols[2]:
            # Default to blank if no S/N, otherwise default to "OK"
            if barometer_sn:
                barometer_condition_index = 1  # Default to "OK" when there's a S/N
                if default_barometer_condition:
                    # Case-insensitive matching
                    for i, option in enumerate(condition_options):
                        if option.lower() == default_barometer_condition.lower():
                            barometer_condition_index = i
                            break
            else:
                barometer_condition_index = 0  # Default to blank when no S/N
            barometer_condition = st.selectbox("Barometer Condition", options=condition_options, index=barometer_condition_index, key="barometer_condition", label_visibility="collapsed")
        with barometer_cols[3]:
            barometer_details = st.text_input("Barometer Details", value=default_barometer_details, key="barometer_details", label_visibility="collapsed")

        # SeaCat row
        seacat_cols = st.columns([1.2, 0.8, 0.8, 1.2])
        with seacat_cols[0]:
            st.write("SeaCat")
        with seacat_cols[1]:
            seacat_sn = st.text_input("SeaCat S/N", value=default_seacat_sn, key="seacat_sn", label_visibility="collapsed")
        with seacat_cols[2]:
            # Default to blank if no S/N, otherwise default to "OK"
            if seacat_sn:
                seacat_condition_index = 1  # Default to "OK" when there's a S/N
                if default_seacat_condition:
                    # Case-insensitive matching
                    for i, option in enumerate(condition_options):
                        if option.lower() == default_seacat_condition.lower():
                            seacat_condition_index = i
                            break
            else:
                seacat_condition_index = 0  # Default to blank when no S/N
            seacat_condition = st.selectbox("SeaCat Condition", options=condition_options, index=seacat_condition_index, key="seacat_condition", label_visibility="collapsed")
        with seacat_cols[3]:
            seacat_details = st.text_input("SeaCat Details", value=default_seacat_details, key="seacat_details", label_visibility="collapsed")

        # Evidence of Fishing or Vandalism section
        st.markdown("#### Evidence of Fishing or Vandalism")
        fishing_vandalism = st.text_area(
            "Evidence of Fishing or Vandalism",
            value=default_fishing_vandalism,
            height=150,
            key="fishing_vandalism",
            label_visibility="collapsed",
            help="Record any evidence of fishing activity, vandalism, or other human interference with the buoy"
        )

        # Separator line after Evidence of Fishing section
        st.markdown("---")

        # Subsurface Sensors section
        st.markdown("#### Subsurface Sensors")
        st.markdown("*Fill in subsurface sensor information below (leave rows blank if not needed)*")

        # Create table headers
        col_headers = st.columns([1, 1.5, 1.5, 1, 1.5, 1.5, 2])
        with col_headers[0]:
            st.write("**Depth**")
        with col_headers[1]:
            st.write("**Type**")
        with col_headers[2]:
            st.write("**S/N**")
        with col_headers[3]:
            st.write("**Address**")
        with col_headers[4]:
            st.write("**Time Out**")
        with col_headers[5]:
            st.write("**Condition**")
        with col_headers[6]:
            st.write("**Details**")

        # First 15 rows (always visible)
        subsurface_instruments = []
        for i in range(15):
            cols = st.columns([1, 1.5, 1.5, 1, 1.5, 1.5, 2])

            # Get default values if they exist
            default_instrument = {}
            if default_subsurface_instruments and i < len(default_subsurface_instruments):
                default_instrument = default_subsurface_instruments[i]

            with cols[0]:
                depth = st.text_input(f"Depth {i+1}", value=str(default_instrument.get('depth', '')), key=f"ss_depth_{i}", label_visibility="collapsed")
            with cols[1]:
                inst_type = st.text_input(f"Instrument Type {i+1}", value=default_instrument.get('instrument_type', ''), key=f"ss_type_{i}", label_visibility="collapsed")
            with cols[2]:
                sn = st.text_input(f"Serial Number {i+1}", value=clean_serial_number(default_instrument.get('serial_number', '')), key=f"ss_sn_{i}", label_visibility="collapsed")
            with cols[3]:
                # Don't show address for Sontek instruments - check from default values (including typos)
                inst_type_check = default_instrument.get('instrument_type') or ''
                is_sontek = 'sontek' in inst_type_check.lower() or 'sonteck' in inst_type_check.lower()
                # Get address from instrument data (which was set based on instrument_addresses field)
                db_address = default_instrument.get('address', '')
                # Handle address value - clear for Sontek, convert None to empty string
                if is_sontek:
                    address_value = ''
                elif db_address is None or db_address == 'None' or db_address == '':
                    address_value = ''
                else:
                    address_value = str(db_address).strip()
                address = st.text_input(f"Address {i+1}", value=address_value, key=f"ss_address_{i}", label_visibility="collapsed", placeholder="N/A" if is_sontek else "")
            with cols[4]:
                timeout = st.text_input(f"Timeout {i+1}", value=default_instrument.get('timeout', ''), key=f"ss_timeout_{i}", label_visibility="collapsed", placeholder="HH:mm")
            with cols[5]:
                condition_options = ["", "OK", "Lost", "Damaged", "Fouled"]
                default_condition = default_instrument.get('condition', '')
                condition_index = 0
                if default_condition and default_condition in condition_options:
                    condition_index = condition_options.index(default_condition)
                condition = st.selectbox(f"Condition {i+1}", options=condition_options, index=condition_index, key=f"ss_condition_{i}", label_visibility="collapsed")
            with cols[6]:
                detail = st.text_input(f"Details {i+1}", value=default_instrument.get('detail', '') or '', key=f"ss_detail_{i}", label_visibility="collapsed")

            # Only add to list if at least one field has data
            if any([depth, inst_type, sn, address, timeout, condition, detail]):
                # Convert depth to float if numeric, otherwise keep as string
                try:
                    depth_val = float(depth) if depth else depth
                except ValueError:
                    depth_val = depth

                # Format timeout to HH:mm only
                formatted_timeout = timeout
                if timeout and ':' in timeout:
                    time_parts = timeout.split(':')
                    if len(time_parts) >= 2:
                        formatted_timeout = f"{time_parts[0]}:{time_parts[1]}"

                # Clear address for Sontek instruments (including typos)
                inst_type_str = inst_type or ''
                final_address = '' if ('sontek' in inst_type_str.lower() or 'sonteck' in inst_type_str.lower()) else address

                subsurface_instruments.append({
                    'position': i,  # Position is just the row index/order
                    'depth': depth_val,
                    'instrument_type': inst_type,
                    'serial_number': sn,
                    'address': final_address,  # Address is stored as its own field in the JSON
                    'timeout': formatted_timeout,
                    'condition': condition if condition else None,
                    'detail': detail if detail else None
                })

        # Expandable section for rows 16-30
        # Auto-expand if there's data in this range
        has_data_16_30 = False
        if default_subsurface_instruments and isinstance(default_subsurface_instruments, list):
            has_data_16_30 = any(
                i < len(default_subsurface_instruments) and default_subsurface_instruments[i]
                for i in range(15, min(30, len(default_subsurface_instruments)))
            )
        with st.expander("Show rows 16-30 (click to expand)", expanded=has_data_16_30):
            for i in range(15, 30):
                cols = st.columns([1, 1.5, 1.5, 1, 1.5, 1.5, 2])

                # Get default values if they exist
                default_instrument = {}
                if default_subsurface_instruments and i < len(default_subsurface_instruments):
                    default_instrument = default_subsurface_instruments[i]

                with cols[0]:
                    depth = st.text_input(f"Depth {i+1}", value=str(default_instrument.get('depth', '')), key=f"ss_depth_{i}", label_visibility="collapsed")
                with cols[1]:
                    inst_type = st.text_input(f"Instrument Type {i+1}", value=default_instrument.get('instrument_type', ''), key=f"ss_type_{i}", label_visibility="collapsed")
                with cols[2]:
                    sn = st.text_input(f"Serial Number {i+1}", value=clean_serial_number(default_instrument.get('serial_number', '')), key=f"ss_sn_{i}", label_visibility="collapsed")
                with cols[3]:
                    # Don't show address for Sontek instruments - check from default values (including typos)
                    inst_type_check = default_instrument.get('instrument_type') or ''
                    is_sontek = 'sontek' in inst_type_check.lower() or 'sonteck' in inst_type_check.lower()
                    # Get address from instrument data (which was set based on instrument_addresses field)
                    db_address = default_instrument.get('address', '')
                    # Handle address value - clear for Sontek, convert None to empty string
                    if is_sontek:
                        address_value = ''
                    elif db_address is None or db_address == 'None' or db_address == '':
                        address_value = ''
                    else:
                        address_value = str(db_address).strip()
                    address = st.text_input(f"Address {i+1}", value=address_value, key=f"ss_address_{i}", label_visibility="collapsed", placeholder="N/A" if is_sontek else "")
                with cols[4]:
                    timeout = st.text_input(f"Timeout {i+1}", value=default_instrument.get('timeout', ''), key=f"ss_timeout_{i}", label_visibility="collapsed", placeholder="HH:mm")
                with cols[5]:
                    condition_options = ["", "OK", "Lost", "Damaged", "Fouled"]
                    default_condition = default_instrument.get('condition', '')
                    condition_index = 0
                    if default_condition and default_condition in condition_options:
                        condition_index = condition_options.index(default_condition)
                    condition = st.selectbox(f"Condition {i+1}", options=condition_options, index=condition_index, key=f"ss_condition_{i}", label_visibility="collapsed")
                with cols[6]:
                    detail = st.text_input(f"Details {i+1}", value=default_instrument.get('detail', '') or '', key=f"ss_detail_{i}", label_visibility="collapsed")

                # Only add to list if at least one field has data
                if any([depth, inst_type, sn, address, timeout, condition, detail]):
                    # Convert depth to float if numeric, otherwise keep as string
                    try:
                        depth_val = float(depth) if depth else depth
                    except ValueError:
                        depth_val = depth

                    # Format timeout to HH:mm only
                    formatted_timeout = timeout
                    if timeout and ':' in timeout:
                        time_parts = timeout.split(':')
                        if len(time_parts) >= 2:
                            formatted_timeout = f"{time_parts[0]}:{time_parts[1]}"

                    # Clear address for Sontek instruments (including typos)
                    inst_type_str = inst_type or ''
                    final_address = '' if ('sontek' in inst_type_str.lower() or 'sonteck' in inst_type_str.lower()) else address

                    subsurface_instruments.append({
                        'position': i,  # Position is just the row index/order
                        'depth': depth_val,
                        'instrument_type': inst_type,
                        'serial_number': sn,
                        'address': final_address,  # Address is stored as its own field in the JSON
                        'timeout': formatted_timeout,
                        'condition': condition if condition else None,
                        'detail': detail if detail else None
                    })

        # Expandable section for rows 31-45 (if needed)
        # Auto-expand if there's data in this range
        has_data_31_45 = False
        if default_subsurface_instruments and isinstance(default_subsurface_instruments, list):
            has_data_31_45 = any(
                i < len(default_subsurface_instruments) and default_subsurface_instruments[i]
                for i in range(30, min(45, len(default_subsurface_instruments)))
            )
        with st.expander("Show rows 31-45 (click to expand)", expanded=has_data_31_45):
            for i in range(30, 45):
                cols = st.columns([1, 1.5, 1.5, 1, 1.5, 1.5, 2])

                # Get default values if they exist
                default_instrument = {}
                if default_subsurface_instruments and i < len(default_subsurface_instruments):
                    default_instrument = default_subsurface_instruments[i]

                with cols[0]:
                    depth = st.text_input(f"Depth {i+1}", value=str(default_instrument.get('depth', '')), key=f"ss_depth_{i}", label_visibility="collapsed")
                with cols[1]:
                    inst_type = st.text_input(f"Instrument Type {i+1}", value=default_instrument.get('instrument_type', ''), key=f"ss_type_{i}", label_visibility="collapsed")
                with cols[2]:
                    sn = st.text_input(f"Serial Number {i+1}", value=clean_serial_number(default_instrument.get('serial_number', '')), key=f"ss_sn_{i}", label_visibility="collapsed")
                with cols[3]:
                    # Don't show address for Sontek instruments - check from default values (including typos)
                    inst_type_check = default_instrument.get('instrument_type') or ''
                    is_sontek = 'sontek' in inst_type_check.lower() or 'sonteck' in inst_type_check.lower()
                    # Get address from instrument data (which was set based on instrument_addresses field)
                    db_address = default_instrument.get('address', '')
                    # Handle address value - clear for Sontek, convert None to empty string
                    if is_sontek:
                        address_value = ''
                    elif db_address is None or db_address == 'None' or db_address == '':
                        address_value = ''
                    else:
                        address_value = str(db_address).strip()
                    address = st.text_input(f"Address {i+1}", value=address_value, key=f"ss_address_{i}", label_visibility="collapsed", placeholder="N/A" if is_sontek else "")
                with cols[4]:
                    timeout = st.text_input(f"Timeout {i+1}", value=default_instrument.get('timeout', ''), key=f"ss_timeout_{i}", label_visibility="collapsed", placeholder="HH:mm")
                with cols[5]:
                    condition_options = ["", "OK", "Lost", "Damaged", "Fouled"]
                    default_condition = default_instrument.get('condition', '')
                    condition_index = 0
                    if default_condition and default_condition in condition_options:
                        condition_index = condition_options.index(default_condition)
                    condition = st.selectbox(f"Condition {i+1}", options=condition_options, index=condition_index, key=f"ss_condition_{i}", label_visibility="collapsed")
                with cols[6]:
                    detail = st.text_input(f"Details {i+1}", value=default_instrument.get('detail', '') or '', key=f"ss_detail_{i}", label_visibility="collapsed")

                # Only add to list if at least one field has data
                if any([depth, inst_type, sn, address, timeout, condition, detail]):
                    # Convert depth to float if numeric, otherwise keep as string
                    try:
                        depth_val = float(depth) if depth else depth
                    except ValueError:
                        depth_val = depth

                    # Format timeout to HH:mm only
                    formatted_timeout = timeout
                    if timeout and ':' in timeout:
                        time_parts = timeout.split(':')
                        if len(time_parts) >= 2:
                            formatted_timeout = f"{time_parts[0]}:{time_parts[1]}"

                    # Clear address for Sontek instruments (including typos)
                    inst_type_str = inst_type or ''
                    final_address = '' if ('sontek' in inst_type_str.lower() or 'sonteck' in inst_type_str.lower()) else address

                    subsurface_instruments.append({
                        'position': i,  # Position is just the row index/order
                        'depth': depth_val,
                        'instrument_type': inst_type,
                        'serial_number': sn,
                        'address': final_address,  # Address is stored as its own field in the JSON
                        'timeout': formatted_timeout,
                        'condition': condition if condition else None,
                        'detail': detail if detail else None
                    })

        # Nylon Recovered section (after Subsurface)
        st.markdown("---")
        st.markdown("#### Nylon Recovered")

        # Create table header
        nylon_headers = st.columns([1, 1, 1, 2])
        with nylon_headers[0]:
            st.write("**Line #**")
        with nylon_headers[1]:
            st.write("**S/N**")
        with nylon_headers[2]:
            st.write("**Length (m)**")
        with nylon_headers[3]:
            st.write("**Condition/Comments**")

        # Create 10 rows for nylon spools
        nylon_spools_form = []
        for i in range(10):
            cols = st.columns([1, 1, 1, 2])

            # Get default values if they exist
            default_spool = {}
            if default_nylon_spools and i < len(default_nylon_spools):
                default_spool = default_nylon_spools[i]

            with cols[0]:
                spool = st.text_input(f"Line {i+1}",
                                    value=default_spool.get('spool', ''),
                                    key=f"nylon_spool_{i}",
                                    label_visibility="collapsed",
                                    placeholder=f"{i+1}")
            with cols[1]:
                sn = st.text_input(f"S/N {i+1}",
                                 value=default_spool.get('sn', ''),
                                 key=f"nylon_sn_{i}",
                                 label_visibility="collapsed")
            with cols[2]:
                length = st.text_input(f"Length {i+1}",
                                     value=default_spool.get('length', ''),
                                     key=f"nylon_length_{i}",
                                     label_visibility="collapsed")
            with cols[3]:
                condition = st.text_input(f"Condition {i+1}",
                                        value=default_spool.get('condition', ''),
                                        key=f"nylon_condition_{i}",
                                        label_visibility="collapsed")

            # Collect data if any field has value
            if any([spool, sn, length, condition]):
                nylon_spools_form.append({
                    'spool': spool,
                    'sn': sn,
                    'length': length,
                    'condition': condition
                })

        # Hardware section (after Nylon Recovered)
        st.markdown("---")
        st.markdown("#### Hardware")

        # Create table header
        hardware_headers = st.columns([0.8, 1, 1.2, 1.5, 1.5])
        with hardware_headers[0]:
            st.write("")  # Empty for row labels
        with hardware_headers[1]:
            st.write("**S/N**")
        with hardware_headers[2]:
            st.write("**Condition**")
        with hardware_headers[3]:
            st.write("**Top Section S/N**")
        with hardware_headers[4]:
            st.write("**No. Glass Balls**")

        # Buoy row
        buoy_hw_cols = st.columns([0.8, 1, 1.2, 1.5, 1.5])
        with buoy_hw_cols[0]:
            st.write("**Buoy**")
        with buoy_hw_cols[1]:
            buoy_hardware_sn = st.text_input("Buoy Hardware S/N",
                                            value=default_buoy_hardware_sn,
                                            key="buoy_hardware_sn",
                                            label_visibility="collapsed")
        with buoy_hw_cols[2]:
            buoy_hardware_condition = st.text_input("Buoy Hardware Condition",
                                                   value=default_buoy_hardware_condition,
                                                   key="buoy_hardware_condition",
                                                   label_visibility="collapsed")
        with buoy_hw_cols[3]:
            buoy_top_section_sn = st.text_input("Buoy Top Section S/N",
                                               value=default_buoy_top_section_sn,
                                               key="buoy_top_section_sn",
                                               label_visibility="collapsed")
        with buoy_hw_cols[4]:
            buoy_glass_balls = st.text_input("Buoy Glass Balls",
                                            value=default_buoy_glass_balls,
                                            key="buoy_glass_balls",
                                            label_visibility="collapsed")

        # Wire row
        wire_hw_cols = st.columns([0.8, 1, 1.2, 1.5, 1.5])
        with wire_hw_cols[0]:
            st.write("**Wire**")
        with wire_hw_cols[1]:
            wire_hardware_sn = st.text_input("Wire Hardware S/N",
                                            value=default_wire_hardware_sn,
                                            key="wire_hardware_sn",
                                            label_visibility="collapsed")
        with wire_hw_cols[2]:
            wire_hardware_condition = st.text_input("Wire Hardware Condition",
                                                   value=default_wire_hardware_condition,
                                                   key="wire_hardware_condition",
                                                   label_visibility="collapsed")
        with wire_hw_cols[3]:
            st.write("")  # Empty cell for wire row
            wire_top_section_sn = ""  # No top section for wire
        with wire_hw_cols[4]:
            st.write("")  # Empty cell for wire row
            wire_glass_balls = ""  # No glass balls for wire

        # Tube section
        st.markdown("---")
        st.markdown("#### Tube")

        # Battery Voltages table
        st.write("**Battery Voltages:**")

        # Headers row with Logic and Transmit left-justified
        battery_header_cols = st.columns([1, 1, 2])
        with battery_header_cols[0]:
            st.write("**Logic**")
        with battery_header_cols[1]:
            st.write("**Transmit**")
        with battery_header_cols[2]:
            st.write("")  # Empty space

        # Battery values row
        battery_value_cols = st.columns([1, 1, 2])
        with battery_value_cols[0]:
            # Ensure the value is a string and handle None/empty cases
            battery_logic_value = '' if pd.isna(default_battery_logic) else str(default_battery_logic) if default_battery_logic not in [None, ''] else ''
            battery_logic = st.text_input("Battery Logic",
                                         value=battery_logic_value,
                                         key="battery_logic",
                                         label_visibility="collapsed",
                                         placeholder="Voltage")
        with battery_value_cols[1]:
            # Ensure the value is a string and handle None/empty cases
            battery_transmit_value = '' if pd.isna(default_battery_transmit) else str(default_battery_transmit) if default_battery_transmit not in [None, ''] else ''
            battery_transmit = st.text_input("Battery Transmit",
                                            value=battery_transmit_value,
                                            key="battery_transmit",
                                            label_visibility="collapsed",
                                            placeholder="Voltage")
        with battery_value_cols[2]:
            st.write("")  # Empty space

        # Tube table
        st.write("**Tube:**")
        tube_header_cols = st.columns([1.5, 1.5, 1.5, 1.5])
        with tube_header_cols[0]:
            st.write("**Date**")
        with tube_header_cols[1]:
            st.write("**Actual Time**")
        with tube_header_cols[2]:
            st.write("**Inst. Time**")
        with tube_header_cols[3]:
            st.write("**Clock Error (M:SS)**")

        # Tube values row
        tube_value_cols = st.columns([1.5, 1.5, 1.5, 1.5])
        with tube_value_cols[0]:
            # Ensure the value is a string and handle None/empty cases
            tube_date_value = '' if pd.isna(default_tube_date) else str(default_tube_date) if default_tube_date not in [None, ''] else ''
            tube_date = st.text_input("Tube Date",
                                     value=tube_date_value,
                                     key="tube_date",
                                     label_visibility="collapsed",
                                     placeholder="YYYY-MM-DD")
        with tube_value_cols[1]:
            # Ensure the value is a string and handle None/empty cases
            tube_actual_time_value = '' if pd.isna(default_tube_actual_time) else str(default_tube_actual_time) if default_tube_actual_time not in [None, ''] else ''
            tube_actual_time = st.text_input("Tube Actual Time",
                                            value=tube_actual_time_value,
                                            key="tube_actual_time",
                                            label_visibility="collapsed",
                                            placeholder="HH:mm:ss")
        with tube_value_cols[2]:
            # Ensure the value is a string and handle None/empty cases
            tube_inst_time_value = '' if pd.isna(default_tube_inst_time) else str(default_tube_inst_time) if default_tube_inst_time not in [None, ''] else ''
            tube_inst_time = st.text_input("Tube Inst. Time",
                                          value=tube_inst_time_value,
                                          key="tube_inst_time",
                                          label_visibility="collapsed",
                                          placeholder="HH:mm:ss")
        with tube_value_cols[3]:
            # Calculate clock error if both times are provided and we're adding a new record
            tube_clock_error_value = '' if pd.isna(default_tube_clock_error) else str(default_tube_clock_error) if default_tube_clock_error not in [None, ''] else ''

            tube_clock_error = st.text_input("Tube Clock Error",
                                            value=tube_clock_error_value,
                                            key="tube_clock_error",
                                            label_visibility="collapsed",
                                            placeholder="M:SS",
                                            help="Will auto-calculate (Actual - Inst) when form is submitted" if st.session_state.mode == 'Add New' else None)

        # Subsurface Clock Errors section
        st.markdown("---")
        st.markdown("#### Subsurface Clock Errors")
        if st.session_state.mode == 'Add New':
            st.markdown("*Clock Error will auto-calculate as (Actual Time - Inst. Time) when the form is submitted*")
        else:
            st.markdown("*Record clock error information for subsurface instruments*")

        # Create table headers (two-line headers)
        header_cols = st.columns([1, 0.8, 1, 1, 0.8, 1.2, 1, 1.2, 2])
        with header_cols[0]:
            st.markdown("**Sensor**<br>**Type**", unsafe_allow_html=True)
        with header_cols[1]:
            st.markdown("<br>**S/N**", unsafe_allow_html=True)
        with header_cols[2]:
            st.markdown("**Actual**<br>**Time**", unsafe_allow_html=True)
        with header_cols[3]:
            st.markdown("**Inst.**<br>**Time**", unsafe_allow_html=True)
        with header_cols[4]:
            st.markdown("**Clock**<br>**Err. (sec)**", unsafe_allow_html=True)
        with header_cols[5]:
            st.markdown("<br>**Filename**", unsafe_allow_html=True)
        with header_cols[6]:
            st.markdown("**Batt.**<br>**Voltage**", unsafe_allow_html=True)
        with header_cols[7]:
            st.markdown("**Number**<br>**of Records**", unsafe_allow_html=True)
        with header_cols[8]:
            st.markdown("<br>**Comments**", unsafe_allow_html=True)

        # Create rows for subsurface clock errors - same as subsurface sensors (15 rows)
        subsurface_clock_errors = []

        for i in range(15):
            cols = st.columns([1, 0.8, 1, 1, 0.8, 1.2, 1, 1.2, 2])

            # Get default values if they exist - simple array indexing like subsurface sensors
            default_clock_error = {}
            if default_subsurface_clock_errors and i < len(default_subsurface_clock_errors):
                if default_subsurface_clock_errors[i] is not None:
                    default_clock_error = default_subsurface_clock_errors[i]

            with cols[0]:
                sensor_type = st.text_input(f"Sensor Type {i+1}",
                                          value=default_clock_error.get('sensor_type', ''),
                                          key=f"sce_sensor_type_{i}",
                                          label_visibility="collapsed")
            with cols[1]:
                sensor_sn = st.text_input(f"Sensor S/N {i+1}",
                                        value=clean_serial_number(default_clock_error.get('serial_number', '')),
                                        key=f"sce_sn_{i}",
                                        label_visibility="collapsed")
            with cols[2]:
                actual_time = st.text_input(f"Actual Time {i+1}",
                                          value=default_clock_error.get('actual_time', ''),
                                          key=f"sce_actual_time_{i}",
                                          label_visibility="collapsed",
                                          placeholder="HH:mm:ss")
            with cols[3]:
                inst_time = st.text_input(f"Inst Time {i+1}",
                                        value=default_clock_error.get('inst_time', ''),
                                        key=f"sce_inst_time_{i}",
                                        label_visibility="collapsed",
                                        placeholder="HH:mm:ss")
            with cols[4]:
                clock_error_value = default_clock_error.get('clock_error', '')
                clock_error = st.text_input(f"Clock Error {i+1}",
                                          value=clock_error_value,
                                          key=f"sce_clock_error_{i}",
                                          label_visibility="collapsed",
                                          placeholder="Auto-calc" if st.session_state.mode == 'Add New' else "M:SS")
            with cols[5]:
                filename = st.text_input(f"Filename {i+1}",
                                       value=default_clock_error.get('filename', ''),
                                       key=f"sce_filename_{i}",
                                       label_visibility="collapsed")
            with cols[6]:
                battery_voltage = st.text_input(f"Battery Voltage {i+1}",
                                               value=default_clock_error.get('battery_voltage', ''),
                                               key=f"sce_battery_voltage_{i}",
                                               label_visibility="collapsed")
            with cols[7]:
                num_records = st.text_input(f"Number of Records {i+1}",
                                          value=default_clock_error.get('number_of_records', ''),
                                          key=f"sce_num_records_{i}",
                                          label_visibility="collapsed")
            with cols[8]:
                comments = st.text_input(f"Comments {i+1}",
                                       value=default_clock_error.get('comments', ''),
                                       key=f"sce_comments_{i}",
                                       label_visibility="collapsed")

            # Only add to list if at least one field has data
            if any([sensor_type, sensor_sn, actual_time, inst_time, clock_error,
                   filename, battery_voltage, num_records, comments]):
                subsurface_clock_errors.append({
                    'position': i,
                    'sensor_type': sensor_type,
                    'serial_number': sensor_sn,
                    'actual_time': actual_time,
                    'inst_time': inst_time,
                    'clock_error': parse_clock_error_from_mmss(clock_error),
                    'filename': filename,
                    'battery_voltage': battery_voltage,
                    'number_of_records': num_records,
                    'comments': comments
                })

        # Expandable section for rows 16-30 (if needed)
        # Auto-expand if there's data in this range
        has_data_16_30 = False
        if default_subsurface_clock_errors and isinstance(default_subsurface_clock_errors, list):
            has_data_16_30 = any(
                i < len(default_subsurface_clock_errors) and default_subsurface_clock_errors[i] is not None
                for i in range(15, min(30, len(default_subsurface_clock_errors)))
            )
        with st.expander("Show rows 16-30 (click to expand)", expanded=has_data_16_30):
            for i in range(15, 30):
                cols = st.columns([1, 0.8, 1, 1, 0.8, 1.2, 1, 1.2, 2])

                # Get default values if they exist
                default_clock_error = {}
                if default_subsurface_clock_errors and i < len(default_subsurface_clock_errors):
                    if default_subsurface_clock_errors[i] is not None:
                        default_clock_error = default_subsurface_clock_errors[i]

                with cols[0]:
                    sensor_type = st.text_input(f"Sensor Type {i+1}",
                                              value=default_clock_error.get('sensor_type', ''),
                                              key=f"sce_sensor_type_{i}",
                                              label_visibility="collapsed")
                with cols[1]:
                    sensor_sn = st.text_input(f"Sensor S/N {i+1}",
                                            value=clean_serial_number(default_clock_error.get('serial_number', '')),
                                            key=f"sce_sn_{i}",
                                            label_visibility="collapsed")
                with cols[2]:
                    actual_time = st.text_input(f"Actual Time {i+1}",
                                            value=default_clock_error.get('actual_time', ''),
                                            key=f"sce_actual_time_{i}",
                                            label_visibility="collapsed",
                                            placeholder="HH:mm:ss")
                with cols[3]:
                    inst_time = st.text_input(f"Inst Time {i+1}",
                                            value=default_clock_error.get('inst_time', ''),
                                            key=f"sce_inst_time_{i}",
                                            label_visibility="collapsed",
                                            placeholder="HH:mm:ss")
                with cols[4]:
                    clock_error_value = default_clock_error.get('clock_error', '')
                    clock_error = st.text_input(f"Clock Error {i+1}",
                                              value=clock_error_value,
                                              key=f"sce_clock_error_{i}",
                                              label_visibility="collapsed",
                                              placeholder="Auto-calc" if st.session_state.mode == 'Add New' else "M:SS")
                with cols[5]:
                    filename = st.text_input(f"Filename {i+1}",
                                           value=default_clock_error.get('filename', ''),
                                           key=f"sce_filename_{i}",
                                           label_visibility="collapsed")
                with cols[6]:
                    battery_voltage = st.text_input(f"Battery Voltage {i+1}",
                                                   value=default_clock_error.get('battery_voltage', ''),
                                                   key=f"sce_battery_voltage_{i}",
                                                   label_visibility="collapsed")
                with cols[7]:
                    num_records = st.text_input(f"Number of Records {i+1}",
                                              value=default_clock_error.get('number_of_records', ''),
                                              key=f"sce_num_records_{i}",
                                              label_visibility="collapsed")
                with cols[8]:
                    comments = st.text_input(f"Comments {i+1}",
                                           value=default_clock_error.get('comments', ''),
                                           key=f"sce_comments_{i}",
                                           label_visibility="collapsed")

                # Only add to list if at least one field has data
                if any([sensor_type, sensor_sn, actual_time, inst_time, clock_error,
                       filename, battery_voltage, num_records, comments]):
                    subsurface_clock_errors.append({
                        'position': i,
                        'sensor_type': sensor_type,
                        'serial_number': sensor_sn,
                        'actual_time': actual_time,
                        'inst_time': inst_time,
                        'clock_error': parse_clock_error_from_mmss(clock_error),
                        'filename': filename,
                        'battery_voltage': battery_voltage,
                        'number_of_records': num_records,
                        'comments': comments
                    })

        # Expandable section for rows 31-45 (if needed)
        # Auto-expand if there's data in this range
        has_data_31_45 = False
        if default_subsurface_clock_errors and isinstance(default_subsurface_clock_errors, list):
            has_data_31_45 = any(
                i < len(default_subsurface_clock_errors) and default_subsurface_clock_errors[i] is not None
                for i in range(30, min(45, len(default_subsurface_clock_errors)))
            )
        with st.expander("Show rows 31-45 (click to expand)", expanded=has_data_31_45):
            for i in range(30, 45):
                cols = st.columns([1, 0.8, 1, 1, 0.8, 1.2, 1, 1.2, 2])

                # Get default values if they exist
                default_clock_error = {}
                if default_subsurface_clock_errors and i < len(default_subsurface_clock_errors):
                    if default_subsurface_clock_errors[i] is not None:
                        default_clock_error = default_subsurface_clock_errors[i]

                with cols[0]:
                    sensor_type = st.text_input(f"Sensor Type {i+1}",
                                              value=default_clock_error.get('sensor_type', ''),
                                              key=f"sce_sensor_type_{i}",
                                              label_visibility="collapsed")
                with cols[1]:
                    sensor_sn = st.text_input(f"Sensor S/N {i+1}",
                                            value=clean_serial_number(default_clock_error.get('serial_number', '')),
                                            key=f"sce_sn_{i}",
                                            label_visibility="collapsed")
                with cols[2]:
                    actual_time = st.text_input(f"Actual Time {i+1}",
                                            value=default_clock_error.get('actual_time', ''),
                                            key=f"sce_actual_time_{i}",
                                            label_visibility="collapsed",
                                            placeholder="HH:mm:ss")
                with cols[3]:
                    inst_time = st.text_input(f"Inst Time {i+1}",
                                            value=default_clock_error.get('inst_time', ''),
                                            key=f"sce_inst_time_{i}",
                                            label_visibility="collapsed",
                                            placeholder="HH:mm:ss")
                with cols[4]:
                    clock_error_value = default_clock_error.get('clock_error', '')
                    clock_error = st.text_input(f"Clock Error {i+1}",
                                              value=clock_error_value,
                                              key=f"sce_clock_error_{i}",
                                              label_visibility="collapsed",
                                              placeholder="Auto-calc" if st.session_state.mode == 'Add New' else "M:SS")
                with cols[5]:
                    filename = st.text_input(f"Filename {i+1}",
                                           value=default_clock_error.get('filename', ''),
                                           key=f"sce_filename_{i}",
                                           label_visibility="collapsed")
                with cols[6]:
                    battery_voltage = st.text_input(f"Battery Voltage {i+1}",
                                                   value=default_clock_error.get('battery_voltage', ''),
                                                   key=f"sce_battery_voltage_{i}",
                                                   label_visibility="collapsed")
                with cols[7]:
                    num_records = st.text_input(f"Number of Records {i+1}",
                                              value=default_clock_error.get('number_of_records', ''),
                                              key=f"sce_num_records_{i}",
                                              label_visibility="collapsed")
                with cols[8]:
                    comments = st.text_input(f"Comments {i+1}",
                                           value=default_clock_error.get('comments', ''),
                                           key=f"sce_comments_{i}",
                                           label_visibility="collapsed")

                # Only add to list if at least one field has data
                if any([sensor_type, sensor_sn, actual_time, inst_time, clock_error,
                       filename, battery_voltage, num_records, comments]):
                    subsurface_clock_errors.append({
                        'position': i,
                        'sensor_type': sensor_type,
                        'serial_number': sensor_sn,
                        'actual_time': actual_time,
                        'inst_time': inst_time,
                        'clock_error': parse_clock_error_from_mmss(clock_error),
                        'filename': filename,
                        'battery_voltage': battery_voltage,
                        'number_of_records': num_records,
                        'comments': comments
                    })

        # Submit button and Export button row
        button_col1, button_col2 = st.columns([3, 1])
        with button_col1:
            button_label = "Update Recovery" if mode == "Search/Edit" and st.session_state.selected_recovery is not None else "Save Recovery"
            submitted = st.form_submit_button(button_label, use_container_width=True)

        # Add Export XML button outside the form (but visible when editing)
        if mode == "Search/Edit" and st.session_state.selected_recovery is not None:
            with button_col2:
                export_placeholder = st.empty()

        if submitted:
            # Auto-calculate clock errors for new records
            if st.session_state.mode == 'Add New':
                # Calculate tube clock error
                tube_actual_time_val = tube_actual_time
                tube_inst_time_val = tube_inst_time
                if tube_actual_time_val and tube_inst_time_val:
                    calculated_error = calculate_clock_error(tube_actual_time_val, tube_inst_time_val)
                    if calculated_error:
                        tube_clock_error = calculated_error

                # Recalculate subsurface_clock_errors with auto-calculated values
                subsurface_clock_errors_updated = []
                for item in subsurface_clock_errors:
                    if item['actual_time'] and item['inst_time']:
                        calculated_error = calculate_clock_error(item['actual_time'], item['inst_time'])
                        if calculated_error:
                            # Update with calculated value (in seconds)
                            item['clock_error'] = parse_clock_error_from_mmss(calculated_error)
                    subsurface_clock_errors_updated.append(item)
                subsurface_clock_errors = subsurface_clock_errors_updated

            # Collect all form data
            form_data = {
                'site': site,
                'mooringid': mooringid,
                'cruise': cruise,
                'argos_latitude': argos_latitude,
                'argos_longitude': argos_longitude,
                'mooring_status': mooring_status,
                'mooring_type': mooring_type,
                'personnel': personnel,
                'touch_time': touch_time,
                'release_latitude': release_latitude,
                'release_longitude': release_longitude,
                'fire_time': fire_time,
                'fire_date': fire_date,
                'time_on_deck': time_on_deck,
                'date_on_deck': date_on_deck,
                'tube_sn': tube_sn,
                'tube_condition': tube_condition,
                'tube_details': tube_details,
                'ptt_hexid_sn': ptt_hexid_sn,
                'ptt_hexid_condition': ptt_hexid_condition,
                'ptt_hexid_details': ptt_hexid_details,
                'at_rh_sn': at_rh_sn,
                'at_rh_condition': at_rh_condition,
                'at_rh_details': at_rh_details,
                'wind_sn': wind_sn,
                'wind_condition': wind_condition,
                'wind_details': wind_details,
                'rain_gauge_sn': rain_gauge_sn,
                'rain_gauge_condition': rain_gauge_condition,
                'rain_gauge_details': rain_gauge_details,
                'sw_radiation_sn': sw_radiation_sn,
                'sw_radiation_condition': sw_radiation_condition,
                'sw_radiation_details': sw_radiation_details,
                'lw_radiation_sn': lw_radiation_sn,
                'lw_radiation_condition': lw_radiation_condition,
                'lw_radiation_details': lw_radiation_details,
                'barometer_sn': barometer_sn,
                'barometer_condition': barometer_condition,
                'barometer_details': barometer_details,
                'seacat_sn': seacat_sn,
                'seacat_condition': seacat_condition,
                'seacat_details': seacat_details,
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
                # Fishing/Vandalism Evidence
                'fishing_vandalism': fishing_vandalism,
                # Subsurface Instruments
                'subsurface_instruments': subsurface_instruments,
                # Nylon Recovered (collect from individual fields)
                **{f'nylon_spool_{i}': st.session_state.get(f'nylon_spool_{i}', '') for i in range(10)},
                **{f'nylon_sn_{i}': st.session_state.get(f'nylon_sn_{i}', '') for i in range(10)},
                **{f'nylon_length_{i}': st.session_state.get(f'nylon_length_{i}', '') for i in range(10)},
                **{f'nylon_condition_{i}': st.session_state.get(f'nylon_condition_{i}', '') for i in range(10)},
                # Hardware
                'buoy_hardware_sn': buoy_hardware_sn,
                'buoy_hardware_condition': buoy_hardware_condition,
                'buoy_top_section_sn': buoy_top_section_sn,
                'buoy_glass_balls': buoy_glass_balls,
                'wire_hardware_sn': wire_hardware_sn,
                'wire_hardware_condition': wire_hardware_condition,
                # Tube
                'battery_logic': battery_logic,
                'battery_transmit': battery_transmit,
                'tube_date': tube_date,
                'tube_actual_time': tube_actual_time,
                'tube_inst_time': tube_inst_time,
                'tube_clock_error': tube_clock_error,
                # Subsurface Clock Errors
                'subsurface_clock_errors': subsurface_clock_errors,
                # Subsurface Sensors
                'wire_top_section_sn': '',  # Not used for wire
                'wire_glass_balls': '',  # Not used for wire
                # Release Information data
                'rel_type_1': rel_type_1,
                'rel_sn_1': rel_sn_1,
                'rel_1_rec': rel_1_rec,
                'rel_type_2': rel_type_2,
                'rel_sn_2': rel_sn_2,
                'rel_2_rec': rel_2_rec,
                'release1_release': release1_release,
                'release1_disable': release1_disable,
                'release1_enable': release1_enable,
                'release2_release': release2_release,
                'release2_disable': release2_disable,
                'release2_enable': release2_enable,
                'release_comments': release_comments,
            }

            # Validate required fields (only Cruise and Mooring ID are required)
            required_fields = {
                'Mooring ID': form_data.get('mooringid'),
                'Cruise': form_data.get('cruise')
            }

            missing_fields = [name for name, value in required_fields.items() if not value]

            if missing_fields:
                st.error(f"Please fill in required fields: {', '.join(missing_fields)}")
            else:
                # Save or update to database
                if mode == "Search/Edit" and st.session_state.selected_recovery is not None:
                    # Update existing record
                    recovery_id = st.session_state.selected_recovery.get('id')

                    if recovery_id is None:
                        st.error("Could not determine recovery ID for update. The 'id' field is missing from the selected record.")
                        st.stop()

                    success, result = update_recovery_data(recovery_id, form_data)
                    if success:
                        if isinstance(result, dict):
                            st.success(f"✅ Recovery updated successfully!")
                            # Show the actual date column that was updated
                            date_info = ""
                            for key, value in result.items():
                                if 'date' in key.lower() or 'fire' in key.lower():
                                    date_info = f" - {key} is now: {value}"
                                    break
                            if date_info:
                                st.info(f"Verified in database{date_info}")
                        else:
                            st.success(f"✅ Recovery updated successfully! (ID: {result})")

                        # Update the current record in session state with the new values
                        st.session_state.selected_recovery.update(form_data)

                        # Also update the search results if they exist
                        if st.session_state.search_results is not None and st.session_state.current_record_index is not None:
                            # Update the dataframe row with new values
                            for key, value in form_data.items():
                                if key in st.session_state.search_results.columns:
                                    st.session_state.search_results.at[st.session_state.current_record_index, key] = value

                        st.success("✅ Data updated and display refreshed!")
                        st.info("The form now shows the updated values. You can continue editing or search for another record.")

                        # Trigger a rerun to refresh the display
                        st.rerun()
                    else:
                        st.error(f"❌ Error updating recovery: {result}")
                else:
                    # Save new record
                    success, result = save_recovery_data(form_data)
                    if success:
                        st.success(f"✅ Recovery saved successfully! (ID: {result})")
                        st.info("The form has been saved. You can continue to add more recoveries by modifying the fields above and clicking 'Save Recovery' again.")
                    else:
                        st.error(f"❌ Error saving recovery: {result}")

                # Show the collected data
                with st.expander("View Saved Data"):
                    st.json(form_data)

    # Add export button at the bottom for Search/Edit mode
    if mode == "Search/Edit" and st.session_state.selected_recovery is not None:
        st.divider()
        bottom_cols = st.columns([1, 1, 2])
        with bottom_cols[0]:
            if st.button("📄 Export Current Record to XML", key="bottom_export", use_container_width=True):
                try:
                    xml_content = export_record_to_xml(st.session_state.selected_recovery)
                    # Generate filename
                    site = st.session_state.selected_recovery.get('site', 'unknown')
                    mooring_id = st.session_state.selected_recovery.get('mooring_id', st.session_state.selected_recovery.get('mooringid', 'unknown'))
                    cruise = st.session_state.selected_recovery.get('cruise', 'unknown')
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"recovery_{site}_{mooring_id}_{cruise}_{timestamp}.xml"

                    # Store in session state for download
                    st.session_state['xml_export'] = {
                        'content': xml_content,
                        'filename': filename
                    }
                    st.success("✅ XML export generated!")
                except Exception as e:
                    st.error(f"❌ Error generating XML: {str(e)}")

        with bottom_cols[1]:
            if 'xml_export' in st.session_state:
                st.download_button(
                    label="⬇️ Download XML",
                    data=st.session_state['xml_export']['content'],
                    file_name=st.session_state['xml_export']['filename'],
                    mime="application/xml",
                    use_container_width=True
                )

if __name__ == "__main__":
    main()
