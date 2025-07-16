#!/bin/bash
set -e

# Default values
PUID=${PUID:-99}
PGID=${PGID:-100}

echo "Starting Minecraft Item Transformation with PUID=$PUID, PGID=$PGID"

# Create group and user if they don't exist
if ! getent group $PGID > /dev/null 2>&1; then
    groupadd -g $PGID appgroup
fi

if ! getent passwd $PUID > /dev/null 2>&1; then
    useradd -u $PUID -g $PGID -d /app -s /bin/bash appuser
fi

# Ensure directories exist
mkdir -p /app/data /app/output /app/textures/blocks

# FORCE CREATE THE CORRECT TEMPLATE - ALWAYS OVERWRITE
echo "Force creating correct transformation template..."
cat > /app/data/recipe.json.j2 << 'EOF'
{
  "format_version": "1.12",
  "minecraft:recipe_shaped": {
    "description": {
      "identifier": "itemtransformation:{{ input_item }}_to_{{ result_item }}"
    },
    "tags": [
      "transformation_table"
    ],
    "pattern": [
      "#"
    ],
    "key": {
      "#": {
        "item": "minecraft:{{ input_item }}"
      }
    },
    "result": {
      "item": "minecraft:{{ result_item }}",
      "count": 1
    }
  }
}
EOF

echo "Template file created with correct content"

# Fix ownership and permissions
echo "Setting up permissions..."
chown -R $PUID:$PGID /app/data /app/output
chmod -R 755 /app/data /app/output

echo "Permissions setup complete. Starting Item Transformation application..."

# Drop privileges and run the application
exec gosu $PUID:$PGID "$@"