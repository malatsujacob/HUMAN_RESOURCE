#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$HOME/app"
BACKEND_DIR="$APP_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"

mkdir -p "$BACKEND_DIR" "$APP_DIR/frontend_dist"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

if [ -f "$BACKEND_DIR/requirements.txt" ]; then
  "$VENV_DIR/bin/pip" install --upgrade pip
  "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
fi

sudo systemctl daemon-reload || true
sudo systemctl restart hr-backend || true
sudo systemctl reload nginx || true
