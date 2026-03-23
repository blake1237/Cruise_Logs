#!/usr/bin/env python3
"""
Repair Data Import Script

Imports FileMaker Pro XML export into the repair_normalized table.
This script follows the same pattern as import_dep.py and import_rec.py but handles repair-specific data.

Usage:
    python import_repair.py import_repair_pm989.xml

The script will:
1. Parse the XML export from FileMaker Pro
2. Transform the data into normalized structures
3. Insert records into the repair_normalized table
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


def build_met_buoy(record):
    """Build meteorological buoy data JSON"""
    met_buoy = {
        'Air Temp': record.get('Met Buoy Air Temp'),
        'Date': format_date(record.get('Met Buoy Date')),  # YYYY-MM-DD format
        'RH': record.get('Met Buoy RH'),
        'SST': record.get('Met Buoy SST'),
        'Time': format_time(record.get('Met Buoy Time')),
        'Wind Dir': record.get('Met Buoy Wind Dir'),
        'Wind Spd': record.get('Met Buoy Wind Spd'),
        'SSC': clean_value(record.get('Buoy SSC'))  # Sea Surface Conductivity/Salinity
    }
    return json.dumps(met_buoy)


def build_met_ship(record):
    """Build meteorological ship data JSON"""
    met_ship = {
        'Air Temp': record.get('Met Ship Air Temp'),
        'Date': format_date(record.get('Met Ship Date')),  # YYYY-MM-DD format
        'RH': record.get('Met Ship RH'),
        'SST': record.get('Met Ship SST'),
        'Time': format_time(record.get('Met Ship Time')),
        'Wind Dir': record.get('Met Ship Wind Dir'),
        'Wind Spd': record.get('Met Ship Wind Spd'),
        'SSC': clean_value(record.get('Ship SSC'))  # Sea Surface Conductivity/Salinity
    }
    return json.dumps(met_ship)


def insert_repair_record(cursor, record):
    """
    Insert a single repair record into the repair_normalized table
    """

    # Core identification fields
    site = record.get("Site")
    mooring_id = record.get("MooringID")
    cruise = record.get("Cruise")
    cruise_site = f"{cruise}_{site}" if cruise and site else None
    counter = record.get("FileCounter")
    repair_date = format_date(record.get("Date"))

    print(f"Processing repair record: {mooring_id} - {cruise} - {site}")

    # Location data
    argos_latitude = clean_value(record.get("ARGOS Lat"))
    argos_longitude = clean_value(record.get("ARGOS Long"))
    actual_latitude = clean_value(record.get("Actual Lat"))
    actual_longitude = clean_value(record.get("Actual Long"))

    # CTD and Depth information
    ctd_number = clean_value(record.get("CTD#"))
    depth = clean_value(record.get("Depth"))

    # Buoy and repair details
    buoy_details = clean_value(record.get("Buoy Details"))
    repair_fishing_vandalism = clean_value(record.get("Repair Fishing or Vandalism"))

    # Repair timing information - combine with date to create timestamps
    start_repair_time = combine_datetime(repair_date, record.get("StartRepairTime"))
    end_repair_time = combine_datetime(repair_date, record.get("EndRepairTime"))
    swap_time = combine_datetime(repair_date, record.get("Touch Time"))

    # Personnel information
    personnel = clean_value(record.get("CruiseInfo8::Personnel"))

    # Comments
    rep_comments = clean_value(record.get("Rep Comments"))

    # Equipment tracking - Old equipment (lost/replaced)
    tube_old_sn = clean_value(record.get("Tube SN"))
    tube_new_sn = clean_value(record.get("NewTubeSN"))
    tube_condition = clean_value(record.get("TubeLost"))

    ptt_old_sn = clean_value(record.get("PTT ID"))
    ptt_new_sn = clean_value(record.get("New PTT Id"))
    ptt_condition = clean_value(record.get("Buoy unavailable"))

    atrh_old_sn = clean_value(record.get("ATRH SN"))
    atrh_new_sn = clean_value(record.get("New ATRH SN"))
    atrh_condition = clean_value(record.get("ATRHlost"))

    sst_old_sn = clean_value(record.get("SST SN"))
    sst_new_sn = clean_value(record.get("New SST SN"))
    sst_condition = clean_value(record.get("SSTlost"))

    wind_old_sn = clean_value(record.get("Wind SN"))
    wind_new_sn = clean_value(record.get("New WindSN"))
    wind_condition = clean_value(record.get("WindLost"))

    rain_old_sn = clean_value(record.get("Rain SN"))
    rain_new_sn = clean_value(record.get("New Rain SN"))
    rain_condition = clean_value(record.get("RainLost"))

    swrad_old_sn = clean_value(record.get("SW Rad SN"))
    swrad_new_sn = clean_value(record.get("New SW Rad SN"))
    swrad_condition = clean_value(record.get("SWRadLost"))

    baro_old_sn = clean_value(record.get("Baro"))
    baro_new_sn = clean_value(record.get("New Baro"))
    baro_condition = clean_value(record.get("BaroLost"))

    seacat_old_sn = clean_value(record.get("SeaCat"))
    seacat_new_sn = clean_value(record.get("New SeaCat"))
    seacat_condition = clean_value(record.get("SeaCatLost"))

    lwrad_old_sn = clean_value(record.get("LW Rad"))
    lwrad_new_sn = clean_value(record.get("New LW Rad"))
    lwrad_condition = clean_value(record.get("LWRadLost"))

    # Equipment detail fields
    ptt_details = None  # No PTT details field in XML - Buoy SSC is a measurement, not equipment details
    sst_details = clean_value(record.get("SST Details"))
    tube_details = clean_value(record.get("Tube Details"))
    atrh_details = clean_value(record.get("ATRH Details"))
    rain_details = clean_value(record.get("Rain Details"))
    baro_details = clean_value(record.get("Baro Details"))
    seacat_details = clean_value(record.get("SeaCat Details"))
    wind_details = clean_value(record.get("Wind Details"))
    swrad_details = clean_value(record.get("SW Rad Details"))
    lwrad_details = clean_value(record.get("LW Rad Details"))

    # Additional fields
    tube_time = format_time(record.get("TubeTime"))
    gmt = format_time(record.get("GMT"))
    drift = format_time(record.get("Drift"))
    bat_logic = clean_value(record.get("BatLogic"))
    bat_transmit = clean_value(record.get("Bat Transmit"))
    file_name = clean_value(record.get("File Name"))

    # Status field
    status_of_mooring = record.get("Status of Mooring")

    # Meteorological data
    met_buoy = build_met_buoy(record)
    met_ship = build_met_ship(record)

    # Migration metadata
    migrated_from = os.path.basename(sys.argv[1]) if len(sys.argv) > 1 else None
    migration_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Insert the record (skipping id, created_at, updated_at as they're auto-generated)
    insert_sql = """
        INSERT INTO repair_normalized (
            site, mooring_id, cruise, cruise_site, counter, repair_date,
            argos_latitude, argos_longitude, actual_latitude, actual_longitude,
            ctd_number, depth,
            buoy_details, repair_fishing_vandalism,
            start_repair_time, end_repair_time, swap_time,
            a2_rep_dep, a2_rep_rec, check_duplicates,
            personnel, rep_comments,
            lost_equipment, replacement_equipment, equipment_status,
            ptt_details, sst_details, tube_details, atrh_details,
            rain_details, baro_details, seacat_details, wind_details,
            swrad_details,
            met_buoy, met_ship,
            tube_time, gmt, drift, bat_logic, bat_transmit, file_name,
            migrated_from, migration_date,
            tube_old_sn, tube_new_sn, tube_condition,
            ptt_old_sn, ptt_new_sn, ptt_condition,
            atrh_old_sn, atrh_new_sn, atrh_condition,
            sst_old_sn, sst_new_sn, sst_condition,
            wind_old_sn, wind_new_sn, wind_condition,
            rain_old_sn, rain_new_sn, rain_condition,
            swrad_old_sn, swrad_new_sn, swrad_condition,
            baro_old_sn, baro_new_sn, baro_condition,
            seacat_old_sn, seacat_new_sn, seacat_condition,
            lwrad_old_sn, lwrad_new_sn, lwrad_condition,
            lwrad_details
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    cursor.execute(insert_sql, (
        site, mooring_id, cruise, cruise_site, counter, repair_date,
        argos_latitude, argos_longitude, actual_latitude, actual_longitude,
        ctd_number, depth,
        buoy_details, repair_fishing_vandalism,
        start_repair_time, end_repair_time, swap_time,
        None, None, None,  # a2_rep_dep, a2_rep_rec, check_duplicates
        personnel, rep_comments,
        None, None, None,  # lost_equipment, replacement_equipment, equipment_status (JSON fields)
        ptt_details, sst_details, tube_details, atrh_details,
        rain_details, baro_details, seacat_details, wind_details,
        swrad_details,
        met_buoy, met_ship,
        tube_time, gmt, drift, bat_logic, bat_transmit, file_name,
        migrated_from, migration_date,
        tube_old_sn, tube_new_sn, tube_condition,
        ptt_old_sn, ptt_new_sn, ptt_condition,
        atrh_old_sn, atrh_new_sn, atrh_condition,
        sst_old_sn, sst_new_sn, sst_condition,
        wind_old_sn, wind_new_sn, wind_condition,
        rain_old_sn, rain_new_sn, rain_condition,
        swrad_old_sn, swrad_new_sn, swrad_condition,
        baro_old_sn, baro_new_sn, baro_condition,
        seacat_old_sn, seacat_new_sn, seacat_condition,
        lwrad_old_sn, lwrad_new_sn, lwrad_condition,
        lwrad_details
    ))


def main():
    """
    Main function to import XML data into SQLite database

    Process:
    1. Parse command line arguments for XML filename
    2. Check for required files (XML and Cruise_Logs.db)
    3. Parse XML data using ElementTree
    4. Transform data into normalized structures
    5. Insert into repair_normalized table
    6. Provide import summary and verification
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Import FileMaker Pro XML export into repair_normalized table'
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
                insert_repair_record(cursor, record)
                imported_count += 1
                print(f"✓ Imported record {i+1}: {record.get('Site', 'Unknown')} - {record.get('MooringID', 'Unknown')} - {record.get('Cruise', 'Unknown')}")

            except Exception as e:
                print(f"✗ Error importing record {i+1}: {e}")
                continue

        # Commit changes
        conn.commit()
        print(f"\n{'='*60}")
        print(f"Successfully imported {imported_count} record(s) into repair_normalized table")
        print(f"{'='*60}")

        # Show summary
        cursor.execute("SELECT COUNT(*) FROM repair_normalized")
        total_records = cursor.fetchone()[0]
        print(f"Total records in repair_normalized table: {total_records}")

    except Exception as e:
        print(f"Database error: {e}")
        sys.exit(1)

    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    main()
