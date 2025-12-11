#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_JSON="${ROOT_DIR}/client/package.json"
PKG_LOCK="${ROOT_DIR}/client/package-lock.json"
README_FILE="${ROOT_DIR}/README.md"

detect_version_from_package_json() {
  local file=$1
  if [[ -f "$file" ]]; then
    node -e "const fs = require('fs'); const data = JSON.parse(fs.readFileSync('$file')); console.log(data.version || '');" 2>/dev/null
  fi
}

detect_version_from_readme() {
  local file=$1
  if [[ -f "$file" ]]; then
    local line
    line=$(grep -m1 -E 'Current version' "$file" || true)
    if [[ -n "$line" ]]; then
      echo "$line" | sed -E 's/.*\*\*([^*]+)\*\*.*/\1/'
      return 0
    fi
  fi
  return 1
}

suggest_next_version() {
  local current=$1

  # e.g., 1.0.0-beta.19 -> bump last numeric token
  if [[ $current =~ ^(.*[^0-9])([0-9]+)$ ]]; then
    local prefix=${BASH_REMATCH[1]}
    local number=${BASH_REMATCH[2]}
    echo "${prefix}$((number + 1))"
    return
  fi

  # e.g., 1.2.3 -> bump patch
  if [[ $current =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    local major=${BASH_REMATCH[1]}
    local minor=${BASH_REMATCH[2]}
    local patch=${BASH_REMATCH[3]}
    echo "${major}.${minor}.$((patch + 1))"
    return
  fi

  echo "${current}.1"
}

update_package_json() {
  local next=$1
  node -e "const fs = require('fs'); const path = '$PKG_JSON'; const data = JSON.parse(fs.readFileSync(path)); data.version = '$next'; fs.writeFileSync(path, JSON.stringify(data, null, 2) + '\n');"
}

update_package_lock() {
  local next=$1
  if [[ ! -f "$PKG_LOCK" ]]; then
    return
  fi
  node -e "const fs = require('fs'); const path = '$PKG_LOCK'; const data = JSON.parse(fs.readFileSync(path)); data.version = '$next'; if (data.packages && data.packages['']) { data.packages[''].version = '$next'; } fs.writeFileSync(path, JSON.stringify(data, null, 2) + '\n');"
}

update_readme() {
  local next=$1
  if [[ -f "$README_FILE" ]]; then
    perl -0pi -e 's/Current version: \*\*[^*]+\*\*/Current version: **'"$next"'**/' "$README_FILE"
  fi
}

main() {
  local current_version=""

  current_version=$(detect_version_from_package_json "$PKG_JSON" || true)
  if [[ -z "$current_version" ]]; then
    current_version=$(detect_version_from_readme "$README_FILE" || true)
  fi

  if [[ -z "$current_version" ]]; then
    echo "Could not determine current version. Please check package.json or README.md." >&2
    exit 1
  fi

  echo "Current version: $current_version"
  local suggested next_version
  suggested=$(suggest_next_version "$current_version")

  read -rp "Next version [${suggested}]: " next_version
  next_version=${next_version:-$suggested}

  if [[ -z "$next_version" ]]; then
    echo "No version provided. Exiting." >&2
    exit 1
  fi

  echo "Next version will be: $next_version"

  read -rp "Apply version update to package.json, package-lock.json, and README? [Y/n] " confirm
  confirm=${confirm:-Y}
  if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
  fi

  update_package_json "$next_version"
  update_package_lock "$next_version"
  update_readme "$next_version"

  echo "Updated files to version: $next_version"
}

main "$@"
