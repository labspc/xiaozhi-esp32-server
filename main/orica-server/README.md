# ORica Axum+PyO3 Prototype

## Endpoints (stub)
- WS: `/xiaozhi/v1/` (legacy), `/orica/v1/` (new) — calls Python `py_ai_handler` for text/binary.
- REST:
  - `POST /api/auth/login` (stub token)
  - `GET /api/devices` / `GET /api/devices/:mac` (EloqKV)
  - `GET /api/agents` / `GET /api/agents/:id` (EloqKV)
  - `GET /api/config` (EloqKV)

## Env
- `ELOQKV_URL` (default `redis://127.0.0.1:6379`)
- `KEY_DEVICES_INDEX` (default `devices`)
- `KEY_AGENTS_INDEX` (default `agents`)
- `KEY_CONFIG` (default `config:global`)

## Python Handler
- `main/orica-server/py_ai_handler.py` with `handle_text(text)->str|None`, `handle_binary(bytes)->None`; replace with real AI logic.

## OpenAPI
- Stub generator: `scripts/generate_openapi.sh`
- Baseline: `scripts/openapi-baseline.json`

## Build
```
cd main/orica-server/server
cargo check
```

## Notes
- Auth is stubbed; replace with real JWT.
- Redis key naming aligns with `docs-refactor/ELOQKV_KEYS.md` (configurable via env).
