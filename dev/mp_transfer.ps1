param(
    [Parameter(Mandatory=$true)]
    [string]$ComPort
)

# Files that should remain as .py files (not compiled to .mpy)
$PY_ONLY_FILES = @("boot.py", "main.py")

# Check that we have mpremote installed
$mpremoteExists = Get-Command mpremote -ErrorAction SilentlyContinue
if (-not $mpremoteExists) {
    Write-Host "mpremote could not be found, please install it first."
    exit 1
}

# Check if mpy_cross module is available in Python
$mpyCrossExists = python -c "import mpy_cross" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "mpy_cross Python module could not be found, please install it first."
    exit 1
}

# Create assets directory on device (ignore errors)
& mpremote connect $ComPort mkdir :assets *> $null

# Process all Python files
Get-ChildItem -Filter "*.py" | ForEach-Object {
    if ($PY_ONLY_FILES -contains $_.Name) {
        # Transfer Python files that should not be compiled
        Write-Host "Transferring $($_.Name) as Python file"
        & mpremote connect $ComPort cp $_.Name ":"
    } else {
        # Compile and transfer as MPY
        $mpyFile = [System.IO.Path]::ChangeExtension($_.Name, "mpy")
        Write-Host "Compiling $($_.Name) to $mpyFile"
        & python -m mpy_cross $_.Name
        Write-Host "Transferring $mpyFile"
        & mpremote connect $ComPort cp $mpyFile ":"
    }
}

# Transfer all files from assets directory
if (Test-Path "assets") {
    Get-ChildItem -Path "assets" -File | ForEach-Object {
        Write-Host "Transferring assets/$($_.Name)"
        & mpremote connect $ComPort cp "assets/$($_.Name)" ":assets/"
    }
}
