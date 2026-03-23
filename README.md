# Cruise Logs Management System

A comprehensive database and form management system for oceanographic cruise data, mooring deployments, recoveries, repairs, and equipment inventory.

## Overview

The Cruise Logs system provides Streamlit-based web forms and search interfaces for managing:

- **Cruise Information** - Vessel, dates, personnel, and cruise details
- **Mooring Deployments** - Deployment records with instrument details
- **Mooring Recoveries** - Recovery operations and instrument condition
- **Equipment Repairs** - Maintenance and repair tracking
- **ADCP Operations** - Acoustic Doppler Current Profiler deployment/recovery
- **Release Inventory** - 569 acoustic release instruments
- **Nylon Inventory** - 1,723+ nylon spool records

All data is stored in a SQLite database (`Cruise_Logs.db`) with Git LFS support for version control.

## Features

✅ **Cross-platform** - Works on macOS, Windows, and Linux  
✅ **Web-based forms** - Streamlit interface accessible via browser  
✅ **SQLite database** - No external database server required  
✅ **Excel integration** - Import inventory data from Excel files  
✅ **XML export** - Generate deployment/recovery XML files  
✅ **Search capabilities** - Find equipment by serial number or spool ID  
✅ **Database sync** - Remote synchronization with spectrum.pmel.noaa.gov  
✅ **Inventory management** - Track acoustic releases and nylon spools  

## Quick Start

### macOS/Linux

```bash
# Clone repository
cd ~/Github
git clone git@github.com:blake1237/Cruise_Logs.git
cd Cruise_Logs

# Install dependencies
pip install -r requirements.txt

# Run main form
streamlit run cruise_form.py
```

### Windows

```cmd
# Clone repository
cd C:\
git clone git@github.com:blake1237/Cruise_Logs.git
cd Cruise_Logs

# Create conda environment
conda create -n cruise_logs python=3.11 -y
conda activate cruise_logs

# Install dependencies
pip install -r requirements.txt

# Run main form
streamlit run cruise_form.py
```

See **[SETUP_WINDOWS.md](windows/SETUP_WINDOWS.md)** for detailed Windows installation instructions.

## System Requirements

- **Python** 3.9 or higher (3.11 recommended)
- **Git** with Git LFS support
- **Anaconda** (recommended for Windows)

### Python Packages

- `streamlit` - Web interface framework
- `pandas` - Data manipulation
- `xlrd` - Reading .xls files
- `openpyxl` - Reading .xlsx files
- `sqlite3` - Database (included with Python)

Install all packages:
```bash
pip install -r requirements.txt
```

Or with conda:
```bash
conda env create -f windows/environment_windows.yml
```

## Applications

### Main Forms

| Application | Description | Command |
|------------|-------------|---------|
| `cruise_form.py` | Main cruise information form | `streamlit run cruise_form.py` |
| `dep_form_JSON.py` | Mooring deployment form | `streamlit run dep_form_JSON.py` |
| `rec_form_JSON.py` | Mooring recovery form | `streamlit run rec_form_JSON.py` |
| `repair_form_JSON.py` | Equipment repair form | `streamlit run repair_form_JSON.py` |
| `adcp_dep_form.py` | ADCP deployment form | `streamlit run adcp_dep_form.py` |
| `adcp_rec_form.py` | ADCP recovery form | `streamlit run adcp_rec_form.py` |

### Search & Inventory

| Application | Description | Command |
|------------|-------------|---------|
| `release_inventory_search.py` | Search 569 acoustic releases | `streamlit run release_inventory_search.py` |
| `nylon_inventory_search.py` | Search 1,723 nylon spools | `streamlit run nylon_inventory_search.py` |

### Data Import Scripts

| Script | Description | Usage |
|--------|-------------|-------|
| `import_release_inventory.py` | Import from Equipment.xls | `python import_release_inventory.py` |
| `import_nylon_inventory.py` | Import from NYLON LENGTHS_MostRecent.xls | `python import_nylon_inventory.py` |
| `import_dep.py` | Import deployment XML | `python import_dep.py <file.xml>` |
| `import_rec.py` | Import recovery XML | `python import_rec.py <file.xml>` |
| `import_repair.py` | Import repair XML | `python import_repair.py <file.xml>` |
| `import_adcp_dep.py` | Import ADCP deployment XML | `python import_adcp_dep.py <file.xml>` |
| `import_adcp_rec.py` | Import ADCP recovery XML | `python import_adcp_rec.py <file.xml>` |

## Database

**File:** `Cruise_Logs.db` (SQLite database, managed by Git LFS)

### Tables

- `cruise` - Cruise information
- `deployment` - Mooring deployments
- `recovery` - Mooring recoveries
- `repair` - Equipment repairs
- `adcp_deployment` - ADCP deployments
- `adcp_recovery` - ADCP recoveries
- `release_inventory` - 569 acoustic release records
- `nylon_inventory` - 1,723 nylon spool records

### Database Commands

```bash
# Open database
sqlite3 Cruise_Logs.db

# List tables
.tables

# View table schema
.schema deployment

# Query data
SELECT * FROM cruise ORDER BY cruise_id DESC LIMIT 10;

# Export to CSV
.mode csv
.output data.csv
SELECT * FROM deployment;
.quit
```

## Documentation

### Platform-Specific Guides

| Document | Description |
|----------|-------------|
| **[SETUP_MACOS.md](macos/SETUP_MACOS.md)** | Complete macOS installation guide |
| **[SETUP_WINDOWS.md](windows/SETUP_WINDOWS.md)** | Complete Windows installation guide |
| **[WINDOWS_INSTALL_CHECKLIST.md](windows/WINDOWS_INSTALL_CHECKLIST.md)** | Step-by-step Windows setup checklist |
| **[GITHUB_SETUP.md](windows/GITHUB_SETUP.md)** | GitHub repository setup & cloning |

### Inventory Documentation

| Document | Description |
|----------|-------------|
| **[README_inventories.md](README_inventories.md)** | Inventory systems overview |
| **[README_release_inventory.md](README_release_inventory.md)** | Acoustic release inventory details |
| **[README_nylon_inventory.md](README_nylon_inventory.md)** | Nylon spool inventory details |

## File Structure

```
Cruise_Logs/
├── Cruise_Logs.db              # SQLite database (Git LFS)
├── Equipment.xls               # Acoustic releases source data
├── NYLON LENGTHS_MostRecent.xls # Nylon spools source data
│
├── cruise_form.py              # Main cruise form
├── dep_form_JSON.py            # Deployment form
├── rec_form_JSON.py            # Recovery form
├── repair_form_JSON.py         # Repair form
├── adcp_dep_form.py            # ADCP deployment
├── adcp_rec_form.py            # ADCP recovery
│
├── release_inventory_search.py # Release search app
├── nylon_inventory_search.py   # Nylon search app
│
├── import_*.py                 # Data import scripts
├── db_sync2.py                 # Database sync utility
├── config.py                   # Cross-platform configuration
├── verify_setup.py             # Setup verification script
│
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
├── .gitattributes              # Git LFS configuration
│
├── macos/                      # macOS-specific files
│   ├── SETUP_MACOS.md          # macOS setup guide
│   └── README.md               # macOS documentation
│
├── windows/                    # Windows-specific files
│   ├── SETUP_WINDOWS.md        # Windows setup guide
│   ├── WINDOWS_INSTALL_CHECKLIST.md # Step-by-step checklist
│   ├── GITHUB_SETUP.md         # Git repository guide
│   ├── environment_windows.yml # Conda environment
│   ├── run_cruise_form.bat     # Windows launcher
│   └── README.md               # Windows documentation
│
├── README.md                   # This file
└── README_inventories.md       # Inventory documentation
```

## Installation

### Option 1: Quick Install (Existing Repository)

```bash
# Clone the repository
git clone git@github.com:blake1237/Cruise_Logs.git
cd Cruise_Logs

# Pull database file
git lfs pull

# Install packages
pip install -r requirements.txt

# Verify setup
python verify_setup.py

# Run application
streamlit run cruise_form.py
```

### Option 2: Windows Field Computer

Follow the comprehensive guide in **[windows/SETUP_WINDOWS.md](windows/SETUP_WINDOWS.md)**:

1. Install Anaconda (full installation)
2. Install Git with Git LFS
3. Clone repository to `C:\Cruise_Logs`
4. Create conda environment
5. Update database paths in Python files
6. Run verification script
7. Create desktop shortcuts

### Option 3: New Repository Setup

See **[windows/GITHUB_SETUP.md](windows/GITHUB_SETUP.md)** for instructions on:

- Creating a new repository
- Setting up Git LFS
- Configuring SSH keys
- Managing branches
- Syncing between machines

## Configuration

### Cross-Platform Paths

The system includes `config.py` for automatic platform detection:

```python
from config import DB_PATH, BASE_DIR

# Automatically uses correct path for Windows/Mac/Linux
```

### Manual Configuration

Update database paths in these files for Windows:

- `adcp_dep_form.py` (Line 9)
- `cruise_form.py` (Line 8)
- `rec_form_JSON.py` (Line 11)
- `repair_form_JSON.py` (Line 10)

Change to:
```python
DB_PATH = r'C:\Cruise_Logs\Cruise_Logs.db'
```

## Usage Examples

### Running Forms

```bash
# Main cruise form (port 8501)
streamlit run cruise_form.py

# Deployment form (auto-selects next port)
streamlit run dep_form_JSON.py

# Search releases
streamlit run release_inventory_search.py
```

### Importing Data

```bash
# Import inventory from Excel
python import_release_inventory.py
python import_nylon_inventory.py

# Import deployment XML
python import_dep.py zm263a_inp.xml
```

### Database Sync

```bash
# Sync with remote server
python db_sync2.py --push    # Upload local changes
python db_sync2.py --pull    # Download remote changes
python db_sync2.py --status  # Check sync status
```

## Troubleshooting

### Setup Verification

Run the verification script to check your installation:

```bash
python verify_setup.py
```

This checks:
- Python version
- Required packages
- Database file
- Excel files
- Application files
- Git LFS configuration

### Common Issues

**Database not found:**
```bash
# Pull LFS files
git lfs pull

# Verify database exists
ls -lh Cruise_Logs.db
```

**Import errors:**
```bash
# Install missing packages
pip install -r requirements.txt
```

**Port already in use:**
- Streamlit automatically uses next available port (8502, 8503, etc.)

**Excel files not importing:**
```bash
pip install xlrd openpyxl
```

## Database Synchronization

Sync local database with remote server (spectrum.pmel.noaa.gov):

```bash
# Check sync status
python db_sync2.py --status

# Pull from remote
python db_sync2.py --pull

# Push to remote
python db_sync2.py --push

# Interactive mode
python db_sync2.py
```

Requires SSH key authentication for user `lake`.

## Development

### Adding New Forms

1. Create new Streamlit form: `new_form.py`
2. Import config: `from config import DB_PATH`
3. Create database connection
4. Add form fields with `st.form()`
5. Implement save/update logic
6. Test with `streamlit run new_form.py`

### Database Schema Changes

```python
import sqlite3
conn = sqlite3.connect('Cruise_Logs.db')
cursor = conn.cursor()

# Add new column
cursor.execute("ALTER TABLE deployment ADD COLUMN new_field TEXT")

# Create new table
cursor.execute("""
CREATE TABLE new_table (
    id INTEGER PRIMARY KEY,
    name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()
```

## Contributing

1. Create feature branch: `git checkout -b feature-name`
2. Make changes and test thoroughly
3. Commit: `git commit -m "Description"`
4. Push: `git push origin feature-name`
5. Create pull request on GitHub

## Backup

### Database Backups

```bash
# Create timestamped backup
sqlite3 Cruise_Logs.db ".backup backup_$(date +%Y%m%d).db"

# Export to SQL
sqlite3 Cruise_Logs.db .dump > backup.sql

# Export specific table
sqlite3 Cruise_Logs.db "SELECT * FROM deployment" > deployments.csv
```

### Git Backups

The database is tracked in Git with LFS:
```bash
git add Cruise_Logs.db
git commit -m "Database backup"
git push
```

## Support & Contact

- **Repository:** https://github.com/blake1237/Cruise_Logs
- **Issues:** Create GitHub issue for bugs or feature requests
- **Documentation:** See README files in repository

## License

Internal NOAA/PMEL project. Contact repository owner for usage permissions.

## Acknowledgments

Developed for NOAA/PMEL oceanographic cruise data management.

---

**Version:** 1.0  
**Last Updated:** 2024  
**Platform:** Cross-platform (Windows, macOS, Linux)