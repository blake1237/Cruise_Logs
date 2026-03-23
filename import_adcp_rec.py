#!/usr/bin/env python3
"""
ADCP Recovery Data Import Script

Imports FileMaker Pro XML export into the adcp_rec2 table.
This script follows the same pattern as import_adcp_dep.py but handles ADCP recovery-specific data.

Usage:
    python import_adcp_rec.py rec_adcp_zm030.xml

The script will:
1. Parse the XML export from FileMaker Pro
2. Transform the data into normalized JSON structures
3. Insert records into the adcp_rec2 table
4. Provide import summary and verification

Author: Generated for Cruise_Logs database
"""

import xml.etree.ElementTree as ET
import sqlite3
import json
import sys
import os
import argparse
from datetime import datetime


def parse_xml_to_dict(xml_file):
    """
    Parse FileMaker Pro XML export and extract field data
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Define namespace
        ns = {'fmp': 'http://www.filemaker.com/fmpxmlresult'}

        # Get field names from metadata
        metadata = root.find('fmp:METADATA', ns)
        field_names = []
        for field in metadata.findall('fmp:FIELD', ns):
            field_names.append(field.get('NAME'))

        # Get data from resultset
        resultset = root.find('fmp:RESULTSET', ns)
        records = []

        for row in resultset.findall('fmp:ROW', ns):
            record = {}
            cols = row.findall('fmp:COL', ns)

            for i, col in enumerate(cols):
                if i < len(field_names):
                    data_elem = col.find('fmp:DATA', ns)
                    value = data_elem.text if data_elem is not None else None
                    record[field_names[i]] = value

            records.append(record)

        return records

    except Exception as e:
        print(f"Error parsing XML: {e}")
        return []


def clean_value(value):
    """Clean up values from XML - convert 'None' strings and empty strings to None"""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == '' or value.lower() == 'none':
            return None
    return value


def format_date(date_str):
    """Convert date from MM/dd/yyyy to YYYY-MM-DD format for database consistency"""
    if not date_str:
        return None
    try:
        # Parse the date from FileMaker format (MM/dd/yyyy) and return in YYYY-MM-DD format
        dt = datetime.strptime(date_str, '%m/%d/%Y')
        return dt.strftime('%Y-%m-%d')
    except:
        return date_str


def format_time(time_str):
    """Convert time string to standardized format"""
    time_str = clean_value(time_str)
    if not time_str:
        return None
    return time_str


def combine_datetime(date_str, time_str):
    """Combine date and time into timestamp format (YYYY-MM-DD HH:mm:ss)"""
    if not date_str:
        return None

    if not time_str or not time_str.strip():
        return None

    formatted_date = format_date(date_str)
    if not formatted_date:
        return None

    # Clean up time string - handle formats like "00:15", "00:15:00", etc.
    time_clean = time_str.strip()
    # If time is already HH:mm:ss, use it; if HH:mm, add :00
    if len(time_clean) == 5:  # HH:mm
        time_clean = f"{time_clean}:00"
    return f"{formatted_date} {time_clean}"


def build_recovery_metadata(record):
    """Build recovery metadata JSON"""
    recovery_metadata = {
        "mooring_id": clean_value(record.get('MooringID')),
        "site": clean_value(record.get('Site')),
        "cruise": clean_value(record.get('Cruise')),
        "recovery_date": format_date(record.get('Date')),
        "julian_date": clean_value(record.get('Julian Date'))
    }
    return json.dumps(recovery_metadata)


def build_recovery_location(record):
    """Build recovery location JSON"""
    recovery_location = {
        "buoy_latitude": clean_value(record.get('Buoy Latitude')),
        "buoy_longitude": clean_value(record.get('Buoy Longitude')),
        "depth": clean_value(record.get('Depth'))
    }
    return json.dumps(recovery_location)


def build_recovery_timing(record):
    """Build recovery timing JSON"""
    recovery_timing = {
        "release_enable_date": format_date(record.get('RelEnableDate')),
        "release_enable_time": format_time(record.get('Release Enable Time')),
        "confirmed_release_time": format_time(record.get('Confirmed Release Time')),
        "float_ball_sighted_on_surface": format_time(record.get('Float Ball Sighted On Surface')),
        "float_ball_on_deck": format_time(record.get('Float Ball On Deck')),
        "last_release_on_deck": format_time(record.get('Last Release On Deck'))
    }
    return json.dumps(recovery_timing)


def build_instrument_data_collection(record):
    """Build instrument data collection JSON with instruments 0-4"""
    instrument_data = {}

    for i in range(5):  # 0 through 4
        sn = clean_value(record.get(f'Instr{i}_SN'))
        # Only add instrument if it has a serial number
        if sn:
            instr = {
                "serial_number": sn,
                "type": clean_value(record.get(f'Instr{i}_type')) if i > 0 else "ADCP",
                "battery": clean_value(record.get(f'Instr{i}_batt')),
                "status": clean_value(record.get(f'Instr{i}_status')),
                "comment": clean_value(record.get(f'Instr{i}_com')),
                "clock_comment": clean_value(record.get(f'Instr{i}_clk_com')),
                "filename": clean_value(record.get(f'Instr{i}_fname')),
                "number_records": clean_value(record.get(f'Instr{i}_numrec')),
                "date": combine_datetime(record.get(f'Instr{i}_date'), record.get(f'Instr{i}_Time')) if record.get(f'Instr{i}_date') and record.get(f'Instr{i}_Time') else format_date(record.get(f'Instr{i}_date')),
                "time": format_time(record.get(f'Instr{i}_Time')),
                "gmt_date": format_date(record.get(f'Instr{i}_GMTdate')),
                "gmt_time": format_time(record.get(f'Instr{i}_GMT')),
                "date_error": clean_value(record.get(f'Instr{i}_dateerr')),
                "error": clean_value(record.get(f'Instr{i}_err'))
            }
            instrument_data[f'instrument_{i}'] = instr

    return json.dumps(instrument_data)


def build_mooring_line_recovery(record):
    """Build mooring line recovery JSON"""
    mooring_line_recovery = {}

    for i in range(1, 7):  # lines 1-6
        sn = clean_value(record.get(f'line{i}_sn'))
        length = clean_value(record.get(f'line{i}_len'))
        line_type = clean_value(record.get(f'line{i}_type'))
        status = clean_value(record.get(f'line{i}_status'))
        comment = clean_value(record.get(f'line{i}_com'))

        # Only add line if it has some data
        if sn or length or line_type or status or comment:
            mooring_line_recovery[f'line_{i}'] = {
                "serial_number": sn,
                "length": length,
                "type": line_type,
                "status": status,
                "comment": comment
            }

    # Add actual nylon cut length if present
    actual_nylon = clean_value(record.get('ActualNylonCutLength'))
    if actual_nylon:
        mooring_line_recovery['actual_nylon_cut_length'] = actual_nylon

    return json.dumps(mooring_line_recovery)


def build_release_system_recovery(record):
    """Build release system recovery JSON"""
    release_system = {
        "top_release": {
            "serial_number": clean_value(record.get('RelTopSN')),
            "type": clean_value(record.get('RelTopType')),
            "lost": clean_value(record.get('RelTopLost'))
        },
        "bottom_release": {
            "serial_number": clean_value(record.get('RelBtmSN')),
            "type": clean_value(record.get('RelBtmType')),
            "lost": clean_value(record.get('RelBtmLost'))
        },
        "release_comment": clean_value(record.get('ReleaseComm')),
        "release_communication": clean_value(record.get('ReleaseComm')),
        "slant_ranges": clean_value(record.get('Slant Ranges')),
        "post_release_slant_ranges": clean_value(record.get('Post Release Slant Ranges'))
    }
    return json.dumps(release_system)


def build_beacon_recovery(record):
    """Build beacon recovery JSON"""
    beacon_recovery = {
        "argos_beacon": {
            "ptt": clean_value(record.get('ARGOS Beacon PTT')),
            "serial_number": clean_value(record.get('ARGOS Beacon SN')),
            "status": clean_value(record.get('ARGOS_Bea_status')),
            "comment": clean_value(record.get('ARGOS_Bea_com'))
        },
        "rf_beacon": {
            "serial_number": clean_value(record.get('RF Beacon SN')),
            "status": clean_value(record.get('RF Beacon_status')),
            "channel_freq": clean_value(record.get('RF Xmit CHFreq')),
            "comment": clean_value(record.get('RF_Beacon_comment'))
        }
    }
    return json.dumps(beacon_recovery)


def build_flasher_recovery(record):
    """Build flasher recovery JSON"""
    flasher_recovery = {
        "serial_number": clean_value(record.get('Flasher SN')),
        "status": clean_value(record.get('Flasher_status')),
        "comment": clean_value(record.get('Flasher_comment'))
    }
    return json.dumps(flasher_recovery)


def build_subsurface_recovery(record):
    """Build subsurface recovery JSON"""
    subsurface_recovery = {
        "notes": clean_value(record.get('Subsurface Recovery Notes'))
    }
    return json.dumps(subsurface_recovery)


def build_cruise_information(record):
    """Build cruise information JSON"""
    cruise_information = {
        "cruise": clean_value(record.get('Cruise')),
        "beginning_date": format_date(record.get('CruiseInfo8::Beginning Date')),
        "ending_date": format_date(record.get('CruiseInfo8::Ending Date')),
        "personnel": clean_value(record.get('CruiseInfo8::Personnel'))
    }
    return json.dumps(cruise_information)


def build_instrumentation(record):
    """Build instrumentation JSON - legacy format for compatibility"""
    instrumentation = {
        "instr0_sn": clean_value(record.get('Instr0_SN')),
        "instr1_sn": clean_value(record.get('Instr1_SN')),
        "instr1_type": clean_value(record.get('Instr1_type')),
        "instr2_sn": clean_value(record.get('Instr2_SN')),
        "instr2_type": clean_value(record.get('Instr2_type')),
        "instr3_sn": clean_value(record.get('Instr3_SN')),
        "instr3_type": clean_value(record.get('Instr3_type')),
        "instr4_sn": clean_value(record.get('Instr4_SN')),
        "instr4_type": clean_value(record.get('Instr4_type'))
    }
    return json.dumps(instrumentation)


def build_beacons(record):
    """Build beacons JSON - legacy format for compatibility"""
    beacons = {
        "argos_beacon_ptt": clean_value(record.get('ARGOS Beacon PTT')),
        "argos_beacon_sn": clean_value(record.get('ARGOS Beacon SN')),
        "rf_beacon_sn": clean_value(record.get('RF Beacon SN'))
    }
    return json.dumps(beacons)


def build_data_quality_analysis(record):
    """Build data quality analysis JSON - placeholder for future use"""
    data_quality = {
        "analysis_notes": None,
        "data_quality_flag": None
    }
    return json.dumps(data_quality)


def insert_adcp_recovery_record(cursor, record):
    """
    Insert a single ADCP recovery record into the adcp_rec2 table
    """

    # Core identification
    mooring_id = clean_value(record.get("MooringID"))

    print(f"Processing ADCP recovery record: {mooring_id}")

    # Build JSON structures
    recovery_metadata = build_recovery_metadata(record)
    recovery_location = build_recovery_location(record)
    recovery_timing = build_recovery_timing(record)
    instrument_data_collection = build_instrument_data_collection(record)
    mooring_line_recovery = build_mooring_line_recovery(record)
    release_system_recovery = build_release_system_recovery(record)
    beacon_recovery = build_beacon_recovery(record)
    flasher_recovery = build_flasher_recovery(record)
    subsurface_recovery = build_subsurface_recovery(record)
    cruise_information = build_cruise_information(record)
    data_quality_analysis = build_data_quality_analysis(record)
    instrumentation = build_instrumentation(record)
    beacons = build_beacons(record)

    # General comments - use subsurface recovery notes
    general_comments = clean_value(record.get('Subsurface Recovery Notes'))

    # Insert the record
    insert_sql = """
        INSERT INTO adcp_rec2 (
            mooring_id,
            recovery_metadata,
            recovery_location,
            recovery_timing,
            instrument_data_collection,
            mooring_line_recovery,
            release_system_recovery,
            beacon_recovery,
            flasher_recovery,
            subsurface_recovery,
            cruise_information,
            data_quality_analysis,
            instrumentation,
            beacons,
            general_comments
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    cursor.execute(insert_sql, (
        mooring_id,
        recovery_metadata,
        recovery_location,
        recovery_timing,
        instrument_data_collection,
        mooring_line_recovery,
        release_system_recovery,
        beacon_recovery,
        flasher_recovery,
        subsurface_recovery,
        cruise_information,
        data_quality_analysis,
        instrumentation,
        beacons,
        general_comments
    ))


def main():
    """
    Main function to import XML data into SQLite database

    Process:
    1. Parse command line arguments for XML filename
    2. Check for required files (XML and Cruise_Logs.db)
    3. Parse XML data using ElementTree
    4. Transform data into normalized JSON structures
    5. Insert into adcp_rec2 table
    6. Provide import summary and verification
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Import FileMaker Pro XML export into adcp_rec2 table'
    )
    parser.add_argument(
        'xml_file',
        help='XML file to import (e.g., rec_adcp_zm030.xml)'
    )

    args = parser.parse_args()
    xml_file = args.xml_file
    db_file = 'Cruise_Logs.db'

    # Check if files exist
    if not os.path.exists(xml_file):
        print(f"Error: XML file '{xml_file}' not found!")
        print(f"Usage: python {sys.argv[0]} xml_filename")
        sys.exit(1)

    if not os.path.exists(db_file):
        print(f"Error: Database file '{db_file}' not found!")
        sys.exit(1)

    # Parse XML data
    print(f"Parsing XML data from '{xml_file}'...")
    records = parse_xml_to_dict(xml_file)

    if not records:
        print("No records found in XML file!")
        sys.exit(1)

    print(f"Found {len(records)} record(s) to import")

    # Connect to database
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Import each record
        imported_count = 0
        for i, record in enumerate(records):
            try:
                insert_adcp_recovery_record(cursor, record)
                imported_count += 1
                mooring_id = record.get('MooringID', 'Unknown')
                cruise = record.get('Cruise', 'Unknown')
                recovery_date = record.get('Date', 'Unknown')
                print(f"✓ Imported record {i+1}: {mooring_id} - {cruise} - {recovery_date}")

            except Exception as e:
                print(f"✗ Error importing record {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue

        # Commit changes
        conn.commit()
        print(f"\n{'='*60}")
        print(f"Successfully imported {imported_count} record(s) into adcp_rec2 table")
        print(f"{'='*60}")

        # Show summary
        cursor.execute("SELECT COUNT(*) FROM adcp_rec2")
        total_records = cursor.fetchone()[0]
        print(f"Total records in adcp_rec2 table: {total_records}")

    except Exception as e:
        print(f"Database error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    main()
