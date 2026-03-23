#!/usr/bin/env python
"""
Import Equipment.xls into the Cruise_Logs.db database as release_inventory table
"""

import pandas as pd
import sqlite3
import sys

def import_release_inventory():
    """Import the equipment Excel file into the database"""

    # Read the Excel file
    print("Reading Equipment.xls...")
    try:
        df = pd.read_excel('Equipment.xls')
        print(f"Successfully read {len(df)} rows and {len(df.columns)} columns")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        sys.exit(1)

    # Clean up column names for SQLite (replace spaces and special characters)
    df.columns = df.columns.str.replace(' ', '_')
    df.columns = df.columns.str.replace('/', '_')
    df.columns = df.columns.str.replace('#', 'Num')
    df.columns = df.columns.str.replace('(', '')
    df.columns = df.columns.str.replace(')', '')
    df.columns = df.columns.str.replace('-', '_')
    df.columns = df.columns.str.replace('+', 'plus')
    df.columns = df.columns.str.replace(':', '')

    print("\nColumn names after cleaning:")
    for col in df.columns:
        print(f"  - {col}")

    # Connect to the database
    print("\nConnecting to Cruise_Logs.db...")
    try:
        conn = sqlite3.connect('Cruise_Logs.db')
        print("Connected successfully")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

    # Import the data (replace if table exists)
    print("\nImporting data into release_inventory table...")
    try:
        df.to_sql('release_inventory', conn, if_exists='replace', index=False)
        print(f"Successfully imported {len(df)} rows into release_inventory table")
    except Exception as e:
        print(f"Error importing data: {e}")
        conn.close()
        sys.exit(1)

    # Verify the import
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM release_inventory")
    count = cursor.fetchone()[0]
    print(f"\nVerification: release_inventory table now contains {count} rows")

    # Show a sample
    print("\nSample of imported data:")
    cursor.execute("SELECT * FROM release_inventory LIMIT 3")
    rows = cursor.fetchall()
    cols = [description[0] for description in cursor.description]
    print(f"Columns: {cols[:5]}...")  # Show first 5 columns
    for row in rows:
        print(f"  {row[:5]}...")  # Show first 5 values

    conn.close()
    print("\nImport completed successfully!")

if __name__ == "__main__":
    import_release_inventory()
