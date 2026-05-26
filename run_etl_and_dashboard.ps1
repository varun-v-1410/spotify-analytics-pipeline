$ErrorActionPreference = "Stop"

$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $PROJECT_ROOT

$VENV_DIR = Join-Path $PROJECT_ROOT "spotify_analytics_piepeline"
$PYTHON_EXE = Join-Path $VENV_DIR "Scripts\python.exe"

if (-not (Test-Path $PYTHON_EXE)) {
  throw "Virtualenv python not found: $PYTHON_EXE"
}

Write-Host "Running ETL pipeline..."
& $PYTHON_EXE "scripts\run_pipeline.py"

$PORT = 8501
$ADDRESS = "127.0.0.1"

Write-Host "Starting Streamlit dashboard..."
& $PYTHON_EXE -m streamlit run "dashboards\app.py" --server.address $ADDRESS --server.port $PORT

