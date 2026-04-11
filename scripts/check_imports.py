#!/usr/bin/env python3
"""
CI import smoke test for app/main.py

Catches the "APFA has never actually started" bug class at PR time instead of
deploy time. This script was introduced after four sequential production
container crashes all caused by import-time failures:

  1. aioredis 2.0.1 — duplicate TimeoutError base class on Python 3.11+
  2. Hardcoded redis://localhost — resolved at import via settings
  3. langgraph==1.1.2 — internal ExecutionInfo/ServerInfo symbol skew
  4. langchain==1.2.12 — AgentExecutor/create_tool_calling_agent removed
     (the langchain 0.x → 1.x migration that APFA-008 missed)

All four bugs crash the container on `import app.main`. None were caught by
pytest (the old CI check) because the test suite didn't import main.py.

APPROACH
--------
We cannot naively run `python -c "import app.main"` in CI because app/main.py
has module-level calls to `load_llm()` and `load_rag_index()` (lines ~188,
~255) that would download multi-GB HuggingFace models and read from S3 on
every CI run.

Instead, this script parses app/main.py with `ast`, extracts every top-level
`import` and `from ... import ...` statement, and resolves each one via
`importlib.import_module()` + `getattr`. Importing a module executes its
body (which is where aioredis's TimeoutError bug fires and langgraph's
ExecutionInfo bug fires), and `getattr` on the imported names catches
the langchain.agents.AgentExecutor removal case.

This gives us the full "does every import-time dependency resolve cleanly"
check without triggering app/main.py's own module body.

FAILURE MODE
------------
Exit code 1 on any broken import. Prints each broken import with the exact
error message and the source line in app/main.py. CI workflow should treat
any non-zero exit as a hard failure (no continue-on-error).
"""

import ast
import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET = REPO_ROOT / "app" / "main.py"


def collect_top_level_imports(source: str, filename: str):
    """
    Return a list of (lineno, module, [names], raw_line) tuples for every
    top-level import statement in `source`.

    `names` is a list of (imported_name, alias) pairs for `ImportFrom`. For
    plain `Import` statements it's empty — we only need to resolve the module.
    """
    tree = ast.parse(source, filename=filename)
    results = []
    for node in tree.body:  # top level only — no nested imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                results.append((node.lineno, alias.name, [], f"import {alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            # Skip relative imports — they're internal to the package and
            # would require the package to actually be importable as a
            # whole, which is exactly what we're avoiding.
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
        # `from pkg import submodule` is valid even if submodule is not a
        # direct attribute — Python resolves it as a submodule. Handle both.
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
    source = TARGET.read_text()
    imports = collect_top_level_imports(source, str(TARGET))

    # Skip first-party imports — they depend on the package being importable,
    # which pulls in app/main.py's body and defeats the point. We're checking
    # third-party + stdlib only. First-party checks are handled by pytest.
    def is_first_party(mod: str) -> bool:
        return mod == "app" or mod.startswith("app.") or mod == "config"

    external = [i for i in imports if not is_first_party(i[1])]
    skipped = len(imports) - len(external)

    print(f"Checking {len(external)} top-level imports in {TARGET.relative_to(REPO_ROOT)}")
    print(f"  (skipped {skipped} first-party imports — those are covered by pytest)")
    print()

    failures = []
    for lineno, module, names, raw in external:
        ok, err = check_import(module, names)
        status = "OK  " if ok else "FAIL"
        print(f"  [{status}] line {lineno:>4}: {raw}")
        if not ok:
            print(f"         {err}")
            failures.append((lineno, raw, err))

    print()
    if failures:
        print(f"FAILED: {len(failures)} broken import(s) in app/main.py")
        print()
        print("This smoke test exists to catch import-time failures before they")
        print("crash the production container. If a dependency version bump")
        print("broke an import, either fix the import path or pin to a version")
        print("that provides the expected symbols.")
        return 1

    print(f"OK: all {len(external)} top-level imports resolve cleanly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
