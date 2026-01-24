import streamlit as st
import sqlite3
import json
import pandas as pd
from datetime import datetime, date, time

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect('Cruise_Logs.db', check_same_thread=False)

def search_recoveries(search_criteria=None):
    """Search for existing recovery records."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Base query
        query = """
            SELECT id, mooring_id, recovery_metadata, recovery_location, recovery_timing,
                   instrument_data_collection, mooring_line_recovery, release_system_recovery,
                   beacon_recovery, flasher_recovery, subsurface_recovery, cruise_information,
                   data_quality_analysis, instrumentation, beacons
            FROM adcp_rec2 WHERE 1=1
        """
        params = []

        # Add search criteria
        if search_criteria:
            if search_criteria.get('site'):
                query += " AND json_extract(recovery_metadata, '$.site') LIKE ?"
                params.append(f"%{search_criteria['site']}%")
            if search_criteria.get('mooring_id'):
                query += " AND mooring_id LIKE ?"
                params.append(f"%{search_criteria['mooring_id']}%")
            if search_criteria.get('cruise'):
                query += " AND json_extract(cruise_information, '$.cruise') LIKE ?"
                params.append(f"%{search_criteria['cruise']}%")

        query += " ORDER BY id DESC"
        cursor.execute(query, params)

        # Convert to DataFrame for easier handling
        columns = ['id', 'mooring_id', 'recovery_metadata', 'recovery_location', 'recovery_timing',
                  'instrument_data_collection', 'mooring_line_recovery', 'release_system_recovery',
                  'beacon_recovery', 'flasher_recovery', 'subsurface_recovery', 'cruise_information',
                  'data_quality_analysis', 'instrumentation', 'beacons']
        results = cursor.fetchall()

        if results:
            df = pd.DataFrame(results, columns=columns)
            return df
        else:
            return pd.DataFrame()

    finally:
        conn.close()

def get_distinct_sites():
    """Get list of unique sites from recovery records."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT json_extract(recovery_metadata, '$.site') as site
            FROM adcp_rec2
            WHERE json_extract(recovery_metadata, '$.site') IS NOT NULL
            ORDER BY site
        """)
        sites = [row[0] for row in cursor.fetchall() if row[0]]
        return sites
    finally:
        conn.close()

def parse_json_field(json_str):
    """Parse JSON field safely."""
    try:
        if isinstance(json_str, str):
            return json.loads(json_str)
        return json_str if json_str else {}
    except (json.JSONDecodeError, TypeError):
        return {}

def get_personnel_by_cruise(cruise_name):
    """Get personnel information for a specific cruise."""
    if not cruise_name or not cruise_name.strip():
        return ""

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Personnel FROM Cruise_Info WHERE Cruise = ?", (cruise_name.strip(),))
        result = cursor.fetchone()
        return result[0] if result and result[0] else ""
    except Exception as e:
        return ""
    finally:
        conn.close()

def calculate_time_error(gmt_time, inst_time):
    """Calculate time error as GMT Time - Inst. Time"""
    if not gmt_time or not inst_time:
        return ''

    try:
        from datetime import datetime, timedelta

        # Parse times - assume format HH:MM:SS or HH:MM
        def parse_time(time_str):
            time_str = time_str.strip()
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) == 2:  # HH:MM
                    hours, minutes = int(parts[0]), int(parts[1])
                    seconds = 0
                elif len(parts) == 3:  # HH:MM:SS
                    hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                else:
                    return None
                return hours * 3600 + minutes * 60 + seconds
            return None

        gmt_seconds = parse_time(gmt_time)
        inst_seconds = parse_time(inst_time)

        if gmt_seconds is None or inst_seconds is None:
            return ''

        # Calculate difference in seconds
        diff_seconds = gmt_seconds - inst_seconds

        # Handle day boundary crossing
        if diff_seconds > 12 * 3600:  # More than 12 hours positive
            diff_seconds -= 24 * 3600
        elif diff_seconds < -12 * 3600:  # More than 12 hours negative
            diff_seconds += 24 * 3600

        # Format as MM:SS with sign
        sign = '+' if diff_seconds >= 0 else '-'
        abs_seconds = abs(diff_seconds)
        minutes = abs_seconds // 60
        seconds = abs_seconds % 60

        return f"{sign}{minutes}:{seconds:02d}"

    except (ValueError, TypeError):
        return ''

def calculate_date_error(gmt_date, inst_date):
    """Calculate date error as GMT Date - Inst. Date (in days)"""
    if not gmt_date or not inst_date:
        return ''

    try:
        from datetime import datetime

        # Parse dates - assume format YYYY-MM-DD
        def parse_date(date_str):
            date_str = date_str.strip()
            if len(date_str) >= 10:  # At least YYYY-MM-DD
                date_part = date_str[:10]
                return datetime.strptime(date_part, "%Y-%m-%d")
            return None

        gmt_date_obj = parse_date(gmt_date)
        inst_date_obj = parse_date(inst_date)

        if gmt_date_obj is None or inst_date_obj is None:
            return ''

        # Calculate difference in days
        diff_days = (gmt_date_obj - inst_date_obj).days

        # Format with sign
        if diff_days == 0:
            return '0'
        elif diff_days > 0:
            return f"+{diff_days}"
        else:
            return f"{diff_days}"

    except (ValueError, TypeError):
        return ''

def save_recovery(form_data, record_id=None):
    """Save recovery record to database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Prepare JSON data structures for new organized format
        recovery_metadata = {
            "recovery_date": form_data.get('recovery_date', ''),
            "site": form_data.get('site', ''),
            "cruise": form_data.get('cruise', ''),
            "julian_date": form_data.get('julian_date', ''),
            "actual_nylon_cut_length": form_data.get('actual_nylon_cut_length', ''),
            "depth": form_data.get('depth', ''),
            "subsurface_recovery_notes": form_data.get('subsurface_recovery_notes', '')
        }

        recovery_location = {
            "buoy_latitude": form_data.get('latitude', ''),
            "buoy_longitude": form_data.get('longitude', ''),
            "slant_ranges": form_data.get('slant_ranges', ''),
            "post_release_slant_ranges": form_data.get('post_release_slant_ranges', '')
        }

        recovery_timing = {
            "confirmed_release_time": form_data.get('release_fire_time', ''),
            "release_enable_time": form_data.get('release_enable_time', ''),
            "rel_enable_date": form_data.get('rel_enable_date', ''),
            "float_ball_on_deck": form_data.get('time_on_deck', ''),
            "float_ball_sighted_on_surface": form_data.get('float_ball_sighted', ''),
            "last_release_on_deck": form_data.get('last_release_on_deck', '')
        }

        # Get instrumentation data to sync with instrument_data_collection
        instrumentation_data = form_data.get('instrumentation', {})
        pressure_instruments = instrumentation_data.get('pressure_instruments', [])

        # Start with existing instrument_data_collection or empty dict
        instrument_data_collection = {}

        # Process pressure instruments and map to instrument_data_collection
        instrument_index = 0
        for instrument in pressure_instruments:
            inst_type = instrument.get('type', '')
            serial_number = instrument.get('serial_number', '')
            status = instrument.get('status', '')
            comments = instrument.get('comments', '')

            if inst_type and (serial_number or status != 'OK' or comments):  # Only save if has meaningful data
                instrument_key = f"instrument_{instrument_index}"
                instrument_data_collection[instrument_key] = {
                    "type": inst_type,
                    "serial_number": serial_number,
                    "status": status,
                    "comment": comments,
                    "battery": form_data.get('adcp_battery', '') if inst_type == 'ADCP' else '',
                    "clock_comment": form_data.get('adcp_clock_comment', '') if inst_type == 'ADCP' else '',
                    "date": form_data.get('adcp_date', '') if inst_type == 'ADCP' else '',
                    "date_error": form_data.get('adcp_date_error', '') if inst_type == 'ADCP' else '',
                    "error": form_data.get('adcp_error', '') if inst_type == 'ADCP' else '',
                    "filename": form_data.get('adcp_filename', '') if inst_type == 'ADCP' else '',
                    "gmt_time": form_data.get('adcp_gmt_time', '') if inst_type == 'ADCP' else '',
                    "gmt_date": form_data.get('adcp_gmt_date', '') if inst_type == 'ADCP' else '',
                    "number_records": form_data.get('adcp_number_records', '') if inst_type == 'ADCP' else '',
                    "time": form_data.get('adcp_time', '') if inst_type == 'ADCP' else ''
                }
                instrument_index += 1

        # Ensure instrument_0 is always ADCP (fallback if no instrumentation data)
        if 'instrument_0' not in instrument_data_collection:
            instrument_data_collection["instrument_0"] = {
                "type": "ADCP",
                "serial_number": form_data.get('adcp_sn', ''),
                "status": form_data.get('adcp_status', ''),
                "comment": form_data.get('adcp_comment', ''),
                "battery": form_data.get('adcp_battery', ''),
                "clock_comment": form_data.get('adcp_clock_comment', ''),
                "date": form_data.get('adcp_date', ''),
                "date_error": form_data.get('adcp_date_error', ''),
                "error": form_data.get('adcp_error', ''),
                "filename": form_data.get('adcp_filename', ''),
                "gmt_time": form_data.get('adcp_gmt_time', ''),
                "gmt_date": form_data.get('adcp_gmt_date', ''),
                "number_records": form_data.get('adcp_number_records', ''),
                "time": form_data.get('adcp_time', '')
            }

        # Get mooring components data from form and convert to line_X format
        mooring_components_data = form_data.get('mooring_components', {})
        components_list = mooring_components_data.get('components', [])

        mooring_line_recovery = {}

        # Convert components list to line_X format for database storage
        for i, component in enumerate(components_list):
            line_key = f"line_{i+1}"
            mooring_line_recovery[line_key] = {
                'type': component.get('type') or None,
                'serial_number': component.get('serial_number') or None,
                'length': float(component.get('length')) if component.get('length') and component.get('length').replace('.', '').isdigit() else None,
                'status': component.get('status') or 'OK',
                'comment': component.get('comments') or None
            }

        release_system_recovery = {
            "top_release": {
                "serial_number": form_data.get('rel_top_sn', ''),
                "type": form_data.get('rel_top_type', ''),
                "lost": form_data.get('rel_top_lost', '')
            },
            "bottom_release": {
                "serial_number": form_data.get('rel_btm_sn', ''),
                "type": form_data.get('rel_btm_type', ''),
                "lost": form_data.get('rel_btm_lost', '')
            },
            "release_communication": form_data.get('release_communication', '')
        }

        # Get beacons data from form
        beacons_data = form_data.get('beacons', {})
        beacons_list = beacons_data.get('beacons', [])

        # Initialize beacon and flasher structures
        beacon_recovery = {
            "rf_beacon": {
                "serial_number": form_data.get('rf_beacon_sn', ''),
                "status": form_data.get('rf_beacon_status', ''),
                "transmit_frequency": form_data.get('rf_beacon_freq', ''),
                "comment": form_data.get('rf_beacon_comment', '')
            },
            "argos_beacon": {
                "serial_number": form_data.get('argos_beacon_sn', ''),
                "ptt": form_data.get('argos_beacon_ptt', ''),
                "status": form_data.get('argos_beacon_status', ''),
                "comment": form_data.get('argos_beacon_comment', '')
            }
        }

        flasher_recovery = {
            "serial_number": form_data.get('flasher_sn', ''),
            "status": form_data.get('flasher_status', ''),
            "comment": form_data.get('flasher_comment', '')
        }

        # Update beacon and flasher structures from beacons data
        for beacon in beacons_list:
            beacon_type = beacon.get('type', '').lower()
            if 'rf' in beacon_type or beacon_type == 'rf beacon':
                beacon_recovery["rf_beacon"] = {
                    "serial_number": beacon.get('serial_number', ''),
                    "status": beacon.get('status', ''),
                    "transmit_frequency": form_data.get('rf_beacon_freq', ''),
                    "comment": beacon.get('comments', '')
                }
            elif 'argos' in beacon_type or beacon_type == 'argos beacon':
                beacon_recovery["argos_beacon"] = {
                    "serial_number": beacon.get('serial_number', ''),
                    "ptt": form_data.get('argos_beacon_ptt', ''),
                    "status": beacon.get('status', ''),
                    "comment": beacon.get('comments', '')
                }
            elif 'flasher' in beacon_type:
                flasher_recovery = {
                    "serial_number": beacon.get('serial_number', ''),
                    "status": beacon.get('status', ''),
                    "comment": beacon.get('comments', '')
                }

        subsurface_recovery = {
            "notes": form_data.get('subsurface_notes', ''),
            "slant_ranges": form_data.get('slant_ranges', ''),
            "post_release_slant_ranges": form_data.get('post_release_slant_ranges', ''),
            "buoy_position": {
                "latitude": form_data.get('latitude', ''),
                "longitude": form_data.get('longitude', '')
            }
        }

        cruise_information = {
            "cruise": form_data.get('cruise', ''),
            "site": form_data.get('site', ''),
            "beginning_date": form_data.get('cruise_beginning_date', ''),
            "ending_date": form_data.get('cruise_ending_date', ''),
            "personnel": form_data.get('personnel', '')
        }

        instrumentation = form_data.get('instrumentation', {})

        data_quality_analysis = {}

        recovery_info = form_data.get('recovery_info', {})

        if record_id:
            # Update existing record
            cursor.execute("""
                UPDATE adcp_rec2 SET
                mooring_id = ?, recovery_metadata = ?, recovery_location = ?, recovery_timing = ?,
                instrument_data_collection = ?, mooring_line_recovery = ?, release_system_recovery = ?,
                beacon_recovery = ?, flasher_recovery = ?, subsurface_recovery = ?, cruise_information = ?,
                data_quality_analysis = ?, instrumentation = ?, beacons = ?, recovery_info = ?
                WHERE id = ?
            """, (
                form_data.get('mooring_id', ''),
                json.dumps(recovery_metadata),
                json.dumps(recovery_location),
                json.dumps(recovery_timing),
                json.dumps(instrument_data_collection),
                json.dumps(mooring_line_recovery),
                json.dumps(release_system_recovery),
                json.dumps(beacon_recovery),
                json.dumps(flasher_recovery),
                json.dumps(subsurface_recovery),
                json.dumps(cruise_information),
                json.dumps(data_quality_analysis),
                json.dumps(instrumentation),
                json.dumps(beacons_data),
                json.dumps(recovery_info),
                record_id
            ))
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO adcp_rec2
                (mooring_id, recovery_metadata, recovery_location, recovery_timing,
                 instrument_data_collection, mooring_line_recovery, release_system_recovery,
                 beacon_recovery, flasher_recovery, subsurface_recovery, cruise_information,
                 data_quality_analysis, instrumentation, beacons, recovery_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                form_data.get('mooring_id', ''),
                json.dumps(recovery_metadata),
                json.dumps(recovery_location),
                json.dumps(recovery_timing),
                json.dumps(instrument_data_collection),
                json.dumps(mooring_line_recovery),
                json.dumps(release_system_recovery),
                json.dumps(beacon_recovery),
                json.dumps(flasher_recovery),
                json.dumps(subsurface_recovery),
                json.dumps(cruise_information),
                json.dumps(data_quality_analysis),
                json.dumps(instrumentation),
                json.dumps(beacons_data),
                json.dumps(recovery_info)
            ))
            record_id = cursor.lastrowid

        conn.commit()
        return True, record_id
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def main():
    """Main Streamlit application function."""

    # Page configuration
    st.set_page_config(
        page_title="ADCP Recovery Form",
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
        color: #1f77b4;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .stTextInput label {
        font-weight: 600;
        color: var(--text-color);
    }
    .instrumentation-table {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        margin: 10px 0;
        background-color: #f9f9f9;
    }
    .inst-header {
        font-weight: bold;
        padding: 5px;
        background-color: #e9ecef;
        border-bottom: 1px solid #ddd;
        margin-bottom: 10px;
    }
    .inst-row {
        padding: 5px 0;
        border-bottom: 1px solid #eee;
    }
    .inst-row:last-child {
        border-bottom: none;
    }
    </style>
    """, unsafe_allow_html=True)

    # Main title
    st.title("ADCP Recovery Form")

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
    if 'last_filled_cruise' not in st.session_state:
        st.session_state.last_filled_cruise = ""

    # Mode selection
    mode = st.radio("Mode", ["Search/Edit", "Add New"], key="mode_selector", horizontal=True)

    # Reset instruments when switching to Add New mode
    if mode == "Add New" and st.session_state.mode != mode:
        st.session_state.instruments = []
        st.session_state.beacons = []

    st.session_state.mode = mode

    # Get list of sites for dropdown
    available_sites = get_distinct_sites()

    # Search section
    if mode == "Search/Edit":
        st.subheader("Search Recoveries")

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
                results = search_recoveries(search_criteria)
                st.session_state.search_results = results
                st.session_state.current_record_index = 0

                if results.empty:
                    st.warning("No recoveries found matching your criteria.")
                else:
                    st.success(f"Found {len(results)} recovery/recoveries")

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
                st.session_state.selected_recovery = current_record_dict

                # Reset instruments session state when selecting a record
                # First try to get data from instrumentation column
                instrumentation_data = parse_json_field(current_record_dict.get('instrumentation', '{}'))
                default_instruments = instrumentation_data.get('pressure_instruments', [])

                # If no instrumentation data, populate from instrument_data_collection
                if not default_instruments:
                    instrument_data_collection = parse_json_field(current_record_dict.get('instrument_data_collection', '{}'))
                    default_instruments = []

                    # Create instruments directly from database data
                    for key, instrument in sorted(instrument_data_collection.items()):
                        if instrument:
                            # Handle instrument_0 specially (always ADCP)
                            if key == 'instrument_0':
                                default_instruments.append({
                                    'type': 'ADCP',
                                    'serial_number': str(instrument.get('serial_number', '')) if instrument.get('serial_number') else '',
                                    'status': instrument.get('status', 'OK') or 'OK',
                                    'comments': instrument.get('comment', '') or instrument.get('comments', '') or ''
                                })
                            elif instrument.get('type'):
                                default_instruments.append({
                                    'type': instrument.get('type'),
                                    'serial_number': str(instrument.get('serial_number', '')) if instrument.get('serial_number') else '',
                                    'status': instrument.get('status', 'OK') or 'OK',
                                    'comments': instrument.get('comment', '') or instrument.get('comments', '') or ''
                                })

                st.session_state.instruments = default_instruments

                # Reset beacons session state when selecting a record
                # First try to get data from beacons column
                beacons_data = parse_json_field(current_record_dict.get('beacons', '{}'))
                default_beacons = beacons_data.get('beacons', [])

                # If no beacons data, populate from beacon_recovery and flasher_recovery
                if not default_beacons:
                    beacon_recovery = parse_json_field(current_record_dict.get('beacon_recovery', '{}'))
                    flasher_recovery = parse_json_field(current_record_dict.get('flasher_recovery', '{}'))
                    default_beacons = []

                    # Add RF beacon if it exists
                    if beacon_recovery.get('rf_beacon') and (beacon_recovery['rf_beacon'].get('serial_number') or beacon_recovery['rf_beacon'].get('status')):
                        rf_beacon = beacon_recovery['rf_beacon']
                        default_beacons.append({
                            'type': 'RF Beacon',
                            'serial_number': str(rf_beacon.get('serial_number', '')) if rf_beacon.get('serial_number') else '',
                            'status': rf_beacon.get('status', 'OK') or 'OK',
                            'comments': rf_beacon.get('comment', '') or ''
                        })

                    # Add Argos beacon if it exists
                    if beacon_recovery.get('argos_beacon') and (beacon_recovery['argos_beacon'].get('serial_number') or beacon_recovery['argos_beacon'].get('status')):
                        argos_beacon = beacon_recovery['argos_beacon']
                        default_beacons.append({
                            'type': 'Argos Beacon',
                            'serial_number': str(argos_beacon.get('serial_number', '')) if argos_beacon.get('serial_number') else '',
                            'status': argos_beacon.get('status', 'OK') or 'OK',
                            'comments': argos_beacon.get('comment', '') or ''
                        })

                    # Add Flasher - always include even if empty
                    default_beacons.append({
                        'type': 'Flasher',
                        'serial_number': str(flasher_recovery.get('serial_number', '')) if flasher_recovery and flasher_recovery.get('serial_number') else '',
                        'status': flasher_recovery.get('status', 'OK') if flasher_recovery else 'OK',
                        'comments': flasher_recovery.get('comment', '') if flasher_recovery else ''
                    })

                st.session_state.beacons = default_beacons

                # Initialize mooring components session state when selecting a record
                mooring_line_recovery = parse_json_field(current_record_dict.get('mooring_line_recovery', '{}'))
                default_components = []

                # Parse line_1, line_2, etc. format from database
                for key, component in sorted(mooring_line_recovery.items()):
                    if key.startswith('line_') and component:
                        # Only add components that have meaningful data
                        if (component.get('type') or
                            component.get('serial_number') or
                            component.get('length') or
                            component.get('comment')):
                            default_components.append({
                                'type': component.get('type') or '',
                                'serial_number': component.get('serial_number') or '',
                                'length': str(component.get('length', '')) if component.get('length') else '',
                                'status': component.get('status') or 'OK',
                                'comments': component.get('comment') or ''
                            })

                st.session_state.mooring_components = default_components

                # Initialize releases session state when selecting a record
                release_system_data = parse_json_field(current_record_dict.get('release_system_recovery', '{}'))

                # Extract top and bottom release data
                top_release = release_system_data.get('top_release', {})
                bottom_release = release_system_data.get('bottom_release', {})

                # Convert to our internal format
                def get_recovered_status(release_data):
                    lost_value = release_data.get('lost')
                    if lost_value is None:
                        return ''
                    elif lost_value is True:
                        return 'No'
                    elif lost_value is False:
                        return 'Yes'
                    else:
                        return ''

                default_releases = [
                    {
                        'position': 'Top',
                        'serial_number': str(top_release.get('serial_number', '')) if top_release.get('serial_number') else '',
                        'type': str(top_release.get('type', '')) if top_release.get('type') else '',
                        'recovered': get_recovered_status(top_release)
                    },
                    {
                        'position': 'Bottom',
                        'serial_number': str(bottom_release.get('serial_number', '')) if bottom_release.get('serial_number') else '',
                        'type': str(bottom_release.get('type', '')) if bottom_release.get('type') else '',
                        'recovered': get_recovered_status(bottom_release)
                    }
                ]

                st.session_state.releases = default_releases
                st.session_state.release_communication = release_system_data.get('release_communication', '')

                # Initialize clock errors session state when selecting a record
                instrument_data_collection = parse_json_field(current_record_dict.get('instrument_data_collection', '{}'))

                # Extract clock errors from instrument_data_collection
                default_clock_errors = [
                    {'instrument': 'ADCP', 'serial_number': '', 'gmt_date': '', 'inst_date': '', 'date_error': '', 'gmt_time': '', 'inst_time': '', 'time_error': '', 'file_name': '', 'comments': ''},
                    {'instrument': 'P1', 'serial_number': '', 'gmt_date': '', 'inst_date': '', 'date_error': '', 'gmt_time': '', 'inst_time': '', 'time_error': '', 'file_name': '', 'comments': ''},
                    {'instrument': 'P2', 'serial_number': '', 'gmt_date': '', 'inst_date': '', 'date_error': '', 'gmt_time': '', 'inst_time': '', 'time_error': '', 'file_name': '', 'comments': ''}
                ]

                # Map instrument_data_collection to clock errors format
                # Check specific instrument positions for ADCP, P1, P2
                instrument_keys = ['instrument_0', 'instrument_1', 'instrument_2']

                for i, inst_key in enumerate(instrument_keys):
                    if inst_key in instrument_data_collection:
                        instrument = instrument_data_collection[inst_key]
                        if instrument and (instrument.get('type') or instrument.get('serial_number') or
                                         instrument.get('filename') or instrument.get('clock_comment')):

                            clock_error_entry = {
                                'serial_number': str(instrument.get('serial_number', '')) if instrument.get('serial_number') else '',
                                'gmt_date': str(instrument.get('gmt_date', ''))[:10] if instrument.get('gmt_date') else '',  # Extract date part
                                'inst_date': str(instrument.get('date', ''))[:10] if instrument.get('date') else '',  # Extract date part
                                'date_error': '',  # Will be calculated from GMT and Inst dates
                                'gmt_time': str(instrument.get('gmt_time', '')) if instrument.get('gmt_time') else '',
                                'inst_time': str(instrument.get('time', '')) if instrument.get('time') else '',
                                'time_error': '',  # Will be calculated from GMT and Inst times
                                'file_name': str(instrument.get('filename', '')) if instrument.get('filename') else '',
                                'comments': str(instrument.get('clock_comment', '')) if instrument.get('clock_comment') else ''
                            }

                            if i == 0:  # instrument_0 -> ADCP
                                default_clock_errors[0].update({
                                    'instrument': 'ADCP',
                                    **clock_error_entry
                                })
                            elif i == 1:  # instrument_1 -> P1
                                default_clock_errors[1].update({
                                    'instrument': 'P1',
                                    **clock_error_entry
                                })
                            elif i == 2:  # instrument_2 -> P2
                                default_clock_errors[2].update({
                                    'instrument': 'P2',
                                    **clock_error_entry
                                })

                st.session_state.clock_errors = default_clock_errors

                # Initialize general comments session state when selecting a record
                st.session_state.general_comments = current_record_dict.get('general_comments', '')

                # Parse JSON fields for display
                recovery_metadata = parse_json_field(current_record_dict.get('recovery_metadata', '{}'))
                cruise_information = parse_json_field(current_record_dict.get('cruise_information', '{}'))

                # Display current record summary
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Mooring ID", current_record_dict.get('mooring_id', 'N/A'))
                with col2:
                    st.metric("Site", recovery_metadata.get('site', 'N/A'))
                with col3:
                    st.metric("Cruise", cruise_information.get('cruise', 'N/A'))
                with col4:
                    recovery_date = recovery_metadata.get('recovery_date', 'N/A')
                    if recovery_date and recovery_date != 'N/A':
                        try:
                            formatted_date = datetime.strptime(recovery_date, "%Y-%m-%d %H:%M:%S").strftime("%m/%d/%Y")
                        except:
                            formatted_date = recovery_date
                    else:
                        formatted_date = 'N/A'
                    st.metric("Recovery Date", formatted_date)

    st.markdown("---")

    # Set up default values based on mode
    if mode == "Search/Edit" and st.session_state.selected_recovery:
        # Use selected recovery data for defaults
        current_record = st.session_state.selected_recovery
        recovery_metadata = parse_json_field(current_record.get('recovery_metadata', '{}'))
        recovery_location = parse_json_field(current_record.get('recovery_location', '{}'))
        recovery_timing = parse_json_field(current_record.get('recovery_timing', '{}'))
        cruise_information = parse_json_field(current_record.get('cruise_information', '{}'))

        default_mooring_id = current_record.get('mooring_id', '')
        default_site = recovery_metadata.get('site', '')
        default_cruise = cruise_information.get('cruise', '')
        default_personnel = cruise_information.get('personnel', '')

        default_latitude = recovery_location.get('buoy_latitude', '') if recovery_location else ''
        default_longitude = recovery_location.get('buoy_longitude', '') if recovery_location else ''
        default_release_fire_time = recovery_timing.get('confirmed_release_time', '') if recovery_timing else ''
        default_time_on_deck = recovery_timing.get('float_ball_on_deck', '') if recovery_timing else ''

        # Recovery Info defaults - map from recovery_timing and recovery_info
        recovery_info_data = parse_json_field(current_record.get('recovery_info', '{}'))

        # Combine release enable time and date with proper formatting
        enable_time = recovery_timing.get('release_enable_time', '') if recovery_timing else ''
        enable_date = recovery_timing.get('rel_enable_date', '') if recovery_timing else ''

        # Format enable date to YYYY-MM-DD
        formatted_enable_date = ''
        if enable_date:
            try:
                from datetime import datetime
                parsed_date = datetime.strptime(enable_date, "%Y-%m-%d %H:%M:%S")
                formatted_enable_date = parsed_date.strftime("%Y-%m-%d")
            except:
                formatted_enable_date = enable_date.split()[0] if ' ' in enable_date else enable_date

        default_release_enable_combined = f"{formatted_enable_date} / {enable_time}".strip() if formatted_enable_date or enable_time else ''

        # Combine confirmed release time with enable date (same date)
        confirmed_time = recovery_timing.get('confirmed_release_time', '') if recovery_timing else ''

        # Use the same formatted date as release enable date
        default_confirmed_release_combined = f"{formatted_enable_date} / {confirmed_time}".strip() if formatted_enable_date or confirmed_time else ''
        default_depth = recovery_metadata.get('depth', '') if recovery_metadata else ''

        default_final_pre_release_slant_range = recovery_location.get('slant_ranges', '') if recovery_location else ''
        default_time_float_sighted = recovery_timing.get('float_ball_sighted_on_surface', '') if recovery_timing else ''
        # Handle null values for post_release_slant_ranges
        post_release_slant = recovery_location.get('post_release_slant_ranges') if recovery_location else None
        default_first_post_release_slant_range = post_release_slant if post_release_slant is not None else ''
        default_time_float_on_deck = recovery_timing.get('float_ball_on_deck', '') if recovery_timing else ''
        default_time_releases_on_deck = recovery_timing.get('last_release_on_deck', '') if recovery_timing else ''

        # Convert recovery_date string to date object if it exists
        default_recovery_date = date.today()
        if recovery_metadata.get('recovery_date'):
            try:
                default_recovery_date = datetime.strptime(recovery_metadata['recovery_date'], "%Y-%m-%d %H:%M:%S").date()
            except:
                pass
    else:
        # Defaults for Add New mode
        default_mooring_id = ""
        default_site = ""
        default_cruise = ""
        default_personnel = ""
        default_latitude = ""
        default_longitude = ""
        default_release_fire_time = ""
        default_time_on_deck = ""
        default_recovery_date = date.today()

        # Recovery Info defaults for Add New mode
        default_release_enable_combined = ""
        default_confirmed_release_combined = ""
        default_depth = ""
        default_final_pre_release_slant_range = ""
        default_time_float_sighted = ""
        default_first_post_release_slant_range = ""
        default_time_float_on_deck = ""
        default_time_releases_on_deck = ""

        # Initialize empty mooring components for Add New mode
        if 'mooring_components' not in st.session_state:
            st.session_state.mooring_components = []

        # Initialize releases for Add New mode
        if 'releases' not in st.session_state:
            st.session_state.releases = [
                {'position': 'Top', 'serial_number': '', 'type': '', 'recovered': ''},
                {'position': 'Bottom', 'serial_number': '', 'type': '', 'recovered': ''}
            ]
        if 'release_communication' not in st.session_state:
            st.session_state.release_communication = ''

        # Initialize clock errors for Add New mode
        if 'clock_errors' not in st.session_state:
            st.session_state.clock_errors = [
                {'instrument': 'ADCP', 'serial_number': '', 'gmt_date': '', 'inst_date': '', 'date_error': '', 'gmt_time': '', 'inst_time': '', 'time_error': '', 'file_name': '', 'comments': ''},
                {'instrument': 'P1', 'serial_number': '', 'gmt_date': '', 'inst_date': '', 'date_error': '', 'gmt_time': '', 'inst_time': '', 'time_error': '', 'file_name': '', 'comments': ''},
                {'instrument': 'P2', 'serial_number': '', 'gmt_date': '', 'inst_date': '', 'date_error': '', 'gmt_time': '', 'inst_time': '', 'time_error': '', 'file_name': '', 'comments': ''}
            ]

        # Initialize general comments for Add New mode
        if 'general_comments' not in st.session_state:
            st.session_state.general_comments = ''

    # Create the main form
    with st.form("recovery_form"):
        st.subheader("Basic Information")

        # Row 1: Mooring ID, Release Date
        basic_row1 = st.columns([1, 1])
        with basic_row1[0]:
            st.write("**Mooring ID**")
            mooring_id = st.text_input("Mooring ID", value=default_mooring_id, key="mooring_id", label_visibility="collapsed")
        with basic_row1[1]:
            st.write("**Release Date**")
            recovery_date = st.date_input("Release Date", value=default_recovery_date, key="recovery_date", label_visibility="collapsed")

        # Row 2: Site, Cruise
        basic_row2 = st.columns([1, 1])
        with basic_row2[0]:
            st.write("**Site**")
            site = st.text_input("Site", value=default_site, key="site", label_visibility="collapsed")
        with basic_row2[1]:
            st.write("**Cruise**")
            cruise = st.text_input("Cruise", value=default_cruise, key="cruise", label_visibility="collapsed")

        # Row 3: Personnel with simple auto-fill functionality
        st.write("**Personnel**")

        # Check if cruise has changed and auto-fill personnel if found
        current_cruise = cruise.strip() if cruise else ""
        if current_cruise and current_cruise != st.session_state.get('last_filled_cruise', ''):
            auto_personnel = get_personnel_by_cruise(current_cruise)
            if auto_personnel and not default_personnel:
                default_personnel = auto_personnel
                st.session_state['last_filled_cruise'] = current_cruise

        personnel = st.text_input("Personnel", value=default_personnel, key="personnel", label_visibility="collapsed")

        # Row 4: Latitude, Longitude
        basic_row4 = st.columns([1, 1])
        with basic_row4[0]:
            st.write("**Latitude**")
            latitude = st.text_input("Latitude", value=default_latitude, key="latitude", label_visibility="collapsed")
        with basic_row4[1]:
            st.write("**Longitude**")
            longitude = st.text_input("Longitude", value=default_longitude, key="longitude", label_visibility="collapsed")

        # Row 5: Release Fire Time, Time on Deck
        basic_row5 = st.columns([1, 1])
        with basic_row5[0]:
            st.write("**Release Fire Time**")
            release_fire_time = st.text_input("Release Fire Time", value=default_release_fire_time, key="release_fire_time", label_visibility="collapsed")
        with basic_row5[1]:
            st.write("**Time on Deck**")
            time_on_deck = st.text_input("Time on Deck", value=default_time_on_deck, key="time_on_deck", label_visibility="collapsed")

        st.markdown("---")

        st.subheader("Instrumentation")

        if mode == "Search/Edit" and st.session_state.selected_recovery:
            # Get existing instrumentation data if available
            instrumentation_data = parse_json_field(current_record.get('instrumentation', '{}'))
            default_instruments = instrumentation_data.get('pressure_instruments', [])

            # If no instrumentation data, populate from instrument_data_collection
            if not default_instruments:
                instrument_data_collection = parse_json_field(current_record.get('instrument_data_collection', '{}'))
                default_instruments = []

                # Create instruments directly from database data
                for key, instrument in sorted(instrument_data_collection.items()):
                    if instrument:
                        # Handle instrument_0 specially (always ADCP)
                        if key == 'instrument_0':
                            default_instruments.append({
                                'type': 'ADCP',
                                'serial_number': str(instrument.get('serial_number', '')) if instrument.get('serial_number') else '',
                                'status': instrument.get('status', 'OK') or 'OK',
                                'comments': instrument.get('comment', '') or instrument.get('comments', '') or ''
                            })
                        elif instrument.get('type'):
                            default_instruments.append({
                                'type': instrument.get('type'),
                                'serial_number': str(instrument.get('serial_number', '')) if instrument.get('serial_number') else '',
                                'status': instrument.get('status', 'OK') or 'OK',
                                'comments': instrument.get('comment', '') or instrument.get('comments', '') or ''
                            })
        else:
            # Defaults for Add New mode - start with empty list
            default_instruments = []

        # Handle beacons initialization for instrumentation section
        if mode == "Search/Edit" and st.session_state.selected_recovery:
            # Beacon data already initialized above in the session state reset
            pass
        else:
            # Initialize empty beacons for Add New mode with default Flasher
            if 'beacons' not in st.session_state:
                st.session_state.beacons = [
                    {'type': 'Flasher', 'serial_number': '', 'status': 'OK', 'comments': ''}
                ]

        st.write("**Instruments**")

        # Initialize session state for instruments if not exists
        if 'instruments' not in st.session_state:
            st.session_state.instruments = default_instruments.copy()

        # Display existing instrument rows
        header_cols = st.columns([2, 2, 1.5, 3])
        with header_cols[0]:
            st.write("**Inst Type**")
        with header_cols[1]:
            st.write("**S/N**")
        with header_cols[2]:
            st.write("**Status**")
        with header_cols[3]:
            st.write("**Comments**")

        for i, instrument in enumerate(st.session_state.instruments):
            cols = st.columns([2, 2, 1.5, 3])

            with cols[0]:
                # Allow editing of instrument type
                inst_type = st.text_input(
                    f"Type {i+1}",
                    value=instrument.get('type', ''),
                    key=f"inst_type_{i}",
                    label_visibility="collapsed"
                )

            with cols[1]:
                serial_number = st.text_input(
                    f"S/N {i+1}",
                    value=instrument.get('serial_number', ''),
                    key=f"inst_sn_{i}",
                    label_visibility="collapsed"
                )

            with cols[2]:
                instrument_status = instrument.get('status', 'OK') or 'OK'
                status = st.selectbox(
                    f"Status {i+1}",
                    options=['OK', 'Damaged', 'Lost'],
                    index=['OK', 'Damaged', 'Lost'].index(instrument_status),
                    key=f"inst_status_{i}",
                    label_visibility="collapsed"
                )

            with cols[3]:
                comments = st.text_input(
                    f"Comments {i+1}",
                    value=instrument.get('comments', ''),
                    key=f"inst_comments_{i}",
                    label_visibility="collapsed"
                )

            # Update the instrument data in session state
            st.session_state.instruments[i] = {
                'type': inst_type,
                'serial_number': serial_number,
                'status': status,
                'comments': comments
            }

        st.markdown("---")

        st.subheader("Beacons")

        # Initialize session state for beacons if not exists
        if 'beacons' not in st.session_state:
            st.session_state.beacons = []



        # Display existing beacon rows
        header_cols = st.columns([2, 2, 1.5, 3])
        with header_cols[0]:
            st.write("**Type**")
        with header_cols[1]:
            st.write("**S/N**")
        with header_cols[2]:
            st.write("**Status**")
        with header_cols[3]:
            st.write("**Comments**")

        for i, beacon in enumerate(st.session_state.beacons):
            cols = st.columns([2, 2, 1.5, 3])

            with cols[0]:
                # Allow editing of beacon type
                beacon_type = st.text_input(
                    f"Type {i+1}",
                    value=beacon.get('type', ''),
                    key=f"beacon_type_{i}",
                    label_visibility="collapsed"
                )

            with cols[1]:
                serial_number = st.text_input(
                    f"S/N {i+1}",
                    value=beacon.get('serial_number', ''),
                    key=f"beacon_sn_{i}",
                    label_visibility="collapsed"
                )

            with cols[2]:
                beacon_status = beacon.get('status', 'OK') or 'OK'
                status = st.selectbox(
                    f"Status {i+1}",
                    options=['OK', 'Damaged', 'Lost'],
                    index=['OK', 'Damaged', 'Lost'].index(beacon_status),
                    key=f"beacon_status_{i}",
                    label_visibility="collapsed"
                )

            with cols[3]:
                comments = st.text_input(
                    f"Comments {i+1}",
                    value=beacon.get('comments', ''),
                    key=f"beacon_comments_{i}",
                    label_visibility="collapsed"
                )

            # Update the beacon data in session state
            st.session_state.beacons[i] = {
                'type': beacon_type,
                'serial_number': serial_number,
                'status': status,
                'comments': comments
            }

        st.markdown("---")

        st.subheader("Recovery Info")

        # Row 1: Release Enable DateTime, Confirmed Release DateTime
        recovery_row1 = st.columns([1, 1])
        with recovery_row1[0]:
            st.write("**Release Enable DateTime**")
            placeholder_enable = "YYYY-MM-DD / HH:MM:SS" if mode == "Add New" else ""
            release_enable_combined = st.text_input("Release Enable DateTime", value=default_release_enable_combined, placeholder=placeholder_enable, key="release_enable_combined", label_visibility="collapsed")
        with recovery_row1[1]:
            st.write("**Confirmed Release DateTime**")
            placeholder_confirmed = "YYYY-MM-DD / HH:MM:SS" if mode == "Add New" else ""
            confirmed_release_combined = st.text_input("Confirmed Release DateTime", value=default_confirmed_release_combined, placeholder=placeholder_confirmed, key="confirmed_release_combined", label_visibility="collapsed")

        # Row 2: Depth (single column)
        recovery_row2 = st.columns([1, 1])
        with recovery_row2[0]:
            st.write("**Depth**")
            depth = st.text_input("Depth", value=default_depth, key="depth", label_visibility="collapsed")

        # Row 3: Pre-release Slant Range, Time Float sighted
        recovery_row3 = st.columns([1, 1])
        with recovery_row3[0]:
            st.write("**Pre-release Slant Range**")
            final_pre_release_slant_range = st.text_input("Pre-release Slant Range", value=default_final_pre_release_slant_range, key="final_pre_release_slant_range", label_visibility="collapsed")
        with recovery_row3[1]:
            st.write("**Time Float sighted**")
            time_float_sighted = st.text_input("Time Float sighted", value=default_time_float_sighted, key="time_float_sighted", label_visibility="collapsed")

        # Row 4: Post-release Slant Range, Time Float on deck
        recovery_row4 = st.columns([1, 1])
        with recovery_row4[0]:
            st.write("**Post-release Slant Range**")
            first_post_release_slant_range = st.text_input("Post-release Slant Range", value=default_first_post_release_slant_range, key="first_post_release_slant_range", label_visibility="collapsed")
        with recovery_row4[1]:
            st.write("**Time Float on deck**")
            time_float_on_deck = st.text_input("Time Float on deck", value=default_time_float_on_deck, key="time_float_on_deck", label_visibility="collapsed")

        # Row 5: Time releases on deck (single column)
        recovery_row5 = st.columns([1, 1])
        with recovery_row5[0]:
            st.write("**Time releases on deck**")
            time_releases_on_deck = st.text_input("Time releases on deck", value=default_time_releases_on_deck, key="time_releases_on_deck", label_visibility="collapsed")

        st.markdown("---")

        st.subheader("Mooring Components")

        # Initialize session state for mooring components if not exists
        if 'mooring_components' not in st.session_state:
            st.session_state.mooring_components = []

        # Display mooring components table header
        header_cols = st.columns([0.5, 2, 2, 1.5, 1.5, 3])
        with header_cols[0]:
            st.write("**#**")
        with header_cols[1]:
            st.write("**Type**")
        with header_cols[2]:
            st.write("**S/N**")
        with header_cols[3]:
            st.write("**Length**")
        with header_cols[4]:
            st.write("**Status**")
        with header_cols[5]:
            st.write("**Comments**")

        # Display existing mooring component rows
        for i, component in enumerate(st.session_state.mooring_components):
            cols = st.columns([0.5, 2, 2, 1.5, 1.5, 3])

            with cols[0]:
                st.write(f"{i+1}")

            with cols[1]:
                component_type = st.text_input(
                    f"Type {i+1}",
                    value=component.get('type', ''),
                    key=f"component_type_{i}",
                    label_visibility="collapsed"
                )

            with cols[2]:
                serial_number = st.text_input(
                    f"S/N {i+1}",
                    value=component.get('serial_number', ''),
                    key=f"component_sn_{i}",
                    label_visibility="collapsed"
                )

            with cols[3]:
                length = st.text_input(
                    f"Length {i+1}",
                    value=component.get('length', ''),
                    key=f"component_length_{i}",
                    label_visibility="collapsed"
                )

            with cols[4]:
                component_status = component.get('status', 'OK') or 'OK'
                status = st.selectbox(
                    f"Status {i+1}",
                    options=['OK', 'Damaged', 'Lost'],
                    index=['OK', 'Damaged', 'Lost'].index(component_status),
                    key=f"component_status_{i}",
                    label_visibility="collapsed"
                )

            with cols[5]:
                comments = st.text_input(
                    f"Comments {i+1}",
                    value=component.get('comments', ''),
                    key=f"component_comments_{i}",
                    label_visibility="collapsed"
                )

            # Update the component data in session state
            st.session_state.mooring_components[i] = {
                'type': component_type,
                'serial_number': serial_number,
                'length': length,
                'status': status,
                'comments': comments
            }

        st.markdown("---")

        st.subheader("Releases")

        # Initialize session state for releases if not exists
        if 'releases' not in st.session_state:
            st.session_state.releases = [
                {'position': 'Top', 'serial_number': '', 'type': '', 'recovered': ''},
                {'position': 'Bottom', 'serial_number': '', 'type': '', 'recovered': ''}
            ]

        # Display releases table header
        header_cols = st.columns([1, 2, 2, 2])
        with header_cols[0]:
            st.write("**Position**")
        with header_cols[1]:
            st.write("**S/N**")
        with header_cols[2]:
            st.write("**Type**")
        with header_cols[3]:
            st.write("**Recovered?**")

        # Display releases rows
        for i, release in enumerate(st.session_state.releases):
            cols = st.columns([1, 2, 2, 2])

            with cols[0]:
                st.write(f"**{release['position']}**")

            with cols[1]:
                serial_number = st.text_input(
                    f"{release['position']} S/N",
                    value=release.get('serial_number', ''),
                    key=f"release_sn_{i}",
                    label_visibility="collapsed"
                )

            with cols[2]:
                release_type = st.text_input(
                    f"{release['position']} Type",
                    value=release.get('type', ''),
                    key=f"release_type_{i}",
                    label_visibility="collapsed"
                )

            with cols[3]:
                recovered_status = release.get('recovered', '')
                recovered = st.selectbox(
                    f"{release['position']} Recovered",
                    options=['', 'Yes', 'No'],
                    index=['', 'Yes', 'No'].index(recovered_status) if recovered_status in ['', 'Yes', 'No'] else 0,
                    key=f"release_recovered_{i}",
                    label_visibility="collapsed"
                )

            # Update the release data in session state
            st.session_state.releases[i] = {
                'position': release['position'],
                'serial_number': serial_number,
                'type': release_type,
                'recovered': recovered
            }

        # Add Release Communication field
        st.write("**Release Comments**")
        release_communication = st.text_area(
            "Release Comments",
            value=st.session_state.get('release_communication', ''),
            key="release_communication_input",
            label_visibility="collapsed",
            height=100
        )

        st.markdown("---")

        st.subheader("Clock Errors")

        # Initialize session state for clock errors if not exists
        if 'clock_errors' not in st.session_state:
            st.session_state.clock_errors = [
                {'instrument': 'ADCP', 'serial_number': '', 'gmt_date': '', 'inst_date': '', 'date_error': '', 'gmt_time': '', 'inst_time': '', 'time_error': '', 'file_name': '', 'comments': ''},
                {'instrument': 'P1', 'serial_number': '', 'gmt_date': '', 'inst_date': '', 'date_error': '', 'gmt_time': '', 'inst_time': '', 'time_error': '', 'file_name': '', 'comments': ''},
                {'instrument': 'P2', 'serial_number': '', 'gmt_date': '', 'inst_date': '', 'date_error': '', 'gmt_time': '', 'inst_time': '', 'time_error': '', 'file_name': '', 'comments': ''}
            ]

        # Display clock errors table header
        header_cols = st.columns([1, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.8])
        with header_cols[0]:
            st.write("**Type**")
        with header_cols[1]:
            st.write("**S/N**")
        with header_cols[2]:
            st.write("**GMT Date**")
        with header_cols[3]:
            st.write("**Inst. Date**")
        with header_cols[4]:
            st.write("**Date Error**")
        with header_cols[5]:
            st.write("**GMT Time**")
        with header_cols[6]:
            st.write("**Inst. Time**")
        with header_cols[7]:
            st.write("**Time Error**")
        with header_cols[8]:
            st.write("**File Name**")
        with header_cols[9]:
            st.write("**Comments**")

        # Display clock errors rows
        for i, clock_error in enumerate(st.session_state.clock_errors):
            cols = st.columns([1, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.8])

            with cols[0]:
                st.write(f"**{clock_error['instrument']}**")

            with cols[1]:
                serial_number = st.text_input(
                    f"{clock_error['instrument']} S/N",
                    value=clock_error.get('serial_number', ''),
                    key=f"clock_error_sn_{i}",
                    label_visibility="collapsed"
                )

            with cols[2]:
                gmt_date = st.text_input(
                    f"{clock_error['instrument']} GMT Date",
                    value=clock_error.get('gmt_date', ''),
                    key=f"clock_error_gmt_date_{i}",
                    label_visibility="collapsed"
                )

            with cols[3]:
                inst_date = st.text_input(
                    f"{clock_error['instrument']} Inst. Date",
                    value=clock_error.get('inst_date', ''),
                    key=f"clock_error_inst_date_{i}",
                    label_visibility="collapsed"
                )

            with cols[4]:
                # Calculate date error from GMT and Inst dates
                calculated_date_error = calculate_date_error(gmt_date, inst_date)
                date_error = st.text_input(
                    f"{clock_error['instrument']} Date Error",
                    value=calculated_date_error,
                    key=f"clock_error_date_error_{i}",
                    label_visibility="collapsed",
                    disabled=True
                )

            with cols[5]:
                gmt_time = st.text_input(
                    f"{clock_error['instrument']} GMT Time",
                    value=clock_error.get('gmt_time', ''),
                    key=f"clock_error_gmt_time_{i}",
                    label_visibility="collapsed"
                )

            with cols[6]:
                inst_time = st.text_input(
                    f"{clock_error['instrument']} Inst. Time",
                    value=clock_error.get('inst_time', ''),
                    key=f"clock_error_inst_time_{i}",
                    label_visibility="collapsed"
                )

            with cols[7]:
                # Calculate time error from GMT and Inst times
                calculated_time_error = calculate_time_error(gmt_time, inst_time)
                time_error = st.text_input(
                    f"{clock_error['instrument']} Time Error",
                    value=calculated_time_error,
                    key=f"clock_error_time_error_{i}",
                    label_visibility="collapsed",
                    disabled=True
                )

            with cols[8]:
                file_name = st.text_input(
                    f"{clock_error['instrument']} File Name",
                    value=clock_error.get('file_name', ''),
                    key=f"clock_error_file_name_{i}",
                    label_visibility="collapsed"
                )

            with cols[9]:
                comments = st.text_input(
                    f"{clock_error['instrument']} Comments",
                    value=clock_error.get('comments', ''),
                    key=f"clock_error_comments_{i}",
                    label_visibility="collapsed"
                )

            # Update the clock error data in session state
            st.session_state.clock_errors[i] = {
                'instrument': clock_error['instrument'],
                'serial_number': serial_number,
                'gmt_date': gmt_date,
                'inst_date': inst_date,
                'date_error': date_error,
                'gmt_time': gmt_time,
                'inst_time': inst_time,
                'time_error': time_error,
                'file_name': file_name,
                'comments': comments
            }

        st.markdown("---")

        st.subheader("General Comments")

        general_comments = st.text_area(
            "General Comments",
            value=st.session_state.get('general_comments', ''),
            key="general_comments_input",
            label_visibility="collapsed",
            height=250
        )

        st.markdown("---")

        # Form submission buttons
        col_button1, col_spacer = st.columns([1, 11])
        with col_button1:
            if mode == "Search/Edit" and st.session_state.selected_recovery:
                submitted = st.form_submit_button("Update", use_container_width=True, type="primary")
            else:
                submitted = st.form_submit_button("Save", use_container_width=True, type="primary")

        if submitted:
            # Prepare form data including instrumentation and beacons
            instrumentation_data = {
                'pressure_instruments': st.session_state.get('instruments', [])
            }

            beacons_data = {
                'beacons': st.session_state.get('beacons', [])
            }

            # Prepare recovery info data
            recovery_info_data = {
                'release_enable_combined': release_enable_combined,
                'confirmed_release_combined': confirmed_release_combined,
                'depth': depth,
                'final_pre_release_slant_range': final_pre_release_slant_range,
                'time_float_sighted': time_float_sighted,
                'first_post_release_slant_range': first_post_release_slant_range,
                'time_float_on_deck': time_float_on_deck,
                'time_releases_on_deck': time_releases_on_deck
            }

            # Prepare mooring components data
            mooring_components_data = {
                'components': st.session_state.get('mooring_components', [])
            }

            # Prepare release system recovery data in the expected format
            top_release_data = {}
            bottom_release_data = {}

            for release in st.session_state.get('releases', []):
                # Convert recovered status back to lost field
                recovered_status = release.get('recovered', '')
                if recovered_status == '':
                    lost_value = None
                elif recovered_status == 'Yes':
                    lost_value = False
                elif recovered_status == 'No':
                    lost_value = True
                else:
                    lost_value = None

                release_dict = {
                    'serial_number': release.get('serial_number') or None,
                    'type': release.get('type') or None,
                    'lost': lost_value
                }

                if release['position'] == 'Top':
                    top_release_data = release_dict
                elif release['position'] == 'Bottom':
                    bottom_release_data = release_dict

            release_system_recovery_data = {
                'top_release': top_release_data,
                'bottom_release': bottom_release_data,
                'release_communication': release_communication
            }

            # Prepare clock errors data - convert back to instrument_data_collection format
            existing_instrument_data = {}
            if mode == "Search/Edit" and st.session_state.selected_recovery:
                existing_instrument_data = parse_json_field(st.session_state.selected_recovery.get('instrument_data_collection', '{}'))

            # Update existing instrument data with clock errors
            clock_errors = st.session_state.get('clock_errors', [])
            instrument_counter = 0

            for clock_error in clock_errors:
                if (clock_error.get('serial_number') or clock_error.get('gmt_date') or
                    clock_error.get('inst_date') or clock_error.get('date_error') or
                    clock_error.get('gmt_time') or clock_error.get('inst_time') or
                    clock_error.get('time_error') or clock_error.get('file_name') or
                    clock_error.get('comments')):

                    instrument_key = f"instrument_{instrument_counter}"

                    # Get existing instrument data or create new
                    if instrument_key in existing_instrument_data:
                        instrument_data = existing_instrument_data[instrument_key].copy()
                    else:
                        instrument_data = {}

                    # Update with clock error data
                    if clock_error.get('serial_number'):
                        instrument_data['serial_number'] = clock_error['serial_number']
                    if clock_error['instrument'] == 'ADCP':
                        instrument_data['type'] = 'ADCP'
                    elif clock_error['instrument'] in ['P1', 'P2']:
                        instrument_data['type'] = 'SBE39'

                    if clock_error.get('gmt_date'):
                        instrument_data['gmt_date'] = clock_error['gmt_date'] + ' 00:00:00'
                    if clock_error.get('inst_date'):
                        instrument_data['date'] = clock_error['inst_date'] + ' 00:00:00'
                    if clock_error.get('date_error'):
                        try:
                            instrument_data['date_error'] = float(clock_error['date_error'])
                        except:
                            instrument_data['date_error'] = None
                    if clock_error.get('gmt_time'):
                        instrument_data['gmt_time'] = clock_error['gmt_time']
                    if clock_error.get('inst_time'):
                        instrument_data['time'] = clock_error['inst_time']
                    # Don't save time_error to database since it's calculated
                    if clock_error.get('file_name'):
                        instrument_data['filename'] = clock_error['file_name']
                    if clock_error.get('comments'):
                        instrument_data['clock_comment'] = clock_error['comments']

                    existing_instrument_data[instrument_key] = instrument_data
                    instrument_counter += 1

            clock_errors_data = existing_instrument_data

            form_data = {
                'mooring_id': mooring_id,
                'site': site,
                'cruise': cruise,
                'personnel': personnel,
                'recovery_date': recovery_date.strftime("%Y-%m-%d %H:%M:%S") if recovery_date else "",
                'latitude': latitude,
                'longitude': longitude,
                'release_fire_time': release_fire_time,
                'time_on_deck': time_on_deck,
                'instrumentation': instrumentation_data,
                'beacons': beacons_data,
                'recovery_info': recovery_info_data,
                'mooring_components': mooring_components_data,
                'release_system_recovery': release_system_recovery_data,
                'instrument_data_collection': clock_errors_data,
                'general_comments': general_comments
            }

            # Save record
            record_id = st.session_state.selected_recovery.get('id') if mode == "Search/Edit" and st.session_state.selected_recovery else None
            success, result = save_recovery(form_data, record_id)

            if success:
                if mode == "Add New":
                    st.success(f"✅ New recovery saved successfully! Record ID: {result}")
                else:
                    st.success("✅ Recovery updated successfully!")

                # Clear search results to refresh
                st.session_state.search_results = None
                st.session_state.selected_recovery = None
            else:
                st.error(f"❌ Error saving recovery: {result}")



if __name__ == '__main__':
    main()
