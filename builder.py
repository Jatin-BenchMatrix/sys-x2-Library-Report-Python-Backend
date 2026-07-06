"""Widget builder — validate the AI's SQL, run it, and map the result rows into a
widget block (chart / kpi / table) with data embedded, ready for the frontend.
"""
import re

from report import html_to_text

_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|replace|grant|revoke|call|merge)\b",
    re.IGNORECASE,
)


def validate_sql(sql: str):
    """Allow a single read-only SELECT only. Returns (ok, error)."""
    s = (sql or "").strip().rstrip(";").strip()
    if not s:
        return False, "empty SQL"
    if ";" in s:
        return False, "multiple statements are not allowed"
    low = s.lower()
    if not (low.startswith("select") or low.startswith("with")):
        return False, "only SELECT queries are allowed"
    if _FORBIDDEN.search(s):
        return False, "only read-only SELECT queries are allowed"
    return True, ""


def _to_number(v):
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return v


def run_widget(conn, spec):
    """Execute spec['sql'] and return a widget block with data, per spec['type']."""
    ok, err = validate_sql(spec.get("sql"))
    if not ok:
        raise ValueError(err)

    with conn.cursor() as cur:
        cur.execute(spec["sql"])
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()

    wtype = spec.get("type", "table")
    block = {"type": wtype, "title": spec.get("title", "Report"), "chartType": spec.get("chartType")}

    if wtype == "chart":
        labels, series = [], []
        for row in rows:
            labels.append(html_to_text(row.get("label")))
            series.append(_to_number(row.get("value")))
        block["data"] = {"labels": labels, "series": series}

    elif wtype == "kpi":
        value = ""
        if rows:
            first = rows[0]
            value = first.get("value", next(iter(first.values()), ""))
        block["data"] = [{"label": spec.get("title", "Total"), "value": _to_number(value)}]

    else:  # table
        clean = [{c: html_to_text(r.get(c)) for c in columns} for r in rows]
        block["data"] = {"columns": columns, "rows": clean}

    return block
