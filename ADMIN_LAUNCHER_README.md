# 🔐 Admin Launcher - Documentation

**Password-Protected Administrative Tools for Cruise Logs Database Management**

---

## 📋 Overview

The **Admin Launcher** is a secure, password-protected application for performing administrative database operations. It provides a GUI interface for running import scripts that modify the database.

**Features:**
- 🔐 Password-protected access
- 🎨 Modern CustomTkinter interface
- 📊 Real-time output console
- ⚠️ Safe execution of import scripts
- 🌙 Dark/Light theme support
- 📁 File browser for XML imports
- ✅ Cross-platform (Windows, macOS, Linux)

---

## 🔑 Access & Authentication

### Default Password

**Password:** `admin123`

⚠️ **Important:** Change this password before deploying to production!

### Launching Admin Tools

**macOS:**
```bash
cd ~/Github/Cruise_Logs
python admin_launcher.py
```

**Windows:**
```cmd
cd C:\Users\blake\Cruise_Logs
python admin_launcher.py
```

A password dialog will appear. Enter the password to access admin tools.

---

## 🛠️ Available Tools

The admin launcher provides buttons for the following import operations:

### Data Import Tools

| Tool | Icon | Description | Requires File |
|------|------|-------------|---------------|
| **Import Deployment** | ⬇️ | Import deployment XML data | Yes (.xml) |
| **Import Recovery** | ⬆️ | Import recovery XML data | Yes (.xml) |
| **Import Repair** | 🔧 | Import repair XML data | Yes (.xml) |
| **Import ADCP Deploy** | 📡 | Import ADCP deployment XML | Yes (.xml) |
| **Import ADCP Recovery** | 📥 | Import ADCP recovery XML | Yes (.xml) |
| **Import Releases** | 🔍 | Import Equipment.xls (569 releases) | No |
| **Import Nylon** | 🧵 | Import NYLON LENGTHS_MostRecent.xls | No |

### How Each Tool Works

**XML Import Tools:**
- Click the button
- File browser opens
- Select the XML file to import
- Import runs with real-time output
- Results shown in output console

**Excel Import Tools:**
- Click the button
- Import runs immediately (uses files in directory)
- Progress shown in output console
- Table replaced with new data

---

## 💻 Using the Admin Launcher

### Step 1: Launch and Authenticate

1. Run `python admin_launcher.py`
2. Enter password: `admin123`
3. Click "OK" or press Enter

### Step 2: Select Import Tool

1. Click the button for the import you want to run
2. If required, select the XML file in the file browser
3. Watch the output console for progress

### Step 3: Review Output

- ✅ Green messages = Success
- ❌ Red messages = Errors
- ⚠️ Orange messages = Warnings
- Console shows all script output in real-time

### Step 4: Clear or Exit

- Click "🗑️ Clear Output" to clear the console
- Click "Exit" to close when done

---

## 🔒 Changing the Password

### Method 1: Using Python

```python
import hashlib

# Your new password
new_password = "your_secure_password_here"

# Generate hash
password_hash = hashlib.sha256(new_password.encode()).hexdigest()
print(password_hash)
```

### Method 2: Command Line

```bash
python -c "import hashlib; print(hashlib.sha256(b'your_new_password').hexdigest())"
```

### Method 3: Edit the File

1. Open `admin_launcher.py` in a text editor
2. Find line ~22: `PASSWORD_HASH = "240be518..."`
3. Replace the hash with your new hash
4. Save the file

**Example:**
```python
# Line 22 in admin_launcher.py
PASSWORD_HASH = "your_new_hash_here"
```

---

## 🎨 Interface Features

### Main Window Layout

```
┌─────────────────────────────────────────────┐
│  🔐 Admin Tools - Database Management      │
│  Import data and manage database tables     │
│  ⚠️ Caution: These tools modify database   │
├─────────────────────────────────────────────┤
│                                             │
│  [⬇️ Deploy]  [⬆️ Recovery]  [🔧 Repair]   │
│  [📡 ADCP D]  [📥 ADCP R]   [🔍 Releases] │
│  [🧵 Nylon]                                 │
│                                             │
├─────────────────────────────────────────────┤
│  📋 Output Console                          │
│  ┌───────────────────────────────────────┐ │
│  │ Script output appears here...         │ │
│  │                                       │ │
│  └───────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ [🗑️ Clear] [🌙 Theme] [Exit]               │
└─────────────────────────────────────────────┘
```

### Output Console Features

- **Real-time output** - See script execution live
- **Scrollable** - Handles long outputs
- **Monospace font** - Easy to read console output
- **Auto-scroll** - Follows output as it appears
- **Clear button** - Reset console when needed

---

## ⚠️ Security Considerations

### Password Storage

- Password is stored as SHA-256 hash (not plaintext)
- Hash is stored in the Python file
- **Not secure for highly sensitive environments**
- Good enough for preventing casual access

### Recommended Practices

1. ✅ **Change default password** immediately
2. ✅ **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
3. ✅ **Don't share password** with unauthorized users
4. ✅ **Keep backups** of database before running imports
5. ✅ **Test imports** on sample data first

### What This Protects Against

- ✅ Casual users accidentally running admin tools
- ✅ Unauthorized modifications to database
- ✅ Accidental data imports

### What This Does NOT Protect Against

- ❌ Determined attacker with file access (they can read the hash)
- ❌ Someone who can edit Python files
- ❌ Database-level security issues

---

## 🔧 Troubleshooting

### "No module named 'customtkinter'"

```bash
pip install customtkinter
```

### Password Not Working

1. Check for typos (passwords are case-sensitive)
2. Verify you haven't changed the hash incorrectly
3. Reset to default password (see "Changing Password" section)

### Import Script Not Found

- Ensure you're running from the Cruise_Logs directory
- Check that import_*.py files exist

### XML File Not Importing

1. Verify XML file is valid FileMaker Pro export
2. Check file extension is .xml
3. Review output console for specific errors

### Database Errors

- Ensure `Cruise_Logs.db` exists in current directory
- Check database file permissions
- Close other applications using the database

### Window Too Small

- Window is resizable - drag corners to resize
- Minimum size: 800x600

---

## 📊 Import Script Details

### XML-Based Imports

**Deployment Import (`import_dep.py`)**
- Imports to: `deployments_normalized` table
- Format: FileMaker Pro XML
- Fields: Mooring info, location, instruments, etc.

**Recovery Import (`import_rec.py`)**
- Imports to: `recovery` table
- Format: FileMaker Pro XML
- Fields: Recovery details, instrument status, etc.

**Repair Import (`import_repair.py`)**
- Imports to: `repair` table
- Format: FileMaker Pro XML
- Fields: Repair records, maintenance logs

**ADCP Imports (`import_adcp_dep.py`, `import_adcp_rec.py`)**
- Imports to: `adcp_dep` and `adcp_rec2` tables
- Format: FileMaker Pro XML
- Fields: ADCP-specific deployment/recovery data

### Excel-Based Imports

**Release Inventory (`import_release_inventory.py`)**
- Imports: `Equipment.xls`
- Imports to: `release_inventory` table
- Records: ~569 acoustic release instruments
- Action: **REPLACES** entire table

**Nylon Inventory (`import_nylon_inventory.py`)**
- Imports: `NYLON LENGTHS_MostRecent.xls`
- Imports to: `nylon_inventory` table
- Records: ~1,723 nylon spool records
- Action: **REPLACES** entire table

⚠️ **Note:** Excel imports replace the entire table!

---

## 🎯 Best Practices

### Before Running Imports

1. ✅ **Backup the database**
   ```bash
   cp Cruise_Logs.db Cruise_Logs_backup_$(date +%Y%m%d).db
   ```

2. ✅ **Verify source files** are correct and up-to-date

3. ✅ **Close other applications** using the database

4. ✅ **Check disk space** is adequate

### During Imports

1. ✅ **Watch the output console** for errors
2. ✅ **Don't close the admin launcher** during import
3. ✅ **Wait for completion** message

### After Imports

1. ✅ **Review import summary** in output console
2. ✅ **Verify record counts** match expectations
3. ✅ **Test database queries** to confirm data integrity
4. ✅ **Check applications** still work correctly

---

## 📝 Quick Reference

### Launch Commands

```bash
# macOS
cd ~/Github/Cruise_Logs && python admin_launcher.py

# Windows
cd C:\Users\blake\Cruise_Logs && python admin_launcher.py
```

### Default Credentials

- **Password:** `admin123`
- **Hash:** `240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9`

### Generate New Password Hash

```bash
python -c "import hashlib; print(hashlib.sha256(b'YourNewPassword').hexdigest())"
```

### Common Import Files

- `Equipment.xls` - Release inventory
- `NYLON LENGTHS_MostRecent.xls` - Nylon inventory
- `*.xml` - Deployment/recovery/repair data

---

## 🆘 Support

### Check These First

1. Run verification script: `python verify_setup.py`
2. Check database exists: `ls -la Cruise_Logs.db`
3. Verify imports exist: `ls -la import_*.py`
4. Review output console for specific errors

### Documentation

- **Main README:** `README.md`
- **Windows Setup:** `windows/SETUP_WINDOWS.md`
- **Launcher Guide:** `LAUNCHER_GUIDE.md`

### File Locations

- **Admin Launcher:** `admin_launcher.py`
- **Import Scripts:** `import_*.py`
- **Database:** `Cruise_Logs.db`
- **Excel Files:** `Equipment.xls`, `NYLON LENGTHS_MostRecent.xls`

---

## ✨ Summary

The Admin Launcher provides a **secure, easy-to-use interface** for database administrative tasks:

- 🔐 **Password-protected** - Prevents unauthorized access
- 🎨 **Modern GUI** - Clean, professional interface
- 📊 **Real-time feedback** - See what's happening
- ⚠️ **Safe operations** - Controlled import environment
- 🌙 **Theme support** - Light or dark mode
- 📁 **File selection** - Easy XML file browsing

**Perfect for field computer administrators who need to import data safely!**

---

**Version:** 1.0  
**Password:** `admin123` (change this!)  
**Platform:** Cross-platform (Windows, macOS, Linux)  
**Last Updated:** January 2025