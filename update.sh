#!/usr/bin/env bash
set -e

CURRENT_USER=$(whoami)
USER_HOME=$(eval echo ~$CURRENT_USER)

APP_DIR="$USER_HOME/AlcuinCalendar"
SERVICE_NAME="alcuin"

echo "🔄 Updating $APP_DIR..."

cd "$APP_DIR"

git pull origin main

if command -v uv >/dev/null 2>&1; then
    echo "📦 Updating dependencies with uv..."
    uv sync
fi

echo "🚀 Restarting $SERVICE_NAME service..."
sudo systemctl daemon-reload
sudo systemctl restart "$SERVICE_NAME"

echo "✅ Update complete. Check status with: sudo systemctl status $SERVICE_NAME"
