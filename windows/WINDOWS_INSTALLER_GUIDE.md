# Windows Installer Guide for Cruise_Logs

This guide explains the different installation methods available for Windows and helps you choose the best approach for your needs.

## Overview

Cruise_Logs provides **three installer options** for Windows, equivalent to a Unix Makefile:

| Method | Type | Best For | Difficulty |
|--------|------|----------|-----------|
| **PowerShell Script** (`install.ps1`) | Modern, automated | Full automation, new installations | Easy |
| **Makefile.bat** | Classic batch, target-based | Incremental steps, experienced users | Medium |
| **Manual Setup** | Step-by-step commands | Learning, debugging | Hard |

## Quick Start

### Option 1: Automated PowerShell Installer (Recommended)

The easiest way to get started:

```cmd
# 1. Right-click Windows PowerShell and select "Run as Administrator"
# 2. Navigate to the windows directory
cd C:\Users\YourName\Downloads\Cruise_Logs\windows

# 3. Run the installer
powershell -ExecutionPolicy Bypass -File install.ps1
```

**What it does:**
- ✅ Detects and installs Anaconda (if needed)
- ✅ Installs Git and Git LFS
- ✅ Clones the repository
- ✅ Creates conda environment
- ✅ Installs all Python dependencies
- ✅ Pulls the database from Git LFS
- ✅ Creates desktop shortcuts
- ✅ Verifies everything works

**Time required:** 10-20 minutes (depending on internet speed)

---

## Detailed Installation Methods

### Method 1: PowerShell Installer (install.ps1)

#### Prerequisites
- Windows 7 or later
- Administrator access
- Internet connection
- ~2 GB free disk space

#### Step-by-Step

**Step 1: Get Administrator Access**

Right-click on PowerShell and select "Run as Administrator"

```
Windows Key → Type "PowerShell" → Right-click → "Run as Administrator"
```

**Step 2: Navigate to Windows Directory**

```powershell
cd "C:\Users\YourName\Downloads\Cruise_Logs\windows"
```

Replace `YourName` with your actual Windows username.

**Step 3: Run the Installer**

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

Or if you prefer to set the execution policy first:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\install.ps1
```

**Step 4: Follow the Prompts**

The script will:
1. Check if Anaconda is installed
2. Check if Git is installed
3. Ask about the installation path
4. Clone the repository (if needed)
5. Create conda environment
6. Install Python packages
7. Offer to create desktop shortcuts

**Step 5: Verify Installation**

When complete, the script offers to run the verification test.

#### Command-Line Options

The PowerShell script accepts parameters:

```powershell
# Skip Git operations (use existing repository)
.\install.ps1 -SkipGit

# Skip Conda environment setup
.\install.ps1 -SkipConda

# Install to custom location
.\install.ps1 -InstallPath "D:\MyApps\Cruise_Logs"

# Full setup with all features
.\install.ps1 -FullSetup

# Multiple options
.\install.ps1 -SkipGit -InstallPath "C:\Cruise_Logs"
```

#### Troubleshooting PowerShell

**"Cannot be loaded because running scripts is disabled"**

Run this first:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then run the installer again.

**"PowerShell not found"**

- Windows 7: Install PowerShell 5.0 from Microsoft
- Windows 10/11: Already installed, use "Run as Administrator"

**Installation hangs**

Press `Ctrl+C` to cancel and try again. Check your internet connection.

---

### Method 2: Makefile.bat (Target-Based)

For those who prefer incremental control, `Makefile.bat` provides Unix Makefile-like targets.

#### Prerequisites
- Anaconda already installed
- Administrator access
- Git already installed (for some targets)

#### Installation with Makefile.bat

**Step 1: Open Command Prompt as Administrator**

```
Windows Key → Type "cmd" → Right-click → "Run as Administrator"
```

**Step 2: Navigate to Cruise_Logs Directory**

```cmd
cd C:\Cruise_Logs\windows
```

**Step 3: Run Installation Targets**

```cmd
REM Full installation
Makefile.bat install

REM Or install step-by-step
Makefile.bat conda-env      REM Create environment
Makefile.bat install-deps   REM Install packages
Makefile.bat pull-db        REM Pull database
Makefile.bat verify         REM Verify setup
```

#### Available Targets

**Installation Targets:**

```cmd
Makefile.bat help              # Show all available targets
Makefile.bat install           # Full automated installation
Makefile.bat setup             # Setup without installing prerequisites
Makefile.bat conda-env         # Create conda environment only
Makefile.bat install-deps      # Install Python packages only
```

**Database & Verification:**

```cmd
Makefile.bat pull-db           # Pull database from Git LFS
Makefile.bat verify            # Run installation verification
```

**Data Import:**

```cmd
Makefile.bat import-releases   # Import acoustic release inventory
Makefile.bat import-nylon      # Import nylon spool inventory
```

**Running Applications:**

```cmd
Makefile.bat run-cruise        # Start main cruise form
Makefile.bat run-deployment    # Start deployment form
Makefile.bat run-recovery      # Start recovery form
Makefile.bat run-launcher      # Start GUI launcher
```

**Maintenance:**

```cmd
Makefile.bat clean             # Remove conda environment only
Makefile.bat clean-all         # Remove environment + database
```

#### Examples

**Scenario 1: Full Fresh Installation**

```cmd
cd C:\Cruise_Logs\windows
Makefile.bat install
```

**Scenario 2: Already Have Repository, Just Need Environment**

```cmd
cd C:\Cruise_Logs
Makefile.bat conda-env
Makefile.bat install-deps
Makefile.bat pull-db
```

**Scenario 3: Just Run the Application**

```cmd
cd C:\Cruise_Logs
Makefile.bat run-cruise
```

**Scenario 4: Import Inventory Data**

```cmd
cd C:\Cruise_Logs
Makefile.bat import-releases
Makefile.bat import-nylon
```

#### Troubleshooting Makefile.bat

**"This target requires Administrator privileges"**

You must run Command Prompt as Administrator.

**"Conda not found"**

The script couldn't locate Anaconda. Ensure it's installed in one of these locations:
- `C:\Users\YourName\anaconda3`
- `C:\Users\YourName\miniconda3`
- `C:\ProgramData\Anaconda3`

**"Pip not found in conda environment"**

The conda environment doesn't exist. Run:

```cmd
Makefile.bat conda-env
```

---

### Method 3: Manual Setup (For Developers)

If you prefer to understand each step or need more control:

#### Step 1: Install Prerequisites

**Anaconda:**
1. Download from https://www.anaconda.com/download/
2. Run installer
3. Check "Add Anaconda to PATH"

**Git:**
1. Download from https://git-scm.com/download/win
2. Run installer
3. Check "Add Git to PATH"

**Git LFS:**
```cmd
git lfs install
```

#### Step 2: Clone Repository

```cmd
cd C:\
git clone https://github.com/blake1237/Cruise_Logs.git
cd Cruise_Logs
```

#### Step 3: Create Conda Environment

```cmd
conda create -n cruise_logs python=3.11 -y
conda activate cruise_logs
```

#### Step 4: Install Dependencies

```cmd
pip install -r requirements.txt
```

#### Step 5: Pull Database

```cmd
git lfs pull
```

#### Step 6: Verify Installation

```cmd
python verify_setup.py
```

#### Step 7: Run Application

```cmd
streamlit run cruise_form.py
```

---

## Post-Installation

### Using Desktop Shortcuts

If you created desktop shortcuts during installation:

1. **Cruise Logs - Main Form** - Opens the main cruise information form
2. **Cruise Logs - Launcher** - Opens the GUI application menu
3. (Additional shortcuts may be available)

### Running Applications Without Shortcuts

**From Command Prompt (with conda environment activated):**

```cmd
# Activate environment
conda activate cruise_logs

# Navigate to directory
cd C:\Cruise_Logs

# Run any application
streamlit run cruise_form.py
streamlit run release_inventory_search.py
streamlit run nylon_inventory_search.py
```

### Importing Data

**Acoustic Release Inventory:**

```cmd
conda activate cruise_logs
cd C:\Cruise_Logs
python import_release_inventory.py
```

**Nylon Spool Inventory:**

```cmd
conda activate cruise_logs
cd C:\Cruise_Logs
python import_nylon_inventory.py
```

### Database Synchronization

Sync with remote server:

```cmd
conda activate cruise_logs
cd C:\Cruise_Logs
python db_sync2.py --status    # Check status
python db_sync2.py --pull      # Download changes
python db_sync2.py --push      # Upload changes
```

---

## Uninstallation

### Remove Conda Environment Only

**Using Makefile.bat:**

```cmd
cd C:\Cruise_Logs\windows
Makefile.bat clean
```

**Manual method:**

```cmd
conda env remove -n cruise_logs -y
```

### Complete Uninstallation

**Using Makefile.bat:**

```cmd
cd C:\Cruise_Logs\windows
Makefile.bat clean-all
```

**Manual method:**

```cmd
# Remove environment
conda env remove -n cruise_logs -y

# Remove directory (optional)
rmdir /s /q C:\Cruise_Logs

# Remove desktop shortcuts (if created)
del "%USERPROFILE%\Desktop\Cruise Logs*"
```

---

## Troubleshooting

### Common Issues

#### 1. "Database file not found"

**Problem:** Application starts but can't find the database.

**Solution:**

```cmd
cd C:\Cruise_Logs
git lfs pull
```

Verify the file size:

```cmd
dir Cruise_Logs.db
```

Should be several MB, not a few KB.

#### 2. "ModuleNotFoundError: No module named 'streamlit'"

**Problem:** Python can't find installed packages.

**Solution:** Make sure to activate the conda environment:

```cmd
conda activate cruise_logs
```

#### 3. "Port 8501 already in use"

**Problem:** Another Streamlit instance is running.

**Solution:** 
- Option A: Specify different port:
  ```cmd
  streamlit run cruise_form.py --server.port 8502
  ```
- Option B: Close existing Streamlit window and try again

#### 4. "Permission denied" errors

**Problem:** Files are locked or read-only.

**Solution:**
- Run Command Prompt as Administrator
- Close any programs using the database
- Check file permissions

#### 5. "Git command not found"

**Problem:** Git is not installed or not in PATH.

**Solution:**
- Install Git from https://git-scm.com/download/win
- Add Git to PATH:
  - Right-click "This PC" → Properties
  - Advanced system settings → Environment Variables
  - Add `C:\Program Files\Git\cmd` to PATH

#### 6. "Anaconda not found"

**Problem:** Script can't locate Anaconda installation.

**Solution:**
- Install Anaconda from https://www.anaconda.com/download/
- Or manually set CONDA_PATH in Makefile.bat
- Ensure "Add Anaconda to PATH" was checked during installation

### Getting Help

1. **Check existing documentation:**
   - `windows/SETUP_WINDOWS.md` - Original Windows setup guide
   - `windows/WINDOWS_INSTALL_CHECKLIST.md` - Step-by-step checklist
   - `README.md` - Main project documentation

2. **Run verification script:**
   ```cmd
   conda activate cruise_logs
   cd C:\Cruise_Logs
   python verify_setup.py
   ```
   This checks all requirements and reports issues.

3. **Check system information:**
   ```cmd
   python --version
   conda --version
   git --version
   ```

4. **Create an issue on GitHub:**
   https://github.com/blake1237/Cruise_Logs/issues

---

## Choosing the Right Method

### Use PowerShell Installer (install.ps1) if:
- ✅ You want fully automated installation
- ✅ This is your first time
- ✅ You don't have Anaconda installed yet
- ✅ You want desktop shortcuts created automatically
- **Recommended for most users**

### Use Makefile.bat if:
- ✅ You prefer step-by-step control
- ✅ You already have Anaconda/Git installed
- ✅ You want to run specific tasks individually
- ✅ You need to troubleshoot or reinstall components
- **Recommended for experienced users**

### Use Manual Setup if:
- ✅ You're a developer who needs full control
- ✅ You want to understand each step
- ✅ You're troubleshooting complex issues
- ✅ You need custom paths or configurations
- **Recommended for advanced users**

---

## Version Information

- **Created:** 2024
- **Tested on:** Windows 10, Windows 11
- **Python:** 3.11
- **Anaconda:** Latest version
- **Git:** 2.43+
- **Git LFS:** 3.4+

---

## See Also

- **[SETUP_WINDOWS.md](SETUP_WINDOWS.md)** - Original Windows setup documentation
- **[WINDOWS_INSTALL_CHECKLIST.md](WINDOWS_INSTALL_CHECKLIST.md)** - Step-by-step checklist
- **[GITHUB_SETUP.md](GITHUB_SETUP.md)** - Repository and Git setup
- **[../README.md](../README.md)** - Main project documentation

---

## Support

For questions or issues:

1. Check this guide first
2. Review the troubleshooting section
3. Check `verify_setup.py` output
4. Review original documentation files
5. Create an issue on GitHub with error messages and system information
