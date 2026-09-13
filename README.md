# Argo Bot

Argo Bot is a full-stack assistant for exploring ARGO ocean-float data. Users ask questions in natural language; the backend turns those questions into SQL, runs them against PostgreSQL, and can return charts alongside the answer.

The repo is a monorepo:

| Directory | Stack | Role |
| --- | --- | --- |
| `frontend/` | Next.js 15, React 19, NextAuth, Sass, D3 | Auth, chat UI, profile, rendered visualizations |
| `backend/` | FastAPI, SQLAlchemy, LangChain, Gemini, MCP | Users, chats, SQL agent, visualization pipeline |

## Features

- Email/username registration and JWT login (NextAuth on the frontend, FastAPI on the backend)
- Persistent chat sessions with history
- SQL LLM that generates and executes read-oriented queries against the ARGO database
- HTTP MCP servers for SQL execution (port `8001`) and chart generation (port `8002`)
- Combined pipeline that can return text, HTML, and hosted or local plots
- Health endpoints for the API and both MCP processes

## Architecture

```
Browser (Next.js)
    │  NextAuth + /api/chat/* proxies
    ▼
FastAPI (:8000)
    ├── /api/v1          users, login, chats
    ├── /api/v1/http     SQL agent (HTTP MCP)
    └── /api/v1/pipeline SQL + visualization
            │
            ├── SQL MCP        127.0.0.1:8001
            └── Visualization  127.0.0.1:8002
                    │
                    ▼
            PostgreSQL (ARGO data) + SQLite (users/chats)
```

On startup the API launches both MCP servers as asyncio tasks. Gemini is used for SQL generation and for deciding whether a result should be plotted.

## Prerequisites

- Node.js 20+ and npm
- Python 3.11+
- PostgreSQL with the ARGO dataset loaded
- A [Google AI](https://aistudio.google.com/) API key (Gemini)

Optional: AWS credentials if you want visualization images uploaded to S3 instead of stored locally.

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set at least:

```env
GOOGLE_API_KEY=your_google_api_key
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/DATABASE
USER_DATABASE_URL=sqlite:///./user_data.db
SECRET_KEY=generate-a-long-random-string
VALID_API_KEY=generate-another-random-string
PORT=8000
```

Never commit `.env`. `SECRET_KEY` and `VALID_API_KEY` must be unique values, not the placeholders in `.env.example`.

Start the API (this also starts the MCP servers):

```bash
python main.py
```

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- SQL MCP: `http://127.0.0.1:8001/mcp`
- Visualization MCP: `http://127.0.0.1:8002/mcp`

### 2. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXTAUTH_SECRET=generate-a-long-random-string
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000/
```

```bash
npm run dev
```

Open `http://localhost:3000`. Register an account, then use the chat UI.

`NEXT_PUBLIC_BACKEND_API_URL` must include the trailing slash.

## Environment variables

### Backend (`backend/.env`)

| Variable | Required | Purpose |
| --- | --- | --- |
| `GOOGLE_API_KEY` | Yes | Gemini for SQL and visualization LLMs |
| `DATABASE_URL` | Yes | PostgreSQL ARGO database |
| `USER_DATABASE_URL` | Yes | SQLite (or other) store for users and chats |
| `SECRET_KEY` | Yes | JWT signing for login and chat tokens |
| `VALID_API_KEY` | Recommended | Internal API key check |
| `PORT` | No (default `8000`) | FastAPI bind port |
| `MCP_SERVER_HOST` / `MCP_SERVER_PORT` | No | SQL MCP bind (default `localhost:8001`) |
| `SQL_MAX_RESULTS` | No (default `1000`) | Cap on SQL rows returned |
| `SQL_QUERY_TIMEOUT` | No (default `30`) | Query timeout in seconds |
| `CSV_OUTPUT_DIR` | No (default `datasets`) | Directory for exported CSVs |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION` | No | S3 upload for generated charts |

See `backend/.env.example` for the full list. Replace every sample secret and database URL before running.

### Frontend (`frontend/.env.local`)

| Variable | Required | Purpose |
| --- | --- | --- |
| `NEXTAUTH_SECRET` | Yes | NextAuth JWT secret |
| `NEXTAUTH_URL` | Yes in production | Public site URL |
| `NEXT_PUBLIC_BACKEND_API_URL` | Yes | FastAPI base URL, with trailing slash |

## API surface

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Service info |
| `GET` | `/health` | API + MCP health |
| `POST` | `/api/v1/register` | Create a user |
| `POST` | `/api/v1/login` | OAuth2 password login, returns JWT |
| `GET` | `/api/v1/getusers` | List users (authenticated) |
| `POST` | `/api/v1/chat/newchat` | Start a chat session |
| `POST` | `/api/v1/http/...` | HTTP SQL agent routes |
| `POST` | `/api/v1/pipeline/combined-pipeline` | SQL + optional visualization |
| `POST` | `/api/v1/pipeline/sql-only` | SQL only |
| `GET` | `/api/v1/pipeline/health` | Pipeline health |

Interactive docs live at `/docs` while the backend is running.

## Project layout

```
.
├── frontend/                 Next.js app
│   ├── src/app/              routes: auth, chat, profile, API proxies
│   ├── src/components/       chat, layout, auth, profile
│   ├── src/context/          auth and sidebar state
│   └── src/middleware.js     session gate
└── backend/
    ├── main.py               FastAPI app + MCP lifespan
    ├── config.py             environment and model settings
    ├── routers/              users, chats, SQL, pipeline
    ├── agents/               SQL and visualization agents
    ├── services/             LLM and MCP client setup
    ├── models/               User, Chat, Message
    ├── database/             SQLAlchemy engines
    ├── datasets/             schema notes and SQL examples
    └── mcp_*.py              HTTP MCP servers and clients
```

## Scripts

Frontend (`frontend/`):

```bash
npm run dev      # Next.js with Turbopack
npm run build    # production build
npm run start    # serve the production build
npm run lint     # ESLint
```

Backend (`backend/`):

```bash
python main.py                 # API + both MCP servers
python start_mcp_server.py     # SQL MCP only, if you need it standalone
```

## Data

`backend/datasets/` includes `database_schema.json`, example SQL, and ARGO context used to ground the SQL agent. Point `DATABASE_URL` at a PostgreSQL instance that matches that schema.

## Security notes

- Keep `.env` and `.env.local` out of git (the root `.gitignore` already ignores them).
- Generate unique `SECRET_KEY`, `VALID_API_KEY`, and `NEXTAUTH_SECRET` values. Do not use the example strings.
- MCP servers bind to `127.0.0.1` by default. Do not expose them on a public interface.
- Restrict FastAPI CORS `allow_origins` before deploying to production; the current default is open for local development.
- Treat `backend/.env.example` as a template only. Rotate any credential that was ever committed in git history.
