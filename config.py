"""
Cruise_Logs Configuration Module
Cross-platform configuration for database paths and system settings
"""

import os
import platform
from pathlib import Path

# Detect operating system
SYSTEM = platform.system()  # 'Windows', 'Darwin' (macOS), 'Linux'

# Determine base directory
def get_base_directory():
    """
    Get the base directory for the Cruise_Logs installation.
    Returns the directory containing this config.py file.
    """
    return Path(__file__).parent.resolve()

# Base directory (where the repository is located)
BASE_DIR = get_base_directory()

# Database path configuration
def get_database_path():
    """
    Get the database path based on the operating system.
    Returns a string path to Cruise_Logs.db
    """
    if SYSTEM == 'Windows':
        # Windows: C:\Cruise_Logs\Cruise_Logs.db
        db_path = r'C:\Cruise_Logs\Cruise_Logs.db'
    else:
        # Mac/Linux: Use expanduser for home directory
        # Assumes ~/Github/Cruise_Logs/Cruise_Logs.db
        db_path = os.path.expanduser('~/Github/Cruise_Logs/Cruise_Logs.db')

    # Check if database exists, if not try relative path
    if not os.path.exists(db_path):
        # Fall back to database in same directory as this script
        db_path = str(BASE_DIR / 'Cruise_Logs.db')

    return db_path

# Database path
DB_PATH = get_database_path()

# Excel file paths (relative to base directory)
EQUIPMENT_FILE = str(BASE_DIR / 'Equipment.xls')
NYLON_FILE = str(BASE_DIR / 'NYLON LENGTHS_MostRecent.xls')

# Streamlit configuration
STREAMLIT_CONFIG = {
    'server.port': 8501,
    'server.address': 'localhost',
    'server.enableCORS': False,
    'server.enableXsrfProtection': True,
}

# Network configuration (for multi-user access)
NETWORK_CONFIG = {
    'enable_network_access': False,  # Set to True to allow network access
    'network_address': '0.0.0.0',
    'network_port': 8501,
}

# Database sync configuration
SYNC_CONFIG = {
    'remote_host': 'spectrum.pmel.noaa.gov',
    'remote_user': 'lake',
    'remote_path': '/home/lake/database/',
    'local_backup_dir': str(BASE_DIR / 'backups'),
}

# Application settings
APP_SETTINGS = {
    'app_title': 'Cruise Logs Management System',
    'page_icon': '🚢',
    'layout': 'wide',
    'debug_mode': False,
}

# File system helpers
def ensure_directory_exists(path):
    """Ensure a directory exists, create if it doesn't."""
    Path(path).mkdir(parents=True, exist_ok=True)
    return path

def get_backup_directory():
    """Get or create the backup directory."""
    backup_dir = BASE_DIR / 'backups'
    ensure_directory_exists(backup_dir)
    return str(backup_dir)

# Logging configuration
LOG_CONFIG = {
    'log_file': str(BASE_DIR / 'cruise_logs.log'),
    'log_level': 'INFO',
    'max_log_size': 10 * 1024 * 1024,  # 10 MB
}

# Print configuration info (for debugging)
def print_config():
    """Print current configuration for debugging."""
    print("=" * 60)
    print("Cruise_Logs Configuration")
    print("=" * 60)
    print(f"Operating System: {SYSTEM}")
    print(f"Base Directory: {BASE_DIR}")
    print(f"Database Path: {DB_PATH}")
    print(f"Database Exists: {os.path.exists(DB_PATH)}")
    print(f"Equipment File: {EQUIPMENT_FILE}")
    print(f"Equipment File Exists: {os.path.exists(EQUIPMENT_FILE)}")
    print(f"Nylon File: {NYLON_FILE}")
    print(f"Nylon File Exists: {os.path.exists(NYLON_FILE)}")
    print(f"Backup Directory: {get_backup_directory()}")
    print("=" * 60)

# Export main configuration items
__all__ = [
    'DB_PATH',
    'BASE_DIR',
    'SYSTEM',
    'EQUIPMENT_FILE',
    'NYLON_FILE',
    'STREAMLIT_CONFIG',
    'NETWORK_CONFIG',
    'SYNC_CONFIG',
    'APP_SETTINGS',
    'LOG_CONFIG',
    'get_database_path',
    'get_backup_directory',
    'ensure_directory_exists',
    'print_config',
]

# Run configuration check if executed directly
if __name__ == '__main__':
    print_config()
