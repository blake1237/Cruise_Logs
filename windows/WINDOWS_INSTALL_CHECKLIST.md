# Windows Installation Checklist

A step-by-step checklist for setting up Cruise_Logs on a Windows field computer.

**Target Location:** `C:\Cruise_Logs`

---

## Pre-Installation Checklist

### Software Prerequisites

- [ ] **Anaconda** (full installation) is installed
  - Download from: https://www.anaconda.com/download
  - Verify: Open Anaconda Prompt and run `conda --version`

- [ ] **Git** is installed with Git Bash
  - Download from: https://git-scm.com/download/win
  - Verify: Open Git Bash and run `git --version`

- [ ] **Git LFS** (Large File Storage) is installed
  - Download from: https://git-lfs.github.com/
  - Verify: Run `git lfs version`
  - Initialize: Run `git lfs install`

- [ ] **GitHub access** is configured
  - [ ] Have GitHub account credentials
  - [ ] OR SSH key is set up (recommended)

---

## Installation Steps

### 1. Clone Repository

- [ ] Open **Git Bash** or **Command Prompt**

- [ ] Navigate to C:\ drive
  ```cmd
  cd C:\
  ```

- [ ] Clone the repository using **HTTPS** (recommended for Windows):
  ```cmd
  git clone https://github.com/blake1237/Cruise_Logs.git
  ```
  
  **OR** Clone using SSH (if port 22 is not blocked):
  ```cmd
  git clone git@github.com:blake1237/Cruise_Logs.git
  ```
  
  **Note:** HTTPS works better on corporate/government networks where SSH port 22 may be blocked.
</text>

<old_text line=351>
**Issue: Git clone fails with SSH**
- [ ] Solution: Use HTTPS instead
  ```cmd
  git clone https://github.com/blake1237/Cruise_Logs.git
  ```

- [ ] Verify directory was created
  ```cmd
  dir Cruise_Logs
  ```

### 2. Download Database File

- [ ] Navigate into the repository
  ```cmd
  cd C:\Cruise_Logs
  ```

- [ ] Pull the Git LFS files (important!)
  ```cmd
  git lfs pull
  ```

- [ ] Verify database file size
  ```cmd
  dir Cruise_Logs.db
  ```
  - Should be **several MB**, not a few KB
  - If it's tiny, it's a pointer file - run `git lfs pull` again

### 3. Create Conda Environment

- [ ] Open **Anaconda Prompt** (or use Git Bash with conda)

- [ ] Create new environment with Python 3.11
  ```cmd
  conda create -n cruise_logs python=3.11 -y
  ```

- [ ] Wait for environment creation to complete

- [ ] Activate the environment
  ```cmd
  conda activate cruise_logs
  ```
  - Your prompt should now show `(cruise_logs)` prefix

### 4. Install Python Packages

- [ ] Ensure you're in the Cruise_Logs directory
  ```cmd
  cd C:\Cruise_Logs
  ```

- [ ] Install required packages using pip
  ```cmd
  pip install -r requirements.txt
  ```

  **OR** using conda:
  ```cmd
  conda install -c conda-forge streamlit pandas xlrd openpyxl -y
  ```

- [ ] Verify Streamlit is installed
  ```cmd
  streamlit version
  ```

### 5. Verify Database Paths (No Changes Needed!)

**Good news:** All Python files now use **relative paths** that work automatically on both Windows and macOS!

- [ ] **Verify** all files use: `DB_PATH = "Cruise_Logs.db"`
- [ ] **No manual editing required** - as long as you run from `C:\Cruise_Logs` directory

All database paths are now cross-platform compatible!

### 6. Run Setup Verification

- [ ] Run the verification script
  ```cmd
  conda activate cruise_logs
  cd C:\Cruise_Logs
  python verify_setup.py
  ```

- [ ] Review the output
  - All critical checks should pass ✓
  - Note any failures and resolve them

### 7. Test the Installation

#### Test 1: Database Connection

- [ ] Test Python database connection
  ```cmd
  python -c "import sqlite3; conn = sqlite3.connect('Cruise_Logs.db'); print('Database OK'); conn.close()"
  ```

#### Test 2: Import Release Inventory

- [ ] Run the import script
  ```cmd
  python import_release_inventory.py
  ```
  - Expected: "Successfully imported 569 records..."

#### Test 3: Import Nylon Inventory

- [ ] Run the import script
  ```cmd
  python import_nylon_inventory.py
  ```
  - Expected: "Successfully imported 1723 records..."

#### Test 4: Launch Main Application

- [ ] Start the cruise form
  ```cmd
  streamlit run cruise_form.py
  ```

- [ ] Verify browser opens to `http://localhost:8501`

- [ ] Check that the form loads correctly

- [ ] Test entering some data (optional)

- [ ] Press `Ctrl+C` in the terminal to stop the server

#### Test 5: Launch Search Applications

- [ ] Test release inventory search
  ```cmd
  streamlit run release_inventory_search.py
  ```

- [ ] Test searching for a serial number

- [ ] Stop with `Ctrl+C`

- [ ] Test nylon inventory search
  ```cmd
  streamlit run nylon_inventory_search.py
  ```

- [ ] Test searching for a spool ID

- [ ] Stop with `Ctrl+C`

---

## Optional: Create Desktop Shortcuts

### Option 1: Batch File Method (Recommended)

- [ ] Verify `run_cruise_form.bat` exists in `C:\Cruise_Logs`

- [ ] Test the batch file by double-clicking it
  - Should launch the cruise form

- [ ] Right-click on `run_cruise_form.bat` → "Create shortcut"

- [ ] Move shortcut to Desktop

- [ ] Rename to "Cruise Log Form"

- [ ] (Optional) Right-click shortcut → Properties → Change Icon

### Option 2: Direct Streamlit Shortcut

- [ ] Right-click on Desktop → New → Shortcut

- [ ] Enter location (replace `<YourUsername>` with your Windows username):
  ```
  C:\Users\<YourUsername>\anaconda3\Scripts\streamlit.exe run C:\Cruise_Logs\cruise_form.py
  ```

- [ ] Click "Next"

- [ ] Name it "Cruise Logs"

- [ ] Click "Finish"

---

## Optional: Auto-Start on Boot

- [ ] Press `Win+R` to open Run dialog

- [ ] Type `shell:startup` and press Enter

- [ ] Copy your batch file shortcut into this folder

- [ ] The application will now start when Windows boots

---

## Optional: Network Access Configuration

If you need to access the application from other computers on the network:

- [ ] Edit the batch file or run command to include:
  ```cmd
  streamlit run cruise_form.py --server.address 0.0.0.0
  ```

- [ ] Find your computer's IP address
  ```cmd
  ipconfig
  ```
  - Look for "IPv4 Address"

- [ ] Access from other computers using:
  ```
  http://<your-ip-address>:8501
  ```

- [ ] Configure Windows Firewall to allow port 8501 (if needed)

---

## Verification Checklist

### Final Checks

- [ ] Python 3.11 is installed and accessible
- [ ] Conda environment "cruise_logs" exists and activates
- [ ] All required Python packages are installed
- [ ] Repository is at `C:\Cruise_Logs`
- [ ] Database file `Cruise_Logs.db` is present and > 1MB
- [ ] Database paths are relative (no changes needed!)
- [ ] Main cruise form launches successfully
- [ ] Search apps work correctly
- [ ] Excel import scripts run without errors
- [ ] Desktop shortcuts created (optional)

### Test All Applications

- [ ] `streamlit run cruise_form.py` - Main cruise form
- [ ] `streamlit run dep_form_JSON.py` - Deployment form
- [ ] `streamlit run rec_form_JSON.py` - Recovery form
- [ ] `streamlit run repair_form_JSON.py` - Repair form
- [ ] `streamlit run adcp_dep_form.py` - ADCP deployment
- [ ] `streamlit run adcp_rec_form.py` - ADCP recovery
- [ ] `streamlit run release_inventory_search.py` - Release search
- [ ] `streamlit run nylon_inventory_search.py` - Nylon search

---

## Troubleshooting

### Common Issues and Solutions

**Issue: "conda: command not found"**
- [ ] Solution: Open **Anaconda Prompt** instead of regular Command Prompt
- [ ] Or add Anaconda to PATH (during installation)

**Issue: "No module named 'streamlit'"**
- [ ] Solution: Activate conda environment first
  ```cmd
  conda activate cruise_logs
  ```

**Issue: Database file is only a few KB**
- [ ] Solution: It's a Git LFS pointer file
  ```cmd
  git lfs pull
  ```

**Issue: "Permission denied" on database**
- [ ] Solution: Close all applications that might have the database open
- [ ] Check file permissions in Windows Explorer

**Issue: Excel import fails**
- [ ] Solution: Install Excel support packages
  ```cmd
  pip install xlrd openpyxl
  ```

**Issue: Port 8501 already in use**
- [ ] Solution: Streamlit will auto-select next port (8502, 8503, etc.)
- [ ] Or stop other Streamlit instances

**Issue: Can't find Python files**
- [ ] Solution: Ensure you're in correct directory
  ```cmd
  cd C:\Cruise_Logs
  dir *.py
  ```

**Issue: Git clone fails with SSH**
- [ ] Solution: Use HTTPS instead
  ```cmd
  git clone https://github.com/blake1237/Cruise_Logs.git
  ```

---

## Post-Installation

### Regular Usage

1. **Open Anaconda Prompt**
2. **Activate environment:** `conda activate cruise_logs`
3. **Navigate to directory:** `cd C:\Cruise_Logs`
4. **Run application:** `streamlit run cruise_form.py`

**OR** just double-click the desktop shortcut!

### Keeping Updated

- [ ] Periodically pull updates from GitHub
  ```cmd
  cd C:\Cruise_Logs
  git pull origin main
  git lfs pull
  ```

- [ ] Update Python packages as needed
  ```cmd
  pip install --upgrade -r requirements.txt
  ```

### Backup Recommendations

- [ ] Database is backed up via Git commits
- [ ] Consider periodic manual backups of `Cruise_Logs.db`
- [ ] Use database sync script for remote backups

---

## Support Resources

- **Setup Guide:** `SETUP_WINDOWS.md`
- **Main README:** `README.md`
- **GitHub Guide:** `GITHUB_SETUP.md`
- **Inventory Docs:** `README_inventories.md`
- **Verification Script:** `python verify_setup.py`

---

## Installation Complete! ✓

**Date Completed:** _______________

**Installed By:** _______________

**Computer Name:** _______________

**Notes:**
_______________________________________________________________________________
_______________________________________________________________________________
_______________________________________________________________________________

---

**Ready to use! Launch the cruise form and start logging data.**