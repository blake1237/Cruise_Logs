# 🚢 Cruise Logs Desktop Launcher

**Quick and easy access to all Cruise Logs applications with a modern, attractive desktop interface.**

---

## 🎯 Overview

The **Cruise Logs Desktop Launcher** is a modern, native desktop application that provides a beautiful interface with large, colorful buttons to launch all Cruise Logs forms.

**No browser needed - it's a true desktop application!**

---

## ✨ Features

- ✅ **Beautiful native desktop window** - Professional, modern interface
- ✅ **Dark/Light theme toggle** - Adjust for your environment
- ✅ **Large, colorful buttons** - Easy to see and click
- ✅ **No browser required** - Native Windows application
- ✅ **Fast and responsive** - Instant button response
- ✅ **Process management** - Track and stop running apps
- ✅ **Clean, attractive design** - Not clunky at all!

---

## 📋 Available Applications

Launch any of these applications with a single click:

| Application | Icon | Description |
|------------|------|-------------|
| **Cruise Form** | 🚢 | Main cruise information |
| **Deployment Form** | ⬇️ | Mooring deployments |
| **Recovery Form** | ⬆️ | Mooring recoveries |
| **Repair Form** | 🔧 | Equipment repairs |
| **ADCP Deployment** | 📡 | ADCP deployment records |
| **ADCP Recovery** | 📥 | ADCP recovery records |
| **Release Inventory** | 🔍 | Search acoustic releases |
| **Nylon Inventory** | 🧵 | Search nylon spools |

---

## 🚀 Quick Start

### 1. Install CustomTkinter (One-Time Setup)

```cmd
conda activate cruise_logs
pip install customtkinter psutil
```

### 2. Run the Launcher

**Option A: Use the Batch File (Easiest)**
```cmd
cd C:\Cruise_Logs
launch_menu.bat
```

**Option B: Direct Python Command**
```cmd
conda activate cruise_logs
cd C:\Cruise_Logs
python launcher.py
```

### 3. Create Desktop Shortcut (Recommended)

1. Navigate to `C:\Cruise_Logs`
2. Right-click `launch_menu.bat`
3. Select "Create shortcut"
4. Move shortcut to Desktop
5. Rename to "Cruise Logs"

**Daily use:** Just double-click the desktop shortcut! 🎉

---

## 💡 How to Use

### Launching Applications

1. **Start the launcher** - Double-click desktop shortcut or run `launch_menu.bat`
2. **Click a button** - Click any application button to launch it
3. **Browser opens** - Streamlit app opens automatically in your browser
4. **Work normally** - Use the form as you normally would
5. **Close when done** - Click "Close All Apps" in the launcher

### Theme Switching

- Click **"🌙 Toggle Theme"** to switch between dark and light modes
- Default is dark mode
- Great for different lighting conditions

### Stopping Applications

- Click **"❌ Close All Apps"** to stop all running applications
- Clean shutdown of all Streamlit processes
- Recommended before exiting the launcher

---

## 🎨 Interface Preview

**Main Window Layout:**

```
┌─────────────────────────────────────────┐
│  🚢 Cruise Logs Management System      │
│  Select an application to launch        │
├─────────────────────────────────────────┤
│                                         │
│  [🚢 Cruise Form]  [⬇️ Deployment]     │
│                                         │
│  [⬆️ Recovery]      [🔧 Repair]         │
│                                         │
│  [📡 ADCP Deploy]  [📥 ADCP Recovery]  │
│                                         │
│  [🔍 Releases]     [🧵 Nylon]          │
│                                         │
├─────────────────────────────────────────┤
│  Status: Ready                          │
├─────────────────────────────────────────┤
│ [🌙 Toggle Theme] [❌ Close All] [Exit]│
└─────────────────────────────────────────┘
```

**Features:**
- 2x4 grid of large buttons
- Icon + Name + Description for each
- Color-coded buttons with hover effects
- Status bar showing activity
- Control buttons at bottom

---

## 🔧 Troubleshooting

### "No module named 'customtkinter'"

```cmd
conda activate cruise_logs
pip install customtkinter psutil
```

### "launcher.py not found"

```cmd
# Make sure you're in the correct directory
cd C:\Cruise_Logs
dir launcher.py
```

### Apps don't launch

- Verify conda environment is activated
- Check that .py files exist in current directory
- Look for error messages in status bar (red text)

### Environment not activating

```cmd
# Check environment exists
conda env list

# See Windows setup guide if needed
# windows/SETUP_WINDOWS.md
```

---

## 📖 Documentation

- **Full Guide:** `LAUNCHER_GUIDE.md` - Comprehensive documentation
- **Windows Setup:** `windows/SETUP_WINDOWS.md` - Windows installation
- **Main README:** `README.md` - System overview

---

## 🎯 Daily Workflow

**Morning:**
1. Double-click "Cruise Logs" desktop shortcut
2. Wait for launcher window to appear
3. Click the application you need

**During Day:**
1. Work in your Streamlit applications
2. Return to launcher to open other apps
3. Multiple apps can run simultaneously

**End of Day:**
1. Save your work
2. Click "❌ Close All Apps" in launcher
3. Click "Exit Launcher"

---

## ✅ Installation Checklist

- [ ] Conda environment `cruise_logs` activated
- [ ] CustomTkinter installed: `pip install customtkinter psutil`
- [ ] Tested launcher: `python launcher.py`
- [ ] Created desktop shortcut
- [ ] Verified apps launch correctly

---

## 📦 What's Included

- **`launcher.py`** - Desktop launcher application
- **`launch_menu.bat`** - Batch file for easy launching
- **`LAUNCHER_GUIDE.md`** - Complete documentation
- **`LAUNCHER_README.md`** - This quick reference

---

## 🎓 Pro Tips

💡 **Create desktop shortcut** - Fastest way to launch daily  
💡 **Use "Close All Apps"** - Clean shutdown before exiting  
💡 **Toggle theme** - Adjust for lighting conditions  
💡 **Keep launcher open** - While working with apps  
💡 **Pin to taskbar** - For even quicker access  

---

## 🆘 Need Help?

**Run verification:**
```cmd
python verify_setup.py
```

**Check installation:**
```cmd
conda activate cruise_logs
python -c "import customtkinter; print('OK')"
```

**See full guide:**
- Read `LAUNCHER_GUIDE.md` for detailed help
- Check `windows/SETUP_WINDOWS.md` for Windows setup

---

**Version:** 1.0  
**Platform:** Windows (also works on macOS, Linux)  
**Last Updated:** January 2025

**Ready to launch? Run `launch_menu.bat` or create your desktop shortcut!** 🚀