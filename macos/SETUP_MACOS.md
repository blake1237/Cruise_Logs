# macOS Setup Guide for Cruise_Logs

This guide will help you set up the Cruise_Logs repository on a macOS system.

## Prerequisites

- **macOS** 10.15 (Catalina) or later
- **Homebrew** package manager (recommended)
- **Git** with Git LFS support
- **Python** 3.9 or higher (Anaconda recommended, or system Python with venv)
- **GitHub account** with repository access

## Installation Steps

### 1. Install Homebrew (if not already installed)

Homebrew is the recommended package manager for macOS.

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Verify installation
brew --version
```

### 2. Install Git and Git LFS

```bash
# Install Git (if not already installed)
brew install git

# Install Git LFS for large file handling
brew install git-lfs

# Initialize Git LFS
git lfs install

# Verify installations
git --version
git lfs version
```

### 3. Clone the Repository

```bash
# Navigate to your Github directory
cd ~/Github

# Clone the repository
git clone git@github.com:blake1237/Cruise_Logs.git

# Or use HTTPS if SSH is not configured:
git clone https://github.com/blake1237/Cruise_Logs.git

# Navigate into the directory
cd Cruise_Logs

# Pull LFS files (important!)
git lfs pull
```

### 4. Set Up Python Environment

#### Option A: Using Anaconda (Recommended)

```bash
# Install Anaconda (if not already installed)
brew install --cask anaconda

# Add conda to your PATH (if needed)
export PATH="/usr/local/anaconda3/bin:$PATH"

# Create conda environment
conda create -n cruise_logs python=3.11 -y

# Activate environment
conda activate cruise_logs

# Install packages
conda install -c conda-forge streamlit pandas xlrd openpyxl -y
```

#### Option B: Using venv (Built-in Python)

```bash
# Ensure Python 3.9+ is installed
python3 --version

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### 5. Verify Database File

```bash
# Check database file size
ls -lh Cruise_Logs.db

# Should be several MB, not just a few KB
# If it's tiny, pull LFS files:
git lfs pull
```

### 6. Configure Paths

The default configuration should work for macOS if you cloned to `~/Github/Cruise_Logs`.

**Current default paths in the code:**
- `~/Github/Cruise_Logs/Cruise_Logs.db`
- `/Users/lake/Github/Cruise_Logs/Cruise_Logs.db`

**If you cloned to a different location**, update these files:

#### Files to Update:

**1. `adcp_dep_form.py`** (Line 9)
```python
# Change from:
DB_PATH = '/Users/lake/Github/Cruise_Logs/Cruise_Logs.db'

# To your path:
DB_PATH = os.path.expanduser('~/Github/Cruise_Logs/Cruise_Logs.db')
```

**2. `cruise_form.py`** (Line 8)
```python
# Already uses expanduser, should work automatically
DB_PATH = os.path.expanduser("~/Github/Cruise_Logs/Cruise_Logs.db")
```

**3. `rec_form_JSON.py`** (Line 11)
```python
# Already uses expanduser, should work automatically
DB_PATH = os.path.expanduser("~/Github/Cruise_Logs/Cruise_Logs.db")
```

**4. `repair_form_JSON.py`** (Line 10)
```python
# Already uses expanduser, should work automatically
DB_PATH = os.path.expanduser("~/Github/Cruise_Logs/Cruise_Logs.db")
```

**Better Solution:** Use the cross-platform `config.py` module:
```python
from config import DB_PATH
```

### 7. Test the Installation

#### Test 1: Verify Python Environment
```bash
# Activate environment
conda activate cruise_logs
# or: source venv/bin/activate

# Check Python version
python --version

# Check installed packages
pip list | grep streamlit
pip list | grep pandas
```

#### Test 2: Database Connection
```bash
# Test database access
python -c "import sqlite3; conn = sqlite3.connect('Cruise_Logs.db'); print('Database OK'); conn.close()"
```

#### Test 3: Import Inventory Data
```bash
# Import release inventory
python import_release_inventory.py

# Expected output: "Successfully imported 569 records..."

# Import nylon inventory
python import_nylon_inventory.py

# Expected output: "Successfully imported 1723 records..."
```

#### Test 4: Launch Main Application
```bash
# Start the cruise form
streamlit run cruise_form.py

# Browser should open to http://localhost:8501
# Press Ctrl+C to stop
```

#### Test 5: Launch Search Applications
```bash
# Test release inventory search
streamlit run release_inventory_search.py

# Test nylon inventory search
streamlit run nylon_inventory_search.py
```

### 8. Run Setup Verification

```bash
# Run comprehensive verification
python verify_setup.py

# This checks:
# - Python version
# - Required packages
# - Database file
# - Application files
# - Git configuration
```

## Running the Applications

### Main Forms

```bash
# Always activate environment first
conda activate cruise_logs
# or: source venv/bin/activate

# Navigate to repository
cd ~/Github/Cruise_Logs

# Run main cruise form
streamlit run cruise_form.py

# Run deployment form
streamlit run dep_form_JSON.py

# Run recovery form
streamlit run rec_form_JSON.py

# Run repair form
streamlit run repair_form_JSON.py

# Run ADCP forms
streamlit run adcp_dep_form.py
streamlit run adcp_rec_form.py
```

### Search Applications

```bash
# Release inventory search
streamlit run release_inventory_search.py

# Nylon inventory search
streamlit run nylon_inventory_search.py
```

## Creating Shortcuts

### Terminal Alias

Add to your `~/.zshrc` or `~/.bash_profile`:

```bash
# Cruise Logs aliases
alias cruise-form='cd ~/Github/Cruise_Logs && conda activate cruise_logs && streamlit run cruise_form.py'
alias cruise-deploy='cd ~/Github/Cruise_Logs && conda activate cruise_logs && streamlit run dep_form_JSON.py'
alias cruise-recover='cd ~/Github/Cruise_Logs && conda activate cruise_logs && streamlit run rec_form_JSON.py'
alias cruise-releases='cd ~/Github/Cruise_Logs && conda activate cruise_logs && streamlit run release_inventory_search.py'
```

Reload your shell:
```bash
source ~/.zshrc  # or source ~/.bash_profile
```

Then just type: `cruise-form`

### Shell Script

Create `~/cruise_logs.sh`:

```bash
#!/bin/bash
cd ~/Github/Cruise_Logs
source ~/anaconda3/bin/activate cruise_logs
streamlit run cruise_form.py
```

Make executable:
```bash
chmod +x ~/cruise_logs.sh
```

Run with: `~/cruise_logs.sh`

### macOS Automator App (Optional)

1. Open **Automator** (Applications → Automator)
2. Choose **Application**
3. Add **Run Shell Script** action
4. Enter:
   ```bash
   source ~/anaconda3/bin/activate cruise_logs
   cd ~/Github/Cruise_Logs
   streamlit run cruise_form.py
   ```
5. Save as "Cruise Logs.app" to Applications folder

## Database Synchronization

Sync with remote server (spectrum.pmel.noaa.gov):

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

**Requirements:**
- SSH key configured for user `lake`
- Access to spectrum.pmel.noaa.gov

## Troubleshooting

### Issue: "command not found: conda"

**Solution:** Conda not in PATH
```bash
# Add to ~/.zshrc or ~/.bash_profile
export PATH="/usr/local/anaconda3/bin:$PATH"

# Or if using Apple Silicon Mac:
export PATH="/opt/homebrew/anaconda3/bin:$PATH"

# Reload shell
source ~/.zshrc
```

### Issue: "No module named 'streamlit'"

**Solution:** Activate environment first
```bash
conda activate cruise_logs
# or: source venv/bin/activate
```

### Issue: Database file is only a few KB

**Solution:** Git LFS pointer file
```bash
git lfs pull
```

### Issue: Permission denied on database

**Solution:** Check file permissions
```bash
ls -l Cruise_Logs.db
chmod 644 Cruise_Logs.db
```

### Issue: Port 8501 already in use

**Solution:** Streamlit auto-selects next port (8502, 8503, etc.)

Or kill existing process:
```bash
lsof -ti:8501 | xargs kill
```

### Issue: Excel import fails

**Solution:** Install Excel support
```bash
pip install xlrd openpyxl
```

### Issue: "xcrun: error" on Git operations

**Solution:** Install Xcode Command Line Tools
```bash
xcode-select --install
```

### Issue: Homebrew not working on Apple Silicon

**Solution:** Use correct path
```bash
# Apple Silicon (M1/M2/M3)
eval "$(/opt/homebrew/bin/brew shellenv)"

# Intel Macs
eval "$(/usr/local/bin/brew shellenv)"
```

## macOS-Specific Notes

- **Default shell:** zsh (macOS Catalina+) - use `~/.zshrc`
- **Older macOS:** bash - use `~/.bash_profile`
- **Apple Silicon:** Some packages may need ARM64 versions
- **File paths:** Case-sensitive by default (but HFS+ is case-insensitive)
- **Python:** macOS includes Python 2.7, but you need Python 3.9+

## Network Access

To access from other computers on your network:

```bash
# Get your IP address
ifconfig | grep "inet " | grep -v 127.0.0.1

# Run with network access
streamlit run cruise_form.py --server.address 0.0.0.0

# Access from other computers:
# http://<your-ip>:8501
```

## Updating the Repository

```bash
cd ~/Github/Cruise_Logs

# Pull latest code
git pull origin main

# Pull LFS files
git lfs pull

# Update packages if needed
pip install --upgrade -r requirements.txt
```

## Conda Environment Management

```bash
# List environments
conda env list

# Activate environment
conda activate cruise_logs

# Deactivate environment
conda deactivate

# Export environment
conda env export > environment_macos.yml

# Remove environment
conda env remove -n cruise_logs

# Update packages
conda update --all
```

## SSH Key Setup (for GitHub)

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Start ssh-agent
eval "$(ssh-agent -s)"

# Add key to ssh-agent
ssh-add ~/.ssh/id_ed25519

# Copy public key to clipboard
pbcopy < ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH and GPG keys → New SSH key
# Paste the key and save

# Test connection
ssh -T git@github.com
```

## Performance Tips

- **Use conda** for better package management
- **Close unused Streamlit instances** to free ports
- **Database backups:** Git commits or manual copies
- **Large datasets:** Use SQLite indexes for faster queries

## Development Tips

### Run in Development Mode

```bash
# Run with auto-reload on file changes
streamlit run cruise_form.py --server.runOnSave true
```

### Database Queries

```bash
# Open database
sqlite3 Cruise_Logs.db

# Useful commands
.tables
.schema deployment
SELECT COUNT(*) FROM cruise;
.quit
```

### Check Logs

```bash
# Streamlit logs location
~/Library/Application Support/streamlit/logs/

# View most recent log
tail -f ~/Library/Application\ Support/streamlit/logs/streamlit.log
```

## Backup Strategy

### Regular Backups

```bash
# Create timestamped backup
cp Cruise_Logs.db "Cruise_Logs_backup_$(date +%Y%m%d_%H%M%S).db"

# Or use sqlite3
sqlite3 Cruise_Logs.db ".backup 'backup.db'"

# Backup to Time Machine
# (ensure ~/Github/Cruise_Logs is included)
```

### Git Backups

```bash
# Commit database changes
git add Cruise_Logs.db
git commit -m "Database update"
git push origin main
```

## Quick Reference

```bash
# Start workflow
cd ~/Github/Cruise_Logs
conda activate cruise_logs
streamlit run cruise_form.py

# Stop application
# Press Ctrl+C in terminal

# Verify installation
python verify_setup.py

# Import data
python import_release_inventory.py
python import_nylon_inventory.py

# Check database
sqlite3 Cruise_Logs.db ".tables"

# Update repository
git pull && git lfs pull
```

## Additional Resources

- **Main README:** `../README.md`
- **Inventory Docs:** `../README_inventories.md`
- **Windows Setup:** `../windows/SETUP_WINDOWS.md`
- **Streamlit Docs:** https://docs.streamlit.io/
- **SQLite Docs:** https://www.sqlite.org/docs.html

## System Requirements Summary

| Component | Requirement |
|-----------|-------------|
| macOS | 10.15 (Catalina) or later |
| Python | 3.9+ (3.11 recommended) |
| Git | Latest version with LFS |
| Disk Space | ~100 MB for database + code |
| RAM | 2 GB minimum, 4 GB recommended |
| Browser | Safari, Chrome, Firefox, Edge |

## Installation Complete! ✓

Your macOS installation is ready when:
- ✓ `conda activate cruise_logs` works without errors
- ✓ `python verify_setup.py` passes all checks
- ✓ `streamlit run cruise_form.py` opens in browser
- ✓ Inventory searches return data
- ✓ Forms load correctly

**Happy cruising! 🚢**