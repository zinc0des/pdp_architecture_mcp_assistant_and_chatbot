# Stop the PDP Architecture Assistant API server

$ErrorActionPreference = "SilentlyContinue"

Write-Host "Stopping PDP Architecture Assistant..." -ForegroundColor Yellow

# Find and kill the uvicorn process on port 8003
$connections = Get-NetTCPConnection -LocalPort 8003 -ErrorAction SilentlyContinue
if ($connections) {
    $currentProcessId = $PID
    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -gt 0 -and $_ -ne $currentProcessId }
    foreach ($procId in $pids) {
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  Stopping process: $($proc.ProcessName) (PID: $procId)" -ForegroundColor Gray
            Stop-Process -Id $procId -Force
        }
    }
    Write-Host "Server stopped." -ForegroundColor Green
} else {
    Write-Host "No server running on port 8003." -ForegroundColor Gray
}
