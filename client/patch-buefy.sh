#!/bin/sh
# Fix Buefy 3.0.3 bug where CSS contains invalid checkmark() function reference
# This is a bug in the published package that prevents webpack from processing the CSS

BUEFY_CSS_FILE="node_modules/buefy/dist/css/buefy.css"

if [ -f "$BUEFY_CSS_FILE" ]; then
  echo "Patching Buefy CSS for webpack compatibility..."

  # Check if the bug exists
  if grep -q 'url(checkmark(var' "$BUEFY_CSS_FILE"; then
    # Replace the broken checkmark() function with inline SVG data URI
    sed -i.bak 's|url(checkmark(var(--bulma-table-row-active-background-color)))|url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 1 1%27%3E%3Cpath style=%27fill:%23fff%27 d=%27M 0.04038059,0.6267767 0.14644661,0.52071068 0.42928932,0.80355339 0.3232233,0.90961941 z M 0.21715729,0.80355339 0.85355339,0.16715729 0.95961941,0.2732233 0.3232233,0.90961941 z%27%3E%3C/path%3E%3C/svg%3E")|g' "$BUEFY_CSS_FILE"
    echo "✓ Fixed broken checkmark function in CSS"
  else
    echo "✓ Buefy CSS already patched or doesn't need patching"
  fi

  echo "Buefy patch applied successfully!"
else
  echo "Warning: Buefy CSS not found at $BUEFY_CSS_FILE"
  exit 1
fi
