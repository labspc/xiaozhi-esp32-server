# Repository Guidelines

## Project Structure & Module Organization
- Root docs and deployment guides live in `docs/` and `docs-refactor/`. Dockerfiles for server and web images sit at repo root.
- Core services are under `main/`: `xiaozhi-server/` (Python, WebSocket/HTTP gateway), `manager-api/` (Spring Boot + MySQL/Redis), `manager-web/` (Vue 2 SPA console), and `manager-mobile/` (uni-app + Vite).
- Runtime configs: Python uses `main/xiaozhi-server/config.yaml` and `config/assets/`; API uses `main/manager-api/src/main/resources/`; frontends read `.env`/`env/.env.*`.

## Build, Test, and Development Commands
- Python core: `cd main/xiaozhi-server && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && python app.py`. Docker: `docker compose -f main/xiaozhi-server/docker-compose.yml up -d`.
- Management API: `cd main/manager-api && mvn spring-boot:run`; package with `mvn clean package -DskipTests=false`; tests run via `mvn test`.
- Web console: `cd main/manager-web && npm install && npm run serve` for dev, `npm run build` for production bundle.
- Mobile console: `cd main/manager-mobile && pnpm i`; dev on web with `pnpm dev:h5`, WeChat mini program with `pnpm dev:mp-weixin`, build with `pnpm build:mp`.

## Coding Style & Naming Conventions
- Python: target 3.10, 4-space indent, type hints where practical; keep async flows non-blocking and configurations in lower_snake_case YAML keys. Plugins live in `plugins_func/` and should register cleanly.
- Java: follow Spring layered structure (controller/service/mapper/entity), camelCase methods/fields, PascalCase classes; keep configuration in `application*.yml` under `src/main/resources`.
- Vue/uni-app: PascalCase `.vue` components, kebab-case file names, keep API calls in service modules; prefer SCSS variables and reuse Element UI components; store secrets in env files, not in code.

## Testing Guidelines
- API: `mvn test` before commits; ensure MySQL/Redis test configs align with local env or use containerized services.
- Web/mobile: no formal test suite; at minimum run `npm run build` or `pnpm build:mp` to catch compile issues and verify critical flows (auth, device management) manually.
- Python core currently lacks automated tests; when adding features, include minimal unit/behavior checks and validate device/LLM paths with a local run of `python app.py`.

## Commit & Pull Request Guidelines
- Use concise, conventional-style messages (e.g., `fix: ...`, `docs(scope): ...`) in imperative mood; include scope when touching a specific module.
- PRs should describe what changed, why, and how to verify; link issues when relevant and attach screenshots for UI updates or API contract changes.
- Keep changes scoped to one area when possible (Python core vs. API vs. frontends) and note any config/schema migrations explicitly.

## Security & Configuration Tips
- Do not commit secrets or `.config.yaml`/`.env` files; provide samples instead. Rotate keys if they were exposed.
- Ensure FFmpeg and model assets exist before running `xiaozhi-server`; check ports 8000 (server), 8001 (web), 8002 (API) for conflicts.
- Validate CORS and auth settings when exposing the management API; restrict docker deployments with proper env overrides and persistent volumes for `data/` and `models/`.
