#!/usr/bin/env bash
# Starts the finished game on this computer only (http://127.0.0.1:8080) and opens the browser.
# Usage: ./scripts/play.sh            (use the existing build)
#        ./scripts/play.sh --rebuild  (build again first, e.g. after changes)
set -euo pipefail

PORT=8080
URL="http://127.0.0.1:${PORT}/"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if [[ "${1:-}" == "--rebuild" || ! -f dist/index.html ]]; then
  echo "Building the game…"
  export NVM_DIR="$HOME/.nvm"
  # shellcheck source=/dev/null
  [[ -s "$NVM_DIR/nvm.sh" ]] && source "$NVM_DIR/nvm.sh" && nvm use --silent >/dev/null
  export PATH="$HOME/.local/bin:$PATH"
  npm run build --silent
fi

echo "Game running at ${URL}  —  press Ctrl+C here to stop it."
(sleep 1 && xdg-open "$URL" >/dev/null 2>&1 || true) &
exec python3 -m http.server "$PORT" --bind 127.0.0.1 --directory dist
