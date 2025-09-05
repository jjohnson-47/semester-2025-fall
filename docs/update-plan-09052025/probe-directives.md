# Executable Probe Directives for Orchestration

## Quick Start for Claude Code CLI

```bash
# Save this file as probe_directives.md
# Then execute with:
claude-code --task "Execute Probe V2 from probe_directives.md"
claude-code --task "Execute Probe V3 from probe_directives.md"
```

---

# Probe V2: Repository State & Architecture

**Objective**: Produce a precise snapshot of the current system (code, data, schemas, templates, tests, pipelines) so we can plan work that aligns with reality. Read-only only. Redact secrets.

**Deliverables**:
* `docs/_generated/state_probe.md` – human summary (≤300 lines)
* `docs/_generated/state_probe.json` – machine summary
* `docs/_generated/db_schema.sql` – SQLite schema dump (if DB exists)
* `docs/_generated/templates_report.csv` – template sizes & complexity
* `docs/_generated/workflows_list.txt` – CI workflows list (one per line)

## Execute This Complete Script:

```bash
#!/bin/bash
set -eu

# 0) Create output dir
mkdir -p docs/_generated

# 1) Quick context (git, runtime, tools)
{
  printf "## GIT\n"; git log -1 --oneline || true
  printf "\n## BRANCH\n"; git rev-parse --abbrev-ref HEAD || true
  printf "\n## TAGS (last 5)\n"; git tag --sort=-creatordate | head -5 || true

  printf "\n## PY/TOOLS\n"
  python --version || true
  uv --version 2>/dev/null || true
  pip --version || true

  printf "\n## OS\n"; uname -a || true
} > docs/_generated/state_probe.md

# 2) Project configuration snapshot
{
  printf "\n## PYPROJECT (tool sections)\n"
  awk '/^\[tool\./,/^\[/{print}' pyproject.toml || true

  printf "\n## MYPY/MAKE/PRE-COMMIT\n"
  [ -f mypy.ini ] && sed -n '1,200p' mypy.ini || echo "mypy.ini: none"
  [ -f Makefile ] && awk 'NF && !/^\t#/{print}' Makefile | sed -n '1,200p' || echo "Makefile: none"
  [ -f .pre-commit-config.yaml ] && sed -n '1,200p' .pre-commit-config.yaml || echo "pre-commit: none"
} >> docs/_generated/state_probe.md

# 3) Workflows & deploy config
find .github/workflows -maxdepth 1 -type f -name "*.yml" -o -name "*.yaml" 2>/dev/null | sort > docs/_generated/workflows_list.txt || true

{
  printf "\n## WORKFLOWS (names)\n"
  sed -n '1,200p' docs/_generated/workflows_list.txt || true

  printf "\n## DEPLOY HINTS\n"
  [ -f dashboard/api/deploy.py ] && sed -n '1,200p' dashboard/api/deploy.py || echo "deploy.py: none"
} >> docs/_generated/state_probe.md

# 4) Content & course manifests (facts only)
python - <<'PY' > docs/_generated/_content_scan.json
import os, json, re, sys, hashlib, glob
root = "content/courses"
courses = []
for d in sorted(glob.glob(os.path.join(root, "*"))):
    if not os.path.isdir(d): continue
    code = os.path.basename(d)
    files = sorted(glob.glob(os.path.join(d, "*.json")))
    manifest = os.path.join(d, "course_manifest.json")
    has_manifest = os.path.exists(manifest)
    schema_version = None
    if has_manifest:
        try:
            import json as _j
            with open(manifest, "r", encoding="utf-8") as f:
                j = _j.load(f)
            schema_version = j.get("$schema") or j.get("version")
        except Exception:
            schema_version = "unreadable"
    courses.append({
        "course_code": code,
        "json_files": len(files),
        "has_manifest": has_manifest,
        "schema_version": schema_version,
    })
print(json.dumps({
    "courses_dir_exists": os.path.isdir(root),
    "course_count": len(courses),
    "courses": courses
}, indent=2))
PY

printf "\n## COURSES SUMMARY\n" >> docs/_generated/state_probe.md
sed -n '1,200p' docs/_generated/_content_scan.json >> docs/_generated/state_probe.md

# 5) Templates inventory
python - <<'PY' > docs/_generated/templates_report.csv
import os, csv, glob
rows=[["path","lines","bytes"]]
for p in sorted(glob.glob("templates/**/*.j2", recursive=True)+glob.glob("dashboard/templates/**/*.html", recursive=True)):
    try:
        with open(p,"r",encoding="utf-8",errors="ignore") as f:
            data=f.read()
        rows.append([p, str(data.count("\n")+1), str(len(data.encode("utf-8")))])
    except Exception:
        rows.append([p, "ERR", "ERR"])
with open("docs/_generated/templates_report.csv","w",newline="",encoding="utf-8") as f:
    csv.writer(f).writerows(rows)
print("ok")
PY

printf "\n## LARGE TEMPLATES (>2000 lines or >80KB)\n" >> docs/_generated/state_probe.md
awk -F, 'NR>1 && (($2+0)>2000 || ($3+0)>81920) {printf "%s (%s lines, %s bytes)\n",$1,$2,$3}' docs/_generated/templates_report.csv >> docs/_generated/state_probe.md || true

# 6) SQLite schema & feature flags
DB="dashboard/state/tasks.db"
if [ -f "$DB" ]; then
  sqlite3 "$DB" ".schema" > docs/_generated/db_schema.sql || true
  sqlite3 "$DB" "SELECT name FROM sqlite_master WHERE type='table' ORDER BY 1;" > docs/_generated/_tables.txt || true
  sqlite3 "$DB" "PRAGMA table_info('tasks');" > docs/_generated/_tasks_cols.txt || true
  sqlite3 "$DB" "PRAGMA table_info('course_registry');" > docs/_generated/_registry_cols.txt || true
  sqlite3 "$DB" "PRAGMA table_info('course_projection');" > docs/_generated/_proj_cols.txt || true
  sqlite3 "$DB" "PRAGMA table_info('events');" > docs/_generated/_events_cols.txt || true
  sqlite3 "$DB" "SELECT count(*) FROM tasks;" > docs/_generated/_tasks_count.txt || true
  sqlite3 "$DB" "SELECT count(*) FROM now_queue;" > docs/_generated/_nowq_count.txt 2>/dev/null || true
  sqlite3 "$DB" "SELECT COUNT(*) FROM pragma_table_info('tasks') WHERE name IN ('origin_ref','origin_kind','origin_version');" > docs/_generated/_origin_cols.txt || true

  {
    printf "\n## DB TABLES\n"; sed -n '1,200p' docs/_generated/_tables.txt
    printf "\n## TASKS COLS\n"; sed -n '1,200p' docs/_generated/_tasks_cols.txt
    printf "\n## COURSE REGISTRY COLS\n"; sed -n '1,200p' docs/_generated/_registry_cols.txt
    printf "\n## COURSE PROJECTION COLS\n"; sed -n '1,200p' docs/_generated/_proj_cols.txt
    printf "\n## EVENTS COLS\n"; sed -n '1,200p' docs/_generated/_events_cols.txt
    printf "\n## ROW COUNTS\n"
    printf "tasks: "; sed -n '1p' docs/_generated/_tasks_count.txt
    printf "now_queue: "; sed -n '1p' docs/_generated/_nowq_count.txt || true
    printf "tasks has origin_* cols (count of 3): "; sed -n '1p' docs/_generated/_origin_cols.txt
  } >> docs/_generated/state_probe.md
else
  echo "DB not found at $DB" >> docs/_generated/state_probe.md
fi

# 7) Tests & coverage snapshot
pytest --collect-only -q > docs/_generated/_pytest_collect.txt || true
pytest --markers > docs/_generated/_pytest_markers.txt 2>/dev/null || true

{
  printf "\n## TESTS (collect-only excerpt)\n"
  sed -n '1,60p' docs/_generated/_pytest_collect.txt || true
  printf "\n## MARKERS\n"
  sed -n '1,200p' docs/_generated/_pytest_markers.txt || true
} >> docs/_generated/state_probe.md

( coverage run -m pytest -q && coverage json -o docs/_generated/coverage.json ) || true

# 8) Lint/type configs
{
  printf "\n## RUFF\n"
  [ -f ruff.toml ] && sed -n '1,200p' ruff.toml || echo "ruff.toml: none"
  printf "\n## TYPE CHECK\n"
  grep -nE 'strict|ignore-missing-imports|warn' mypy.ini 2>/dev/null || echo "mypy: summary not available"
} >> docs/_generated/state_probe.md

# 9) Summarize to machine-readable JSON
python - <<'PY' > docs/_generated/state_probe.json
import json, os, re, glob, pathlib
out = {
  "git": {},
  "workflows": [],
  "config": {
    "pyproject_present": os.path.exists("pyproject.toml"),
    "mypy_ini": os.path.exists("mypy.ini"),
    "ruff_toml": os.path.exists("ruff.toml"),
    "makefile": os.path.exists("Makefile"),
    "pre_commit": os.path.exists(".pre-commit-config.yaml"),
  },
  "courses": {},
  "db": {"present": False},
  "tests": {"markers": [], "collect_excerpt": ""},
  "templates": {"large": []},
}
# Git (best-effort)
try:
    head = os.popen("git log -1 --pretty=%H").read().strip()
    branch = os.popen("git rev-parse --abbrev-ref HEAD").read().strip()
    out["git"] = {"head": head, "branch": branch}
except Exception:
    pass

# Workflows
for w in open("docs/_generated/workflows_list.txt","r",encoding="utf-8").read().splitlines() if os.path.exists("docs/_generated/workflows_list.txt") else []:
    out["workflows"].append(w)

# Courses
try:
    import json as _j
    j = _j.load(open("docs/_generated/_content_scan.json","r",encoding="utf-8"))
    out["courses"] = j
except Exception:
    out["courses"] = {"error":"scan failed"}

# DB
db_path = "dashboard/state/tasks.db"
if os.path.exists(db_path):
    out["db"]["present"] = True
    def grep(path, token):
        try:
            for line in open(path,encoding="utf-8"): 
                if token in line: return True
        except Exception:
            pass
        return False
    out["db"]["has_course_registry"] = grep("docs/_generated/_tables.txt","course_registry")
    out["db"]["has_course_projection"] = grep("docs/_generated/_tables.txt","course_projection")
    out["db"]["has_events"] = grep("docs/_generated/_tables.txt","events")
    try:
        cnt = int(open("docs/_generated/_origin_cols.txt","r",encoding="utf-8").read().strip() or "0")
    except Exception:
        cnt = 0
    out["db"]["tasks_has_origin_triplet"] = (cnt == 3)

# Tests
if os.path.exists("docs/_generated/_pytest_markers.txt"):
    out["tests"]["markers"] = [l.strip() for l in open("docs/_generated/_pytest_markers.txt",encoding="utf-8").read().splitlines() if l.strip().startswith("@pytest.mark.")]
if os.path.exists("docs/_generated/_pytest_collect.txt"):
    txt = open("docs/_generated/_pytest_collect.txt",encoding="utf-8").read().splitlines()[:40]
    out["tests"]["collect_excerpt"] = "\n".join(txt)

# Templates
import csv
try:
    with open("docs/_generated/templates_report.csv",encoding="utf-8") as f:
        rd = csv.DictReader(f)
        for r in rd:
            try:
                lines = int(r["lines"]); bytes_ = int(r["bytes"])
                if lines>2000 or bytes_>81920:
                    out["templates"]["large"].append({"path": r["path"], "lines": lines, "bytes": bytes_})
            except Exception:
                pass
except Exception:
    pass

print(json.dumps(out, indent=2))
PY

# 10) Final human summary
{
  printf "\n## QUICK TAKEAWAYS\n"
  if [ -f docs/_generated/_content_scan.json ]; then
    python - <<'PY'
import json; j=json.load(open("docs/_generated/_content_scan.json")); 
cc=j.get("course_count",0)
mf=sum(1 for c in j.get("courses",[]) if c.get("has_manifest"))
print(f"- Courses detected: {cc} (manifests present: {mf})")
PY
  fi
  if [ -f docs/_generated/_tables.txt ]; then
    echo "- DB present: yes"
    grep -q course_projection docs/_generated/_tables.txt && echo "- Projection cache: present" || echo "- Projection cache: missing"
    grep -q course_registry docs/_generated/_tables.txt && echo "- Course registry: present" || echo "- Course registry: missing"
    grep -q events docs/_generated/_tables.txt && echo "- Events table: present" || echo "- Events table: missing"
  else
    echo "- DB present: no (dashboard/state/tasks.db missing)"
  fi
  L=$(awk 'END{print NR-1}' docs/_generated/templates_report.csv 2>/dev/null || echo 0)
  echo "- Templates indexed: $L (see templates_report.csv; watch large files section)"
  echo "- Pytest markers recorded (see _pytest_markers.txt)."
} >> docs/_generated/state_probe.md

echo "Probe V2 Complete. Check docs/_generated/state_probe.{md,json}"
```

---

# Probe V3: Delta-to-Plan Enrichment

**Objective**: Collect the missing, high-signal facts needed for intelligent planning: routes & HTMX, deploy API surface, DB truth, task graph, prioritizer/solver knobs, template modularity, course JSON semantics, test presence, and env/config touchpoints. **Read-only.**

**Deliverables**:
* `docs/_generated/plan_input.json` — machine summary for planners
* `docs/_generated/plan_input.md` — concise human brief (≤250 lines)
* `docs/_generated/api_routes.json` — Flask/HTMX endpoints
* `docs/_generated/deploy_api_map.json` — deploy.py surface & shell calls
* `docs/_generated/db_introspection.json` — tables, indexes, FTS, counts, NULLs
* `docs/_generated/task_graph.dot` — DOT graph (tasks + deps)
* `docs/_generated/template_map.json` — Jinja extends/include/macro map
* `docs/_generated/content_semantics.json` — first-level keys & IDs across JSONs
* `docs/_generated/env_vars.json` — env var names referenced
* `docs/_generated/tests_inventory.json` — test files & collection
* `docs/_generated/make_targets.txt` — Make targets

## Execute This Complete Script:

```bash
#!/bin/bash
set -eu

# 0) Prep
mkdir -p docs/_generated

# 1) API & HTMX routes
python - <<'PY' > docs/_generated/api_routes.json
import os, re, json, glob
routes=[]
ROUTE_RX = re.compile(r'\.route\(\s*[\'"]([^\'"]+)[\'"]\s*(?:,\s*methods\s*=\s*\[([^\]]+)\])?')
HTMX_RX  = re.compile(r'hx-(?:get|post|patch|put|delete)\s*=\s*"[^\"]+"', re.I)
for path in sorted(glob.glob("**/*.py", recursive=True)):
    if not any(seg in path for seg in ("venv","site-packages","/.git/")):
        try:
            txt=open(path,encoding="utf-8",errors="ignore").read()
        except: 
            continue
        file_routes=[]
        for m in ROUTE_RX.finditer(txt):
            methods = []
            raw = m.group(2) or ""
            for meth in re.findall(r"[\'\"]([A-Z]+)[\'\"]", raw):
                methods.append(meth)
            file_routes.append({"path": m.group(1), "methods": methods or ["GET"]})
        htmx = bool(HTMX_RX.search(txt))
        if file_routes or htmx:
            routes.append({"file": path, "routes": file_routes, "htmx_tags_present": htmx})
print(json.dumps({"routes": routes}, indent=2))
PY

# 2) Deploy API surface
python - <<'PY' > docs/_generated/deploy_api_map.json
import re, json
p="dashboard/api/deploy.py"
out={"file": p, "functions": [], "shell_calls":[]}
try:
    t=open(p,encoding="utf-8").read()
    for m in re.finditer(r'^def\s+([a-zA-Z_][\w]*)\s*\(([^)]*)\):', t, re.M):
        out["functions"].append({"name": m.group(1), "params": m.group(2).strip()})
    for m in re.finditer(r'create_subprocess_shell\(\s*[fru]?["\']([^"\']+)["\']', t):
        out["shell_calls"].append(m.group(1))
    for m in re.finditer(r'run_command\(\s*[fru]?["\']([^"\']+)["\']', t):
        out["shell_calls"].append(m.group(1))
except FileNotFoundError:
    out["error"]="deploy.py not found"
print(json.dumps(out, indent=2))
PY

# 3) DB introspection
DB="dashboard/state/tasks.db"
python - <<'PY' > docs/_generated/db_introspection.json
import os, json, sqlite3, collections
db="dashboard/state/tasks.db"
out={"present": os.path.exists(db)}
if not out["present"]:
    print(json.dumps(out)); raise SystemExit
con=sqlite3.connect(db); con.row_factory=sqlite3.Row
cur=con.cursor()
def q(sql, args=()):
    try:
        cur.execute(sql,args); 
        cols=[c[0] for c in cur.description] if cur.description else []
        return {"ok":True,"rows":[dict(zip(cols,r)) for r in cur.fetchall()]}
    except Exception as e:
        return {"ok":False,"error":str(e),"rows":[]}
out["tables"]=q("SELECT name, type FROM sqlite_master WHERE type in ('table','view') ORDER BY name")
out["indexes"]=q("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' ORDER BY tbl_name,name")
out["fts"]=q("SELECT name FROM sqlite_master WHERE name like 'tasks_fts%'")
counts={}
for t in ("tasks","deps","scores","now_queue","events"):
    counts[t]=q(f"SELECT COUNT(*) AS n FROM {t}")
out["counts"]=counts
out["by_status"]=q("SELECT status, COUNT(*) n FROM tasks GROUP BY status ORDER BY n DESC")
out["by_category"]=q("SELECT COALESCE(category,'') AS category, COUNT(*) n FROM tasks GROUP BY category ORDER BY n DESC")
out["by_course"]=q("SELECT COALESCE(course,'') AS course, COUNT(*) n FROM tasks GROUP BY course ORDER BY n DESC")
out["nulls"]=q("""SELECT 
  SUM(due_at IS NULL) AS due_null,
  SUM(est_minutes IS NULL) AS est_null,
  SUM(title IS NULL) AS title_null
  FROM tasks""")
out["dep_stats"]=q("""SELECT 
  (SELECT COUNT(*) FROM deps) AS edges,
  (SELECT COUNT(*) FROM tasks) AS nodes,
  (SELECT COUNT(*) FROM deps WHERE parent_id NOT IN (SELECT id FROM tasks)) AS missing_parents,
  (SELECT COUNT(*) FROM deps WHERE child_id  NOT IN (SELECT id FROM tasks)) AS missing_children
""")
hot=[]
for name in [r["name"] for r in out["indexes"]["rows"]]:
    hot.append(name)
out["hot_index_present"]={
  "status": any("status" in (r["sql"] or "") for r in out["indexes"]["rows"]),
  "course": any("course" in (r["sql"] or "") for r in out["indexes"]["rows"]),
  "due_at": any("due_at" in (r["sql"] or "") for r in out["indexes"]["rows"]),
}
print(json.dumps(out, indent=2))
PY

# 4) Task graph
python - <<'PY' > docs/_generated/task_graph.dot
import os, sqlite3, sys
db="dashboard/state/tasks.db"
if not os.path.exists(db):
    print("// DB missing"); sys.exit(0)
con=sqlite3.connect(db); cur=con.cursor()
print("digraph tasks {")
print('  rankdir=LR; node [shape=box, fontsize=9];')
for tid,title in cur.execute("SELECT id, substr(replace(title,'\"','\\\"'),1,30) FROM tasks"):
    print(f'  "{tid}" [label="{title}"];')
for p,c in cur.execute("SELECT parent_id, child_id FROM deps"):
    if p and c: print(f'  "{p}" -> "{c}";')
print("}")
PY

# 5) Template modularity
python - <<'PY' > docs/_generated/template_map.json
import glob, re, json, os
EXT=re.compile(r'{%\s*extends\s*[\'"]([^\'"]+)[\'"]\s*%}')
INC=re.compile(r'{%\s*include\s*[\'"]([^\'"]+)[\'"]\s*%}')
MAC=re.compile(r'{%\s*macro\s+([a-zA-Z_]\w*)\(')
files=sorted(glob.glob("templates/**/*.j2", recursive=True)+glob.glob("dashboard/templates/**/*.html", recursive=True))
out=[]
for p in files:
    try:
        t=open(p,encoding="utf-8",errors="ignore").read()
    except: 
        continue
    out.append({
        "path": p,
        "lines": t.count("\n")+1,
        "extends": EXT.findall(t),
        "includes": INC.findall(t),
        "macros": MAC.findall(t)
    })
print(json.dumps({"templates": out}, indent=2))
PY

# 6) Course content semantics
python - <<'PY' > docs/_generated/content_semantics.json
import os, glob, json, hashlib
root="content/courses"
courses=[]
if os.path.isdir(root):
    for d in sorted(glob.glob(os.path.join(root,"*"))):
        if not os.path.isdir(d): continue
        code=os.path.basename(d)
        items=[]
        for f in sorted(glob.glob(os.path.join(d,"*.json"))):
            try:
                j=json.load(open(f,encoding="utf-8"))
            except Exception as e:
                items.append({"file": os.path.basename(f), "error": str(e)}); continue
            keys=list(j.keys()) if isinstance(j,dict) else []
            sample_id=None
            if isinstance(j,dict):
                for k in ("id","_id","code","slug"):
                    if k in j: sample_id=str(j[k]); break
            items.append({"file": os.path.basename(f), "top_keys": keys[:25], "sample_id": sample_id})
        courses.append({"course_code": code, "files": items})
print(json.dumps({"courses": courses}, indent=2))
PY

# 7) Env vars
python - <<'PY' > docs/_generated/env_vars.json
import glob, re, json
ENV=re.compile(r'os\.getenv\(\s*[\'"]([^\'"]+)[\'"]')
names=set()
for p in glob.glob("**/*.py", recursive=True):
    if any(x in p for x in ("venv","site-packages","/.git/")): continue
    try:
        t=open(p,encoding="utf-8",errors="ignore").read()
    except: 
        continue
    names.update(ENV.findall(t))
print(json.dumps({"env_vars": sorted(names)}, indent=2))
PY

# 8) Tests inventory
python - <<'PY' > docs/_generated/tests_inventory.json
import os, glob, json
tests=sorted(glob.glob("tests/**/*.py", recursive=True))
print(json.dumps({"test_files": tests, "count": len(tests)}, indent=2))
PY

( pytest --collect-only -q -s -vv > docs/_generated/_pytest_collect.out 2> docs/_generated/_pytest_collect.err ) || true

# 9) Make targets
{ [ -f Makefile ] && awk -F: '/^[A-Za-z0-9_.-]+:/{print $1}' Makefile | sort -u || echo "Makefile missing"; } > docs/_generated/make_targets.txt

# 10) Aggregate planner input
python - <<'PY' > docs/_generated/plan_input.json
import json, os
def load(p):
    try: 
        return json.load(open(p,encoding="utf-8"))
    except Exception as e:
        return {"error": str(e), "__file__": p}
base="docs/_generated"
out={
  "api_routes": load(f"{base}/api_routes.json"),
  "deploy_api": load(f"{base}/deploy_api_map.json"),
  "db": load(f"{base}/db_introspection.json"),
  "templates": load(f"{base}/template_map.json"),
  "content": load(f"{base}/content_semantics.json"),
  "env_vars": load(f"{base}/env_vars.json"),
  "tests": load(f"{base}/tests_inventory.json"),
  "make_targets": open(f"{base}/make_targets.txt",encoding="utf-8").read().splitlines() if os.path.exists(f"{base}/make_targets.txt") else [],
}
print(json.dumps(out, indent=2))
PY

# 11) Human brief
python - <<'PY' > docs/_generated/plan_input.md
import json, os, sys
base="docs/_generated"
j=json.load(open(f"{base}/plan_input.json"))
db=j.get("db",{})
counts=db.get("counts",{}); tasks=counts.get("tasks",{}).get("rows",[{"n":0}])[0].get("n",0)
due_null=(db.get("nulls",{}).get("rows") or [{"due_null":0}])[0].get("due_null",0)
routes=sum(len(x.get("routes",[])) for x in j.get("api_routes",{}).get("routes",[]))
htmx=sum(1 for x in j.get("api_routes",{}).get("routes",[]) if x.get("htmx_tags_present"))
tmpl=len(j.get("templates",{}).get("templates",[]))
tests=j.get("tests",{}).get("count",0)
print("# Plan Input – Quick Brief\n")
print(f"- Tasks in DB: **{tasks}**  | `due_at` NULL: **{due_null}**")
print(f"- API files with routes: **{routes}** endpoints across files; HTMX present in some templates: {'yes' if htmx else 'no'}")
print(f"- Templates scanned: **{tmpl}**  | Make targets: {len(j.get('make_targets',[]))}")
print(f"- Test files detected: **{tests}**  | (see tests_inventory.json & _pytest_collect.*)")
print(f"- Env var names referenced: **{len(j.get('env_vars',{}).get('env_vars',[]))}**")
print("\n## Immediate Signals")
if not db.get("present"): 
    print("- ❗ DB missing; projections/reconciliation planning blocked until DB is created.")
else:
    if not any(ix.get("ok") and ix.get("rows") for ix in [db.get("indexes",{})]):
        print("- ⚠️ No indexes reported; consider adding indexes on status, course, due_at.")
    hot=db.get("hot_index_present",{})
    for k,v in hot.items():
        if not v: print(f"- 🧭 Add index on `{k}` for dashboard queries.")
    if (counts.get("now_queue",{}).get("rows",[{"n":0}])[0].get("n",0)==0):
        print("- ℹ️ `now_queue` empty; prioritization path likely not refreshed.")
if tests==0:
    print("- ⚠️ No test files found or collection failed; see `_pytest_collect.err`.")
print("\n## Next Planning Hooks\n- Use `plan_input.json` to auto-generate lanes: DB tuning, HTMX/API tests, template modularization, content manifest mapping, deploy surface tests.\n")
PY

echo "Probe V3 Complete. Check docs/_generated/plan_input.{md,json}"
```

---

## Usage Instructions

### With Claude Code CLI

1. **Run both probes to establish baseline:**
```bash
# Run V2 probe
claude-code --task "Execute the complete Probe V2 script from this document"

# Run V3 probe  
claude-code --task "Execute the complete Probe V3 script from this document"
```

2. **Verify outputs exist:**
```bash
ls -la docs/_generated/*.json docs/_generated/*.md
```

3. **Use probe outputs for orchestration:**
- `state_probe.json` - System configuration and structure
- `plan_input.json` - Detailed implementation gaps and opportunities
- `task_graph.dot` - Visual dependency graph
- `db_introspection.json` - Database optimization opportunities

### Expected Outputs

After running both probes, you should have:

**From Probe V2:**
- state_probe.md (human summary)
- state_probe.json (machine data)
- db_schema.sql
- templates_report.csv
- workflows_list.txt

**From Probe V3:**
- plan_input.md (human brief)
- plan_input.json (orchestration data)
- api_routes.json
- deploy_api_map.json
- db_introspection.json
- task_graph.dot
- template_map.json
- content_semantics.json
- env_vars.json
- tests_inventory.json
- make_targets.txt

### Error Handling

Both probes are designed to be fault-tolerant:
- Missing files are noted but don't stop execution
- Database operations fail gracefully if DB is missing
- Test collection errors are captured but don't block
- All errors are recorded in the JSON outputs

---

*These probes provide complete system introspection for orchestrated planning. Execute them sequentially or in parallel depending on your needs.*
