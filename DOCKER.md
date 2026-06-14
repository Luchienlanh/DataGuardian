# Docker Quick Start

Run these commands from the project root:

```powershell
cd "C:\Users\Luc\OneDrive\Documents\Multi Agent"
docker compose up --build
```

Open the app:

```text
http://127.0.0.1:8017
```

Stop the app:

```powershell
docker compose down
```

Run in the background:

```powershell
docker compose up -d --build
```

View logs:

```powershell
docker compose logs -f backend
```

Rebuild after changing dependencies:

```powershell
docker compose build --no-cache
docker compose up
```

Notes:

- `backend/.env` is loaded into the container for LLM keys and model settings.
- `backend/dataguard.db` is mounted into the container so your SQLite data persists.
- `backend/storage` is mounted into the container so uploaded, cleaned, and report files persist.
- Never commit `.env`, database files, or storage files.
