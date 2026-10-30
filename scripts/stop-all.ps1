$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
foreach ($taskPort in @(8000,8188)) {
    $taskListeners = Get-NetTCPConnection -LocalPort $taskPort -State Listen -ErrorAction SilentlyContinue
    foreach ($taskConnection in $taskListeners) {
        $taskOwner = $taskConnection.OwningProcess
        $taskCurrent = $taskOwner
        $taskOwned = $false
        for ($taskDepth=0; $taskDepth -lt 5 -and $taskCurrent -gt 0; $taskDepth++) {
            $taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$taskCurrent" -ErrorAction SilentlyContinue
            if (-not $taskProcess) { break }
            $taskCommand = $taskProcess.CommandLine
            if ($taskCommand -like "*$taskRoot\.venv\Scripts\python.exe*" -or $taskCommand -like "*$taskRoot\scripts\start-comfy.ps1*" -or $taskCommand -like '*C:\_IA\ComfyUI_windows_portable\python_embeded\python.exe*') { $taskOwned = $true; break }
            $taskCurrent = $taskProcess.ParentProcessId
        }
        if ($taskOwned) {
            Stop-Process -Id $taskOwner
            Write-Output "Servicio del proyecto detenido en el puerto $taskPort."
        } else {
            Write-Output "El puerto $taskPort pertenece a otro servicio; no se ha detenido."
        }
    }
}
