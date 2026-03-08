import os
from core.config import PROJECT_ROOT

def retrieve_graph_context(script_file, code_graph, max_related=3):
    if not script_file:
        return []

    rel_key = os.path.basename(script_file)
    graph_info = code_graph.get(rel_key, {})

    imports = graph_info.get("imports", [])[:max_related]
    used_by = graph_info.get("used_by", [])[:max_related]

    results = []
    seen = set()

    def add_file(rel, tag):
        rel_file = rel.split(".")[-1] + ".py"
        if rel_file in seen:
            return
        seen.add(rel_file)

        rel_path = os.path.join(PROJECT_ROOT, rel_file)
        if not os.path.exists(rel_path):
            return

        try:
            with open(rel_path, "r", encoding="utf-8", errors="ignore") as f:
                preview = f.read(2000)
            results.append(f"[{tag}]\n{rel_file}\n\n{preview}")
        except:
            pass

    for rel in imports:
        add_file(rel, "GRAPH IMPORT")

    for rel in used_by:
        add_file(rel, "GRAPH USED BY")

    return results