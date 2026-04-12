#!/usr/bin/env python3
"""
CI import smoke test for app/main.py and all first-party modules it depends on.

Catches the "APFA has never actually started" bug class at PR time instead of
deploy time. This script was introduced after five sequential production
container crashes all caused by import-time failures:

  1. aioredis 2.0.1 — duplicate TimeoutError base class on Python 3.11+
  2. Hardcoded redis://localhost — resolved at import via settings
  3. langgraph==1.1.2 — internal ExecutionInfo/ServerInfo symbol skew
  4. langchain==1.2.12 — AgentExecutor/create_tool_calling_agent removed
  5. profanity-check==1.0.3 — imports joblib from removed sklearn.externals
  6. tenacity.circuit_breaker — hallucinated symbol that never existed
  7. pydantic_settings — split out of pydantic in v2, never added to requirements

Bugs 1-6 crash on `import app.main`. Bug 7 crashes on `from config import settings`
which is a first-party import that the earlier version of this script skipped.

APPROACH
--------
Two-phase check:

Phase A — walk the tree of FIRST-PARTY modules starting from app/main.py (and
the alembic/env.py module used by migrations), recursively, following every
`from app.X import Y` / `import app.X` / `from config import Z` statement.
For each first-party file visited, collect the external packages it imports.

Phase B — for each external (non-first-party, non-stdlib) package collected,
try to resolve the full import statement via importlib + hasattr/getattr.
Importing a module executes its body (which is where aioredis's TimeoutError
bug fires, langgraph's ExecutionInfo bug fires, profanity_check's sklearn
bug fires, and — critically — pydantic_settings's ModuleNotFoundError fires).

WHY NOT `python -c "import app.main"`
-------------------------------------
app/main.py has module-level calls to `load_llm()` and `load_rag_index()`
that would download multi-GB HuggingFace models and read from S3 on every
CI run. The AST-based approach sees every import without executing the
heavy module bodies of first-party files.

WHY RECURSE INTO FIRST-PARTY MODULES
------------------------------------
Earlier versions of this script skipped first-party imports entirely on the
theory that "first-party checks are handled by pytest." This was wrong. Pytest
doesn't import app.main (it imports specific test fixtures), so first-party
modules like config.py that are transitively imported at app.main module-init
time can reference missing external packages without pytest ever catching it.

Bug #7 (pydantic_settings) is the canonical example: config.py:3 does
`from pydantic_settings import BaseSettings`, pydantic_settings was never
added to requirements.txt, and pytest never tripped because pytest never
imported config.py directly. The container crashed on deploy in run #99.

By recursing into first-party modules, we follow the same import chain the
Python interpreter would follow at app.main init time, but without executing
heavy bodies. This catches missing-requirement bugs in any first-party file
that app.main transitively imports.

FAILURE MODE
------------
Exit code 1 on any broken external import from any first-party file. Prints
each failure with the specific first-party file + line where it's referenced.
CI workflow should treat non-zero as a hard failure (no continue-on-error,
once the baseline is clean).
"""

import ast
import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Entry points to start the first-party walk from. Add new entry points here
# when the codebase grows a new independently-executed module (alembic env,
# celery worker, scripts, etc.).
ENTRY_POINTS = [
    REPO_ROOT / "app" / "main.py",
    REPO_ROOT / "app" / "alembic" / "env.py",  # used by `alembic upgrade head` at deploy time
]


def collect_top_level_imports(source: str, filename: str):
    """
    Return a list of (lineno, module, [names], raw_line) tuples for every
    top-level import statement in `source`.

    Skips relative imports (level > 0) since they're internal to a package
    and don't map cleanly to importlib.import_module.
    """
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as e:
        print(f"  [WARN] SyntaxError parsing {filename}: {e}")
        return []

    results = []
    for node in tree.body:  # top level only — no nested imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                results.append((node.lineno, alias.name, [], f"import {alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                continue
            if node.module is None:
                continue
            names = [(a.name, a.asname) for a in node.names]
            line = f"from {node.module} import " + ", ".join(
                f"{n}" + (f" as {a}" if a else "") for n, a in names
            )
            results.append((node.lineno, node.module, names, line))
    return results


def is_first_party(module: str) -> bool:
    """
    First-party modules are `app`, `app.*`, `config`, and `alembic.*`
    (alembic migrations live in the repo, not site-packages).
    """
    return (
        module == "app"
        or module.startswith("app.")
        or module == "config"
        or module == "alembic"
        or module.startswith("alembic.")
    )


def first_party_file(module: str) -> Path | None:
    """
    Resolve a first-party module name to a file in the repo. Handles both
    `foo.bar` -> `foo/bar.py` and `foo.bar` -> `foo/bar/__init__.py`.

    Special cases:
      - `config` resolves to `app/config.py` (app.main does `from config import`
        which works because Dockerfile copies app/ to /app and WORKDIR=/app).
      - `alembic.env` resolves to `alembic/env.py` (real directory in the repo).
    """
    if module == "config":
        candidate = REPO_ROOT / "app" / "config.py"
        return candidate if candidate.exists() else None

    parts = module.split(".")
    base = REPO_ROOT / Path(*parts)
    as_file = base.with_suffix(".py")
    as_package = base / "__init__.py"
    if as_file.exists():
        return as_file
    if as_package.exists():
        return as_package
    return None


def walk_first_party(entry_points: list[Path]):
    """
    BFS over first-party files starting from each entry point. Yields every
    (file, lineno, external_module, names, raw_line) tuple for external
    references, and tracks visited files to prevent cycles.
    """
    visited = set()
    queue = list(entry_points)
    while queue:
        f = queue.pop(0)
        if not f or f in visited or not f.exists():
            continue
        visited.add(f)
        imports = collect_top_level_imports(f.read_text(), str(f))
        for lineno, module, names, raw in imports:
            if is_first_party(module):
                sub = first_party_file(module)
                if sub:
                    queue.append(sub)
                # Also queue `from pkg import submodule` where submodule is
                # itself a first-party module (e.g., `from app.models import
                # user_profile` where user_profile.py is a module).
                for name, _ in names:
                    sub_name = f"{module}.{name}"
                    if is_first_party(sub_name):
                        sub2 = first_party_file(sub_name)
                        if sub2:
                            queue.append(sub2)
            else:
                yield (f, lineno, module, names, raw)
    return visited


def check_import(module_name: str, names: list) -> tuple[bool, str]:
    """
    Try to import `module_name` and verify each requested name exists.
    Returns (ok, error_message). error_message is empty when ok=True.
    """
    try:
        mod = importlib.import_module(module_name)
    except Exception as e:
        return False, f"ImportError: {type(e).__name__}: {e}"

    missing = []
    for name, _alias in names:
        if hasattr(mod, name):
            continue
        try:
            importlib.import_module(f"{module_name}.{name}")
        except Exception:
            missing.append(name)

    if missing:
        return False, f"AttributeError: cannot import {missing} from {module_name!r}"
    return True, ""


def main() -> int:
    entry_points = [p for p in ENTRY_POINTS if p.exists()]
    if not entry_points:
        print("ERROR: no entry points found")
        return 2

    print(f"Walking first-party modules from entry points:")
    for p in entry_points:
        print(f"  - {p.relative_to(REPO_ROOT)}")
    print()

    # Collect every external (module, source-file, lineno, names, raw) tuple
    external_refs = list(walk_first_party(entry_points))

    # Deduplicate by (module, tuple(names)) so we only check each unique
    # import statement once, but preserve all source locations for reporting.
    seen: dict = {}  # key: (module, tuple(sorted names)) -> list of (file, lineno, raw)
    for f, lineno, module, names, raw in external_refs:
        key = (module, tuple(sorted(n for n, _ in names)))
        seen.setdefault(key, []).append((f, lineno, raw))

    print(f"Found {len(external_refs)} external references ({len(seen)} unique)")
    print()

    failures = []
    ok_count = 0
    for (module, name_key), locations in sorted(seen.items()):
        # Recover the names list from the first source occurrence
        first_f, first_line, first_raw = locations[0]
        # Re-parse to get the full (name, asname) pairs
        names_full = []
        if name_key:
            source_imports = collect_top_level_imports(first_f.read_text(), str(first_f))
            for lineno, mod, names, raw in source_imports:
                if lineno == first_line and mod == module:
                    names_full = names
                    break

        ok, err = check_import(module, names_full)
        if ok:
            ok_count += 1
        else:
            failures.append((module, names_full, locations, err))
            print(f"  [FAIL] {first_raw}")
            for loc_f, loc_line, _ in locations:
                print(f"         at {loc_f.relative_to(REPO_ROOT)}:{loc_line}")
            print(f"         {err}")

    print()
    print(f"SUMMARY: {ok_count} OK, {len(failures)} FAIL out of {len(seen)} unique imports")
    print()

    if failures:
        print("This smoke test exists to catch import-time failures before they")
        print("crash the production container. If a dependency version bump")
        print("broke an import, either fix the import path or pin to a version")
        print("that provides the expected symbols. If a new import was added")
        print("to a first-party file, ensure the package is in requirements.txt.")
        return 1

    print("OK: all external dependencies referenced by first-party modules resolve cleanly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
