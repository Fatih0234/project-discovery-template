#!/usr/bin/env bash
set -e

echo "==> Installing libexplorer..."
pip install -e .[dev]

echo ""
echo "==> Setup complete! Available commands:"
echo ""
echo "  libexplorer analyze tenacity --language python --top-k 5"
echo "  libexplorer discover httpx"
echo "  libexplorer report tenacity"
echo ""
echo "  make example   # run tenacity example end-to-end"
echo "  make test      # run test suite"
echo ""

if [ -f .env.example ] && [ ! -f .env ]; then
    cp .env.example .env
    echo "==> Copied .env.example → .env (fill in your API keys)"
fi
