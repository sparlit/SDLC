# IQ400 'Omniscient' Zenith - Unified Bootstrap Script for Windows
# One command to rule them all.

$ErrorActionPreference = "Stop"

Write-Host "🌌 Initializing IQ400 'Omniscient' Zenith Engine for Windows..." -ForegroundColor Cyan

# 1. Environment Setup
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env from template..." -ForegroundColor Yellow
    Copy-Item "setup\.env.example" ".env"

    $absPath = (Get-Item .).FullName
    $projectPath = Join-Path $absPath "project_data"

    # Update PROJECT_PATH in .env (handling Windows backslashes for the file)
    $envContent = Get-Content ".env"
    $envContent = $envContent -replace 'PROJECT_PATH=.*', "PROJECT_PATH=$($projectPath -replace '\\', '/')"
    $envContent | Set-Content ".env"

    Write-Host "⚠️  ACTION REQUIRED: Please edit .env and add your OPENROUTER_API_KEY." -ForegroundColor Magenta
} else {
    Write-Host "✅ .env already exists." -ForegroundColor Green
}

if (-not (Test-Path "project_data")) {
    New-Item -Path "project_data" -ItemType Directory | Out-Null
}

# 2. Dependency Installation
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
pip install -r src/tools/requirements.txt --quiet

# 3. Workflow Injection
Write-Host "💉 Injecting Omniscient Self-Healing Logic into workflows..." -ForegroundColor Yellow
python src/tools/omniscient_injector.py src/workflows

# 4. Infrastructure Launch
Write-Host "🚀 Launching Docker Infrastructure..." -ForegroundColor Yellow
$infraDir = Join-Path (Get-Item .).FullName "src\infrastructure"
Push-Location $infraDir
docker-compose up -d --build
Pop-Location

# 5. Autonomous Workflow Import
Write-Host "⏳ Waiting for n8n to be ready (this may take 30-60 seconds)..." -ForegroundColor Yellow
$n8nReady = $false
while (-not $n8nReady) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5678" -Method Get -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) { $n8nReady = $true }
    } catch {
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 5
    }
}

Write-Host "`n✅ n8n is up! Importing workflows..." -ForegroundColor Green

$n8nContainer = (docker ps --filter "name=n8n" --format "{{.Names}}" | Select-Object -First 1)

if (-not $n8nContainer) {
    Write-Host "❌ Error: Could not find n8n container." -ForegroundColor Red
} else {
    $absPath = (Get-Item .).FullName
    $tempDir = Join-Path $absPath "project_data\temp_workflows"
    if (-not (Test-Path $tempDir)) { New-Item -Path $tempDir -ItemType Directory | Out-Null }
    Copy-Item "src\workflows\*.json" $tempDir

    $files = Get-ChildItem -Path $tempDir -Filter "*.json"
    foreach ($file in $files) {
        Write-Host "   -> Importing $($file.Name)..." -ForegroundColor Gray
        docker exec $n8nContainer n8n import:workflow --file "/data/project/temp_workflows/$($file.Name)" | Out-Null
    }

    Remove-Item -Path $tempDir -Recurse -Force
}

Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "✅ Setup Complete! The IQ400 Engine is fully configured." -ForegroundColor Green
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "🌐 n8n Dashboard: http://localhost:5678"
Write-Host "🛠️  Quick Start:"
Write-Host "   1. Ensure you have set OPENROUTER_API_KEY in your .env."
Write-Host "   2. The workflows are already imported. Just activate 'sdlc_main' and 'autonomous_fixing'."
Write-Host "   3. (Optional) Run the Watcher for real-time healing:"
Write-Host "      python src/tools/watcher.py"
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "🌌 System Status: OPERATIONAL" -ForegroundColor Cyan
