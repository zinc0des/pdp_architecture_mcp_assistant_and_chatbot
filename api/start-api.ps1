# Start the PDP Architecture Assistant API server
# Endpoint: http://127.0.0.1:8003

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Starting PDP Architecture Assistant..." -ForegroundColor Cyan
Write-Host "  Endpoint: http://127.0.0.1:8003" -ForegroundColor Gray

# Reuse an already-running instance when possible.
try {
    $existing = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8003/health" -TimeoutSec 2
    if ($existing.StatusCode -eq 200) {
        Write-Host "  Server is already running - reusing existing instance." -ForegroundColor Green
        exit 0
    }
} catch {
    # No healthy server yet; continue startup.
}

# Clean up any stale process still bound to the port.
$connections = Get-NetTCPConnection -LocalPort 8003 -ErrorAction SilentlyContinue
if ($connections) {
    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -gt 0 }
    foreach ($procId in $pids) {
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  Stopping stale process: $($proc.ProcessName) (PID: $procId)" -ForegroundColor Yellow
            Stop-Process -Id $procId -Force
        }
    }
}

# Prefer a venv that already has the API dependencies installed.
$venvCandidates = @(
    (Join-Path (Resolve-Path (Join-Path $scriptDir "..\..\..")).Path ".venv\Scripts\python.exe"),
    (Join-Path (Resolve-Path (Join-Path $scriptDir "..")).Path ".venv\Scripts\python.exe")
)

$pythonExe = $null
foreach ($candidate in $venvCandidates) {
    if (Test-Path $candidate) {
        try {
            & $candidate -c "import fastapi, uvicorn" *> $null
            if ($LASTEXITCODE -eq 0) {
                $pythonExe = $candidate
                break
            }
        } catch {
            # Try the next candidate.
        }
    }
}

if (-not $pythonExe) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pythonExe = $pythonCmd.Source
    } else {
        throw "Python was not found in the project virtual environments or on PATH."
    }
}

Write-Host "  Using Python: $pythonExe" -ForegroundColor Gray

# Start uvicorn as a single process to avoid the extra reload child process in VS Code tasks.
Push-Location $scriptDir
try {
    & $pythonExe -m uvicorn main:app --host 127.0.0.1 --port 8003
} finally {
    Pop-Location
}
