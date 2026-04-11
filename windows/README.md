# Cruise_Logs Windows Installation & Usage

This directory contains Windows-specific installation scripts and documentation for the Cruise_Logs project.

## 🚀 Quick Start

### Fastest Way (Recommended for Most Users)
```powershell
# 1. Right-click PowerShell → "Run as Administrator"
# 2. Run this command:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
cd C:\Cruise_Logs\windows
.\install.ps1
```

**That's it!** The script will:
- Install Anaconda and Git (if needed)
- Clone the repository
- Create conda environment
- Install Python packages
- Download the database
- Create desktop shortcuts

### For Developers (More Control)
```cmd
cd C:\Cruise_Logs\windows
Makefile.bat install
```

### Or Run Individual Commands
```cmd
Makefile.bat help        # Show all available commands
Makefile.bat run-cruise  # Start the main application
```

---

## 📁 Files in This Directory

### Installation Scripts
| File | Purpose | Usage |
|------|---------|-------|
| **install.ps1** | PowerShell automated installer | `.\install.ps1` |
| **install.bat** | Batch wrapper for PowerShell | Double-click or run |
| **Makefile.bat** | Make-style task runner | `Makefile.bat [target]` |

### Documentation
| File | Purpose |
|------|---------|
| **WINDOWS_INSTALLER_GUIDE.md** | Complete installation guide with all options |
| **QUICK_REFERENCE.md** | Quick cheat sheet for commands |
| **SETUP_WINDOWS.md** | Original detailed setup guide |
| **WINDOWS_INSTALL_CHECKLIST.md** | Step-by-step checklist |
| **GITHUB_SETUP.md** | Git repository setup guide |
| **README.md** | This file |

---

## 📖 Installation Methods

### Method 1: PowerShell Installer (Easiest) ⭐

**Best for:** First-time users, full automation, non-technical users

```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File install.ps1
```

**What it does:** Everything in one script
- ✅ Checks for prerequisites
- ✅ Installs Anaconda if needed
- ✅ Installs Git and Git LFS
- ✅ Clones repository
- ✅ Creates conda environment
- ✅ Installs dependencies
- ✅ Pulls database
- ✅ Creates desktop shortcuts
- ✅ Verifies installation

**Time:** 10-20 minutes  
**Difficulty:** Easy  
**Best for:** Most users

---

### Method 2: Makefile.bat (Flexible) 

**Best for:** Developers, step-by-step control, individual tasks

```cmd
cd C:\Cruise_Logs\windows
Makefile.bat [target]
```

**Common targets:**

```cmd
Makefile.bat help              # Show all commands
Makefile.bat install           # Full installation
Makefile.bat setup             # Setup without prerequisites
Makefile.bat conda-env         # Create environment only
Makefile.bat install-deps      # Install packages only
Makefile.bat pull-db           # Download database only
Makefile.bat run-cruise        # Start main application
Makefile.bat import-releases   # Import acoustic releases
Makefile.bat import-nylon      # Import nylon spools
Makefile.bat verify            # Verify installation
Makefile.bat clean             # Remove environment
Makefile.bat clean-all         # Remove everything
```

**Time:** 15-30 minutes  
**Difficulty:** Medium  
**Best for:** Developers

---

### Method 3: Manual Setup (Advanced)

**Best for:** Maximum control, troubleshooting, learning

1. Install Anaconda: https://www.anaconda.com/download/
2. Install Git: https://git-scm.com/download/win
3. Clone repository:
   ```cmd
   git clone https://github.com/blake1237/Cruise_Logs.git
   cd Cruise_Logs
   ```
4. Create environment:
   ```cmd
   conda create -n cruise_logs python=3.11 -y
   conda activate cruise_logs
   ```
5. Install packages:
   ```cmd
   pip install -r requirements.txt
   ```
6. Get database:
   ```cmd
   git lfs pull
   ```
7. Run application:
   ```cmd
   streamlit run cruise_form.py
   ```

**Time:** 20-40 minutes  
**Difficulty:** Advanced  
**Best for:** Developers and troubleshooting

---

## 🎯 After Installation

### Running the Application

**Option 1: Desktop Shortcut (Easiest)**
- Look for "Cruise Logs - Main Form" on your desktop
- Double-click to launch

**Option 2: Command Line**
```cmd
conda activate cruise_logs
cd C:\Cruise_Logs
streamlit run cruise_form.py
```

**Option 3: Makefile**
```cmd
Makefile.bat run-cruise
```

### Importing Data

**Import acoustic release inventory:**
```cmd
Makefile.bat import-releases
```

**Import nylon spool inventory:**
```cmd
Makefile.bat import-nylon
```

### Updating Database

```cmd
cd C:\Cruise_Logs
git lfs pull
```

---

## 📋 Available Applications

Once installed, you can run any of these Streamlit applications:

| Application | Command | Purpose |
|-------------|---------|---------|
| Main Cruise Form | `streamlit run cruise_form.py` | Record cruise information |
| Deployment Form | `streamlit run dep_form_JSON.py` | Record mooring deployments |
| Recovery Form | `streamlit run rec_form_JSON.py` | Record mooring recoveries |
| Repair Form | `streamlit run repair_form_JSON.py` | Record equipment repairs |
| ADCP Deployment | `streamlit run adcp_dep_form.py` | Record ADCP deployments |
| ADCP Recovery | `streamlit run adcp_rec_form.py` | Record ADCP recoveries |
| Release Search | `streamlit run release_inventory_search.py` | Search acoustic releases |
| Nylon Search | `streamlit run nylon_inventory_search.py` | Search nylon spools |

Or use the GUI Launcher:
```cmd
python launcher.py
```

---

## 🔧 System Requirements

### Minimum
- Windows 7 or later
- 2 GB free disk space
- Administrator privileges
- Internet connection (for installation)

### Recommended
- Windows 10 or 11
- 4+ GB free disk space
- Administrator privileges
- Fast internet connection

### Software
- Python 3.11 (installed via Anaconda)
- Git 2.20+
- Git LFS 3.0+

---

## ❓ Troubleshooting

### PowerShell Execution Policy Error
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Anaconda Not Found
- Download from: https://www.anaconda.com/download/
- Install with "Add Anaconda to PATH" checked
- Restart PowerShell/Command Prompt

### Git Not Found
- Download from: https://git-scm.com/download/win
- Install with "Add Git to PATH" checked
- Restart PowerShell/Command Prompt

### Database File Not Found or Too Small
```cmd
cd C:\Cruise_Logs
git lfs pull
```

### ModuleNotFoundError: No module named 'streamlit'
```cmd
conda activate cruise_logs
```
Make sure you activate the conda environment first!

### Port 8501 Already in Use
Streamlit will automatically use the next available port (8502, 8503, etc.). No action needed.

### Verification Script Issues
```cmd
conda activate cruise_logs
cd C:\Cruise_Logs
python verify_setup.py
```

---

## 📚 Documentation Guide

**Choose based on your need:**

| If you want to... | Read this file |
|-------------------|----------------|
| Get started quickly | **QUICK_REFERENCE.md** (this directory) |
| Understand all options | **WINDOWS_INSTALLER_GUIDE.md** (this directory) |
| Follow step-by-step | **WINDOWS_INSTALL_CHECKLIST.md** (this directory) |
| Original detailed guide | **SETUP_WINDOWS.md** (this directory) |
| Git/GitHub setup | **GITHUB_SETUP.md** (this directory) |
| General project info | **../README.md** (project root) |
| Data import help | **../README_inventories.md** |
| Database info | **../README_release_inventory.md**, **../README_nylon_inventory.md** |

---

## 🎓 Learning Path

### For First-Time Users
1. Read: **QUICK_REFERENCE.md**
2. Run: `install.ps1`
3. Run: `Makefile.bat run-cruise`
4. Enter some test data
5. Read: **WINDOWS_INSTALLER_GUIDE.md** (if interested)

### For Developers
1. Read: **WINDOWS_INSTALLER_GUIDE.md**
2. Read: **QUICK_REFERENCE.md**
3. Run: `Makefile.bat install`
4. Customize as needed
5. Create custom targets in `Makefile.bat`

### For System Administrators
1. Review: `install.ps1`
2. Customize for your environment
3. Test on single machine
4. Deploy to multiple machines
5. Monitor using `verify_setup.py`

---

## 🚨 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "PowerShell is disabled" | Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| "Anaconda not found" | Install from https://www.anaconda.com/download/ |
| "Git not found" | Install from https://git-scm.com/download/win |
| "Database is tiny" | Run: `git lfs pull` |
| "Port already in use" | Streamlit automatically uses next port (8502, 8503, etc.) |
| "Module not found" | Activate conda environment: `conda activate cruise_logs` |
| "Permission denied" | Run Command Prompt/PowerShell as Administrator |
| "Can't clone repository" | Check internet connection, try HTTPS instead of SSH |

---

## 📞 Getting Help

1. **Quick answers:** See **QUICK_REFERENCE.md**
2. **Detailed help:** See **WINDOWS_INSTALLER_GUIDE.md**
3. **Step-by-step:** See **WINDOWS_INSTALL_CHECKLIST.md**
4. **Verify setup:** Run `python verify_setup.py`
5. **Check logs:** Review error messages in terminal

---

## 🔄 Installation Comparison

| Aspect | PowerShell | Makefile | Manual |
|--------|-----------|----------|--------|
| Setup time | 10-20 min | 15-30 min | 20-40 min |
| Difficulty | Easy | Medium | Hard |
| Automation | Full | Partial | None |
| Control | Low | Medium | High |
| Learning | Low | Medium | High |
| Error recovery | Good | Very good | Excellent |
| Customization | Limited | Good | Unlimited |
| Best for | Most users | Developers | Learning |

---

## 🔗 Important Links

| Resource | Link |
|----------|------|
| Anaconda | https://www.anaconda.com/download/ |
| Git | https://git-scm.com/download/win |
| Git LFS | https://git-lfs.github.com/ |
| Repository | https://github.com/blake1237/Cruise_Logs |
| Streamlit | https://streamlit.io/ |
| Python | https://www.python.org/ |

---

## 📝 Version Information

| Component | Version |
|-----------|---------|
| Created | 2024 |
| Tested on | Windows 10, Windows 11 |
| Python | 3.11 |
| Anaconda | Latest |
| Git | 2.43+ |
| Git LFS | 3.4+ |
| Streamlit | 1.28+ |

---

## 🎉 What's Included

### Scripts
- ✅ Automated PowerShell installer
- ✅ Makefile-style batch task runner
- ✅ Verification and setup scripts
- ✅ Data import utilities

### Documentation
- ✅ Quick reference guide
- ✅ Complete installation guide
- ✅ Step-by-step checklist
- ✅ Troubleshooting guide
- ✅ GitHub setup guide

### Applications
- ✅ Web-based forms (Streamlit)
- ✅ Search and inventory apps
- ✅ Data import tools
- ✅ GUI launcher

---

## 📊 System Architecture

```
Windows Environment
├── Anaconda (Python distribution)
│   ├── Base environment (system Python)
│   └── cruise_logs environment
│       ├── Python 3.11
│       ├── Streamlit
│       ├── Pandas
│       ├── SQLite
│       └── Other packages
├── Git & Git LFS (version control)
├── Cruise_Logs Repository
│   ├── Python scripts
│   ├── SQLite database
│   ├── Excel data files
│   └── Configuration
└── Desktop Shortcuts
    ├── Main Form
    ├── Launcher
    └── ...
```

---

## 🎯 Next Steps

### After Installation
1. Launch the application
2. Verify data import functionality
3. Create desktop shortcuts (if not done automatically)
4. Test with sample data
5. Start using for real work

### For Development
1. Review the codebase
2. Check out the Python scripts
3. Understand the database schema
4. Create custom targets in Makefile.bat
5. Contribute improvements

### For Maintenance
1. Keep Anaconda updated: `conda update anaconda`
2. Keep packages updated: `pip install --upgrade -r requirements.txt`
3. Back up the database regularly
4. Pull latest changes: `git pull && git lfs pull`

---

## 📄 File Structure

```
Cruise_Logs/windows/
├── install.ps1                      # PowerShell installer (recommended)
├── install.bat                      # Batch wrapper
├── Makefile.bat                     # Task-based runner
├── README.md                        # This file
├── QUICK_REFERENCE.md               # Command cheat sheet
├── WINDOWS_INSTALLER_GUIDE.md       # Complete guide
├── SETUP_WINDOWS.md                 # Original setup guide
├── WINDOWS_INSTALL_CHECKLIST.md     # Step-by-step checklist
├── GITHUB_SETUP.md                  # Git setup guide
└── environment_windows.yml          # Conda environment file
```

---

## 💡 Tips & Tricks

### Speed Up Installation
- Use PowerShell installer for fastest setup
- Install Anaconda before running installer
- Use wired internet connection

### Troubleshoot Effectively
- Always run verification script first
- Check error messages carefully
- Read the full guide before asking for help
- Use Makefile.bat for step-by-step control

### Optimize for Development
- Create custom Makefile.bat targets
- Use conda for environment isolation
- Keep requirements.txt updated
- Use version control for changes

### Keep It Running
- Create system restore point before installation
- Back up database regularly
- Update Python packages monthly
- Monitor disk space usage

---

## 🆘 Support Resources

### Built-in Help
- Run `Makefile.bat help` for available commands
- Run `python verify_setup.py` to check installation
- Review error messages in terminal output

### Documentation
- Check README.md files in each directory
- Review inline code comments
- Read GitHub issues for common problems

### External Resources
- Anaconda docs: https://docs.anaconda.com/
- Git docs: https://git-scm.com/book/
- Streamlit docs: https://docs.streamlit.io/
- Python docs: https://docs.python.org/

---

## ✨ Summary

**To get started:**
1. Choose your installation method (PowerShell recommended)
2. Follow the instructions in this README
3. Run the installer
4. Use desktop shortcuts or `Makefile.bat run-cruise` to start
5. Refer to full documentation if you need help

**Need more details?** See **WINDOWS_INSTALLER_GUIDE.md** or **QUICK_REFERENCE.md**

---

**Created:** 2024  
**Platform:** Windows 7+  
**For:** Cruise_Logs Project  
**Latest:** Version 1.0