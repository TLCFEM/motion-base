$scriptDir = Split-Path $MyInvocation.MyCommand.Path
$scriptDir = Split-Path $scriptDir

$pyinstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
if ($pyinstaller -eq $null) {
    Write-Host "PyInstaller is not installed."
    exit
}

cd $scriptDir
pyinstaller --onefile --additional-hooks-dir extra-hooks --hidden-import mb.app.main --hidden-import mb.app.jp --hidden-import mb.app.nz --hidden-import mb.taskiq --icon gui/src/assets/logo.png ./mb_runner.py
pyinstaller --onefile src/crawler/nied_crawler.py
pyinstaller --onefile src/crawler/nzsm_crawler.py
