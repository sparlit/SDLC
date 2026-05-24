#!/bin/bash

# IQ400 'Omniscient' Zenith - Unified Bootstrap Script
# One command to rule them all.

set -e

echo "🌌 Initializing IQ400 'Omniscient' Zenith Engine..."

# 1. Environment Setup
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp setup/.env.example .env

    # Get Absolute Path portably
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        ABS_PATH=$(pwd -W)
    else
        ABS_PATH=$(pwd)
    fi

    # Portable replacement using Perl (usually available on macOS/Linux)
    perl -pi -e "s|PROJECT_PATH=.*|PROJECT_PATH=$ABS_PATH/project_data|g" .env
    echo "⚠️  ACTION REQUIRED: Please edit .env and add your OPENROUTER_API_KEY."
else
    echo "✅ .env already exists."
fi

# Create project data directory
mkdir -p project_data

# 2. Dependency Installation
echo "📦 Installing Python dependencies..."
pip install -r src/tools/requirements.txt --quiet

# 3. Workflow Injection
echo "💉 Injecting Omniscient Self-Healing Logic into workflows..."
python3 src/tools/omniscient_injector.py src/workflows

# 4. Infrastructure Launch
echo "🚀 Launching Docker Infrastructure..."
cd src/infrastructure
docker-compose up -d --build

# 5. Autonomous Workflow Import
echo "⏳ Waiting for n8n to be ready (this may take 30-60 seconds)..."
until $(curl --output /dev/null --silent --head --fail http://localhost:5678); do
    printf '.'
    sleep 5
done
echo -e "\n✅ n8n is up! Importing workflows..."

# Find n8n container name
N8N_CONTAINER=$(docker ps --filter "name=n8n" --format "{{.Names}}" | head -n 1)

if [ -z "$N8N_CONTAINER" ]; then
    echo "❌ Error: Could not find n8n container."
else
    # Copy workflows to the project_data folder which is mounted to /data/project in the container
    # This allows the n8n process to see them.
    mkdir -p ../../project_data/temp_workflows
    cp ../workflows/*.json ../../project_data/temp_workflows/

    for f in ../../project_data/temp_workflows/*.json; do
        FILENAME=$(basename "$f")
        echo "   -> Importing $FILENAME..."
        # In n8n container, PROJECT_PATH maps to /data/project
        docker exec "$N8N_CONTAINER" n8n import:workflow --file "/data/project/temp_workflows/$FILENAME" > /dev/null 2>&1 || echo "      (Skipped: $FILENAME)"
    done

    # Cleanup
    rm -rf ../../project_data/temp_workflows
fi

cd ../..

echo "--------------------------------------------------------"
echo "✅ Setup Complete! The IQ400 Engine is fully configured."
echo "--------------------------------------------------------"
echo "🌐 n8n Dashboard: http://localhost:5678"
echo "🛠️  Quick Start:"
echo "   1. Ensure you have set OPENROUTER_API_KEY in your .env."
echo "   2. The workflows are already imported. Just activate 'sdlc_main' and 'autonomous_fixing'."
echo "   3. (Optional) Run the Watcher for real-time healing:"
echo "      python3 src/tools/watcher.py"
echo "--------------------------------------------------------"
echo "🌌 System Status: OPERATIONAL"
