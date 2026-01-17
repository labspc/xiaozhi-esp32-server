#!/usr/bin/env bash
set -euo pipefail

# Placeholder: generate OpenAPI from Axum routes (requires a generator).
# For now, output a minimal stub to allow diffing.

OUTPUT=${1:-openapi.json}

cat > "$OUTPUT" <<'EOF'
{
  "openapi": "3.0.0",
  "info": { "title": "ORica API", "version": "0.1.0" },
  "paths": {
    "/api/auth/login": { "post": { "summary": "Login" } },
    "/api/devices": { "get": { "summary": "List devices" } },
    "/api/devices/{mac}": { "get": { "summary": "Get device" } },
    "/api/agents": { "get": { "summary": "List agents" } },
    "/api/agents/{id}": { "get": { "summary": "Get agent" } },
    "/api/config": { "get": { "summary": "Get config" } },
    "/xiaozhi/v1/": { "get": { "summary": "WebSocket legacy" } },
    "/orica/v1/": { "get": { "summary": "WebSocket new" } }
  }
}
EOF

echo "OpenAPI stub generated to $OUTPUT"
