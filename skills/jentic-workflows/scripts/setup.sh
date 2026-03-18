#!/usr/bin/env bash
# Install @jentic/arazzo-validator globally (idempotent)
set -e

if command -v arazzo-validator &>/dev/null; then
  echo "arazzo-validator already installed: $(arazzo-validator --version 2>&1)"
  exit 0
fi

echo "Installing @jentic/arazzo-validator..."
npm install -g @jentic/arazzo-validator
echo "Installed: $(arazzo-validator --version 2>&1)"
