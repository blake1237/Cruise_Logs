# Cruise Logs Launcher Guide

This guide explains how to use the Desktop Launcher for the Cruise Logs Management System.

## 📋 Overview

The **Cruise Logs Desktop Launcher** is a modern, native desktop application that provides a clean, attractive interface with buttons to launch:

- 🚢 Cruise Form
- ⬇️ Deployment Form
- ⬆️ Recovery Form
- 🔧 Repair Form
- 📡 ADCP Deployment
- 📥 ADCP Recovery

## 🎨 Desktop Launcher Features

### Visual Design
- ✅ **Native desktop application** - No browser required
- ✅ **Modern, attractive UI** - Professional appearance
- ✅ **Dark/Light theme support** - Toggle between modes
- ✅ **Fast and responsive** - Instant button clicks
- ✅ **Window management** - Centered on screen, resizable
- ✅ **Large colorful buttons** - 2x3 grid layout with icons
- ✅ **Hover effects** - Visual feedback on interaction
- ✅ **Process tracking** - Shows running applications
- ✅ **One-click controls** - Launch, stop, and manage apps easily

### Main Window Features

**Header Section:**
- Large title: "🚢 Cruise Logs Management System"
- Subtitle: "Select an application to launch"

**Application Buttons (2x3 grid):**
- Each button shows:
  - Large icon (emoji)
  - Application name
  - Brief description
  - Custom color scheme
- Hover effect changes button color
- Click to launch the application

**Status Bar:**
- Shows current activity
- Success messages (green)
- Error messages (red)
- Warning messages (orange)
- Auto-clears after 5 seconds

**Footer Controls:**
- 🌙 Toggle Theme - Switch between dark and light modes
- ❌ Close All Apps - Stop all running applications
- Exit Launcher - Close the launcher

## 🚀 Installation

### Prerequisites

- Anaconda/Conda environment (`cruise_logs`)
- Python 3.9 or higher
- Cruise_Logs repository installed

### Install CustomTkinter

```cmd
# Activate your conda environment
conda activate cruise_logs

# Install CustomTkinter and psutil
pip install customtkinter psutil
```

**What gets installed:**
- `customtkinter` - Modern UI framework (≥5.2.0)
- `psutil` - Process management utilities (≥5.9.0)

### Verify Installation

```cmd
# Test that CustomTkinter is installed
python -c "import customtkinter; print('CustomTkinter installed successfully!')"
```

## 💻 Usage

### Method 1: Batch File (Recommended for Windows)

```cmd
# Navigate to Cruise_Logs
cd C:\Cruise_Logs

# Run the batch file
launch_menu.bat
```

The batch file automatically:
- Activates the conda environment
- Changes to the correct directory
- Checks for CustomTkinter (installs if missing)
- Launches the application

### Method 2: Direct Python Command

```cmd
# Activate environment
conda activate cruise_logs

# Navigate to directory
cd C:\Cruise_Logs

# Run launcher
python launcher.py
```

### Method 3: Desktop Shortcut (Best for Daily Use)

See "Creating Desktop Shortcut" section below.

## 🖥️ Creating Desktop Shortcut

### Windows

**Option A: Using the Batch File (Easiest)**

1. Navigate to `C:\Cruise_Logs`
2. Right-click `launch_menu.bat`
3. Select "Create shortcut"
4. Move the shortcut to your Desktop
5. Rename to "Cruise Logs Launcher" or "Cruise Logs"
6. (Optional) Right-click shortcut → Properties → Change Icon

**Option B: Direct Python Shortcut**

1. Right-click on Desktop → New → Shortcut
2. Enter location (replace `YourUsername` with your Windows username):
   ```
   C:\Users\YourUsername\anaconda3\envs\cruise_logs\python.exe C:\Cruise_Logs\launcher.py
   ```
3. Click "Next"
4. Name it "Cruise Logs Launcher"
5. Click "Finish"
6. (Optional) Change the icon

**Daily Use:**
Just double-click the desktop shortcut to launch!

## 🎯 How to Use the Launcher

### Launching Applications

1. **Start the launcher** (double-click desktop shortcut or run `launch_menu.bat`)
2. **Click a button** to launch that application
   - Example: Click "🚢 Cruise Form" to launch cruise_form.py
3. **Browser opens automatically** to the Streamlit app
4. **Work in the application** as normal
5. **Return to launcher** when you want to open another app or close apps

### Managing Running Applications

**Tracking:**
- Launcher keeps track of which applications are running
- Status bar shows launch confirmations
- Applications run in separate console windows (Windows)

**Stopping Apps:**
- Click "❌ Close All Apps" to stop all running applications
- This terminates all Streamlit processes started from the launcher

**Exiting:**
- Click "Exit Launcher" or close the window
- If apps are running, you'll be prompted to close them first

### Theme Switching

- Click "🌙 Toggle Theme" to switch between dark and light modes
- Default is dark mode
- Preference is not saved (resets on restart)

## 🎨 Customization

You can customize the launcher by editing `launcher.py`:

### Change Default Theme

Find line ~15 and change:

```python
ctk.set_appearance_mode("dark")  # Options: "dark", "light", "system"
```

### Change Color Theme

Find line ~16 and change:

```python
ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"
```

### Change Window Size

Find line ~24 in the `__init__` method:

```python
self.geometry("800x600")  # Change to desired width x height
```

### Modify Button Colors

Find the `apps` list (around line 94) and edit the color values:

```python
"color": "#1f538d"  # Any hex color code
```

### Add Custom Applications

Add new entries to the `apps` list:

```python
{
    "name": "Your App Name",
    "icon": "🎯",  # Any emoji
    "file": "your_app.py",
    "description": "Description here",
    "color": "#hexcolor"
}
```

## 🔧 Troubleshooting

### Installation Issues

**Issue: "No module named 'customtkinter'"**

**Solution:**
```cmd
conda activate cruise_logs
pip install customtkinter
```

**Issue: "No module named 'psutil'"**

**Solution:**
```cmd
pip install psutil
```

**Issue: "Failed to activate conda environment 'cruise_logs'"**

**Solution:**
- Verify environment exists: `conda env list`
- Create environment if missing: See `windows/SETUP_WINDOWS.md`

### Launcher Issues

**Issue: Blank window or immediate crash**

**Solutions:**
1. Update CustomTkinter:
   ```cmd
   pip install --upgrade customtkinter
   ```
2. Check Python version (requires 3.7+):
   ```cmd
   python --version
   ```
3. Run from command line to see error messages

**Issue: "launcher.py not found"**

**Solution:**
```cmd
# Ensure you're in the correct directory
cd C:\Cruise_Logs
dir launcher.py
```

**Issue: Window too small or too large**

**Solution:**
- Window is resizable - drag corners to resize
- Or edit window size in launcher.py (see Customization)

### Application Launch Issues

**Issue: Apps don't launch when clicking buttons**

**Solutions:**
1. Verify you're in Cruise_Logs directory
2. Check that the .py files exist:
   ```cmd
   dir cruise_form.py
   dir dep_form_JSON.py
   ```
3. Ensure conda environment is activated
4. Check error messages in status bar (red text)

**Issue: "cruise_form.py not found" or similar**

**Solution:**
- Navigate to correct directory before launching
- Run from `C:\Cruise_Logs`

**Issue: Browser doesn't open automatically**

**Solution:**
- Streamlit usually opens browser automatically
- If not, check the console window for the URL
- Manually open browser to `http://localhost:8501` (or shown port)

### Process Management Issues

**Issue: "Application is already running" but I don't see it**

**Solution:**
- App may have crashed
- Close launcher and reopen
- Or check Task Manager for Python processes

**Issue: Can't stop applications with "Close All Apps"**

**Solutions:**
1. Check Windows Task Manager for Python/Streamlit processes
2. Manually end processes in Task Manager
3. Restart launcher

**Issue: Multiple instances of same app**

**Solution:**
- Launcher prevents this, but if it happens:
- Use Task Manager to close duplicate processes
- Restart launcher

## 📋 Best Practices

### Daily Workflow

**Morning startup:**
1. Double-click "Cruise Logs Launcher" on desktop
2. Wait for launcher window to appear
3. Click the application you need first

**Working:**
1. Complete your work in the Streamlit app
2. Return to launcher to open another app if needed
3. Multiple apps can run simultaneously

**End of day:**
1. Save all your work in the apps
2. Return to launcher
3. Click "❌ Close All Apps"
4. Click "Exit Launcher"

### Tips

- **Create a desktop shortcut** - Fastest way to start
- **Use "Close All Apps"** - Clean shutdown of all applications
- **Check status bar** - Shows what's happening
- **Theme preference** - Set dark or light based on lighting conditions
- **Keep launcher open** - While working with the apps
- **One launcher instance** - Don't run multiple launchers

## 🔐 Security & Privacy

- Launcher runs entirely on your local computer
- No network connections (except Streamlit apps on localhost)
- All data stays on your machine
- Applications only accessible from `localhost` by default
- No external dependencies beyond Python packages

## 🆘 Getting Help

### Verification

Run the setup verification script:
```cmd
cd C:\Cruise_Logs
python verify_setup.py
```

### Check Environment

```cmd
# List conda environments
conda env list

# Activate environment
conda activate cruise_logs

# Check installed packages
pip list | findstr customtkinter
pip list | findstr psutil
```

### Documentation

- **Windows Setup:** See `windows/SETUP_WINDOWS.md`
- **Main README:** See `README.md`
- **Quick Reference:** See `LAUNCHER_README.md`

### Common Checks

```cmd
# Verify you're in the right directory
cd C:\Cruise_Logs
dir launcher.py

# Verify conda environment is activated
# (should see "(cruise_logs)" in prompt)

# Test Python
python --version

# Test CustomTkinter import
python -c "import customtkinter; print('OK')"
```

## 🎓 Advanced Usage

### Auto-Start on Windows Boot

1. Create desktop shortcut (see above)
2. Press `Win+R`, type `shell:startup`, press Enter
3. Copy the shortcut to the Startup folder
4. Launcher will start automatically when Windows boots

### Pin to Taskbar

1. Create desktop shortcut
2. Right-click the shortcut
3. Select "Pin to taskbar"
4. Quick access from taskbar

### Run from Any Location

The batch file (`launch_menu.bat`) can be run from anywhere:
- It automatically navigates to `C:\Cruise_Logs`
- Activates the correct environment
- Launches the application

## 📦 Files & Structure

### Launcher Files

- `launcher.py` - Main launcher application
- `launch_menu.bat` - Windows batch file launcher
- `LAUNCHER_GUIDE.md` - This comprehensive guide
- `LAUNCHER_README.md` - Quick reference

### Dependencies

Listed in `requirements.txt`:
- `customtkinter>=5.2.0` - UI framework
- `psutil>=5.9.0` - Process management

### Application Files Launched

- `cruise_form.py` - Main cruise form
- `dep_form_JSON.py` - Deployment form
- `rec_form_JSON.py` - Recovery form
- `repair_form_JSON.py` - Repair form
- `adcp_dep_form.py` - ADCP deployment
- `adcp_rec_form.py` - ADCP recovery

## 🔄 Updating

### Update the Launcher

When pulling updates from Git:

```cmd
cd C:\Cruise_Logs
git pull
git lfs pull

# No additional steps needed
# Just restart the launcher if it was running
```

### Update Dependencies

```cmd
conda activate cruise_logs
pip install --upgrade customtkinter psutil
```

## ✨ Summary

### Quick Reference

**Install (one-time):**
```cmd
conda activate cruise_logs
pip install customtkinter psutil
```

**Run:**
```cmd
launch_menu.bat
```

**Or:**
```cmd
python launcher.py
```

**Daily use:**
- Double-click desktop shortcut
- Click button to launch app
- Click "Close All Apps" when done

### Key Features

✅ Modern, attractive interface  
✅ Native desktop application  
✅ Dark/Light theme toggle  
✅ Large, colorful buttons  
✅ Process tracking  
✅ One-click app launching  
✅ Professional appearance  
✅ Fast and responsive  

### Support

For additional help:
- Run `python verify_setup.py`
- Check `windows/SETUP_WINDOWS.md`
- See `README.md` for system overview

---

**Version:** 1.0  
**Last Updated:** January 2025  
**Platform:** Windows, macOS, Linux (Windows primary)