# Cruise_Logs Windows Installer
# PowerShell script for automated installation and setup
#
# USAGE:
#   powershell -ExecutionPolicy Bypass -File install.ps1

param(
    [string]$InstallPath = "C:\Cruise_Logs"
)

# ============================================================================
# COLOR OUTPUT FUNCTIONS
# ============================================================================
function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

Write-Header "Cruise Logs Windows Installer"

# Check if running as administrator
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $IsAdmin) {
    Write-Warning "Not running as Administrator"
    Write-Info "Recommendation: Right-click PowerShell and select 'Run as Administrator'"
}

# ============================================================================
# STEP 1: Check for Anaconda
# ============================================================================
Write-Info "STEP 1: Checking for Anaconda..."
Write-Host ""

$CondaPath = $null
$PossiblePaths = @(
    "$env:USERPROFILE\anaconda3",
    "$env:USERPROFILE\miniconda3",
    "C:\anaconda3",
    "C:\miniconda3",
    "C:\ProgramData\Anaconda3",
    "C:\ProgramData\Miniconda3"
)

foreach ($path in $PossiblePaths) {
    if (Test-Path "$path\Scripts\conda.exe") {
        $CondaPath = $path
        Write-Success "Found Conda at: $CondaPath"
        break
    }
}

if (-not $CondaPath) {
    Write-Error "Anaconda/Miniconda not found!"
    Write-Info "Please install Anaconda from: https://www.anaconda.com/download/"
    Write-Info "Make sure to check 'Add Anaconda to PATH' during installation."
    Read-Host "Press Enter after installing, then run this script again"
    exit 1
}

Write-Host ""

# ============================================================================
# STEP 2: Check for Git
# ============================================================================
Write-Info "STEP 2: Checking for Git..."
Write-Host ""

$GitFound = $false
try {
    $GitVersion = & git --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Git is installed"
        $GitFound = $true
    }
} catch {
    $GitFound = $false
}

if (-not $GitFound) {
    Write-Error "Git is not installed!"
    Write-Info "Please install Git from: https://git-scm.com/download/win"
    Write-Info "During installation, select 'Add Git to PATH'"
    Read-Host "Press Enter after installing, then run this script again"
    exit 1
}

Write-Host ""

# ============================================================================
# STEP 3: Check for Git LFS
# ============================================================================
Write-Info "STEP 3: Checking for Git LFS..."
Write-Host ""

try {
    $GitLFSVersion = & git lfs version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Git LFS is installed"
    } else {
        Write-Warning "Git LFS not detected, attempting to install..."
        & git lfs install 2>$null
    }
} catch {
    Write-Warning "Could not verify Git LFS"
}

Write-Host ""

# ============================================================================
# STEP 4: Clone Repository
# ============================================================================
Write-Info "STEP 4: Cloning Repository..."
Write-Host ""

if (Test-Path $InstallPath) {
    Write-Warning "Directory already exists: $InstallPath"
    $Response = Read-Host "Use existing directory? (yes/no)"
    if ($Response -ne "yes") {
        Write-Info "Removing existing directory..."
        Remove-Item -Recurse -Force $InstallPath 2>$null
    }
}

if (-not (Test-Path $InstallPath)) {
    Write-Info "Cloning repository..."
    & git clone https://github.com/blake1237/Cruise_Logs.git $InstallPath
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Repository cloned successfully"
    } else {
        Write-Error "Failed to clone repository"
        exit 1
    }
}

Write-Info "Pulling database file..."
Push-Location $InstallPath
& git lfs pull 2>$null
Pop-Location
Write-Success "Database pulled"

Write-Host ""

# ============================================================================
# STEP 5: Create Conda Environment
# ============================================================================
Write-Info "STEP 5: Creating Conda Environment..."
Write-Host ""

$CondaCmd = "$CondaPath\Scripts\conda.exe"

Write-Info "Creating 'cruise_logs' environment (Python 3.11)..."
& $CondaCmd create -n cruise_logs python=3.11 -y 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Success "Environment created successfully"
} else {
    Write-Error "Failed to create environment"
    exit 1
}

Write-Host ""

# ============================================================================
# STEP 6: Install Python Packages
# ============================================================================
Write-Info "STEP 6: Installing Python Packages..."
Write-Host ""

$PipCmd = "$CondaPath\envs\cruise_logs\Scripts\pip.exe"

if (Test-Path "$InstallPath\requirements.txt") {
    Write-Info "Installing packages from requirements.txt..."
    & $PipCmd install -r "$InstallPath\requirements.txt" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Packages installed successfully"
    } else {
        Write-Error "Failed to install packages"
        exit 1
    }
} else {
    Write-Error "requirements.txt not found"
    exit 1
}

Write-Host ""

# ============================================================================
# STEP 7: Verify Installation
# ============================================================================
Write-Info "STEP 7: Verifying Installation..."
Write-Host ""

Push-Location $InstallPath

# Check database
if (Test-Path "Cruise_Logs.db") {
    $DbSize = (Get-Item "Cruise_Logs.db").Length / 1MB
    if ($DbSize -gt 1) {
        Write-Success "Database file OK ($([math]::Round($DbSize, 2)) MB)"
    } else {
        Write-Warning "Database file is small (might need git lfs pull)"
    }
} else {
    Write-Warning "Database file not found"
}

# Check required files
$RequiredFiles = @("cruise_form.py", "launcher.py", "requirements.txt")
foreach ($file in $RequiredFiles) {
    if (Test-Path $file) {
        Write-Success "Found: $file"
    } else {
        Write-Error "Missing: $file"
    }
}

Pop-Location
Write-Host ""

# ============================================================================
# STEP 8: Create Desktop Shortcuts
# ============================================================================
Write-Info "STEP 8: Creating Desktop Shortcuts..."
Write-Host ""

$Response = Read-Host "Create desktop shortcuts? (yes/no)"

if ($Response -eq "yes") {
    $DesktopPath = [Environment]::GetFolderPath("Desktop")

    try {
        $ShellLink = New-Object -ComObject WScript.Shell

        # Main Form Shortcut
        Write-Info "Creating 'Cruise Logs - Main Form' shortcut..."
        $LnkPath = "$DesktopPath\Cruise Logs - Main Form.lnk"
        $Target = "$CondaPath\Scripts\streamlit.exe"
        $Arguments = "run `"$InstallPath\cruise_form.py`""

        $Link = $ShellLink.CreateShortcut($LnkPath)
        $Link.TargetPath = $Target
        $Link.Arguments = $Arguments
        $Link.WorkingDirectory = $InstallPath
        $Link.Save()
        Write-Success "Created: Cruise Logs - Main Form"

        # Launcher Shortcut
        Write-Info "Creating 'Cruise Logs - Launcher' shortcut..."
        $LnkPath = "$DesktopPath\Cruise Logs - Launcher.lnk"
        $Target = "$CondaPath\envs\cruise_logs\Scripts\pythonw.exe"
        $Arguments = "`"$InstallPath\launcher.py`""

        $Link = $ShellLink.CreateShortcut($LnkPath)
        $Link.TargetPath = $Target
        $Link.Arguments = $Arguments
        $Link.WorkingDirectory = $InstallPath
        $Link.Save()
        Write-Success "Created: Cruise Logs - Launcher"

    } catch {
        Write-Warning "Could not create shortcuts: $_"
    }
} else {
    Write-Info "Skipping shortcut creation"
}

Write-Host ""

# ============================================================================
# COMPLETION
# ============================================================================
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Summary:" -ForegroundColor Green
Write-Host "  Install Path: $InstallPath" -ForegroundColor White
Write-Host "  Environment:  cruise_logs (Python 3.11)" -ForegroundColor White
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Double-click 'Cruise Logs - Main Form' on your desktop" -ForegroundColor White
Write-Host "  2. Or run from command line:" -ForegroundColor White
Write-Host "     conda activate cruise_logs" -ForegroundColor White
Write-Host "     cd $InstallPath" -ForegroundColor White
Write-Host "     streamlit run cruise_form.py" -ForegroundColor White
Write-Host ""

Write-Host "For help, see: $InstallPath\windows\FIELD_DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
Write-Host ""
