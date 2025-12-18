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
                   data_quality_analysis
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
                  'data_quality_analysis']
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

        instrument_data_collection = {
            "instrument_0": {
                "serial_number": form_data.get('adcp_sn', ''),
                "status": form_data.get('adcp_status', ''),
                "battery": form_data.get('adcp_battery', ''),
                "clock_comment": form_data.get('adcp_clock_comment', ''),
                "comment": form_data.get('adcp_comment', ''),
                "date": form_data.get('adcp_date', ''),
                "date_error": form_data.get('adcp_date_error', ''),
                "error": form_data.get('adcp_error', ''),
                "filename": form_data.get('adcp_filename', ''),
                "gmt_time": form_data.get('adcp_gmt_time', ''),
                "gmt_date": form_data.get('adcp_gmt_date', ''),
                "number_records": form_data.get('adcp_number_records', ''),
                "time": form_data.get('adcp_time', '')
            }
        }

        mooring_line_recovery = {}

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

        data_quality_analysis = {}

        if record_id:
            # Update existing record
            cursor.execute("""
                UPDATE adcp_rec2 SET
                mooring_id = ?, recovery_metadata = ?, recovery_location = ?, recovery_timing = ?,
                instrument_data_collection = ?, mooring_line_recovery = ?, release_system_recovery = ?,
                beacon_recovery = ?, flasher_recovery = ?, subsurface_recovery = ?, cruise_information = ?,
                data_quality_analysis = ?
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
                record_id
            ))
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO adcp_rec2
                (mooring_id, recovery_metadata, recovery_location, recovery_timing,
                 instrument_data_collection, mooring_line_recovery, release_system_recovery,
                 beacon_recovery, flasher_recovery, subsurface_recovery, cruise_information,
                 data_quality_analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                json.dumps(data_quality_analysis)
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
    h2 {
        color: #1f77b4;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .stTextInput label {
        font-weight: 600;
        color: var(--text-color);
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

        # Form submission buttons
        col_button, col_spacer = st.columns([1, 11])
        with col_button:
            if mode == "Search/Edit" and st.session_state.selected_recovery:
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
                'recovery_date': recovery_date.strftime("%Y-%m-%d %H:%M:%S") if recovery_date else "",
                'latitude': latitude,
                'longitude': longitude,
                'release_fire_time': release_fire_time,
                'time_on_deck': time_on_deck
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
