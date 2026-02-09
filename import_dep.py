#!/usr/bin/env python3
"""
XML Import Script for Deployment Data
Imports FileMaker Pro XML export into the deployments_normalized table

USAGE:
    python import_dep.py xml_filename

    Examples:
        python import_dep.py test.xml
        python import_dep.py deployment_data.xml
        python import_dep.py exports/cruise_data.xml

REQUIREMENTS:
    - XML file (FileMaker Pro XML export)
    - Cruise_Logs.db SQLite database file in the same directory
    - Python 3.x with standard libraries

DESCRIPTION:
    This script parses a FileMaker Pro XML export file containing
    deployment data and imports it into the deployments_normalized table of
    the Cruise_Logs.db SQLite database.

    The script handles:
    - Complex XML parsing with namespace support
    - JSON structure creation for normalized data storage
    - Meteorological sensor data organization
    - Subsurface instrument arrays
    - Nylon spool configurations
    - Acoustic release parameters
    - Anchor drop information
    - Flyby measurements

    All data is properly formatted and stored as JSON in the appropriate
    columns of the deployments_normalized table for efficient querying
    and data integrity.

AUTHOR: Generated for Cruise Logs Database Management
"""

import sqlite3
import xml.etree.ElementTree as ET
import json
from datetime import datetime
import sys
import os
import argparse

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

def format_date(date_str):
    """Keep date in MM/dd/yyyy format for consistency with form"""
    if not date_str:
        return None
    try:
        # Parse the date and return in MM/dd/yyyy format
        dt = datetime.strptime(date_str, '%m/%d/%Y')
        return dt.strftime('%m/%d/%Y')
    except:
        return date_str

def format_time(time_str):
    """Convert time format if needed"""
    if not time_str:
        return None
    return time_str

def build_deployment_info(record):
    """Build deployment_info JSON structure"""
    return json.dumps({
        "dep_date": format_date(record.get("Dep Date")),
        "deployment_start_time": format_time(record.get("DepStartTime")),
        "personnel": record.get("CruiseInfo8::Personnel"),
        "mooring_type": record.get("Mooring Type"),
        "comments": record.get("Dep Com"),
        "mooring_length": record.get("Mooring length"),
        "projected_scope": record.get("Projected Scope"),
        "final_scope": record.get("Final Scope")
    })

def build_met_sensors(record):
    """Build met_sensors JSON structure"""
    return json.dumps({
        "atrh": {
            "type": record.get("ATRH Type"),
            "serial": record.get("ATRH SN")
        },
        "barometer": {
            "type": record.get("Baro Type"),
            "serial": record.get("Baro SN")
        },
        "rain": {
            "type": record.get("Rain Gauge Type"),
            "serial": record.get("Rain Gauge SN")
        },
        "sw_radiation": {
            "type": record.get("SW Rad Type"),
            "serial": record.get("SWRad SN")
        },
        "lw_radiation": {
            "type": record.get("LWRad Type"),
            "serial": record.get("LWRad SN")
        },
        "wind": {
            "type": record.get("Wind Type"),
            "serial": record.get("Wind SN")
        },
        "seacat": {
            "type": record.get("SeaCat Type"),
            "serial": record.get("SeaCat SN")
        }
    })

def build_hardware(record):
    """Build hardware JSON structure"""
    hardware_data = {
        "buoy_sn": record.get("Buoy S/N"),
        "insert": record.get("Insert"),
        "anti_theft_cage": record.get("Anti-theft Cage"),
        "tube_sn": record.get("Tube SN"),
        "ptt_hexid": record.get("PTT Id"),
        "time_zone": record.get("Time Zone"),
        "fairing": record.get("Fairing"),
        "teacup_handle": record.get("Teacup Handle"),
        "software_ver": record.get("Software Version")
    }

    # VALIDATION: Ensure no wire-related fields are included in hardware
    # These fields should ONLY be in nylon_config
    wire_fields_not_allowed = ['wire_length', 'wire_ln', 'wire_sn', 'wire_age', 'wiresn']
    for field in wire_fields_not_allowed:
        if field in hardware_data:
            print(f"WARNING: Removing {field} from hardware - should be in nylon_config only")
            del hardware_data[field]

    return json.dumps(hardware_data)

def build_nylon_spools(record):
    """Build nylon_spools JSON structure"""
    spools = {}
    for i in range(1, 11):  # Nylon1 through Nylon10
        sn_key = f"Nylon{i}sn"
        ln_key = f"Nylon{i}ln"

        sn = record.get(sn_key)
        ln = record.get(ln_key)

        if sn or ln:
            spools[f"spool_{i}"] = {
                "sn": sn,
                "length": ln
            }

    return json.dumps(spools)

def build_nylon_config(record):
    """Build nylon_config JSON structure"""
    nylon_data = {
        "nylon_below_release": record.get("Below release"),
        "nylon_cut_length": record.get("NylonCutLn"),
        "total_nylon": record.get("Total nylon"),
        "wiresn": record.get("WireSN"),
        "wire_ln": record.get("Wire Ln"),
        "projected_scope": record.get("Projected Scope"),
        "wire_age": record.get("Wire Age"),
        "topsecsn": record.get("TopSecSN"),
        "top_sec_usage": record.get("Top Sec Usage")
    }

    # VALIDATION: Hardware length should NOT be in nylon_config
    # It belongs in the hardware section only
    if record.get("Hardware Ln"):
        print(f"INFO: Hardware Ln ({record.get('Hardware Ln')}) belongs in hardware section, not nylon_config")

    # VALIDATION: Ensure wire_ln is the correct field name (not wire_length)
    if 'wire_length' in nylon_data:
        print("WARNING: Found wire_length in nylon_config - converting to wire_ln")
        nylon_data['wire_ln'] = nylon_data['wire_length']
        del nylon_data['wire_length']

    return json.dumps(nylon_data)

def build_subsurface_sensors(record):
    """Build subsurface_sensors JSON array"""
    sensors = []

    # Process Sub 0 through Sub 35
    for i in range(36):
        depth = record.get(f"Sub {i} Depth")
        sn = record.get(f"Sub {i} SN")
        sensor_type = record.get(f"Sub {i} Type")
        time_in = record.get(f"Sub {i} Time In")
        comments = record.get(f"Sub {i} Com")
        address = record.get(f"Sub Addr {i}")

        if any([depth, sn, sensor_type, time_in, comments, address]):
            sensor = {
                "position": i,
                "depth": depth,
                "sn": sn,
                "type": sensor_type,
                "time_in": time_in,
                "comments": comments,
                "address": address
            }
            sensors.append(sensor)

    # Add OTN sensor if present
    otn_sn = record.get("OTN SN")
    otn_depth = record.get("OTN depth")
    otn_time_in = record.get("OTN time in")

    if any([otn_sn, otn_depth, otn_time_in]):
        sensors.append({
            "position": "OTN",
            "depth": otn_depth,
            "sn": otn_sn,
            "type": "OTN",
            "time_in": otn_time_in,
            "comments": None,
            "address": None
        })

    return json.dumps(sensors)

def build_acoustic_releases(record):
    """Build acoustic_releases JSON structure"""
    releases = {}

    # Release 1
    egg_sn_1 = record.get("EGGSN1")
    egg_type_1 = record.get("EGG Type 1")
    if egg_sn_1 or egg_type_1:
        releases["release_1"] = {
            "type": egg_type_1,
            "sn": egg_sn_1,
            "int_freq": record.get("rel8 EGGSN1::INTERROGATE FREQ"),
            "reply_freq": record.get("rel8 EGGSN1::REPLY FREQ"),
            "release": record.get("rel8 EGGSN1::CMD 1/A CODE-FUNCTION-REPLY"),
            "enable": record.get("rel8 EGGSN1::CMD 2/B CODE-FUNCTION-REPLY"),
            "disable": record.get("rel8 EGGSN1::CMD 3/C CODE-FUNCTION-REPLY")
        }

    # Release 2
    egg_sn_2 = record.get("EGGSN2")
    egg_type_2 = record.get("EGG Type 2")
    if egg_sn_2 or egg_type_2:
        releases["release_2"] = {
            "type": egg_type_2,
            "sn": egg_sn_2,
            "int_freq": record.get("rel8 EGGSN2::INTERROGATE FREQ"),
            "reply_freq": record.get("rel8 EGGSN2::REPLY FREQ"),
            "release": record.get("rel8 EGGSN2::CMD 1/A CODE-FUNCTION-REPLY"),
            "enable": record.get("rel8 EGGSN2::CMD 2/B CODE-FUNCTION-REPLY"),
            "disable": record.get("rel8 EGGSN2::CMD 3/C CODE-FUNCTION-REPLY")
        }

    return json.dumps(releases)

def build_anchor_drop(record):
    """Build anchor_drop JSON structure"""
    return json.dumps({
        "date": format_date(record.get("AnchorDrpDate")),
        "time": format_time(record.get("Anchor drop time")),
        "latitude": record.get("Anchor Drp Lat"),
        "longitude": record.get("Anchor Drp Long"),
        "anchor_weight": record.get("Anchor weight"),
        "julian_date": record.get("Jul Anch Date"),
        "tow_time": record.get("Tow Time"),
        "tow_distance": record.get("Tow Distance"),
        "total_time": record.get("DepTotalTime"),
        "dturn": record.get("Dturn")
    })

def build_met_obs(record):
    """Build met_obs JSON structure"""
    ship_met = {}
    buoy_met = {}

    # Ship meteorological data
    if any([record.get("Ship Met Date"), record.get("Ship Met Time"),
            record.get("Ship Met Air Temp"), record.get("Ship Met RH"),
            record.get("Ship Met SST"), record.get("Ship Met Wind Dir"),
            record.get("Ship Met Wind Speed")]):
        ship_met = {
            "date": format_date(record.get("Ship Met Date")),
            "time": format_time(record.get("Ship Met Time")),
            "air_temp": record.get("Ship Met Air Temp"),
            "rh": record.get("Ship Met RH"),
            "sst": record.get("Ship Met SST"),
            "wind_dir": record.get("Ship Met Wind Dir"),
            "wind_spd": record.get("Ship Met Wind Speed"),
            "ssc": record.get("Ship SSC"),
            "unavailable": record.get("Ship unavailable")
        }

    # Buoy meteorological data
    if any([record.get("Buoy Met Date"), record.get("Buoy Met Time"),
            record.get("Buoy Met Air Temp"), record.get("Buoy Met RH"),
            record.get("Buoy Met SST"), record.get("Buoy Met Wind Dir"),
            record.get("Buoy Met Wind Speed")]):
        buoy_met = {
            "date": format_date(record.get("Buoy Met Date")),
            "time": format_time(record.get("Buoy Met Time")),
            "air_temp": record.get("Buoy Met Air Temp"),
            "rh": record.get("Buoy Met RH"),
            "sst": record.get("Buoy Met SST"),
            "wind_dir": record.get("Buoy Met Wind Dir"),
            "wind_spd": record.get("Buoy Met Wind Speed"),
            "ssc": record.get("Buoy SSC"),
            "unavailable": record.get("Buoy unavailable")
        }

    return json.dumps({
        "ship": ship_met,
        "buoy": buoy_met
    })

def build_flyby(record):
    """Build flyby JSON structure"""
    return json.dumps({
        "buoy_latitude": record.get("Flyby Buoy Lat"),
        "buoy_longitude": record.get("Flyby Buoy Long"),
        "anchor_latitude": record.get("Flyby Anch Lat"),
        "anchor_longitude": record.get("Flyby Anch Long"),
        "uncorrected_depth": record.get("UncorrDepth"),
        "corrected_depth": record.get("Corr Depth"),
        "target_depth": record.get("TargetDepth"),
        "depth_correction": record.get("DepthCorrection"),
        "transducer_depth": record.get("TransducerDepth"),
        "range_to_buoy": record.get("Range To Buoy"),
        "bearing_to_buoy": record.get("Bearing To Buoy"),
        "sub_inst_depths": record.get("SubInstDepths")
    })

def insert_deployment_record(cursor, record):
    """
    Insert a single deployment record into the deployments_normalized table
    """

    # Core fields
    site = record.get("Site")
    mooringid = record.get("MooringID")
    cruise = record.get("Cruise")
    latitude = record.get("Anchor Drp Lat")  # Using anchor drop coordinates
    longitude = record.get("Anchor Drp Long")
    depth = record.get("Corr Depth") or record.get("UncorrDepth") or record.get("TargetDepth")

    print(f"Processing record: {mooringid} - {cruise}")

    # JSON fields
    deployment_info = build_deployment_info(record)
    met_sensors = build_met_sensors(record)
    hardware = build_hardware(record)
    nylon_spools = build_nylon_spools(record)
    nylon_config = build_nylon_config(record)
    subsurface_sensors = build_subsurface_sensors(record)
    acoustic_releases = build_acoustic_releases(record)
    anchor_drop = build_anchor_drop(record)
    met_obs = build_met_obs(record)
    flyby = build_flyby(record)

    # VALIDATION: Cross-check for wire field conflicts
    import json
    hardware_dict = json.loads(hardware)
    nylon_config_dict = json.loads(nylon_config)

    wire_conflicts = []
    if 'wire_length' in hardware_dict:
        wire_conflicts.append(f"wire_length in hardware: {hardware_dict['wire_length']}")
    if 'wire_ln' in nylon_config_dict:
        wire_conflicts.append(f"wire_ln in nylon_config: {nylon_config_dict['wire_ln']}")

    if len(wire_conflicts) > 1:
        print(f"⚠️ WIRE FIELD VALIDATION: Multiple wire length fields detected:")
        for conflict in wire_conflicts:
            print(f"   - {conflict}")
        print(f"   Wire length should ONLY be in nylon_config as wire_ln")

    # Insert the record
    insert_sql = """
        INSERT INTO deployments_normalized (
            site, mooringid, cruise, latitude, longitude, depth,
            deployment_info, met_sensors, hardware, nylon_spools, nylon_config,
            subsurface_sensors, acoustic_releases, anchor_drop, met_obs, flyby
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    cursor.execute(insert_sql, (
        site, mooringid, cruise, latitude, longitude, depth,
        deployment_info, met_sensors, hardware, nylon_spools, nylon_config,
        subsurface_sensors, acoustic_releases, anchor_drop, met_obs, flyby
    ))

def main():
    """
    Main function to import XML data into SQLite database

    Process:
    1. Parse command line arguments for XML filename
    2. Check for required files (XML and Cruise_Logs.db)
    3. Parse XML data using ElementTree
    4. Transform data into normalized JSON structures
    5. Insert into deployments_normalized table
    6. Provide import summary and verification
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Import FileMaker Pro XML export into deployments_normalized table'
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
                insert_deployment_record(cursor, record)
                imported_count += 1
                print(f"Imported record {i+1}: {record.get('Site', 'Unknown')} - {record.get('MooringID', 'Unknown')}")

            except Exception as e:
                print(f"Error importing record {i+1}: {e}")
                continue

        # Commit changes
        conn.commit()
        print(f"\nSuccessfully imported {imported_count} record(s) into deployments_normalized table")

        # Show summary
        cursor.execute("SELECT COUNT(*) FROM deployments_normalized")
        total_records = cursor.fetchone()[0]
        print(f"Total records in deployments_normalized table: {total_records}")

    except Exception as e:
        print(f"Database error: {e}")
        sys.exit(1)

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
