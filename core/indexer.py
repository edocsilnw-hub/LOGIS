import os
import json
import numpy as np
import logging
from core.config import PROJECT_ROOT, VECTORS_DIR
from core.ai_engine import call_ollama, get_embedding


import re

def extract_imports(content):
    imports = []
    imports += re.findall(r"import\s+([a-zA-Z0-9_\.]+)", content)
    imports += re.findall(r"from\s+([a-zA-Z0-9_\.]+)\s+import", content)
    return list(set(imports))

def extract_functions(content):
    return re.findall(r"def\s+([a-zA-Z0-9_]+)\(", content)

def extract_classes(content):
    return re.findall(r"class\s+([a-zA-Z0-9_]+)", content)

code_graph = {}

for root, dirs, files in os.walk(PROJECT_ROOT):

    if any(x in root for x in ["venv","__pycache__",".git","logs","vectors","data",".vscode"]):
        continue

    for file in files:

        if not (file.endswith(".py") or file.endswith(".cs")):
            continue

        path = os.path.join(root, file)
        rel_path = os.path.relpath(path, PROJECT_ROOT)

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        line_count = content.count("\n") + 1
        file_size = os.path.getsize(path)

        imports = extract_imports(content)
        functions = extract_functions(content)
        classes = extract_classes(content)

        code_graph[rel_path] = {
            "imports": imports,
            "functions": functions,
            "classes": classes,
            "line_count": line_count,
            "file_size": file_size
        }

# Build reverse dependency map
for script, data in code_graph.items():

    for imp in data["imports"]:

        for target in code_graph.keys():

            if target.replace("/", ".").startswith(imp):

                if "used_by" not in code_graph[target]:
                        code_graph[target]["used_by"] = []

                if script not in code_graph[target]["used_by"]:
                        code_graph[target]["used_by"].append(script)

os.makedirs(VECTORS_DIR, exist_ok=True)
graph_path = os.path.join(VECTORS_DIR,"code_graph.json")

with open(graph_path,"w",encoding="utf-8") as f:
    json.dump(code_graph,f,indent=2)

print("[INDEXER] Code graph saved.")

def summarize_script_content(script_name, content):
    content = content[:12000]
    prompt = (
        "You are generating a structured technical summary of a code file.\n\n"
        "Summarize the following script with:\n"
        "- Purpose\n"
        "- Key Classes\n"
        "- Key Methods\n"
        "- Dependencies\n"
        "- Critical Behaviors\n\n"
        "Keep it under 4000 characters.\n\n"
        f"SCRIPT NAME: {script_name}\n\n"
        f"{content}\n\n"
        "SUMMARY:"
    )
    summary, _ = call_ollama(prompt)
    return summary


def index_codebase():
    registry = {}
    logging.info("[INDEXER] Mapping codebase into vector memory...")
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if any(x in root for x in ["venv", "__pycache__", ".git", "logs", "vectors", "data"]):
            continue
        for file in files:
            if not (file.endswith(".py") or file.endswith(".cs")):
                continue
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, PROJECT_ROOT)

            safe_name = rel_path.replace("\\", "_").replace("/", "_")
            vector_check = os.path.join(VECTORS_DIR, f"{safe_name}_chunk_0.npy")

            if not os.path.exists(vector_check):
                needs_index = True
            else:
                script_time = os.path.getmtime(path)
                vector_time = os.path.getmtime(vector_check)

                if script_time > vector_time:
                    needs_index = True
            if needs_index:
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    chunks = chunk_script(content)

                    registry.setdefault(rel_path, {"chunks": []})

                    for i, chunk in enumerate(chunks):

                        vec = get_embedding(chunk)

                        vector_name = f"{safe_name}_chunk_{i}.npy"
                        vector_path = os.path.join(VECTORS_DIR, vector_name)

                        np.save(vector_path, np.array(vec))

                        registry[rel_path]["chunks"].append({
                            "chunk": i,
                            "vector_file": vector_name
                        })

                    logging.info(f"[INDEXER] Vectorized: {file} ({len(chunks)} chunks)")

                except Exception as e:
                    logging.error(f"[INDEXER] Failed on {file}: {e}")
def save_dependency_map(dep_map):
    path = os.path.join(VECTORS_DIR, "dependency_map.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dep_map, f, indent=2)
        logging.info("[INDEXER] Dependency map saved.")
    except Exception as e:
        logging.error(f"[INDEXER] Failed to save dependency map: {e}")


def build_dependency_map():
    dependency_map = {}
    scripts = []

    for root, dirs, files in os.walk(PROJECT_ROOT):
        if any(x in root for x in ["venv", "__pycache__", ".git"]):
            continue
        for file in files:
            if file.endswith(".py") or file.endswith(".cs"):
                scripts.append(file)

    for root, dirs, files in os.walk(PROJECT_ROOT):
        if any(x in root for x in ["venv", "__pycache__", ".git"]):
            continue
        for file in files:
            if not (file.endswith(".py") or file.endswith(".cs")):
                continue

            path = os.path.join(root, file)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                references = []
                base_name = file.replace(".py", "").replace(".cs", "")

                for script in scripts:
                    name = script.replace(".py", "").replace(".cs", "")

                    import re

                    pattern = r"\b" + re.escape(name) + r"\b"

                    if name != base_name and re.search(pattern, content):
                        references.append(name)

                dependency_map[file] = references

            except:
                dependency_map[file] = []

    print("DEPENDENCY MAP BUILT:", len(dependency_map), "scripts")

    return dependency_map

def chunk_script(content, chunk_size=1200, overlap=200):
    chunks = []
    start = 0

    while start < len(content):
        end = start + chunk_size
        chunk = content[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks

def load_code_graph():

    graph_path = os.path.join(VECTORS_DIR, "code_graph.json")

    if not os.path.exists(graph_path):
        return index_codebase()

    with open(graph_path, "r", encoding="utf-8") as f:
        return json.load(f)