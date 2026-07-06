"""Module Knowledge Base loader.

The AI must NEVER see the whole 600-table schema. Each business module has its own
documentation folder under knowledge/<Module>/, and only the relevant module's docs
are loaded into the AI context for a given request.
"""
import os

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge")
_DOC_FILES = ["module.md", "tables.md", "relationships.md", "business_rules.md", "report_examples.md"]


def _description(module_md_path: str) -> str:
    """First paragraph under '## Description' in module.md (for module routing)."""
    try:
        with open(module_md_path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return ""
    lines = text.splitlines()
    out, capture = [], False
    for line in lines:
        if line.strip().lower().startswith("## description"):
            capture = True
            continue
        if capture:
            if line.strip().startswith("##"):
                break
            if line.strip():
                out.append(line.strip())
    return " ".join(out).strip()


def list_modules():
    """All modules: [{name, description}]. Name = folder name under knowledge/."""
    mods = []
    if not os.path.isdir(KNOWLEDGE_DIR):
        return mods
    for name in sorted(os.listdir(KNOWLEDGE_DIR)):
        path = os.path.join(KNOWLEDGE_DIR, name)
        if os.path.isdir(path):
            mods.append({"name": name, "description": _description(os.path.join(path, "module.md"))})
    return mods


def module_names():
    return [m["name"] for m in list_modules()]


def load_module(name: str):
    """Concatenated docs for one module, or None if unknown. Guards against traversal
    by only accepting an actual module folder name."""
    if name not in module_names():
        return None
    base = os.path.join(KNOWLEDGE_DIR, name)
    parts = []
    for fn in _DOC_FILES:
        path = os.path.join(base, fn)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                parts.append(f"===== {fn} =====\n{f.read()}")
    return "\n\n".join(parts)
