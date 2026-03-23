# Repository Organization Guide

This document explains the organization of the Cruise_Logs repository, particularly the platform-specific documentation structure.

## 📁 Directory Structure

```
Cruise_Logs/
│
├── 📄 README.md                        # Main project documentation
├── 📄 requirements.txt                 # Python dependencies (cross-platform)
├── 📄 config.py                        # Cross-platform configuration module
├── 📄 verify_setup.py                  # Setup verification script (all platforms)
├── 📄 .gitignore                       # Git ignore rules
├── 📄 .gitattributes                   # Git LFS configuration
│
├── 🗄️ Cruise_Logs.db                   # SQLite database (Git LFS tracked)
├── 📊 Equipment.xls                    # Acoustic releases data
├── 📊 NYLON LENGTHS_MostRecent.xls     # Nylon spools data
│
├── 📝 Application Files (Python/Streamlit)
│   ├── cruise_form.py                  # Main cruise information form
│   ├── dep_form_JSON.py                # Mooring deployment form
│   ├── rec_form_JSON.py                # Mooring recovery form
│   ├── repair_form_JSON.py             # Equipment repair form
│   ├── adcp_dep_form.py                # ADCP deployment form
│   ├── adcp_rec_form.py                # ADCP recovery form
│   ├── release_inventory_search.py     # Release inventory search
│   ├── nylon_inventory_search.py       # Nylon inventory search
│   └── db_sync2.py                     # Database synchronization utility
│
├── 🔄 Import Scripts
│   ├── import_release_inventory.py     # Import Equipment.xls
│   ├── import_nylon_inventory.py       # Import NYLON LENGTHS_MostRecent.xls
│   ├── import_dep.py                   # Import deployment XML
│   ├── import_rec.py                   # Import recovery XML
│   ├── import_repair.py                # Import repair XML
│   ├── import_adcp_dep.py              # Import ADCP deployment XML
│   └── import_adcp_rec.py              # Import ADCP recovery XML
│
├── 📖 General Documentation
│   ├── README_inventories.md           # Inventory systems overview
│   ├── README_release_inventory.md     # Release inventory details
│   └── README_nylon_inventory.md       # Nylon inventory details
│
├── 🍎 macos/                           # macOS-specific files
│   ├── README.md                       # macOS quick reference
│   └── SETUP_MACOS.md                  # Complete macOS setup guide
│
└── 🪟 windows/                         # Windows-specific files
    ├── README.md                       # Windows quick reference
    ├── SETUP_WINDOWS.md                # Complete Windows setup guide
    ├── WINDOWS_INSTALL_CHECKLIST.md   # Step-by-step checklist
    ├── GITHUB_SETUP.md                 # Git repository setup
    ├── environment_windows.yml         # Conda environment specification
    └── run_cruise_form.bat             # Windows batch launcher
```

## 🎯 Platform-Specific Documentation

### macOS Users → [`macos/`](macos/)

**Files:**
- `SETUP_MACOS.md` - Complete installation guide for macOS
- `README.md` - Quick reference and overview

**Key Topics:**
- Homebrew installation
- Git and Git LFS setup
- Anaconda or venv configuration
- Terminal aliases and shortcuts
- Automator app creation
- macOS-specific troubleshooting

**Quick Start:**
```bash
cd ~/Github
git clone git@github.com:blake1237/Cruise_Logs.git
cd Cruise_Logs
# Follow macos/SETUP_MACOS.md
```

### Windows Users → [`windows/`](windows/)

**Files:**
- `SETUP_WINDOWS.md` - Complete installation guide for Windows
- `WINDOWS_INSTALL_CHECKLIST.md` - Interactive checklist format
- `GITHUB_SETUP.md` - Git repository setup and SSH configuration
- `environment_windows.yml` - Conda environment file
- `run_cruise_form.bat` - Batch file launcher
- `README.md` - Quick reference and overview

**Key Topics:**
- Anaconda installation on Windows
- Git and Git LFS setup for Windows
- Path configuration for `C:\Cruise_Logs`
- Desktop shortcuts
- Batch file usage
- Windows-specific troubleshooting

**Quick Start:**
```cmd
cd C:\
git clone git@github.com:blake1237/Cruise_Logs.git
cd Cruise_Logs
# Follow windows/SETUP_WINDOWS.md
```

## 📚 Documentation Guide

### Where to Start?

1. **New to the system?** → Read main [`README.md`](README.md)
2. **Installing on macOS?** → Go to [`macos/SETUP_MACOS.md`](macos/SETUP_MACOS.md)
3. **Installing on Windows?** → Go to [`windows/WINDOWS_INSTALL_CHECKLIST.md`](windows/WINDOWS_INSTALL_CHECKLIST.md)
4. **Setting up Git?** → See [`windows/GITHUB_SETUP.md`](windows/GITHUB_SETUP.md)
5. **Need inventory info?** → Read [`README_inventories.md`](README_inventories.md)

### Documentation Hierarchy

```
Main README.md
    ├── Platform Setup
    │   ├── macos/SETUP_MACOS.md
    │   └── windows/SETUP_WINDOWS.md
    │       └── windows/WINDOWS_INSTALL_CHECKLIST.md
    │
    ├── Repository Setup
    │   └── windows/GITHUB_SETUP.md
    │
    └── Feature Documentation
        ├── README_inventories.md
        ├── README_release_inventory.md
        └── README_nylon_inventory.md
```

## 🔧 Cross-Platform Files

These files work on **both** macOS and Windows:

| File | Purpose |
|------|---------|
| `config.py` | Auto-detects OS and sets correct paths |
| `verify_setup.py` | Checks installation on any platform |
| `requirements.txt` | Python packages (platform-independent) |
| All `.py` application files | Run on any OS with Python |

## 🗂️ Why Separate Directories?

**Benefits of the `macos/` and `windows/` structure:**

1. **Clarity** - Clear separation of platform-specific instructions
2. **Organization** - Easier to find relevant documentation
3. **Maintenance** - Update one platform without affecting the other
4. **Scalability** - Easy to add Linux documentation later
5. **Clean Root** - Main directory stays uncluttered

## 📋 File Purpose Quick Reference

### Root Level Files

| Category | Files | Purpose |
|----------|-------|---------|
| **Database** | `Cruise_Logs.db` | Main SQLite database (Git LFS) |
| **Data Sources** | `Equipment.xls`, `NYLON LENGTHS_MostRecent.xls` | Excel inventory data |
| **Forms** | `cruise_form.py`, `dep_form_JSON.py`, etc. | Streamlit web forms |
| **Search** | `*_inventory_search.py` | Inventory search applications |
| **Import** | `import_*.py` | Data import scripts |
| **Config** | `config.py`, `requirements.txt` | Configuration files |
| **Verification** | `verify_setup.py` | Setup checker |
| **Sync** | `db_sync2.py` | Remote database sync |
| **Git** | `.gitignore`, `.gitattributes` | Git configuration |

### macOS Directory

| File | Purpose |
|------|---------|
| `SETUP_MACOS.md` | Complete macOS installation guide |
| `README.md` | Quick start for macOS users |

### Windows Directory

| File | Purpose |
|------|---------|
| `SETUP_WINDOWS.md` | Complete Windows installation guide |
| `WINDOWS_INSTALL_CHECKLIST.md` | Step-by-step checklist |
| `GITHUB_SETUP.md` | Git and GitHub setup |
| `environment_windows.yml` | Conda environment file |
| `run_cruise_form.bat` | Batch launcher script |
| `README.md` | Quick start for Windows users |

## 🚀 Typical Workflows

### First-Time Setup (macOS)
1. Read `macos/SETUP_MACOS.md`
2. Clone repository
3. Run `verify_setup.py`
4. Start using applications

### First-Time Setup (Windows)
1. Read `windows/WINDOWS_INSTALL_CHECKLIST.md` (follow step-by-step)
2. Refer to `windows/SETUP_WINDOWS.md` for details
3. Run `verify_setup.py`
4. Create desktop shortcut with `windows/run_cruise_form.bat`
5. Start using applications

### Daily Usage (Any Platform)
1. Activate environment: `conda activate cruise_logs`
2. Navigate to repository
3. Run desired application: `streamlit run cruise_form.py`

### Updating Repository (Any Platform)
1. `git pull origin main`
2. `git lfs pull`
3. `pip install --upgrade -r requirements.txt`

## 🔍 Finding What You Need

### "I need to install on Windows"
→ [`windows/WINDOWS_INSTALL_CHECKLIST.md`](windows/WINDOWS_INSTALL_CHECKLIST.md)

### "I need to install on macOS"
→ [`macos/SETUP_MACOS.md`](macos/SETUP_MACOS.md)

### "How do I clone the repository?"
→ [`windows/GITHUB_SETUP.md`](windows/GITHUB_SETUP.md) (works for both platforms)

### "What is this system?"
→ Main [`README.md`](README.md)

### "How do I search the inventory?"
→ [`README_inventories.md`](README_inventories.md)

### "Something isn't working"
→ Run `verify_setup.py` and check platform-specific SETUP guide

### "I want to create a shortcut (Windows)"
→ [`windows/SETUP_WINDOWS.md`](windows/SETUP_WINDOWS.md) - Section on shortcuts

### "I want to create an alias (macOS)"
→ [`macos/SETUP_MACOS.md`](macos/SETUP_MACOS.md) - Section on aliases

## 📦 What Gets Committed to Git?

### Tracked Files
- ✅ All `.py` Python files
- ✅ All `.md` documentation
- ✅ `requirements.txt`
- ✅ `config.py`
- ✅ `.gitignore`, `.gitattributes`
- ✅ `Cruise_Logs.db` (via Git LFS)
- ✅ Excel files (`.xls`)
- ✅ Conda environment files (`.yml`)
- ✅ Batch files (`.bat`)

### Ignored Files (see `.gitignore`)
- ❌ `__pycache__/`
- ❌ `*.pyc`
- ❌ Virtual environments (`venv/`, `env/`)
- ❌ OS files (`.DS_Store`, `Thumbs.db`)
- ❌ SQLite temporary files (`*.db-journal`)
- ❌ Excel temporary files (`~$*.xls`)
- ❌ Log files

## 🎓 Best Practices

1. **Use platform-specific docs** - Don't try to use Windows instructions on macOS
2. **Run verify_setup.py** - After installation and when troubleshooting
3. **Use config.py** - When writing new code, import from `config.py`
4. **Keep environments separate** - Use dedicated conda environment
5. **Git LFS** - Always run `git lfs pull` after cloning or pulling
6. **Read the README** - Each directory has a README with quick reference

## 🔄 Future Expansion

Potential additions to the structure:

```
Cruise_Logs/
├── linux/                     # Future: Linux documentation
│   └── SETUP_LINUX.md
├── docker/                    # Future: Docker configuration
│   ├── Dockerfile
│   └── docker-compose.yml
└── docs/                      # Future: Additional documentation
    ├── API.md
    ├── DATABASE_SCHEMA.md
    └── CONTRIBUTING.md
```

## 📞 Support

- **General questions** → See main `README.md`
- **Installation issues** → See platform-specific SETUP guide
- **Git/GitHub issues** → See `windows/GITHUB_SETUP.md`
- **Bugs or features** → Create GitHub issue
- **Verification** → Run `python verify_setup.py`

---

**Last Updated:** January 2025  
**Repository:** https://github.com/blake1237/Cruise_Logs