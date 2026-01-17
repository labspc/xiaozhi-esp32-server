#!/usr/bin/env bash
set -euo pipefail

# OpenAPI stub (handwritten) to support CI diff; update when routes change.

OUTPUT=${1:-openapi.json}

cat > "$OUTPUT" <<'EOF'
{
  "openapi": "3.0.0",
  "info": { "title": "ORica API", "version": "0.1.0" },
  "paths": {
    "/api/auth/login": {
      "post": {
        "summary": "Login",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/LoginRequest" }
            }
          }
        },
        "responses": {
          "200": {
            "description": "OK",
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/LoginResponse" } } }
          }
        }
      }
    },
    "/api/devices": {
      "get": {
        "summary": "List devices",
        "security": [{ "bearerAuth": [] }],
        "responses": {
          "200": {
            "description": "OK",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": { "devices": { "type": "array", "items": { "$ref": "#/components/schemas/Device" } } }
                }
              }
            }
          },
          "401": { "description": "Unauthorized" }
        }
      }
    },
    "/api/devices/{mac}": {
      "get": {
        "summary": "Get device",
        "parameters": [{ "in": "path", "name": "mac", "required": true, "schema": { "type": "string" } }],
        "security": [{ "bearerAuth": [] }],
        "responses": {
          "200": { "description": "OK", "content": { "application/json": { "schema": { "$ref": "#/components/schemas/Device" } } } },
          "401": { "description": "Unauthorized" },
          "404": { "description": "Not found" }
        }
      }
    },
    "/api/agents": {
      "get": {
        "summary": "List agents",
        "security": [{ "bearerAuth": [] }],
        "responses": {
          "200": {
            "description": "OK",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": { "agents": { "type": "array", "items": { "$ref": "#/components/schemas/Agent" } } }
                }
              }
            }
          },
          "401": { "description": "Unauthorized" }
        }
      }
    },
    "/api/agents/{id}": {
      "get": {
        "summary": "Get agent",
        "parameters": [{ "in": "path", "name": "id", "required": true, "schema": { "type": "string" } }],
        "security": [{ "bearerAuth": [] }],
        "responses": {
          "200": { "description": "OK", "content": { "application/json": { "schema": { "$ref": "#/components/schemas/Agent" } } } },
          "401": { "description": "Unauthorized" },
          "404": { "description": "Not found" }
        }
      }
    },
    "/api/config": {
      "get": {
        "summary": "Get config",
        "security": [{ "bearerAuth": [] }],
        "responses": {
          "200": { "description": "OK", "content": { "application/json": { "schema": { "$ref": "#/components/schemas/Config" } } } },
          "401": { "description": "Unauthorized" },
          "404": { "description": "Not found" }
        }
      }
    },
    "/xiaozhi/v1/": { "get": { "summary": "WebSocket legacy" } },
    "/orica/v1/": { "get": { "summary": "WebSocket new" } }
  },
  "components": {
    "schemas": {
      "LoginRequest": {
        "type": "object",
        "properties": { "username": { "type": "string" }, "password": { "type": "string" } },
        "required": ["username", "password"]
      },
      "LoginResponse": { "type": "object", "properties": { "token": { "type": "string" } }, "required": ["token"] },
      "Device": {
        "type": "object",
        "properties": {
          "mac": { "type": "string" },
          "user_id": { "type": "string", "nullable": true },
          "agent_id": { "type": "string", "nullable": true },
          "alias": { "type": "string", "nullable": true },
          "firmware_version": { "type": "string", "nullable": true },
          "board": { "type": "string", "nullable": true },
          "last_seen": { "type": "string", "nullable": true }
        },
        "required": ["mac"]
      },
      "Agent": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string", "nullable": true },
          "asr_model_id": { "type": "string", "nullable": true },
          "vad_model_id": { "type": "string", "nullable": true },
          "llm_model_id": { "type": "string", "nullable": true },
          "tts_model_id": { "type": "string", "nullable": true }
        },
        "required": ["id"]
      },
      "Config": {
        "type": "object",
        "properties": {
          "ws_url": { "type": "string", "nullable": true },
          "http_url": { "type": "string", "nullable": true },
          "tts_model_id": { "type": "string", "nullable": true },
          "asr_model_id": { "type": "string", "nullable": true },
          "llm_model_id": { "type": "string", "nullable": true },
          "extra": { "type": "object", "nullable": true }
        }
      }
    },
    "securitySchemes": {
      "bearerAuth": {
        "type": "http",
        "scheme": "bearer"
      }
    }
  }
}
EOF

echo "OpenAPI stub generated to $OUTPUT"
