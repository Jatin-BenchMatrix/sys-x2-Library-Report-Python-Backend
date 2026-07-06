"""AI via OpenRouter (OpenAI-compatible chat completions).

Two uses, both with deterministic offline fallbacks so the prototype always works:
  - generate_narrative(): a short text summary of a report (AI returns text, not HTML)
  - pick_report():        natural language -> the best matching saved report

Per the agreed model: the AI returns a *response* (text / a choice); Python renders.
"""
import json
import re

import httpx

from config import config


def _chat(messages, model=None, temperature=0.3):
    """One OpenRouter chat-completion call. Returns text, or None on any failure."""
    if not config.openrouter_api_key:
        return None
    try:
        resp = httpx.post(
            f"{config.openrouter_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {config.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model or config.openrouter_model,
                "messages": messages,
                "temperature": temperature,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        return (resp.json()["choices"][0]["message"]["content"] or "").strip()
    except Exception:
        return None


# ---- Narrative ----
def _fallback_narrative(title, columns, row_count):
    cols = ", ".join(columns[:6]) + ("…" if len(columns) > 6 else "")
    return (
        f"This “{title}” report returned {row_count} record(s) across "
        f"{len(columns)} column(s): {cols}."
    )


def generate_narrative(title, columns, rows, model=None):
    row_count = len(rows)
    text = _chat(
        [
            {"role": "system", "content": "You write short, factual report summaries."},
            {
                "role": "user",
                "content": (
                    f"You are a risk & compliance analyst. Write a concise 2-3 sentence "
                    f"executive summary for a report titled '{title}'. Columns: {columns}. "
                    f"Sample data (up to 15 rows): {rows[:15]}. Total rows: {row_count}. "
                    f"Be factual, no markdown, no preamble."
                ),
            },
        ],
        model=model,
    )
    return text or _fallback_narrative(title, columns, row_count)


# ---- Report selection (NL -> report) ----
def _extract_json(text):
    if not text:
        return {}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        return json.loads(match.group(0)) if match else {}
    except Exception:
        return {}


def _keyword_pick(prompt, reports):
    words = {w for w in re.findall(r"[a-z0-9]+", (prompt or "").lower()) if len(w) > 2}
    best, best_score = None, 0
    for r in reports:
        title = (r.get("title") or "").lower()
        score = sum(1 for w in words if w in title)
        if score > best_score:
            best, best_score = r, score
    chosen = best or reports[0]
    reason = (
        f"Matched “{chosen.get('title')}” by keywords."
        if best
        else f"No clear match — defaulted to “{chosen.get('title')}”."
    )
    return {"report_id": chosen["id"], "reason": reason, "chart_column": None}


# ---- Module routing (NL -> which module's knowledge to load) ----
def route_module(message, modules, current=None, model=None):
    """Pick the module a request belongs to. Falls back to keyword match / current."""
    names = [m["name"] for m in modules]
    if not names:
        return None

    listing = [{"name": m["name"], "description": m.get("description", "")} for m in modules]
    text = _chat(
        [
            {"role": "system", "content": "You route a report request to ONE module. Return ONLY JSON."},
            {
                "role": "user",
                "content": (
                    f"Modules (JSON): {listing}\n"
                    f"Current module (may be reused if the request doesn't name a new one): {current}\n"
                    f"User request: {message}\n\n"
                    'Return ONLY: {"module": "<one of the module names, or current>"}'
                ),
            },
        ],
        model=model,
        temperature=0.0,
    )
    data = _extract_json(text)
    chosen = data.get("module")
    if chosen in names:
        return chosen

    # Fallback: keyword match on name, else keep current, else first module.
    low = (message or "").lower()
    for n in names:
        if n.lower() in low:
            return n
    return current if current in names else None


# ---- Widget generation (module KB only -> widget spec + SQL) ----
_WIDGET_SYSTEM = """You are a business analyst that turns a natural-language request into ONE dashboard widget for a MySQL database.

You are given ONLY the knowledge for the relevant module. Rules:
- Use ONLY tables, columns and joins documented in the knowledge. NEVER invent names.
- Generate a single optimized SELECT statement. Use table aliases. No INSERT/UPDATE/DELETE/DDL, no semicolons.
- Support filtering/grouping/sorting as the request implies.

Return ONLY JSON:
{
  "reply": "<one short sentence to the user>",
  "type": "chart" | "kpi" | "table",
  "title": "<widget title>",
  "chartType": "bar|line|pie|donut|area|stacked|hbar"  (only when type=chart, else null),
  "sql": "<the SELECT>"
}

SQL shape by type:
- chart: SELECT must return exactly two columns aliased `label` and `value` (value numeric). For monthly trends, label is the period.
- kpi:   SELECT must return one row with a single numeric column aliased `value`.
- table: SELECT returns the requested display columns with friendly aliases.
"""


def build_widget(messages, module_kb, model=None):
    """Given the conversation + a module's knowledge, return a widget spec dict."""
    convo = [{"role": "system", "content": _WIDGET_SYSTEM},
             {"role": "system", "content": "MODULE KNOWLEDGE:\n" + module_kb}]
    convo.extend(messages)
    text = _chat(convo, model=model, temperature=0.1)
    data = _extract_json(text)
    if not data.get("sql"):
        return None
    return {
        "reply": (data.get("reply") or "").strip() or "Here is your widget.",
        "type": (data.get("type") or "table").strip(),
        "title": (data.get("title") or "Report").strip(),
        "chartType": (data.get("chartType") or None),
        "sql": data["sql"].strip(),
    }


def pick_report(prompt, reports, model=None):
    """Choose the best saved report for a natural-language request.

    Returns {"report_id", "reason", "chart_column"}. Falls back to keyword
    matching when the AI is unavailable or returns something invalid.
    """
    if not reports:
        return {"report_id": None, "reason": "No reports available.", "chart_column": None}

    listing = [{"id": r["id"], "title": r.get("title", "")} for r in reports]
    text = _chat(
        [
            {"role": "system", "content": "You select the single best report and return ONLY JSON."},
            {
                "role": "user",
                "content": (
                    f"User request: {prompt}\n\nAvailable reports (JSON): {listing}\n\n"
                    'Return ONLY: {"report_id": <id from the list>, '
                    '"reason": "one short sentence", "chart_column": null}.'
                ),
            },
        ],
        model=model,
        temperature=0.0,
    )

    data = _extract_json(text)
    valid_ids = {r["id"] for r in reports}
    try:
        rid = int(data.get("report_id"))
    except (TypeError, ValueError):
        rid = None

    if rid not in valid_ids:
        return _keyword_pick(prompt, reports)

    return {
        "report_id": rid,
        "reason": (data.get("reason") or "").strip(),
        "chart_column": data.get("chart_column") or None,
    }
