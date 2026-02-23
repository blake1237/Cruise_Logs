#!/usr/bin/env python3
"""
ADCP Deployment Data Import Script

Imports FileMaker Pro XML export into the adcp_dep table.
This script follows the same pattern as import_repair.py but handles ADCP deployment-specific data.

Usage:
    python import_adcp_dep.py dep_adcp_IO038.xml

The script will:
1. Parse the XML export from FileMaker Pro
2. Transform the data into normalized JSON structures
3. Insert records into the adcp_dep table
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


def build_anchor_drop(record):
    """Build anchor drop JSON"""
    anchor_drop = {
        "anchor_drop_date": format_date(record.get('Anchor Drop Date')),
        "anchor_drop_time": format_time(record.get('Anchor Drop Time')),
        "anchor_drop_lat": clean_value(record.get('Anchor Drop Lat')),
        "anchor_drop_long": clean_value(record.get('Anchor Drop Long')),
        "anchor_drop_depth": clean_value(record.get('Anchor Drop Depth')),
        "anchor_weight": clean_value(record.get('AnchorWeight'))
    }
    return json.dumps(anchor_drop)


def build_deployment_details(record):
    """Build deployment details JSON"""
    deployment_details = {
        "deployment_date": format_date(record.get('Start Date')),
        "deployment_time": format_time(record.get('Start Time')),
        "site_name": clean_value(record.get('Site')),
        "cruise": clean_value(record.get('Cruise')),
        "personnel": clean_value(record.get('CruiseInfo8::Personnel')),
        "deployment_problems": clean_value(record.get('Notes')),
        "latitude": clean_value(record.get('Location_lat')),
        "longitude": clean_value(record.get('Location_lon')),
        "location_source": clean_value(record.get('Location_source')),
        "workboat_lat": clean_value(record.get('workboat_lat')),
        "workboat_lon": clean_value(record.get('workboat_lon')),
        "bottom_depth": clean_value(record.get('Depth')),
        "target_bottom_depth": clean_value(record.get('TargetBottomDepth')),
        "intended_xducer_depth": clean_value(record.get('TargetTransducerDepth')),
        "actual_xducer_depth_calculated": clean_value(record.get('ActualXducerDepth_calculated')),
        "nylon_below_releases": clean_value(record.get('NylonBelowReleases')),
        "nylon_below_float_ball": clean_value(record.get('NylonBelowBall')),
        "intended_nylon_cut_length": clean_value(record.get('CutNylonLength_calc')),
        "actual_nylon_cut_length": clean_value(record.get('ActualNylonCutLength')),
        "instrument_hardware_length": clean_value(record.get('Instrument n Hardware Length')),
        "hardware_length": clean_value(record.get('HardwareLength')),
        "additional_kevlar_length": clean_value(record.get('Additional Kevlar Length')),
        "kevlar_main_spool_length": clean_value(record.get('Kevlar Main Spool Length')),
        "total_kevlar_length": clean_value(record.get('Total Kevlar Length')),
        "total_line_length": clean_value(record.get('total line length')),
        "total_len_by_spool": clean_value(record.get('total_len_by_spool')),
        "mtpr_turn_on": format_time(record.get('MTPR TurnOn')),
        "mtpr_on_ball_set_to_adcp_heads": clean_value(record.get('MTPR On Ball SetTo ADCP Heads')),
        "seacat_on": format_time(record.get('SEACAT_on')),
        "obsolete_argos_dep": clean_value(record.get('obsoleteARGOSDep'))
    }
    return json.dumps(deployment_details)


def build_depth_info(record):
    """Build depth information JSON"""
    depth_info = {
        "depth": clean_value(record.get('Depth')),
        "depth_source": clean_value(record.get('Depth_source')),
        "depth_correction": clean_value(record.get('DepthCorrection')),
        "corrected_depth": clean_value(record.get('CorrectedDepth')),
        "flyby_method": clean_value(record.get('flyby_method')),
        "flyby_corrected_depth": clean_value(record.get('FlyByCorrectedDepth')),
        "target_bottom_depth": clean_value(record.get('TargetBottomDepth')),
        "target_transducer_depth": clean_value(record.get('TargetTransducerDepth')),
        "actual_xducer_depth_calculated": clean_value(record.get('ActualXducerDepth_calculated'))
    }
    return json.dumps(depth_info)


def build_sensor_details(record):
    """Build sensor details JSON"""
    sensor_details = {
        "adcp_sn": clean_value(record.get('ADCP_SN')),
        "flasher_sn": clean_value(record.get('flasher_sn')),
        "instr1_type": clean_value(record.get('Instr1_type')),
        "instr1_sn": clean_value(record.get('Instr1_SN')),
        "instr1_distance_from_adcp": clean_value(record.get('Instr1_distance_fromADCP')),
        "instr2_type": clean_value(record.get('Instr2_type')),
        "instr2_sn": clean_value(record.get('Instr2_SN')),
        "instr2_distance_from_adcp": clean_value(record.get('Instr2_distance_fromADCP')),
        "instr3_type": clean_value(record.get('Instr3_type')),
        "instr3_sn": clean_value(record.get('Instr3_SN')),
        "instr3_distance_from_adcp": clean_value(record.get('Instr3_distance_fromADCP')),
        "instr4_type": clean_value(record.get('Instr4_type')),
        "instr4_sn": clean_value(record.get('Instr4_SN')),
        "instr4_distance_from_adcp": clean_value(record.get('Instr4_distance_fromADCP'))
    }
    return json.dumps(sensor_details)


def build_beacon_details(record):
    """Build beacon details JSON"""
    beacon_details = {
        "rf_beacon_sn": clean_value(record.get('rf_beacon_sn')),
        "sat_beacon_id": clean_value(record.get('sat_beacon_id')),
        "sat_beacon_sn": clean_value(record.get('sat_beacon_sn')),
        "sat_beacon_type": clean_value(record.get('sat_beacon_type'))
    }
    return json.dumps(beacon_details)


def build_release_details(record):
    """Build release details JSON"""
    release_details = {
        "top_sn": clean_value(record.get('TopSN')),
        "top_type": clean_value(record.get('TopType')),
        "rel1_sn": clean_value(record.get('TopSN')),  # Form expects rel1_sn for top release S/N
        "top_rel_new": clean_value(record.get('Top_rel_new')),
        "top_rel_2nd": clean_value(record.get('Top_rel_2nd')),
        "top_rel_rebatt": clean_value(record.get('Top_rel_rebatt')),
        "btm_sn": clean_value(record.get('BtmSN')),
        "btm_type": clean_value(record.get('BtmType')),
        "rel2_sn": clean_value(record.get('BtmSN')),  # Form expects rel2_sn for bottom release S/N
        "btm_rel_new": clean_value(record.get('Btm_rel_new')),
        "btm_rel_2nd": clean_value(record.get('Btm_rel_2nd')),
        "btm_rel_rebatt": clean_value(record.get('Btm_rel_rebatt')),
        "ballset_rel_sn": clean_value(record.get('BallSet Rel SN')),
        "ballset_type": clean_value(record.get('BallSet Type')),
        "ballset_rel_lat": clean_value(record.get('BallSet Rel Lat')),
        "ballset_rel_long": clean_value(record.get('BallSet Rel Long')),
        # Top Release Commands - using full key names to match form expectations
        "rel8_toprelsn_cmd_1a_code_function_reply": clean_value(record.get('rel8 TopRelSN::CMD 1/A CODE-FUNCTION-REPLY')),
        "rel8_toprelsn_cmd_2b_code_function_reply": clean_value(record.get('rel8 TopRelSN::CMD 2/B CODE-FUNCTION-REPLY')),
        "rel8_toprelsn_cmd_3c_code_function_reply": clean_value(record.get('rel8 TopRelSN::CMD 3/C CODE-FUNCTION-REPLY')),
        "rel8_toprelsn_interrogate_freq": clean_value(record.get('rel8 TopRelSN::INTERROGATE FREQ')),
        "rel8_toprelsn_reply_freq": clean_value(record.get('rel8 TopRelSN::REPLY FREQ')),
        # Bottom Release Commands - using full key names to match form expectations
        "rel8_btmrelsn_cmd_1a_code_function_reply": clean_value(record.get('rel8 BtmRelSN::CMD 1/A CODE-FUNCTION-REPLY')),
        "rel8_btmrelsn_cmd_2b_code_function_reply": clean_value(record.get('rel8 BtmRelSN::CMD 2/B CODE-FUNCTION-REPLY')),
        "rel8_btmrelsn_cmd_3c_code_function_reply": clean_value(record.get('rel8 BtmRelSN::CMD 3/C CODE-FUNCTION-REPLY')),
        "rel8_btmrelsn_interrogate_freq": clean_value(record.get('rel8 BtmRelSN::INTERROGATE FREQ')),
        "rel8_btmrelsn_reply_freq": clean_value(record.get('rel8 BtmRelSN::REPLY FREQ')),
        # Ball Set Release Commands - using full key names to match form expectations
        "rel8_ballrelsn_cmd_1a_code_function_reply": clean_value(record.get('rel8 BallRelSN::CMD 1/A CODE-FUNCTION-REPLY')),
        "rel8_ballrelsn_cmd_2b_code_function_reply": clean_value(record.get('rel8 BallRelSN::CMD 2/B CODE-FUNCTION-REPLY')),
        "rel8_ballrelsn_cmd_3c_code_function_reply": clean_value(record.get('rel8 BallRelSN::CMD 3/C CODE-FUNCTION-REPLY')),
        "rel8_ballrelsn_interrogate_freq": clean_value(record.get('rel8 BallRelSN::INTERROGATE FREQ')),
        "rel8_ballrelsn_reply_freq": clean_value(record.get('rel8 BallRelSN::REPLY FREQ'))
    }
    return json.dumps(release_details)


def build_mooring_line_details(record):
    """Build mooring line details JSON"""
    mooring_line_details = {
        "line1_sn": clean_value(record.get('line1_sn')),
        "line1_len": clean_value(record.get('line1_len')),
        "line1_type": clean_value(record.get('line1_type')),
        "line2_sn": clean_value(record.get('line2_sn')),
        "line2_len": clean_value(record.get('line2_len')),
        "line2_type": clean_value(record.get('line2_type')),
        "line3_sn": clean_value(record.get('line3_sn')),
        "line3_len": clean_value(record.get('line3_len')),
        "line3_type": clean_value(record.get('line3_type')),
        "line4_sn": clean_value(record.get('line4_sn')),
        "line4_len": clean_value(record.get('line4_len')),
        "line4_type": clean_value(record.get('line4_type')),
        "line5_sn": clean_value(record.get('line5_sn')),
        "line5_len": clean_value(record.get('line5_len')),
        "line5_type": clean_value(record.get('line5_type')),
        "line6_sn": clean_value(record.get('line6_sn')),
        "line6_len": clean_value(record.get('line6_len')),
        "line6_type": clean_value(record.get('line6_type'))
    }
    return json.dumps(mooring_line_details)


def build_cruise_info(record):
    """Build cruise info JSON"""
    cruise_info = {
        "cruise": clean_value(record.get('Cruise')),
        "site": clean_value(record.get('Site'))
    }
    return json.dumps(cruise_info)


def insert_adcp_deployment_record(cursor, record):
    """
    Insert a single ADCP deployment record into the adcp_dep table
    """

    # Core identification
    mooring_id = clean_value(record.get("MooringID"))

    print(f"Processing ADCP deployment record: {mooring_id}")

    # Build JSON structures
    anchor_drop = build_anchor_drop(record)
    deployment_details = build_deployment_details(record)
    sensor_details = build_sensor_details(record)
    beacon_details = build_beacon_details(record)
    release_details = build_release_details(record)
    mooring_line_details = build_mooring_line_details(record)
    depth_info = build_depth_info(record)
    cruise_info = build_cruise_info(record)

    # Insert the record
    insert_sql = """
        INSERT INTO adcp_dep (
            mooring_id,
            anchor_drop,
            deployment_details,
            sensor_details,
            beacon_details,
            release_details,
            mooring_line_details,
            depth_info,
            cruise_info
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    cursor.execute(insert_sql, (
        mooring_id,
        anchor_drop,
        deployment_details,
        sensor_details,
        beacon_details,
        release_details,
        mooring_line_details,
        depth_info,
        cruise_info
    ))


def main():
    """
    Main function to import XML data into SQLite database

    Process:
    1. Parse command line arguments for XML filename
    2. Check for required files (XML and Cruise_Logs.db)
    3. Parse XML data using ElementTree
    4. Transform data into normalized JSON structures
    5. Insert into adcp_dep table
    6. Provide import summary and verification
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Import FileMaker Pro XML export into adcp_dep table'
    )
    parser.add_argument(
        'xml_file',
        help='XML file to import'
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
                insert_adcp_deployment_record(cursor, record)
                imported_count += 1
                mooring_id = record.get('MooringID', 'Unknown')
                cruise = record.get('Cruise', 'Unknown')
                print(f"✓ Imported record {i+1}: {mooring_id} - {cruise}")

            except Exception as e:
                print(f"✗ Error importing record {i+1}: {e}")
                continue

        # Commit changes
        conn.commit()
        print(f"\n{'='*60}")
        print(f"Successfully imported {imported_count} record(s) into adcp_dep table")
        print(f"{'='*60}")

        # Show summary
        cursor.execute("SELECT COUNT(*) FROM adcp_dep")
        total_records = cursor.fetchone()[0]
        print(f"Total records in adcp_dep table: {total_records}")

    except Exception as e:
        print(f"Database error: {e}")
        sys.exit(1)

    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    main()
