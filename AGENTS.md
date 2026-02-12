# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Non-Obvious, Project-Specific Guidance

- **Python Backend**
  - Uses [`uv`](https://github.com/astral-sh/uv) for dependency management and running (`uv run server.py`). Do not use `pip` or `venv` directly; requirements are only in `pyproject.toml`.
  - Linting and formatting are enforced via [Ruff](https://github.com/astral-sh/ruff) (see [`server/.pre-commit-config.yaml`](server/.pre-commit-config.yaml)). Always run `pre-commit run --all-files` before committing.
  - The backend does not include a test suite by default; there are no standard `pytest` or similar test commands present.
  - Environment variables must be set via `.env` in `server/` (see `.env-sample.txt`). Some features (e.g., ACS integration) require Azure resources and will not work locally without proper secrets.
  - The server expects the built frontend to be present in `server/static/booking/` for `/booking` routes. If missing, users see a 404 with a build instruction.

- **Frontend (React/Vite)**
  - The frontend build output is configured to go to `../server/static/booking` (see [`frontend/vite.config.js`](frontend/vite.config.js)). This is non-standard; do not change the output directory unless you update the backend static file serving logic.
  - WebSocket proxying for `/web/ws` and `/acs/ws` is set up in Vite config to forward to the backend on port 8000. This is required for local development.
  - No test scripts or test framework are present in the frontend (`package.json` has no `test` command). Linting is via `eslint .`.
  - The frontend uses shadcn/ui and Radix UI primitives. Custom booking forms are mapped to customers in both the frontend and backend configs.

- **Multi-Customer Routing**
  - Customer-specific prompts and voice settings are mapped by phone number in [`server/customer_routing.json`](server/customer_routing.json). Adding a new customer requires updating both this file and the frontend customer list.
  - If a prompt file is missing or unreadable, the backend falls back to a basic prompt and logs a warning.

- **Voice/WebSocket Integration**
  - WebSocket endpoints `/web/ws` (browser) and `/acs/ws` (ACS calls) are hardcoded in both frontend and backend. The `customerId` query param is required for customer routing.
  - Audio streaming uses PCM 24kHz mono. The frontend's `useVoiceAgent` hook manages audio context and cleanup.

- **Infrastructure/Deployment**
  - The project is designed for Azure Container Apps and uses Bicep for IaC. The `azd` CLI deploys from the repo root, bundling both backend and frontend.
  - ACS connection string is injected via Azure Key Vault; local development uses `.env`.
  - Voice Live API is only available in certain Azure regions (e.g., `swedencentral`).

- **Logs & Analysis**
  - Conversation logs are saved as JSON in `server/conversation_logs/` and are gitignored. Use `python server/conversation_analyzer.py` for analysis.
  - Log files may contain sensitive data; handle according to privacy policies.

- **AI Assistant Rules**
  - See [`CLAUDE.md`](CLAUDE.md) for detailed architecture, flow, and deployment notes. Do not duplicate content here—reference as needed.

**Do not add obvious framework defaults or generic commands. Only include project-specific, non-obvious requirements discovered by reading the code and configs.**
