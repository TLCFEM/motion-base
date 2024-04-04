$scriptDir = Split-Path $MyInvocation.MyCommand.Path
$scriptDir = Split-Path $scriptDir

$pyinstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
if ($pyinstaller -eq $null) {
    Write-Host "PyInstaller is not installed."
    exit
}

cd $scriptDir
pyinstaller --onefile --additional-hooks-dir extra-hooks --hidden-import mb.app.main --icon gui/src/assets/logo.png ./mb_runner.py
