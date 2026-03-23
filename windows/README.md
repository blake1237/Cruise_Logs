# Windows Setup Files

This directory contains all Windows-specific documentation and configuration files for setting up Cruise_Logs on a Windows field computer.

## 📁 Contents

| File | Description |
|------|-------------|
| **SETUP_WINDOWS.md** | Comprehensive Windows installation guide with detailed instructions, configuration, and troubleshooting |
| **WINDOWS_INSTALL_CHECKLIST.md** | Step-by-step interactive checklist format for installation verification |
| **GITHUB_SETUP.md** | Git repository setup, cloning, SSH configuration, and syncing guide |
| **environment_windows.yml** | Conda environment specification file for easy package installation |
| **run_cruise_form.bat** | Windows batch file to launch the cruise form application |
| **README.md** | This file |

## 🚀 Quick Start for Windows Installation

### 1. Start Here
Read **[WINDOWS_INSTALL_CHECKLIST.md](WINDOWS_INSTALL_CHECKLIST.md)** - follow the checklist step-by-step.

### 2. Detailed Information
Refer to **[SETUP_WINDOWS.md](SETUP_WINDOWS.md)** for detailed explanations and troubleshooting.

### 3. Repository Setup
See **[GITHUB_SETUP.md](GITHUB_SETUP.md)** if you need to clone or configure the Git repository.

## 📋 Installation Summary

```cmd
# 1. Clone repository
cd C:\
git clone git@github.com:blake1237/Cruise_Logs.git
cd Cruise_Logs

# 2. Pull database file
git lfs pull

# 3. Create conda environment
conda env create -f windows/environment_windows.yml

# 4. Activate environment
conda activate cruise_logs

# 5. Verify setup
python verify_setup.py

# 6. Run application
streamlit run cruise_form.py
```

Or use the batch file launcher:
```cmd
cd C:\Cruise_Logs
windows\run_cruise_form.bat
```

## 🔧 Using the Batch File

The `run_cruise_form.bat` file provides an easy way to launch the cruise form:

1. **From Command Prompt:**
   ```cmd
   cd C:\Cruise_Logs
   windows\run_cruise_form.bat
   ```

2. **Create Desktop Shortcut:**
   - Right-click on `run_cruise_form.bat`
   - Select "Create shortcut"
   - Move shortcut to Desktop
   - Rename to "Cruise Logs"

3. **Copy to Main Directory (Optional):**
   ```cmd
   copy windows\run_cruise_form.bat C:\Cruise_Logs\
   ```

## 🔄 Using the Conda Environment File

Instead of installing packages manually, use the environment file:

```cmd
# Create environment from file
conda env create -f windows/environment_windows.yml

# This creates 'cruise_logs' environment with all dependencies

# Activate it
conda activate cruise_logs

# Update environment if needed
conda env update -f windows/environment_windows.yml
```

## 📖 Documentation Overview

### SETUP_WINDOWS.md
- Complete installation guide
- Step-by-step instructions
- Path configuration for Windows
- Network access setup
- Troubleshooting guide
- Desktop shortcut creation

### WINDOWS_INSTALL_CHECKLIST.md
- Interactive checklist format
- Pre-installation requirements
- Installation steps with checkboxes
- Verification tests
- Post-installation tasks

### GITHUB_SETUP.md
- Repository cloning options
- Git LFS configuration
- SSH key setup
- Same vs. separate repository strategies
- Syncing between Mac and Windows
- Branch management

## ⚠️ Important Notes

1. **Target Installation:** `C:\Cruise_Logs`
2. **Anaconda Required:** Full Anaconda installation needed
3. **Git LFS Required:** For database file handling
4. **Path Updates:** Four Python files need Windows paths updated (see SETUP_WINDOWS.md)

## 🔍 Files That Need Path Updates

After cloning, update these files for Windows:
- `adcp_dep_form.py` (Line 9)
- `cruise_form.py` (Line 8)
- `rec_form_JSON.py` (Line 11)
- `repair_form_JSON.py` (Line 10)

Change to: `DB_PATH = r'C:\Cruise_Logs\Cruise_Logs.db'`

**Or** use the cross-platform `config.py` module (recommended for future).

## 💡 Tips

- Use **Anaconda Prompt** instead of regular Command Prompt
- Always activate the conda environment before running applications
- The batch file handles environment activation automatically
- Run `python verify_setup.py` to check your installation

## 🆘 Getting Help

1. **Check the documentation** in this directory
2. **Run verification:** `python verify_setup.py`
3. **Review troubleshooting** section in SETUP_WINDOWS.md
4. **Check main README:** `../README.md`

## 📦 Related Files (in parent directory)

- `requirements.txt` - Python package list (platform-independent)
- `config.py` - Cross-platform configuration module
- `verify_setup.py` - Setup verification script
- `.gitignore` - Git ignore rules
- `.gitattributes` - Git LFS configuration

## ✅ Quick Installation Check

After installation, verify everything works:

```cmd
conda activate cruise_logs
cd C:\Cruise_Logs
python verify_setup.py
```

This will check:
- Python version
- Required packages
- Database file
- Application files
- Git configuration

## 🎯 Success Criteria

Your installation is complete when:
- ✓ Conda environment activates without errors
- ✓ `python verify_setup.py` shows all checks passed
- ✓ `streamlit run cruise_form.py` opens in browser
- ✓ You can search inventory data
- ✓ Forms load and display correctly

---

**Ready to install? Start with [WINDOWS_INSTALL_CHECKLIST.md](WINDOWS_INSTALL_CHECKLIST.md)!**