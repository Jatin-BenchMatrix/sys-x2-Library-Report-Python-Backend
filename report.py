"""Report data layer — reads the same report_builder / report_filter tables the
Go backend writes to, runs the saved query, and shapes rows.

Includes a Python port of the Go filter injection (inject WHERE/AND before the
top-level ORDER BY, paren/quote-aware) so saved filters apply the same way.
"""
import html
import re

# ---- HTML (p-editor rich text) -> plain text, same idea as the frontend ----
_TAG_RE = re.compile(r"<[^>]*>", re.DOTALL)
_WS_RE = re.compile(r"\s+")


def html_to_text(value):
    if value is None:
        return ""
    s = str(value)
    if "<" not in s and "&" not in s:
        return s
    s = _TAG_RE.sub(" ", s)
    s = html.unescape(s)
    return _WS_RE.sub(" ", s).strip()


# ---- report_builder access ----
def _table_missing(err: Exception) -> bool:
    msg = str(err).lower()
    return "doesn't exist" in msg or "does not exist" in msg


def list_reports(conn):
    """All saved reports (for the listing)."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, COALESCE(`key`,'') AS `key`, COALESCE(title,'') AS title, "
                "COALESCE(`module`,'') AS `module`, COALESCE(`status`,'') AS `status` "
                "FROM report_builder ORDER BY id DESC"
            )
            return cur.fetchall()
    except Exception as err:
        if _table_missing(err):
            return []
        raise


def resolve_user_name(conn, user_id):
    """Display name for the report footer. The JWT 'userId' claim is the string
    config_user.USER_ID column (not the numeric PK) — that's the correct lookup."""
    if not user_id:
        return ""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(USER_NAME,'') AS name FROM config_user WHERE USER_ID = %s",
                (user_id,),
            )
            row = cur.fetchone()
            return row["name"] if row else ""
    except Exception:
        return ""


def get_report(conn, report_id):
    """One saved report's title + query."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(title,'') AS title, COALESCE(query,'') AS query "
            "FROM report_builder WHERE id = %s",
            (report_id,),
        )
        return cur.fetchone()


def run_query(conn, query, selections=None):
    """Run the (filter-injected) query; return (columns_in_order, rows_as_dicts)."""
    final_sql, args = inject_filters(query, selections or [])
    with conn.cursor() as cur:
        cur.execute(final_sql, args)
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
    # Convert any rich-text cells to plain text for display.
    clean = [{col: html_to_text(row.get(col)) for col in columns} for row in rows]
    return columns, clean


# ---- Filter injection (port of Go controller/GenerateController.go) ----
def build_conditions(selections):
    conds, args = [], []
    for s in selections or []:
        fp = (s.get("fieldProperty") or "").strip()
        values = s.get("values") or []
        if not fp or not values:
            continue
        ftype = s.get("fieldType")
        if ftype == "datepickerrange":
            vals = [v for v in values if v is not None]
            if len(vals) >= 2:
                conds.append(f"{fp} BETWEEN %s AND %s")
                args.extend([str(vals[0]), str(vals[1])])
        elif ftype == "boolean":
            if values[0] is not None:
                conds.append(f"{fp} = %s")
                args.append(str(values[0]))
        else:  # dropdownmultiselect, treemultiselect, free text
            placeholders = []
            for v in values:
                if v is None:
                    continue
                placeholders.append("%s")
                args.append(str(v))
            if placeholders:
                conds.append(f"{fp} IN ({', '.join(placeholders)})")
    return conds, args


def inject_filters(query, selections):
    conds, args = build_conditions(selections)
    if not conds:
        return query, []
    insert_idx, has_where = _scan_query(query)
    prefix = " AND " if has_where else " WHERE "
    clause = prefix + " AND ".join(conds) + " "
    if insert_idx < 0:
        return query + clause, args
    return query[:insert_idx] + clause + query[insert_idx:], args


def _scan_query(q):
    """Find the first top-level ORDER BY/GROUP BY/LIMIT/HAVING (insertion point)
    and whether a top-level WHERE already exists. Skips quoted strings + parens."""
    lower = q.lower()
    insert_idx, depth = -1, 0
    in_s = in_d = in_b = False

    def at(i, kw):
        if lower[i:i + len(kw)] != kw:
            return False
        if i > 0 and q[i - 1] not in " \t\n\r)":
            return False
        return True

    has_where = False
    i = 0
    while i < len(q):
        ch = q[i]
        if in_s:
            if ch == "'":
                in_s = False
        elif in_d:
            if ch == '"':
                in_d = False
        elif in_b:
            if ch == "`":
                in_b = False
        elif ch == "'":
            in_s = True
        elif ch == '"':
            in_d = True
        elif ch == "`":
            in_b = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0:
            if not has_where and at(i, "where"):
                has_where = True
            if insert_idx == -1 and (
                at(i, "order by") or at(i, "group by") or at(i, "limit") or at(i, "having")
            ):
                insert_idx = i
        i += 1
    return insert_idx, has_where
