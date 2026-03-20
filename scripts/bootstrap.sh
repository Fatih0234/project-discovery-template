#!/usr/bin/env bash
set -e

echo "==> Installing libexplorer..."
pip install -e .[dev]

if [ ! -f .env ]; then
    cp .env.example .env
    echo "==> Created .env from .env.example — fill in your API keys before running."
else
    echo "==> .env already exists, skipping copy."
fi

echo ""
echo "==> Bootstrap complete. Try:"
echo "    make example"
echo "    libexplorer analyze tenacity --language python --top-k 5"
