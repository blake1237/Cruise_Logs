#!/usr/bin/env python
"""
Import NYLON LENGTHS_MostRecent.xls into the Cruise_Logs.db database as nylon_inventory table
"""

import pandas as pd
import sqlite3
import sys

def import_nylon_inventory():
    """Import the nylon lengths Excel file into the database"""

    # Read the Excel file
    print("Reading NYLON LENGTHS_MostRecent.xls...")
    try:
        # Read without header and assign column names
        df = pd.read_excel('NYLON LENGTHS_MostRecent.xls', header=None)

        # Assign meaningful column names based on the data structure
        df.columns = ['Spool_ID', 'Month', 'Year', 'Length_m', 'Flag', 'Lot_Number']

        print(f"Successfully read {len(df)} rows and {len(df.columns)} columns")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        sys.exit(1)

    # Show sample of data
    print("\nSample of data:")
    print(df.head(10))

    # Connect to the database
    print("\nConnecting to Cruise_Logs.db...")
    try:
        conn = sqlite3.connect('Cruise_Logs.db')
        print("Connected successfully")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

    # Import the data (replace if table exists)
    print("\nImporting data into nylon_inventory table...")
    try:
        df.to_sql('nylon_inventory', conn, if_exists='replace', index=False)
        print(f"Successfully imported {len(df)} rows into nylon_inventory table")
    except Exception as e:
        print(f"Error importing data: {e}")
        conn.close()
        sys.exit(1)

    # Verify the import
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM nylon_inventory")
    count = cursor.fetchone()[0]
    print(f"\nVerification: nylon_inventory table now contains {count} rows")

    # Show a sample
    print("\nSample of imported data:")
    cursor.execute("SELECT * FROM nylon_inventory LIMIT 5")
    rows = cursor.fetchall()
    cols = [description[0] for description in cursor.description]
    print(f"Columns: {cols}")
    for row in rows:
        print(f"  {row}")

    # Show some statistics
    print("\nInventory Statistics:")
    cursor.execute("SELECT COUNT(DISTINCT Spool_ID) FROM nylon_inventory")
    unique_spools = cursor.fetchone()[0]
    print(f"  Unique spool IDs: {unique_spools}")

    cursor.execute("SELECT MIN(Length_m), MAX(Length_m), AVG(Length_m) FROM nylon_inventory")
    min_len, max_len, avg_len = cursor.fetchone()
    print(f"  Length range: {min_len}m - {max_len}m (avg: {avg_len:.1f}m)")

    conn.close()
    print("\nImport completed successfully!")

if __name__ == "__main__":
    import_nylon_inventory()
