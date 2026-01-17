# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**xiaozhi-esp32-server** is a comprehensive backend system for ESP32-based smart hardware, providing voice interaction AI capabilities. The system consists of four main modules:

- **xiaozhi-server** (Python, port 8000): Core AI engine handling WebSocket communication with ESP32 devices
- **manager-api** (Java Spring Boot, port 8002): Management backend providing RESTful APIs
- **manager-web** (Vue.js 2, port 8001): Web control panel for system configuration
- **manager-mobile** (uni-app + Vue 3): Cross-platform mobile management application

Communication protocol documentation: https://ccnphfhqs21z.feishu.cn/wiki/M0XiwldO9iJwHikpXD5cEx71nKh

API documentation: https://2662r3426b.vicp.fun/xiaozhi/doc.html

## Development Commands

### xiaozhi-server (Python)

```bash
cd main/xiaozhi-server

# Install dependencies (Python 3.10 recommended)
pip install -r requirements.txt

# Run server directly
python app.py

# Run performance tests
python performance_tester.py

# Docker commands
docker compose up -d
docker logs -f xiaozhi-esp32-server
```

### manager-api (Java Spring Boot)

```bash
cd main/manager-api

# Build with Maven
mvn clean package

# Run application
mvn spring-boot:run

# Run tests
mvn test
```

### manager-web (Vue.js 2)

```bash
cd main/manager-web

# Install dependencies
npm install

# Development server
npm run serve

# Production build
npm run build

# Analyze bundle size
npm run analyze
```

### manager-mobile (uni-app)

```bash
cd main/manager-mobile

# Install dependencies (pnpm required)
pnpm install

# Development
pnpm dev:h5              # H5 development
pnpm dev:mp-weixin       # WeChat mini-program
pnpm dev:app-android     # Android app
pnpm dev:app-ios         # iOS app

# Production build
pnpm build:h5
pnpm build:mp-weixin
pnpm build:app-android
pnpm build:app-ios
```

## Architecture Fundamentals

### Provider Pattern (xiaozhi-server)

The core design pattern for integrating different AI services. Each AI service type (ASR, TTS, LLM, VAD, Intent, Memory, VLLM) has:

- **Abstract base class** in `core/providers/[service_type]/base.py` defining the interface
- **Concrete implementations** as individual Python classes (e.g., `fun_local.py`, `openai.py`)
- **Dynamic loading** via `core/utils/modules_initialize.py` based on `config.yaml`

When adding a new provider:
1. Create a new file in the appropriate `core/providers/` subdirectory
2. Inherit from the base class and implement required methods
3. Add configuration to `config.yaml` under the service type

### Plugin System (xiaozhi-server)

Located in `plugins_func/`:
- **functions/**: Individual plugin scripts (e.g., `get_weather.py`, `hass_set_state.py`)
- **loadplugins.py**: Scans and loads plugins at startup
- **register.py**: Defines plugin metadata (function name, description, parameter schema in JSON Schema format)

Plugins are called by the LLM using function calling when it determines external tools are needed.

### WebSocket Communication Flow

1. ESP32 connects to `ws://[server]:8000/xiaozhi/v1/`
2. Each connection gets a dedicated `ConnectionHandler` instance (ensures state isolation)
3. Binary messages = audio data; Text messages = JSON control/status messages
4. Handlers in `core/handle/` process different message types:
   - `helloHandle.py`: Initial handshake
   - `receiveAudioHandle.py`: Audio input + VAD + ASR
   - `textHandle.py` / `intentHandler.py`: Intent recognition + LLM interaction
   - `functionHandler.py`: Plugin execution
   - `sendAudioHandle.py`: TTS synthesis + audio output
   - `abortHandle.py`: Interrupt handling

### Configuration Management

**xiaozhi-server** configuration:
- **Local**: `main/xiaozhi-server/config.yaml` (primary configuration)
- **Remote**: Pulled from `manager-api` via `config/manage_api_client.py`
- Remote config **overrides** local config for the same keys
- Dynamic reload via `WebSocketServer.update_config()` without full restart

**manager-api** configuration:
- `src/main/resources/application.properties` or `application.yml`
- Database connections (MySQL), Redis, Shiro security settings

**manager-web** configuration:
- `.env`, `.env.development`, `.env.production`
- Key setting: `VUE_APP_API_BASE_URL` (manager-api endpoint)

## Code Organization Principles

### manager-api Module Structure

Under `src/main/java/xiaozhi/modules/`, each business module follows:
```
modules/[module_name]/
├── controller/     # REST endpoints (@RestController)
├── service/        # Business logic (@Service)
├── dao/           # MyBatis-Plus mappers
├── entity/        # Database entities (@TableName)
└── dto/           # Data transfer objects
```

Common utilities in `src/main/java/xiaozhi/common/`:
- Base classes, global configuration, AOP aspects
- `RenExceptionHandler`: Global exception handling
- `MybatisPlusConfig`, `RedisConfig`, `SwaggerConfig`

### manager-web Component Structure

- `src/main.js`: Entry point, plugin registration
- `src/App.vue`: Root component with app layout
- `src/views/`: Page-level components (mapped to routes)
- `src/components/`: Reusable UI components
- `src/router/index.js`: Route definitions + navigation guards
- `src/store/index.js`: Vuex state management
- `src/apis/`: API communication layer (organized by module)

## Key Technical Constraints

### Python (xiaozhi-server)
- **Python 3.10 recommended** for best compatibility
- **DO NOT upgrade**: torch (2.2.2), torchaudio (2.2.2), numpy (1.26.4), websockets (14.2)
- Uses **asyncio** extensively for concurrent WebSocket connections
- FFmpeg required (checked at startup via `check_ffmpeg_installed()`)

### Java (manager-api)
- **Java 21** with Spring Boot 3.4.3
- **Liquibase** manages database schema migrations (changelogs in `src/main/resources/db/changelog/`)
- **Apache Shiro** handles authentication/authorization
- **Druid** for database connection pooling
- **Redis** for caching (session info, hot configurations)

### Vue.js (manager-web)
- **Vue 2.6** with Vue Router 3.x and Vuex 3.x
- **Element UI** as primary component library
- **Webpack** bundling (managed by Vue CLI)
- **Workbox** for PWA/Service Worker capabilities

### uni-app (manager-mobile)
- **uni-app v3 + Vue 3 + Vite**
- **pnpm** as package manager (required)
- **alova + @alova/adapter-uniapp** for API requests
- **pinia** for state management with persistence
- **UnoCSS** for atomic CSS

## Testing and Performance

### Performance Testing (xiaozhi-server)
- **performance_tester.py**: Tests ASR, LLM, VLLM, TTS module response times
- Only tests modules with configured API keys
- Run with: `python performance_tester.py`

### Audio Interaction Testing
- **test/test_page.html**: Browser-based audio playback/receive testing
- Open directly in Chrome to verify audio processing pipeline
- Located in `main/xiaozhi-server/test/`

### Model Speed Testing
Use `performance_tester.py` to compare different AI service providers before committing to a configuration.

## Deployment Considerations

### Simplified Deployment (xiaozhi-server only)
- Suitable for low-resource environments (2 core 2GB if all API-based, 2 core 4GB with FunASR)
- Configuration stored in `config.yaml` (no database required)
- Single container deployment via Docker

### Full Module Deployment
- Requires all four components + MySQL + Redis
- Recommended: 2 core 4GB (all API-based), 4 core 8GB (with FunASR)
- Web interface for multi-user/multi-agent management
- Database-backed persistent storage

### Configuration Strategies
1. **All-free setup**: Uses free-tier cloud services or local models (FunASR, EdgeTTS, Gemini, GLM-4-flash)
2. **Streaming setup**: Prioritizes response speed with streaming-capable services (typically paid)

Performance reports available: https://github.com/xinnan-tech/xiaozhi-performance-research

## Security Notes

- manager-api uses **Apache Shiro** for authentication/authorization
- API endpoints protected by token-based auth (check `modules/security/`)
- **XSS protection** via `XssFilter` in common components
- **Never commit** API keys or secrets to repository
- Vision analysis endpoint (`/mcp/vision/explain`) uses JWT auth_key

## Important Patterns

### Asynchronous Processing
- xiaozhi-server uses `asyncio` for all I/O operations
- Use `async def` and `await` for HTTP requests, WebSocket handling
- Config updates use `asyncio.Lock` for thread safety

### Error Handling
- manager-api: Global exception handler returns standardized JSON errors
- xiaozhi-server: Uses `loguru` for tagged logging (`logger.bind(tag=TAG)`)
- Always check provider responses for errors before proceeding

### Memory Management
- Memory providers (`mem_local_short`, `mem0ai`, `nomem`) manage conversation context
- Local short-term memory includes summarization to prevent context overflow
- Conversation history passed to LLM for multi-turn coherence

## Common Modification Scenarios

**Adding a new AI provider:**
1. Create provider class in `core/providers/[type]/new_provider.py`
2. Inherit from base class, implement required methods
3. Add to `config.yaml` under the service type
4. Update provider initialization logic if needed

**Creating a new plugin function:**
1. Add Python file to `plugins_func/functions/`
2. Define function with clear docstring
3. Register in `register.py` with JSON Schema for parameters
4. Restart xiaozhi-server to load

**Adding a new API endpoint (manager-api):**
1. Create DTO classes if needed
2. Add method to DAO/Mapper for database access
3. Implement business logic in Service layer
4. Create Controller endpoint with Swagger annotations
5. Update Shiro configuration if authentication required

**Adding a new page (manager-web):**
1. Create Vue component in `src/views/`
2. Add route to `src/router/index.js`
3. Create API functions in `src/apis/module/`
4. Update navigation/menu as needed

## Documentation References

- Main README: Comprehensive project overview and deployment guides
- Technical docs: `main/README.md` (architecture deep-dive in Chinese)
- Deployment: `docs/Deployment.md` (simplified), `docs/Deployment_all.md` (full stack)
- FAQ: `docs/FAQ.md`
- Integration guides in `docs/` for specific features (HomeAssistant, Fish-Speech, etc.)
