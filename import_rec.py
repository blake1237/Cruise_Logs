#!/usr/bin/env python3
"""
Recovery Data Import Script

Imports FileMaker Pro XML export into the recoveries_normalized table.
This script follows the same pattern as import_dep.py but handles recovery-specific data.

Usage:
    python import_rec.py rec_input.xml

The script will:
1. Parse the XML export from FileMaker Pro
2. Transform the data into normalized JSON structures
3. Insert records into the recoveries_normalized table
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


def format_date(date_str):
    """Convert date string to standardized format"""
    if not date_str:
        return None
    # Add date formatting logic as needed
    return date_str


def format_time(time_str):
    """Convert time string to standardized format"""
    if not time_str:
        return None
    return time_str


def build_core_recovery_info(record):
    """
    Build core recovery information JSON object
    """
    info = {
        "mooring_lost": record.get("Mooring Lost"),
        "mooring_type": record.get("Mooring Type"),
        "fishing_or_vandalism": record.get("Fishing or Vandalism"),
        "statuspriortodeparture": record.get("StatusPriorToDeparture"),
        "relprob": record.get("RelProb"),
        "recprobcomments": record.get("RecProbComments"),
        "glassballs": record.get("GlassBalls"),
        "check_duplicates": record.get("CheckDuplicates"),
        "okdates": record.get("OkDates"),
        "rturn": record.get("RTurn"),
        "a2_rec": record.get("A2Rec"),
        "batlogic": record.get("BatLogic"),
        "battransmit": record.get("BatTransmit")
    }

    # Remove None values
    info = {k: v for k, v in info.items() if v is not None}
    return json.dumps(info)


def build_met_sensors(record):
    """
    Build meteorological sensors JSON object
    """
    met_sensors = {
        "seacat_sn": record.get("SeaCat SN"),
        "atrh_sn": record.get("ATRH SN"),
        "baro_sn": record.get("Baro SN"),
        "rain_sn": record.get("Rain SN"),
        "lwrad_sn": record.get("LwRad SN"),
        "swrad_sn": record.get("SwRad SN"),
        "wind_sn": record.get("Wind SN"),
        "tube_sn": record.get("TubeSN"),
        "ptt_id": record.get("PTT ID"),
        "buoy_sn": record.get("Buoy SN")
    }

    # Remove None values
    met_sensors = {k: v for k, v in met_sensors.items() if v is not None}
    return json.dumps(met_sensors)


def build_instrument_conditions(record):
    """
    Build instrument conditions JSON objects
    """
    conditions = {}

    # SeaCat condition
    if record.get("SeaCatCond") or record.get("SeaCatDetails") or record.get("SeaCatPic"):
        conditions["seacat_condition"] = {
            "condition": record.get("SeaCatCond"),
            "details": record.get("SeaCatDetails"),
            "pic": record.get("SeaCatPic")
        }

    # ATRH condition
    if record.get("AtRhCond") or record.get("ATRHDetails") or record.get("AtRhPic"):
        conditions["atrh_condition"] = {
            "condition": record.get("AtRhCond"),
            "details": record.get("ATRHDetails"),
            "pic": record.get("AtRhPic")
        }

    # Baro condition
    if record.get("BaroCond") or record.get("BaroDetails") or record.get("BaroPic"):
        conditions["baro_condition"] = {
            "condition": record.get("BaroCond"),
            "details": record.get("BaroDetails"),
            "pic": record.get("BaroPic")
        }

    # Rain condition
    if record.get("RainCond") or record.get("RainDetails") or record.get("RainPic"):
        conditions["rain_condition"] = {
            "condition": record.get("RainCond"),
            "details": record.get("RainDetails"),
            "pic": record.get("RainPic")
        }

    # LwRad condition
    if record.get("LwRadCond") or record.get("LwRadDetails") or record.get("LwRadPic"):
        conditions["lwrad_condition"] = {
            "condition": record.get("LwRadCond"),
            "details": record.get("LwRadDetails"),
            "pic": record.get("LwRadPic")
        }

    # SwRad condition
    if record.get("SwRadCond") or record.get("SwRadDetails") or record.get("SwRadPic"):
        conditions["swrad_condition"] = {
            "condition": record.get("SwRadCond"),
            "details": record.get("SwRadDetails"),
            "pic": record.get("SwRadPic")
        }

    # Wind condition
    if record.get("WindCond") or record.get("WindDetails") or record.get("WindPic"):
        conditions["wind_condition"] = {
            "condition": record.get("WindCond"),
            "details": record.get("WindDetails"),
            "pic": record.get("WindPic")
        }

    # Tube condition
    if record.get("TubeCond") or record.get("TubeDetails") or record.get("TubePic"):
        conditions["tube_condition"] = {
            "condition": record.get("TubeCond"),
            "details": record.get("TubeDetails"),
            "pic": record.get("TubePic")
        }

    return conditions


def build_release_systems(record):
    """
    Build release system information JSON object
    """
    release_info = {}

    # Release serial numbers and types
    if record.get("Rel SN 1"):
        release_info["rel_sn_1"] = record.get("Rel SN 1")
    if record.get("Rel SN 2"):
        release_info["rel_sn_2"] = record.get("Rel SN 2")
    if record.get("Rel Type 1"):
        release_info["rel_type_1"] = record.get("Rel Type 1")
    if record.get("Rel Type 2"):
        release_info["rel_type_2"] = record.get("Rel Type 2")
    if record.get("Rel 1 Rec"):
        release_info["rel_1_rec"] = record.get("Rel 1 Rec")
    if record.get("Rel 2 Rec"):
        release_info["rel_2_rec"] = record.get("Rel 2 Rec")

    return release_info


def build_subsurface_sensors(record):
    """
    Build subsurface sensors JSON array from numbered position fields
    """
    sensors = []

    # Look for instrument positions 0-35 (adjust range as needed)
    for i in range(36):
        position_data = {}

        # Check for various field patterns using 'Sub X FieldName' format
        sn_field = record.get(f"Sub {i} SN")
        depth_field = record.get(f"Sub {i} Depth")
        detail_field = record.get(f"Sub {i} Detail")
        timeout_field = record.get(f"Sub {i} TimeOut")
        condition_field = record.get(f"Sub {i} Condition")
        type_field = record.get(f"Sub {i} Type")

        if any([sn_field, depth_field, detail_field, timeout_field, condition_field, type_field]):
            position_data = {
                "position": i,
                "serial_number": sn_field,
                "depth": depth_field,
                "detail": detail_field,
                "timeout": timeout_field,
                "condition": condition_field,
                "instrument_type": type_field
            }
            # Remove None values
            position_data = {k: v for k, v in position_data.items() if v is not None}
            if len(position_data) > 1:  # More than just position
                sensors.append(position_data)

    return json.dumps(sensors)


def build_fname(record):
    """
    Build filename JSON array from numbered filename fields
    """
    filenames = []

    # Look for filename fields 0-35
    for i in range(36):
        filename = record.get(f"Fname {i}")
        if filename:
            filenames.append({
                "position": i,
                "value": filename
            })

    return json.dumps(filenames)


def build_numofrec(record):
    """
    Build number of records JSON array from numbered record count fields
    """
    records = []

    # Look for record count fields 0-35
    for i in range(36):
        num_records = record.get(f"NumOfRec{i}")
        if num_records:
            records.append({
                "position": i,
                "value": num_records
            })

    return json.dumps(records)


def build_battery_voltages(record):
    """
    Build battery voltages JSON array from numbered voltage fields
    """
    voltages = []

    # Look for voltage fields 0-35
    for i in range(36):
        voltage = record.get(f"Bat {i} Volt")
        if voltage:
            voltages.append({
                "position": i,
                "voltage": voltage
            })

    return json.dumps(voltages)


def build_instrument_addresses(record):
    """
    Build instrument addresses JSON array from numbered address fields
    """
    addresses = []

    # Look for address fields 0-35
    for i in range(36):
        address = record.get(f"Address{i}")
        if address:
            addresses.append({
                "position": i,
                "address": address
            })

    return json.dumps(addresses)


def build_instrument_timing(record):
    """
    Build instrument timing JSON array from GMT time, instrument time, and clock error fields
    """
    timing = []

    # Look for timing fields 0-35
    for i in range(36):
        gmt_time = record.get(f"GMT {i}")
        instr_time = record.get(f"Instr Time {i}")
        clk_err = record.get(f"Clk Err {i}")

        if any([gmt_time, instr_time, clk_err]):
            timing_data = {
                "position": i,
                "gmt_time": gmt_time,
                "instrument_time": instr_time,
                "clock_error": clk_err
            }
            # Remove None values
            timing_data = {k: v for k, v in timing_data.items() if v is not None}
            if len(timing_data) > 1:  # More than just position
                timing.append(timing_data)

    return json.dumps(timing)


def build_data_quality(record):
    """
    Build data quality JSON array from number of records, filename, and error comment fields
    """
    quality = []

    # Look for data quality fields 0-35
    for i in range(36):
        num_records = record.get(f"NumOfRec{i}")
        filename = record.get(f"Fname {i}")
        error_comment = record.get(f"ErrCom{i}")
        damaged = record.get(f"Damaged{i}")

        if any([num_records, filename, error_comment, damaged]):
            quality_data = {
                "position": i,
                "num_records": num_records,
                "filename": filename,
                "error_comment": error_comment,
                "damaged": damaged
            }
            # Remove None values
            quality_data = {k: v for k, v in quality_data.items() if v is not None}
            if len(quality_data) > 1:  # More than just position
                quality.append(quality_data)

    return json.dumps(quality)


def build_nylon_lines(record):
    """
    Build nylon lines JSON array from numbered nylon fields
    """
    nylon_lines = []

    # Look for nylon line fields (1-indexed: Nylon1sn, Nylon2sn, etc.)
    for i in range(1, 11):
        nylon_sn = record.get(f"Nylon{i}sn")
        nylon_length = record.get(f"Nylon{i}ln")
        nylon_comments = record.get(f"Nylon{i}Com")

        if any([nylon_sn, nylon_length, nylon_comments]):
            nylon_data = {
                "line_number": i,
                "serial_number": nylon_sn,
                "length": nylon_length,
                "comments": nylon_comments
            }
            # Remove None values
            nylon_data = {k: v for k, v in nylon_data.items() if v is not None}
            if len(nylon_data) > 1:  # More than just line_number
                nylon_lines.append(nylon_data)

    return json.dumps(nylon_lines)


def build_ship_met_data(record):
    """
    Build ship meteorological data JSON object
    """
    ship_met = {
        "date": record.get("Ship Met Date"),
        "time": record.get("Ship Met Time"),
        "air_temp": record.get("Ship Met Air Temp"),
        "relative_humidity": record.get("Ship Met RH"),
        "sea_surface_temp": record.get("Ship Met SST"),
        "wind_direction": record.get("Ship Met Wind Dir"),
        "wind_speed": record.get("Ship Met Wind Spd"),
        "ssc": record.get("Ship SSC"),
        "unavailable": record.get("Ship unavailable")
    }

    # Remove None values
    ship_met = {k: v for k, v in ship_met.items() if v is not None}
    return json.dumps(ship_met)


def build_buoy_met_data(record):
    """
    Build buoy meteorological data JSON object
    """
    buoy_met = {
        "date": record.get("Buoy Met Date"),
        "time": record.get("Buoy Met Time"),
        "air_temp": record.get("Buoy Met Air Temp"),
        "relative_humidity": record.get("Buoy Met RH"),
        "sea_surface_temp": record.get("Buoy Met SST"),
        "wind_direction": record.get("Buoy Met Wind Dir"),
        "wind_speed": record.get("Buoy Met Wind Spd"),
        "ssc": record.get("Buoy SSC"),
        "unavailable": record.get("Buoy unavailable")
    }

    # Remove None values
    buoy_met = {k: v for k, v in buoy_met.items() if v is not None}
    return json.dumps(buoy_met)


def build_release_commands(record):
    """
    Build release command responses JSON array from rel8 RelSN fields
    Format to match what rec_form_JSON.py expects
    """
    commands = []

    # Look for release command fields with pattern: rel8 RelSN1::CMD X/Y CODE-FUNCTION-REPLY
    # Check both RelSN1 and RelSN2 releases
    for release_num in [1, 2]:
        for cmd_num in range(1, 10):  # CMD 1 through 9
            cmd_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
            if cmd_num <= len(cmd_letters):
                cmd_letter = cmd_letters[cmd_num - 1]
                field_name = f"rel8 RelSN{release_num}::CMD {cmd_num}/{cmd_letter} CODE-FUNCTION-REPLY"
                response_code = record.get(field_name)

                if response_code:
                    # Format field name to match what rec_form_JSON.py expects
                    # Convert to lowercase and replace special characters
                    command_field = field_name.lower().replace('::', '_').replace(' ', '_').replace('/', '_').replace('-', '_')

                    commands.append({
                        "command_field": command_field,
                        "response": response_code
                    })

    return json.dumps(commands)


def insert_recovery_record(cursor, record):
    """
    Insert a single recovery record into the recoveries_normalized table
    """

    # Core identification fields
    cruise = record.get("Cruise")
    site = record.get("Site")
    mooring_id = record.get("Mooring ID")
    cruisesite = f"{cruise}_{site}" if cruise and site else None
    counter = record.get("Counter")

    print(f"Processing recovery record: {mooring_id} - {cruise}")

    # Recovery event details
    dateondeck = format_date(record.get("DateOnDeck"))
    relfiredate = format_date(record.get("RelFireDate"))
    relfiretime = format_time(record.get("RelFireTime"))
    relfirelat = record.get("RelFireLat")
    relfirelong = record.get("RelFireLong")
    touch_time = record.get("Touch Time")
    relon_decktime = record.get("RelOnDeckTime")
    julian_date = record.get("JulianDate")

    # Get release system info
    release_info = build_release_systems(record)

    # Primary surface instruments
    buoy_sn = record.get("Buoy SN")
    ptt_id = record.get("PTT Id")
    seacat_sn = record.get("SeaCat SN")
    atrh_sn = record.get("ATRH SN")
    baro_sn = record.get("Baro SN")
    rain_sn = record.get("Rain SN")
    lwrad_sn = record.get("LwRad SN")
    swrad_sn = record.get("SwRad SN")
    windsn = record.get("Wind SN")
    tubesn = record.get("TubeSN")

    # Build instrument conditions
    conditions = build_instrument_conditions(record)

    # Environmental/physical data
    glassballs = record.get("GlassBalls")
    argoslat = record.get("ArgosLat")
    argoslong = record.get("ArgosLong")

    # Wire and mechanical components
    wiresn = record.get("WireSN")
    wirecond = record.get("WireCond")
    top_section_sn = record.get("TopSectionSN")

    # OTN data
    otn_sn = record.get("OTN SN")
    otn_depth = record.get("OTN Depth")
    otn_time_out = record.get("OTN Time Out")

    # Quality control and metadata
    check_duplicates = record.get("CheckDuplicates")
    okdates = record.get("OkDates")
    rturn = record.get("RTurn")
    a2_rec = record.get("A2Rec")
    batdate = record.get("BatDate")
    batlogic = record.get("BatLogic")
    battransmit = record.get("BatTransmit")

    # Personnel information
    personnel = record.get("CruiseInfo8::Personnel")

    # Build JSON arrays for repeating data
    subsurface_instruments = build_subsurface_sensors(record)
    battery_voltages = build_battery_voltages(record)
    instrument_addresses = build_instrument_addresses(record)
    instrument_timing = build_instrument_timing(record)
    data_quality = build_data_quality(record)
    nylon_lines = build_nylon_lines(record)
    fname = build_fname(record)
    numofrec = build_numofrec(record)
    ship_met_data = build_ship_met_data(record)
    buoy_met_data = build_buoy_met_data(record)
    release_commands = build_release_commands(record)

    # Additional fields that might exist in the table
    mooring_lost = record.get("Mooring Lost")
    mooring_type = record.get("Mooring Type")
    fishing_or_vandalism = record.get("Fishing or Vandalism")
    statuspriortodeparture = record.get("StatusPriorToDeparture")
    relprob = record.get("RelProb")
    recprobcomments = record.get("RecProbComments")

    # Additional fields found in schema
    buoy_condition = record.get("BuoyCond")
    clk_err_tube = record.get("Clk Err Tube")
    gmt_tube = record.get("GMT Tube")
    instr_time_tube = record.get("Instr Time Tube")
    # NOTE: fname and numofrec are already built as JSON from build_fname() and build_numofrec()
    # Do NOT overwrite them with single field lookups
    # numofrec = record.get("NumOfRec")  # REMOVED - was overwriting the JSON
    # fname = record.get("FName")  # REMOVED - was overwriting the JSON
    errcom = record.get("ErrCom")

    # Insert the record (excluding id and migrated_at which have defaults)
    insert_sql = """
        INSERT INTO recoveries_normalized (
            cruise, site, mooring_id, cruisesite, counter,
            dateondeck, relfiredate, relfiretime, relfirelat, relfirelong,
            touch_time, relon_decktime, julian_date,
            mooring_lost, mooring_type, fishing_or_vandalism, statuspriortodeparture,
            relprob, recprobcomments,
            rel_sn_1, rel_sn_2, rel_type_1, rel_type_2, rel_1_rec, rel_2_rec,
            buoy_sn, ptt_id, seacat_sn, atrh_sn, baro_sn, rain_sn, lwrad_sn, swrad_sn,
            windsn, tubesn,
            seacat_condition, atrh_condition, baro_condition, rain_condition,
            lwrad_condition, swrad_condition, wind_condition, tube_condition,
            glassballs, argoslat, argoslong,
            ship_met_data, buoy_met_data,
            wiresn, wirecond, top_section_sn,
            otn_sn, otn_depth, otn_time_out,
            check_duplicates, okdates, rturn, a2_rec, batdate, batlogic, battransmit,
            personnel,
            subsurface_instruments, battery_voltages, instrument_addresses,
            instrument_timing, data_quality, nylon_lines, fname, numofrec, release_commands,
            original_column_count,
            buoy_condition, clk_err_tube, gmt_tube, instr_time_tube, errcom
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    cursor.execute(insert_sql, (
        # 1-5: cruise, site, mooring_id, cruisesite, counter
        cruise, site, mooring_id, cruisesite, counter,
        # 6-13: dateondeck through julian_date
        dateondeck, relfiredate, relfiretime, relfirelat, relfirelong,
        touch_time, relon_decktime, julian_date,
        # 14-19: mooring status fields
        mooring_lost, mooring_type, fishing_or_vandalism, statuspriortodeparture,
        relprob, recprobcomments,
        # 20-25: release system fields
        release_info.get("rel_sn_1"), release_info.get("rel_sn_2"),
        release_info.get("rel_type_1"), release_info.get("rel_type_2"),
        release_info.get("rel_1_rec"), release_info.get("rel_2_rec"),
        # 26-35: primary surface instruments
        buoy_sn, ptt_id, seacat_sn, atrh_sn, baro_sn, rain_sn, lwrad_sn, swrad_sn,
        windsn, tubesn,
        # 36-43: instrument conditions (JSON)
        json.dumps(conditions.get("seacat_condition")) if conditions.get("seacat_condition") else None,
        json.dumps(conditions.get("atrh_condition")) if conditions.get("atrh_condition") else None,
        json.dumps(conditions.get("baro_condition")) if conditions.get("baro_condition") else None,
        json.dumps(conditions.get("rain_condition")) if conditions.get("rain_condition") else None,
        json.dumps(conditions.get("lwrad_condition")) if conditions.get("lwrad_condition") else None,
        json.dumps(conditions.get("swrad_condition")) if conditions.get("swrad_condition") else None,
        json.dumps(conditions.get("wind_condition")) if conditions.get("wind_condition") else None,
        json.dumps(conditions.get("tube_condition")) if conditions.get("tube_condition") else None,
        # 44-46: environmental data
        glassballs, argoslat, argoslong,
        # 47-48: meteorological data (JSON)
        ship_met_data, buoy_met_data,
        # 49-51: wire and mechanical components
        wiresn, wirecond, top_section_sn,
        # 52-54: OTN data
        otn_sn, otn_depth, otn_time_out,
        # 55-61: quality control and metadata
        check_duplicates, okdates, rturn, a2_rec, batdate, batlogic, battransmit,
        # 62: personnel
        personnel,
        # 63-70: JSON arrays for repeating data
        subsurface_instruments, battery_voltages, instrument_addresses,
        instrument_timing, data_quality, nylon_lines, fname, numofrec, release_commands,
        # 71: original column count
        635,
        # 72-76: additional fields
        buoy_condition, clk_err_tube, gmt_tube, instr_time_tube, errcom
    ))


def main():
    """
    Main function to import recovery XML data into SQLite database

    Process:
    1. Parse command line arguments for XML filename
    2. Check for required files (XML and Cruise_Logs.db)
    3. Parse XML data using ElementTree
    4. Transform data into normalized JSON structures
    5. Insert into recoveries_normalized table
    6. Provide import summary and verification
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Import FileMaker Pro XML export into recoveries_normalized table'
    )
    parser.add_argument(
        'xml_file',
        help='XML file to import (e.g., rec_input.xml)'
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
    print(f"Parsing recovery XML data from '{xml_file}'...")
    records = parse_xml_to_dict(xml_file)

    if not records:
        print("No records found in XML file!")
        sys.exit(1)

    print(f"Found {len(records)} recovery record(s) to import")

    # Connect to database
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Import each record
        imported_count = 0
        for i, record in enumerate(records):
            try:
                insert_recovery_record(cursor, record)
                imported_count += 1
                site = record.get('Site', 'Unknown')
                mooring_id = record.get('Mooring ID', 'Unknown')
                cruise = record.get('Cruise', 'Unknown')
                print(f"Imported recovery record {i+1}: {site} - {mooring_id} - {cruise}")

            except Exception as e:
                print(f"Error importing recovery record {i+1}: {e}")
                print(f"Record data: Site={record.get('Site')}, MooringID={record.get('MooringID')}")
                continue

        # Commit changes
        conn.commit()
        print(f"\nSuccessfully imported {imported_count} recovery record(s) into recoveries_normalized table")

        # Show summary
        cursor.execute("SELECT COUNT(*) FROM recoveries_normalized")
        total_records = cursor.fetchone()[0]
        print(f"Total records in recoveries_normalized table: {total_records}")

        # Show sample of imported data
        cursor.execute("""
            SELECT cruise, site, mooring_id, relfiredate, buoy_sn
            FROM recoveries_normalized
            ORDER BY id DESC
            LIMIT 5
        """)
        recent_records = cursor.fetchall()

        if recent_records:
            print("\nRecent imports:")
            for record in recent_records:
                print(f"  {record[0]} | {record[1]} | {record[2]} | {record[3]} | Buoy: {record[4]}")

    except Exception as e:
        print(f"Database error: {e}")
        sys.exit(1)

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
