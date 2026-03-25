# Windows Setup Guide for Cruise_Logs

This guide will help you set up the Cruise_Logs repository on a Windows field computer.

## Prerequisites

- **Anaconda** (full installation) installed on Windows
- **Git** installed on Windows (comes with Git Bash)
- **Git LFS** (Large File Storage) for handling the database file
- **GitHub account** with access to the repository

## Installation Steps

### 1. Install Git LFS (if not already installed)

Git LFS is required to handle the `Cruise_Logs.db` file properly.

```cmd
# Open Git Bash or Command Prompt
git lfs install
```

### 2. Clone the Repository

Open **Git Bash** or **Command Prompt** and run:

**Method 1: HTTPS (Recommended for Windows)**

HTTPS works best on corporate/government networks where SSH port 22 may be blocked:

```cmd
# Navigate to C:\ drive
cd C:\

# Clone the repository using HTTPS
git clone https://github.com/blake1237/Cruise_Logs.git
```

**Method 2: SSH (Alternative)**

If SSH is configured and port 22 is not blocked:

```cmd
cd C:\
git clone git@github.com:blake1237/Cruise_Logs.git
```

**Troubleshooting SSH Timeout:**
If SSH times out, use HTTPS (Method 1) or configure SSH to use port 443:
- Create/edit `C:\Users\YourName\.ssh\config`
- Add:
  ```
  Host github.com
    Hostname ssh.github.com
    Port 443
  ```

This will create `C:\Cruise_Logs` directory.

### 3. Navigate to the Repository

```cmd
cd C:\Cruise_Logs
```

### 4. Create Conda Environment

Create a dedicated conda environment for the project:

```cmd
# Create new environment with Python 3.11
conda create -n cruise_logs python=3.11 -y

# Activate the environment
conda activate cruise_logs
```

### 5. Install Required Python Packages

```cmd
# Install core dependencies
conda install -c conda-forge streamlit pandas xlrd openpyxl sqlite -y

# Or use pip
pip install streamlit pandas xlrd openpyxl
```

**Required packages:**
- `streamlit` - Web interface for forms and search apps
- `pandas` - Data manipulation and Excel file handling
- `xlrd` - Reading older .xls files
- `openpyxl` - Reading newer .xlsx files
- `sqlite3` - Database (comes with Python)

### 6. Update File Paths in Python Scripts

Several Python files contain hardcoded paths that need to be updated for Windows. You'll need to edit these files:

#### Files to Update:

**1. `adcp_dep_form.py`** (Line 9)
```python
# Change from:
DB_PATH = '/Users/lake/Github/Cruise_Logs/Cruise_Logs.db'

# To:
DB_PATH = r'C:\Cruise_Logs\Cruise_Logs.db'
```

**2. `cruise_form.py`** (Line 8)
```python
# Change from:
DB_PATH = os.path.expanduser("~/Github/Cruise_Logs/Cruise_Logs.db")

# To:
DB_PATH = r'C:\Cruise_Logs\Cruise_Logs.db'
```

**3. `rec_form_JSON.py`** (Line 11)
```python
# Change from:
DB_PATH = os.path.expanduser("~/Github/Cruise_Logs/Cruise_Logs.db")

# To:
DB_PATH = r'C:\Cruise_Logs\Cruise_Logs.db'
```

**4. `repair_form_JSON.py`** (Line 10)
```python
# Change from:
DB_PATH = os.path.expanduser("~/Github/Cruise_Logs/Cruise_Logs.db")

# To:
DB_PATH = r'C:\Cruise_Logs\Cruise_Logs.db'
```

**Note:** The `r` prefix before the string makes it a raw string, so backslashes are treated literally.

**Alternative:** Use relative paths (works on all platforms):
```python
DB_PATH = "Cruise_Logs.db"
```

### 7. Verify Database File

Check that the database file was properly downloaded via Git LFS:

```cmd
# Check file size (should be several MB, not a few KB)
dir Cruise_Logs.db

# If it's only a few KB, it's a pointer file - pull the actual file:
git lfs pull
```

### 8. Test the Installation

#### Test 1: Import Release Inventory
```cmd
conda activate cruise_logs
cd C:\Cruise_Logs
python import_release_inventory.py
```

Expected output: "Successfully imported X records from Equipment.xls"

#### Test 2: Import Nylon Inventory
```cmd
python import_nylon_inventory.py
```

Expected output: "Successfully imported X records from NYLON LENGTHS_MostRecent.xls"

#### Test 3: Run Streamlit Apps

```cmd
# Test cruise form
streamlit run cruise_form.py

# Or test inventory search
streamlit run release_inventory_search.py
```

Your default browser should open to `http://localhost:8501`

Press `Ctrl+C` to stop the server.

## Running the Applications

### Main Cruise Form
```cmd
conda activate cruise_logs
cd C:\Cruise_Logs
streamlit run cruise_form.py
```

### Deployment Form
```cmd
streamlit run dep_form_JSON.py
```

### Recovery Form
```cmd
streamlit run rec_form_JSON.py
```

### Repair Form
```cmd
streamlit run repair_form_JSON.py
```

### ADCP Forms
```cmd
streamlit run adcp_dep_form.py
streamlit run adcp_rec_form.py
```

### Inventory Search Apps
```cmd
streamlit run release_inventory_search.py
streamlit run nylon_inventory_search.py
```

## Database Synchronization

The `db_sync2.py` script syncs with a remote server. For Windows, you may need to:

1. Ensure SSH keys are set up for authentication
2. Update the shebang line (line 1) or run directly with Python:

```cmd
python db_sync2.py --help
```

## Troubleshooting

### Issue: "No module named 'streamlit'"
**Solution:** Activate the conda environment first
```cmd
conda activate cruise_logs
```

### Issue: Database file not found
**Solution:** Ensure you're in the correct directory
```cmd
cd C:\Cruise_Logs
python -c "import os; print(os.path.exists('Cruise_Logs.db'))"
```

### Issue: Excel files not importing
**Solution:** Install xlrd for .xls files
```cmd
pip install xlrd openpyxl
```

### Issue: "Permission denied" on database
**Solution:** Close any other programs that might have the database open

### Issue: Git LFS file is just a pointer
**Solution:** 
```cmd
git lfs pull
```

### Issue: Port 8501 already in use
**Solution:** Streamlit will automatically use the next available port (8502, 8503, etc.)

## Creating a Desktop Shortcut

### For Main Cruise Form:

1. Right-click on Desktop → New → Shortcut
2. Enter location:
   ```
   C:\Users\<YourUsername>\anaconda3\Scripts\streamlit.exe run C:\Cruise_Logs\cruise_form.py
   ```
3. Name it "Cruise Log Form"
4. Change icon if desired

### Using a Batch File (Recommended):

Create `C:\Cruise_Logs\run_cruise_form.bat`:
```batch
@echo off
call conda activate cruise_logs
cd C:\Cruise_Logs
streamlit run cruise_form.py
pause
```

Then create a shortcut to this batch file.

## Auto-Start Configuration

To automatically start the cruise form when Windows boots:

1. Press `Win+R`, type `shell:startup`, press Enter
2. Create a shortcut to your batch file in this folder

## Windows-Specific Notes

- Use backslashes (`\`) in Windows paths or raw strings (`r"C:\path"`)
- Or use forward slashes (`/`) which Python accepts on Windows
- File paths are case-insensitive on Windows
- The database file (`Cruise_Logs.db`) uses Git LFS - ensure it's properly pulled
- Some scripts have Unix-specific shebangs (`#!/usr/bin/env python`) - run with `python script.py` instead

## Network Configuration

If accessing from other computers on the network:

```cmd
streamlit run cruise_form.py --server.address 0.0.0.0
```

Then access from other computers using:
```
http://<computer-ip>:8501
```

## Updating the Repository

```cmd
cd C:\Cruise_Logs
git pull
git lfs pull  # Important for database updates
```

## Conda Environment Management

### Save environment (for documentation):
```cmd
conda env export > environment_windows.yml
```

### Recreate environment from file:
```cmd
conda env create -f environment_windows.yml
```

### List installed packages:
```cmd
conda list
```

## Summary of File Paths to Update

After cloning, update these files to use Windows paths:

1. `adcp_dep_form.py` → Line 9: `DB_PATH`
2. `cruise_form.py` → Line 8: `DB_PATH`  
3. `rec_form_JSON.py` → Line 11: `DB_PATH`
4. `repair_form_JSON.py` → Line 10: `DB_PATH`
5. `db_sync2.py` → Line 1: shebang (or just use `python db_sync2.py`)

**Best Practice:** Consider making these paths use relative references or `os.path.join()` for cross-platform compatibility.

## Quick Start Checklist

- [ ] Anaconda installed
- [ ] Git and Git LFS installed
- [ ] Repository cloned to `C:\Cruise_Logs`
- [ ] Conda environment created and activated
- [ ] Python packages installed (streamlit, pandas, xlrd)
- [ ] Database paths updated in Python files
- [ ] Database file pulled via Git LFS
- [ ] Tested at least one Streamlit app
- [ ] Created desktop shortcuts (optional)

## Support

For issues specific to the Windows setup, check:
- Python version: `python --version` (should be 3.11.x)
- Streamlit version: `streamlit version`
- Conda environment: `conda info --envs`

## Additional Resources

- **Anaconda Documentation:** https://docs.anaconda.com/
- **Streamlit Documentation:** https://docs.streamlit.io/
- **Git LFS Documentation:** https://git-lfs.github.com/
- **Original README:** `README_inventories.md`
