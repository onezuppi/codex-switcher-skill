"""Close and reopen the Codex desktop app around an account switch. Windows only."""
import subprocess
import sys

# Matches the Codex desktop package, its helper engine, and the Codex Switcher install.
CLOSE_APPS_SCRIPT = r"""
$match = { param($p) $p.ExecutablePath -and ($p.ExecutablePath -like '*\WindowsApps\OpenAI.Codex_*' -or $p.ExecutablePath -like '*\AppData\Local\OpenAI\Codex\*' -or $p.ExecutablePath -like '*\Codex Switcher\*') }
$targets = @(Get-CimInstance Win32_Process | Where-Object { & $match $_ })
foreach ($t in $targets) {
    $proc = Get-Process -Id $t.ProcessId -ErrorAction SilentlyContinue
    if ($proc -and $proc.MainWindowHandle -ne 0) { [void]$proc.CloseMainWindow() }
}
$deadline = (Get-Date).AddSeconds(15)
while ((Get-Date) -lt $deadline) {
    $left = @(Get-CimInstance Win32_Process | Where-Object { & $match $_ })
    if ($left.Count -eq 0) { break }
    Start-Sleep -Milliseconds 500
}
$left = @(Get-CimInstance Win32_Process | Where-Object { & $match $_ })
foreach ($l in $left) { & taskkill.exe /F /T /PID $l.ProcessId | Out-Null }
Write-Output ('closed processes: ' + $targets.Count + ', force-killed: ' + $left.Count)
"""

OPEN_CODEX_SCRIPT = r"""
$p = Get-AppxPackage -Name 'OpenAI.Codex' | Select-Object -First 1
if ($p) { Start-Process ('shell:AppsFolder\' + $p.PackageFamilyName + '!App') } else { Write-Error 'Codex package not found' }
"""


def run_powershell(script):
    return subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                          capture_output=True, text=True)


def close_apps():
    """Close Codex and Codex Switcher. Force-kills what is still running after 15 seconds."""
    if sys.platform != "win32":
        print("Automatic close works on Windows only. Close Codex and Codex Switcher manually.")
        return
    result = run_powershell(CLOSE_APPS_SCRIPT)
    if result.returncode != 0:
        sys.exit("Could not close Codex. Close it manually and run the command again.")
    print(result.stdout.strip() or "Codex and Codex Switcher closed.")


def open_codex():
    if sys.platform != "win32":
        print("Open Codex manually.")
        return
    result = run_powershell(OPEN_CODEX_SCRIPT)
    print("Codex opened." if result.returncode == 0 else "Could not open Codex. Open it manually.")
