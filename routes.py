"""Routes — mounted under ROUTER_PATH (/api).

  GET  /api/health                      public health check
  GET  /api/report/ping                 verifies the tenant DB connection
  GET  /api/report/list                 saved reports (from report_builder)
  GET  /api/report/generate/{id}        runs the report -> server-rendered HTML
  POST /api/report/generate/{id}        same, with filter selections in the body
  GET  /api/report/data/{id}            JSON variant (columns + rows), for comparison

The Python prototype's signature move: /generate returns fully rendered HTML
(pandas + matplotlib chart + Jinja2 + AI narrative). The frontend just displays it.
"""
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import HTMLResponse

import report as report_data
from ai import build_widget, generate_narrative, pick_report, route_module
from builder import run_widget
from knowledge import list_modules, load_module
from rendering import render_report_html
from security import RequestContext, get_request_context

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "report-python-backend"}


report = APIRouter(prefix="/report")


@report.get("/ping")
def ping(ctx: RequestContext = Depends(get_request_context)):
    with ctx.conn.cursor() as cur:
        cur.execute("SELECT 1 AS ok")
        row = cur.fetchone()
    return {"db": "reachable", "result": row, "tenant": ctx.tenant_id, "user": ctx.user_id}


@report.get("/list")
def list_reports(ctx: RequestContext = Depends(get_request_context)):
    return report_data.list_reports(ctx.conn)


def _run(ctx: RequestContext, report_id: int, selections):
    rpt = report_data.get_report(ctx.conn, report_id)
    if not rpt:
        raise HTTPException(status_code=404, detail="Report not found")
    if not (rpt.get("query") or "").strip():
        raise HTTPException(status_code=400, detail="Report has no query")
    try:
        columns, rows = report_data.run_query(ctx.conn, rpt["query"], selections)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to run report query: {err}")
    return rpt, columns, rows


@report.get("/generate/{report_id}", response_class=HTMLResponse)
def generate_get(report_id: int, ctx: RequestContext = Depends(get_request_context)):
    return _generate_html(ctx, report_id, [])


@report.post("/generate/{report_id}", response_class=HTMLResponse)
def generate_post(report_id: int, body: dict = Body(default={}),
                  ctx: RequestContext = Depends(get_request_context)):
    return _generate_html(ctx, report_id, body.get("selections") or [])


def _generate_html(ctx, report_id, selections):
    rpt, columns, rows = _run(ctx, report_id, selections)
    narrative = generate_narrative(rpt["title"], columns, rows)
    html = render_report_html(
        title=rpt["title"],
        columns=columns,
        rows=rows,
        narrative=narrative,
        generated_by=report_data.resolve_user_name(ctx.conn, ctx.user_id),
        generated_on=datetime.now().isoformat(),
    )
    return HTMLResponse(content=html)


@report.get("/data/{report_id}")
def report_json(report_id: int, ctx: RequestContext = Depends(get_request_context)):
    """JSON variant — to compare the 'Go returns JSON' shape against the HTML one."""
    rpt, columns, rows = _run(ctx, report_id, [])
    return {"title": rpt["title"], "columns": columns, "rows": rows}


@report.post("/ask", response_class=HTMLResponse)
def ask(body: dict = Body(default={}), ctx: RequestContext = Depends(get_request_context)):
    """Natural language -> AI picks the best saved report -> Python renders HTML."""
    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    reports = report_data.list_reports(ctx.conn)
    if not reports:
        raise HTTPException(status_code=404, detail="No reports configured")

    pick = pick_report(prompt, reports)
    if not pick.get("report_id"):
        raise HTTPException(status_code=404, detail="Could not match a report to that request")

    rpt, columns, rows = _run(ctx, pick["report_id"], [])
    narrative = generate_narrative(rpt["title"], columns, rows)
    if pick.get("reason"):
        narrative = f"{pick['reason']} {narrative}"

    html = render_report_html(
        title=rpt["title"],
        columns=columns,
        rows=rows,
        narrative=narrative,
        generated_by=report_data.resolve_user_name(ctx.conn, ctx.user_id),
        generated_on=datetime.now().isoformat(),
        chart_column=pick.get("chart_column"),
    )
    return HTMLResponse(content=html)


@report.get("/modules")
def modules():
    """Available modules in the knowledge base (name + description)."""
    return list_modules()


@report.post("/chat")
def chat(body: dict = Body(default={}), ctx: RequestContext = Depends(get_request_context)):
    """Conversational report builder.

    NL request -> route module -> load ONLY that module's knowledge -> AI builds a
    widget spec + SQL -> validate -> run -> return a widget block with data.
    """
    messages = body.get("messages") or []
    current_module = body.get("module")
    last_user = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")

    mods = list_modules()
    if not mods:
        return {"reply": "No module knowledge is configured on the server.", "module": None, "blocks": []}

    module = route_module(last_user, mods, current=current_module)
    if not module:
        names = ", ".join(m["name"] for m in mods)
        return {"reply": f"Which module is this for? Available: {names}.", "module": None, "blocks": []}

    kb = load_module(module)
    spec = build_widget(messages, kb)
    if not spec:
        return {"reply": "I couldn't turn that into a widget. Try naming the chart type and the field.",
                "module": module, "blocks": []}

    try:
        block = run_widget(ctx.conn, spec)
    except Exception as err:
        return {"reply": f"The generated query failed ({err}). Try rephrasing.",
                "module": module, "blocks": [], "sql": spec.get("sql")}

    return {"reply": spec["reply"], "module": module, "blocks": [block], "sql": spec.get("sql")}


router.include_router(report)
