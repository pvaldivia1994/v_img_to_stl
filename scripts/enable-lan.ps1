$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskLogs = Join-Path $taskRoot 'data\logs'
New-Item -ItemType Directory -Force $taskLogs | Out-Null
$taskResult = Join-Path $taskLogs 'lan-firewall-result.json'
try {
    $taskIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not ([Security.Principal.WindowsPrincipal]::new($taskIdentity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Ejecuta Habilitar-red.cmd y acepta el aviso de administrador.'
    }
    $taskPython = & (Join-Path $taskRoot '.venv\Scripts\python.exe') -c 'import sys; print(sys._base_executable)'
    $taskRoute = Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric | Select-Object -First 1
    if (-not $taskRoute) { throw 'No se encontro una conexion de red activa.' }
    # Windows may have created a blanket public-network block for this Python.
    # Keep that block on every TCP port except the app port; the allow rule below
    # remains restricted to the current LAN interface and local subnet.
    $taskBlocks = Get-NetFirewallApplicationFilter -Program $taskPython -ErrorAction SilentlyContinue | Get-NetFirewallRule | Where-Object { $_.Enabled -eq 'True' -and $_.Direction -eq 'Inbound' -and $_.Action -eq 'Block' }
    $taskBackup = @()
    foreach ($taskRule in $taskBlocks) {
        $taskPort = $taskRule | Get-NetFirewallPortFilter
        if ($taskPort.Protocol -eq 'TCP' -and $taskPort.LocalPort -eq 'Any') {
            $taskBackup += @{name=$taskRule.Name; local_port='Any'; program=$taskPython}
        }
    }
    if ($taskBackup.Count -gt 0) {
        $taskBackupPath = Join-Path $taskLogs ('lan-firewall-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.json')
        $taskBackup | ConvertTo-Json | Set-Content -Encoding UTF8 $taskBackupPath
        foreach ($taskOriginal in $taskBackup) {
            Get-NetFirewallRule -Name $taskOriginal.name | Get-NetFirewallPortFilter | Set-NetFirewallPortFilter -LocalPort @('1-7999','8001-65535') | Out-Null
        }
    }
    $taskRuleName = 'Forma-Local-LAN-8000'
    if (Get-NetFirewallRule -Name $taskRuleName -ErrorAction SilentlyContinue) { Remove-NetFirewallRule -Name $taskRuleName }
    New-NetFirewallRule -Name $taskRuleName -DisplayName 'Forma - acceso desde la red local (8000)' -Description 'Aplicacion C:\_Github\v_img_to_stl. Solo TCP 8000 desde la subred local; ComfyUI sigue local.' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 -Program $taskPython -RemoteAddress LocalSubnet -InterfaceAlias $taskRoute.InterfaceAlias -Profile Any | Out-Null
    @{ok=$true; interface=$taskRoute.InterfaceAlias; port=8000; time=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -Encoding UTF8 $taskResult
} catch {
    @{ok=$false; error=$_.Exception.Message; time=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -Encoding UTF8 $taskResult
    throw
}
