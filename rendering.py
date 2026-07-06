"""Server-side report rendering — the core of the Python prototype.

pandas (shape) + matplotlib (chart, as an embedded PNG) + Jinja2 (HTML template).
Produces a single self-contained HTML document the frontend can display as-is.
"""
import base64
import io
import os
from datetime import datetime

import matplotlib

matplotlib.use("Agg")  # headless: render to a buffer, no display
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from jinja2 import Environment, FileSystemLoader, select_autoescape  # noqa: E402

_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)


def _to_frame(columns, rows):
    return pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame(columns=columns)


def _pick_categorical_column(df: pd.DataFrame):
    """Pick a low-cardinality, short-valued column to chart (e.g. Status, Category)."""
    best = None
    for col in df.columns:
        series = df[col].astype(str).replace("", pd.NA).dropna()
        if series.empty:
            continue
        distinct = series.nunique()
        avg_len = series.str.len().mean()
        if 2 <= distinct <= 15 and avg_len <= 40:
            # Prefer the column with the fewest categories (cleanest bar chart).
            if best is None or distinct < best[1]:
                best = (col, distinct)
    return best[0] if best else None


def build_chart(columns, rows, chart_column=None):
    """Return a base64 PNG data URI of a bar chart, or None if nothing suitable.

    Honors chart_column (e.g. picked by the AI) when it is a real column;
    otherwise auto-picks a low-cardinality column.
    """
    df = _to_frame(columns, rows)
    if df.empty:
        return None, None
    col = chart_column if (chart_column and chart_column in df.columns) else _pick_categorical_column(df)
    if not col:
        return None, None

    counts = df[col].astype(str).replace("", "(blank)").value_counts().head(12)

    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.bar(counts.index.astype(str), counts.values, color="#1e6ea5")
    ax.set_title(f"Count by {col}", fontsize=11, fontweight="bold")
    ax.set_ylabel("Count")
    ax.tick_params(axis="x", labelrotation=30, labelsize=8)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110)
    plt.close(fig)
    buf.seek(0)
    data_uri = "data:image/png;base64," + base64.b64encode(buf.read()).decode("ascii")
    return data_uri, col


def _kpis(columns, rows):
    df = _to_frame(columns, rows)
    kpis = [{"label": "Records", "value": f"{len(df):,}"},
            {"label": "Columns", "value": str(len(columns))}]
    # First column that is mostly numeric -> show its total.
    for col in df.columns:
        numeric = pd.to_numeric(df[col], errors="coerce")
        if numeric.notna().mean() >= 0.6 and numeric.notna().any():
            total = numeric.sum()
            kpis.append({"label": f"Total {col}", "value": f"{total:,.2f}"})
            break
    return kpis


def _format_when(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
    except Exception:
        dt = datetime.now()
    return dt.strftime("%A, %B %d, %Y at %H:%M")


def render_report_html(title, columns, rows, narrative, generated_by="", generated_on="", chart_column=None):
    chart_uri, chart_col = build_chart(columns, rows, chart_column)
    template = _env.get_template("report.html")
    return template.render(
        title=title or "Report",
        columns=columns,
        rows=rows,
        narrative=narrative,
        kpis=_kpis(columns, rows),
        chart_uri=chart_uri,
        chart_col=chart_col,
        generated_by=generated_by,
        generated_on=_format_when(generated_on),
        row_count=len(rows),
    )
