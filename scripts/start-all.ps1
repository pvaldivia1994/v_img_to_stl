$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskLogs = Join-Path $taskRoot 'data\logs'
New-Item -ItemType Directory -Force $taskLogs | Out-Null
try { $taskEngine = Invoke-RestMethod 'http://127.0.0.1:8188/system_stats' -TimeoutSec 3 } catch { $taskEngine = $null }
if (-not $taskEngine) {
    Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + (Join-Path $PSScriptRoot 'start-comfy.ps1') + '"')) -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLogs 'comfy.stdout.log') -RedirectStandardError (Join-Path $taskLogs 'comfy.stderr.log')
}
try { $taskApp = Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 3 } catch { $taskApp = $null }
if (-not $taskApp) {
    Start-Process -FilePath (Join-Path $taskRoot '.venv\Scripts\python.exe') -ArgumentList @('-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8000') -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLogs 'app.stdout.log') -RedirectStandardError (Join-Path $taskLogs 'app.stderr.log')
}
Start-Process 'http://127.0.0.1:8000'
