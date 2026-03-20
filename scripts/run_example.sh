#!/usr/bin/env bash
set -e

echo "==> Running example: analyze tenacity"
libexplorer analyze tenacity --language python --top-k 5

echo ""
echo "==> Report:"
cat reports/tenacity/final_report.md
