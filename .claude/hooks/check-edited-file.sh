#!/usr/bin/env bash
# Lints + format-checks the file Claude just edited; exit 2 feeds the errors back to Claude.
set -uo pipefail

file_path=$(node -e 'let d="";process.stdin.on("data",c=>d+=c).on("end",()=>{try{process.stdout.write(JSON.parse(d).tool_input?.file_path??"")}catch{}})')
[[ -z "$file_path" ]] && exit 0

case "$file_path" in
  *.ts|*.js|*.svelte) ;;
  *) exit 0 ;;
esac
case "$file_path" in
  */node_modules/*|*/dist/*) exit 0 ;;
esac

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
[[ -s "$HOME/.nvm/nvm.sh" ]] && source "$HOME/.nvm/nvm.sh" >/dev/null 2>&1

if ! output=$(npx --no-install eslint --max-warnings 0 "$file_path" 2>&1 && npx --no-install prettier --check "$file_path" 2>&1); then
  echo "$output" >&2
  exit 2
fi
