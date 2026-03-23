#!/usr/bin/env python
"""
Cruise_Logs Setup Verification Script
Verifies that all components are properly installed and configured for Windows.
Run this script after initial setup to ensure everything is working correctly.
"""

import sys
import os
import platform
from pathlib import Path
import importlib.util

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_check(item, status, message=""):
    """Print a check result."""
    status_symbol = "✓" if status else "✗"
    status_text = "OK" if status else "FAIL"
    color = "\033[92m" if status else "\033[91m"  # Green or Red
    reset = "\033[0m"

    if message:
        print(f"  [{status_symbol}] {item}: {color}{status_text}{reset} - {message}")
    else:
        print(f"  [{status_symbol}] {item}: {color}{status_text}{reset}")

    return status

def check_python_version():
    """Check if Python version is compatible."""
    print_header("Python Environment")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    print(f"  Python version: {version_str}")
    print(f"  Python executable: {sys.executable}")

    is_ok = version.major == 3 and version.minor >= 9
    print_check("Python version", is_ok,
                "Requires Python 3.9 or higher" if not is_ok else "Compatible")

    return is_ok

def check_platform():
    """Check operating system."""
    system = platform.system()
    print(f"  Operating System: {system}")
    print(f"  Platform: {platform.platform()}")

    is_windows = system == "Windows"
    if is_windows:
        print_check("Windows detected", True, "Ready for Windows configuration")
    else:
        print_check("Windows detected", False, f"Running on {system} instead")

    return True  # Not critical

def check_package(package_name, import_name=None):
    """Check if a Python package is installed."""
    if import_name is None:
        import_name = package_name

    try:
        __import__(import_name)
        return True
    except ImportError:
        return False

def check_required_packages():
    """Check if all required packages are installed."""
    print_header("Required Python Packages")

    packages = [
        ("streamlit", "streamlit"),
        ("pandas", "pandas"),
        ("xlrd", "xlrd"),
        ("openpyxl", "openpyxl"),
        ("sqlite3", "sqlite3"),
        ("json", "json"),
        ("xml.etree.ElementTree", "xml.etree.ElementTree"),
    ]

    all_ok = True
    for package_name, import_name in packages:
        is_installed = check_package(package_name, import_name)
        print_check(package_name, is_installed,
                   "Installed" if is_installed else "NOT INSTALLED")
        all_ok = all_ok and is_installed

    if not all_ok:
        print("\n  To install missing packages, run:")
        print("    pip install -r requirements.txt")
        print("  Or:")
        print("    conda install -c conda-forge streamlit pandas xlrd openpyxl")

    return all_ok

def check_directory_structure():
    """Check if we're in the correct directory."""
    print_header("Directory Structure")

    current_dir = Path.cwd()
    print(f"  Current directory: {current_dir}")

    # Check if we're in Cruise_Logs directory
    is_correct_dir = current_dir.name == "Cruise_Logs" or (current_dir / "cruise_form.py").exists()
    print_check("In Cruise_Logs directory", is_correct_dir,
                "Found" if is_correct_dir else "Navigate to C:\\Cruise_Logs first")

    return is_correct_dir

def check_database():
    """Check if database file exists and is accessible."""
    print_header("Database Configuration")

    # Check for database file
    db_paths = [
        Path("Cruise_Logs.db"),
        Path("C:/Cruise_Logs/Cruise_Logs.db"),
        Path.home() / "Github" / "Cruise_Logs" / "Cruise_Logs.db"
    ]

    db_found = False
    db_path = None

    for path in db_paths:
        if path.exists():
            db_found = True
            db_path = path
            print(f"  Database found at: {path}")
            break

    print_check("Database file exists", db_found,
                str(db_path) if db_found else "Cruise_Logs.db not found")

    if db_found:
        # Check file size
        size_bytes = db_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        print(f"  Database size: {size_mb:.2f} MB")

        # Check if it's a Git LFS pointer file (very small)
        is_lfs_pointer = size_bytes < 1024  # Less than 1KB is likely a pointer
        if is_lfs_pointer:
            print_check("Database downloaded", False,
                       "File is Git LFS pointer - run: git lfs pull")
        else:
            print_check("Database downloaded", True, "Full database file present")

        # Try to connect to database
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            print(f"  Tables in database: {len(tables)}")
            if tables:
                print("    Tables found:")
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    print(f"      - {table[0]}: {count} records")

            conn.close()
            print_check("Database accessible", True, "Successfully connected")
            return True
        except Exception as e:
            print_check("Database accessible", False, f"Error: {e}")
            return False

    return db_found

def check_excel_files():
    """Check if Excel source files exist."""
    print_header("Excel Source Files")

    files = [
        "Equipment.xls",
        "NYLON LENGTHS_MostRecent.xls"
    ]

    all_ok = True
    for filename in files:
        exists = Path(filename).exists()
        print_check(filename, exists,
                   "Found" if exists else "Not found (optional for viewing data)")
        # Don't fail on missing Excel files as they're not critical for running the app

    return True  # Not critical for basic operation

def check_python_files():
    """Check if main Python application files exist."""
    print_header("Application Files")

    files = [
        "cruise_form.py",
        "dep_form_JSON.py",
        "rec_form_JSON.py",
        "repair_form_JSON.py",
        "adcp_dep_form.py",
        "adcp_rec_form.py",
        "release_inventory_search.py",
        "nylon_inventory_search.py",
        "import_release_inventory.py",
        "import_nylon_inventory.py",
        "db_sync2.py",
        "config.py",
    ]

    all_ok = True
    for filename in files:
        exists = Path(filename).exists()
        print_check(filename, exists, "Found" if exists else "MISSING")
        all_ok = all_ok and exists

    return all_ok

def check_configuration_files():
    """Check if configuration files exist."""
    print_header("Configuration Files")

    files = {
        "requirements.txt": "Python package list",
        "environment_windows.yml": "Conda environment file",
        ".gitignore": "Git ignore file",
        ".gitattributes": "Git LFS configuration",
        "SETUP_WINDOWS.md": "Setup documentation",
    }

    for filename, description in files.items():
        exists = Path(filename).exists()
        print_check(filename, exists,
                   description if exists else f"{description} - Not found")

    return True  # Not critical

def check_git_lfs():
    """Check if Git LFS is configured."""
    print_header("Git Configuration")

    # Check if .git directory exists
    is_git_repo = Path(".git").exists()
    print_check("Git repository", is_git_repo,
                "Initialized" if is_git_repo else "Not a git repository")

    # Check for .gitattributes
    has_gitattributes = Path(".gitattributes").exists()
    print_check("Git LFS configured", has_gitattributes,
                "Found .gitattributes" if has_gitattributes else "Missing .gitattributes")

    return True  # Not critical

def print_summary(checks_passed, total_checks):
    """Print summary of verification."""
    print_header("Verification Summary")

    percentage = (checks_passed / total_checks * 100) if total_checks > 0 else 0

    print(f"  Checks passed: {checks_passed}/{total_checks} ({percentage:.0f}%)")
    print()

    if checks_passed == total_checks:
        print("  ✓ All critical checks passed!")
        print("  You can start using the Cruise_Logs system.")
        print()
        print("  To start the main application, run:")
        print("    streamlit run cruise_form.py")
    elif percentage >= 75:
        print("  ⚠ Most checks passed, but some issues were found.")
        print("  The system may work, but review the failures above.")
    else:
        print("  ✗ Multiple critical issues found.")
        print("  Please resolve the issues above before using the system.")

    print()

def print_quick_start():
    """Print quick start instructions."""
    print_header("Quick Start Guide")
    print("""
  1. Activate conda environment:
       conda activate cruise_logs

  2. Navigate to Cruise_Logs directory:
       cd C:\\Cruise_Logs

  3. Start the main cruise form:
       streamlit run cruise_form.py

  4. Or use the batch file:
       .\\run_cruise_form.bat

  For more information, see SETUP_WINDOWS.md
""")

def main():
    """Main verification routine."""
    print("\n" + "=" * 70)
    print("  CRUISE_LOGS SETUP VERIFICATION")
    print("  Windows Field Computer Configuration Check")
    print("=" * 70)

    checks = []

    # Run all checks
    checks.append(("Python Version", check_python_version()))
    checks.append(("Platform", check_platform()))
    checks.append(("Required Packages", check_required_packages()))
    checks.append(("Directory Structure", check_directory_structure()))
    checks.append(("Database", check_database()))
    checks.append(("Excel Files", check_excel_files()))
    checks.append(("Python Files", check_python_files()))
    checks.append(("Configuration Files", check_configuration_files()))
    checks.append(("Git Configuration", check_git_lfs()))

    # Count passed checks
    checks_passed = sum(1 for _, passed in checks if passed)
    total_checks = len(checks)

    # Print summary
    print_summary(checks_passed, total_checks)

    # Print quick start guide if everything is OK
    if checks_passed == total_checks:
        print_quick_start()

    # Return exit code
    return 0 if checks_passed >= total_checks * 0.75 else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
