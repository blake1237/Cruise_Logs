# GitHub Repository Setup Guide

This guide explains how to create a new GitHub repository for the Windows field computer version of Cruise_Logs.

## Option 1: Use the Same Repository (Recommended)

Since the code is largely platform-independent, you can use the **same repository** for both Mac and Windows installations. This is the simplest approach.

### Advantages:
- Single source of truth for code
- Easy to sync updates between machines
- Simpler version control
- Bug fixes benefit both systems

### Setup on Windows:
1. Clone the existing repository to `C:\Cruise_Logs`
2. Create a Windows-specific branch (optional)
3. Update configuration files for Windows paths
4. Push Windows-specific changes back (or keep local)

```cmd
# On Windows machine
cd C:\
git clone git@github.com:blake1237/Cruise_Logs.git
cd Cruise_Logs
git checkout -b windows-field  # Optional: create Windows branch
```

## Option 2: Create a Separate Repository

If you need completely separate repositories (e.g., different data, configurations):

### Step 1: Create New Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `Cruise_Logs_Windows` (or similar)
3. Description: "Cruise Logs system for Windows field computer"
4. Choose **Private** or **Public**
5. **Do NOT initialize** with README, .gitignore, or license
6. Click "Create repository"

### Step 2: Prepare Local Repository

On your **Mac** (current system), create a copy for the new repo:

```bash
# Create a copy of the repository
cd ~/Github
cp -r Cruise_Logs Cruise_Logs_Windows
cd Cruise_Logs_Windows

# Remove existing git configuration
rm -rf .git

# Initialize new git repository
git init
git add .
git commit -m "Initial commit - Windows version"
```

### Step 3: Configure Git LFS

The database file (`Cruise_Logs.db`) is tracked with Git LFS. Set this up:

```bash
# Install Git LFS (if not already installed)
git lfs install

# Track the database file
git lfs track "*.db"
git add .gitattributes
git commit -m "Configure Git LFS for database"
```

### Step 4: Link to GitHub Remote

Replace `USERNAME` with your GitHub username:

```bash
# Add GitHub remote
git remote add origin git@github.com:USERNAME/Cruise_Logs_Windows.git

# Or use HTTPS:
git remote add origin https://github.com/USERNAME/Cruise_Logs_Windows.git

# Verify remote
git remote -v
```

### Step 5: Push to GitHub

```bash
# Push to GitHub
git push -u origin main

# If using 'master' instead of 'main':
git branch -M main  # Rename to main first
git push -u origin main
```

### Step 6: Verify on GitHub

1. Go to your repository page on GitHub
2. Check that all files are present
3. Verify `Cruise_Logs.db` shows as Git LFS tracked
4. Check repository size (should be reasonable due to LFS)

## Cloning on Windows Field Computer

Once the repository is on GitHub:

```cmd
# Open Git Bash or Command Prompt
cd C:\

# Clone the repository
git clone git@github.com:USERNAME/Cruise_Logs_Windows.git Cruise_Logs

# Or with HTTPS:
git clone https://github.com/USERNAME/Cruise_Logs_Windows.git Cruise_Logs

# Navigate into the directory
cd Cruise_Logs

# Pull LFS files
git lfs pull
```

## Git LFS Setup (Important!)

Git LFS must be installed on both machines to handle the database file.

### On Mac:
```bash
brew install git-lfs
git lfs install
```

### On Windows:
1. Download from https://git-lfs.github.com/
2. Run installer
3. In Git Bash or Command Prompt:
```cmd
git lfs install
```

### Verify LFS is tracking database:
```bash
# Check what's tracked
git lfs ls-files

# Should show:
# Cruise_Logs.db
```

## Repository Configuration Files

Ensure these files are in the repository:

- [x] `.gitignore` - Ignore temporary files
- [x] `.gitattributes` - Git LFS configuration
- [x] `requirements.txt` - Python dependencies
- [x] `environment_windows.yml` - Conda environment
- [x] `SETUP_WINDOWS.md` - Windows setup instructions
- [x] `README_inventories.md` - System documentation

## Branch Strategy (if using same repository)

### Main Branch
- Keep platform-independent code
- Shared by both Mac and Windows

### Platform-Specific Branches
```bash
# Mac branch
git checkout -b mac-system

# Windows branch
git checkout -b windows-field

# Merge shared updates to both
git checkout main
git merge mac-system     # or windows-field
```

### Or Use Platform-Specific Config Files
Better approach - keep one branch, use configuration:

```python
# config.py
import os
import platform

if platform.system() == 'Windows':
    DB_PATH = r'C:\Cruise_Logs\Cruise_Logs.db'
else:
    DB_PATH = os.path.expanduser('~/Github/Cruise_Logs/Cruise_Logs.db')
```

## Syncing Between Machines

### Workflow for updates:

```bash
# On Mac - make changes
git add .
git commit -m "Update cruise form validation"
git push origin main

# On Windows - pull changes
git pull origin main
git lfs pull  # Important for database updates
```

## SSH Key Setup (Recommended)

For easier authentication without passwords:

### Generate SSH Key (Windows):
```cmd
# In Git Bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Press Enter to accept default location
# Enter passphrase (optional)

# Copy public key
cat ~/.ssh/id_ed25519.pub
```

### Add to GitHub:
1. Go to GitHub → Settings → SSH and GPG keys
2. Click "New SSH key"
3. Paste the public key
4. Save

### Test connection:
```cmd
ssh -T git@github.com
```

## Repository Permissions

If working with a team:

1. Go to repository → Settings → Manage access
2. Click "Invite a collaborator"
3. Add team members
4. Set appropriate permissions (Read, Write, or Admin)

## .gitignore Configuration

The `.gitignore` file should exclude:

```
# Python
__pycache__/
*.pyc
.venv/

# Streamlit
.streamlit/secrets.toml

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
~$*.xls
*.log

# Database temporary files
*.db-journal
*.db-wal
```

But **INCLUDE**:
- `Cruise_Logs.db` (via Git LFS)
- Excel template files
- Python source files

## Protecting the Main Branch

On GitHub repository settings:

1. Go to Settings → Branches
2. Add rule for `main` branch
3. Enable:
   - Require pull request reviews before merging
   - Require status checks to pass
4. Save changes

## Backup Strategy

### Regular Backups:
1. **Database**: `Cruise_Logs.db` tracked in Git
2. **Code**: All Python files in Git
3. **Data files**: Excel files in Git

### Export database regularly:
```bash
# Create backup
sqlite3 Cruise_Logs.db ".backup cruise_logs_backup_$(date +%Y%m%d).db"

# Or dump to SQL
sqlite3 Cruise_Logs.db .dump > cruise_logs_backup.sql
```

## Troubleshooting

### Issue: LFS bandwidth limit exceeded
**Solution:** Contact GitHub support or upgrade to GitHub Pro

### Issue: Repository too large
**Solution:** Ensure binary files use Git LFS
```bash
git lfs migrate import --include="*.db,*.xls,*.xlsx"
```

### Issue: Can't push to repository
**Solution:** Check authentication
```bash
# For SSH
ssh -T git@github.com

# For HTTPS
git config credential.helper store
```

### Issue: Merge conflicts in database
**Solution:** Database files shouldn't be edited on both systems simultaneously. Use one as primary, or implement sync script.

## Summary Recommendation

**Best Approach:** Use the **same repository** with:
1. Single main branch
2. Cross-platform compatible code (use `os.path`, `platform.system()`)
3. Git LFS for database
4. Windows-specific documentation in `SETUP_WINDOWS.md`

This keeps maintenance simple while supporting both platforms.

## Quick Commands Reference

```bash
# Clone repository
git clone git@github.com:USERNAME/REPO.git

# Pull latest changes
git pull origin main
git lfs pull

# Push changes
git add .
git commit -m "Description of changes"
git push origin main

# Create new branch
git checkout -b branch-name

# Switch branches
git checkout main

# Check status
git status

# View history
git log --oneline

# Check LFS files
git lfs ls-files
```

## Next Steps

1. ✅ Decide: Same repository or separate?
2. ✅ Set up Git LFS on both machines
3. ✅ Clone repository to Windows (`C:\Cruise_Logs`)
4. ✅ Follow `SETUP_WINDOWS.md` for Windows configuration
5. ✅ Test applications on Windows
6. ✅ Establish workflow for updates and syncing