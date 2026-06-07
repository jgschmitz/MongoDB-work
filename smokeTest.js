#!/usr/bin/env bash
set -euo pipefail

echo "Checking JavaScript syntax..."

found=0

while IFS= read -r -d '' file; do
  found=1
  echo "node --check $file"
  node --check "$file"
done < <(find . -type f -name "*.js" -not -path "./node_modules/*" -print0)

if [ "$found" -eq 0 ]; then
  echo "No JavaScript files found."
else
  echo "JavaScript syntax check passed."
fi
