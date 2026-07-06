# sys-x2-Library-Report-Python-Backend

**Prototype 3** — Python report backend (FastAPI). DB-connection skeleton with the
**same** multi-tenant model as the Go backend, on the **same port (8090)** and the
same `/api/report/*` path, so the Angular proxy works for this prototype unchanged.

## File ↔ Go backend mapping
| Python | Go equivalent |
|---|---|
| `config.py` | `config/viperConfig.go` + `model/config.go` |
| `db.py` | `config/dbConfig.go` + `controller/db.go` + tenant parsing in `middleware/TenantMiddleware.go` |
| `security.py` | `middleware/TokenFilter.go` + `middleware/TenantMiddleware.go` (JWT → master DB → tenant DSN) |
| `routes.py` | `router/reportRoutes.go` |
| `main.py` | `router/routing.go` + `main.go` |

## Connection model (identical to Go)
- `TENANT=true` → validate JWT (HS256, `JWT_SECRET_KEY`), read `tenantID` claim, look it
  up in the master DB (`hostdb.config_tenant`), parse `tenant_connection`
  (`user=..;password=..;server=..;port=..;database=..`), connect to that tenant DB.
- `TENANT=false` → use the default DB (`CLIENT1DB_*`); JWT checked only if `VERIFY_TOKEN=true`.
- The connection is opened per request and closed afterward (FastAPI dependency `get_request_context`).

## Run
```bash
cd sys-x2-Library-Report-Python-Backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
Serves on `http://localhost:8090`.

> Run only **one** report backend (Go or Python) at a time — both use port 8090.

## Verify
- `GET http://localhost:8090/api/health` → `{"status":"ok",...}` (public)
- `GET http://localhost:8090/api/report/ping` with `Authorization: Bearer <jwt>` →
  `{"db":"reachable","result":{"ok":1},"tenant":"...","user":"..."}`

## Next
Report endpoints (run saved query → rows, filters, AI narrative, server-side
charts/HTML/PDF) — to be added on top of this skeleton.

⚠️ `dev.env` holds live local secrets and is git-ignored. Rotate the shared
OpenRouter key before any real deployment.
