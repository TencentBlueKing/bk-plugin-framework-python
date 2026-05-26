# BK Standard Plugin Agent Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an agent-neutral local development kit that helps users develop and verify BlueKing standard plugins from a cookiecutter-generated Demo project.

**Architecture:** Add a root-level `agent-kit/` package with shared workflow docs, templates, thin agent adapters, and local Python scripts. Put reusable script logic in `agent-kit/scripts/bk_plugin_agent_kit/` so all CLIs share project detection, JSON envelopes, version parsing, and HTTP helpers. Test script behavior through focused pytest tests under `tests/agent_kit/` without changing framework runtime code.

**Tech Stack:** Python 3.8+ standard library, pytest, Markdown, YAML manifest, existing repository git workflow.

---

## File Structure

Create these files:

- `agent-kit/AGENT.md` - platform-neutral instructions for agents and humans.
- `agent-kit/manifest.yaml` - machine-readable command and workflow inventory.
- `agent-kit/workflows/01-orient-demo-project.md` - project detection workflow.
- `agent-kit/workflows/02-develop-plugin-requirement.md` - requirement-to-plugin workflow.
- `agent-kit/workflows/03-verify-like-bksops.md` - local protocol verification workflow.
- `agent-kit/workflows/04-troubleshoot-failure.md` - failure diagnosis workflow.
- `agent-kit/scripts/bk_plugin_agent_kit/__init__.py` - package marker and version.
- `agent-kit/scripts/bk_plugin_agent_kit/common.py` - JSON envelope, project detection, version parsing, and file helpers.
- `agent-kit/scripts/bk_plugin_agent_kit/http.py` - standard-library HTTP helpers for local runtime calls.
- `agent-kit/scripts/inspect_demo.py` - CLI for project orientation.
- `agent-kit/scripts/validate_plugin.py` - CLI for static plugin validation.
- `agent-kit/scripts/generate_version.py` - CLI for creating version, form, and test files from templates.
- `agent-kit/scripts/render_call_payload.py` - CLI for building Standard Ops / BKFlow-like invoke payloads.
- `agent-kit/scripts/simulate_invoke.py` - CLI for local `meta/detail/invoke` verification.
- `agent-kit/scripts/poll_schedule.py` - CLI for local schedule polling.
- `agent-kit/scripts/collect_trace.py` - CLI for local trace log collection.
- `agent-kit/templates/version.py.j2` - plugin version template.
- `agent-kit/templates/form.js.j2` - form template.
- `agent-kit/templates/test_plugin.py.j2` - pytest template.
- `agent-kit/templates/verify_payload.json.j2` - local verification payload template.
- `agent-kit/adapters/generic/prompt.md` - generic agent entrypoint.
- `agent-kit/adapters/codex/SKILL.md` - Codex skill adapter.
- `tests/agent_kit/conftest.py` - demo project fixtures and CLI runner helper.
- `tests/agent_kit/test_common.py` - common utility tests.
- `tests/agent_kit/test_inspect_demo.py` - `inspect_demo.py` tests.
- `tests/agent_kit/test_validate_plugin.py` - `validate_plugin.py` tests.
- `tests/agent_kit/test_generate_version.py` - `generate_version.py` tests.
- `tests/agent_kit/test_render_call_payload.py` - payload rendering tests.
- `tests/agent_kit/test_http_scripts.py` - `simulate_invoke.py`, `poll_schedule.py`, and `collect_trace.py` tests.
- `tests/agent_kit/test_manifest_and_docs.py` - manifest and required-doc presence tests.

Do not modify framework runtime files under `bk-plugin-framework/` or `runtime/` for the first implementation.

## Task 1: Shared Script Utilities

**Files:**
- Create: `agent-kit/scripts/bk_plugin_agent_kit/__init__.py`
- Create: `agent-kit/scripts/bk_plugin_agent_kit/common.py`
- Create: `tests/agent_kit/conftest.py`
- Create: `tests/agent_kit/test_common.py`

- [ ] **Step 1: Write tests for JSON envelopes, project detection, version parsing, and form discovery**

Create `tests/agent_kit/conftest.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_KIT = REPO_ROOT / "agent-kit"
SCRIPT_DIR = AGENT_KIT / "scripts"


@pytest.fixture
def demo_project(tmp_path):
    root = tmp_path / "demo_plugin"
    (root / "bin").mkdir(parents=True)
    (root / "bk_plugin" / "versions").mkdir(parents=True)
    (root / "bk_plugin" / "forms" / "1.0.0").mkdir(parents=True)
    (root / "tests").mkdir(parents=True)

    (root / "bin" / "manage.py").write_text("print('manage')\n", encoding="utf-8")
    (root / "bk_plugin" / "meta.py").write_text(
        'description = "demo plugin"\nallow_scope = {}\n',
        encoding="utf-8",
    )
    (root / "bk_plugin" / "__init__.py").write_text("", encoding="utf-8")
    (root / "bk_plugin" / "versions" / "__init__.py").write_text("", encoding="utf-8")
    (root / "bk_plugin" / "versions" / "v1_0_0.py").write_text(
        """
from bk_plugin_framework.kit import Context, ContextRequire, Field, InputsModel, OutputsModel, Plugin


class MyPlugin(Plugin):
    class Meta:
        version = "1.0.0"
        desc = "demo version"

    class Inputs(InputsModel):
        hello: str

    class Outputs(OutputsModel):
        world: str

    class ContextInputs(ContextRequire):
        executor: str = Field(title="task executor")

    def execute(self, inputs: Inputs, context: Context):
        context.outputs["world"] = inputs.hello
""".lstrip(),
        encoding="utf-8",
    )
    (root / "bk_plugin" / "forms" / "1.0.0" / "form.js").write_text(
        "var tag = [];\n",
        encoding="utf-8",
    )
    (root / "requirements.txt").write_text(
        "bk-plugin-framework==2.3.12\nbk-plugin-runtime==2.1.9\n",
        encoding="utf-8",
    )
    (root / "runtime.txt").write_text("python-3.8.18\n", encoding="utf-8")
    (root / "tests" / "test_plugin.py").write_text("def test_demo():\n    assert True\n", encoding="utf-8")
    return root


def run_script(script_name, *args, cwd=None):
    cmd = [sys.executable, str(SCRIPT_DIR / script_name), *args]
    result = subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result


def parse_json(stdout):
    return json.loads(stdout)
```

Create `tests/agent_kit/test_common.py`:

```python
from pathlib import Path

import sys

from tests.agent_kit.conftest import SCRIPT_DIR

sys.path.insert(0, str(SCRIPT_DIR))

from bk_plugin_agent_kit.common import (  # noqa: E402
    discover_forms,
    discover_version_files,
    error,
    find_project_root,
    parse_dependency_versions,
    success,
    version_to_module_name,
)


def test_success_envelope():
    payload = success({"answer": 1}, hints=["done"])

    assert payload == {"result": True, "code": "ok", "message": "success", "data": {"answer": 1}, "hints": ["done"]}


def test_error_envelope():
    payload = error("project_not_found", "No demo project", hints=["run from project root"])

    assert payload["result"] is False
    assert payload["code"] == "project_not_found"
    assert payload["message"] == "No demo project"
    assert payload["data"] == {}
    assert payload["hints"] == ["run from project root"]


def test_find_project_root_from_child(demo_project):
    child = demo_project / "bk_plugin" / "versions"

    assert find_project_root(child) == demo_project


def test_find_project_root_returns_none_for_non_demo(tmp_path):
    assert find_project_root(tmp_path) is None


def test_parse_dependency_versions(demo_project):
    versions = parse_dependency_versions(demo_project / "requirements.txt")

    assert versions["bk-plugin-framework"] == "2.3.12"
    assert versions["bk-plugin-runtime"] == "2.1.9"


def test_discover_version_files_and_forms(demo_project):
    versions = discover_version_files(demo_project)
    forms = discover_forms(demo_project)

    assert versions == [{"version": "1.0.0", "module": "v1_0_0.py", "path": "bk_plugin/versions/v1_0_0.py"}]
    assert forms == [{"version": "1.0.0", "path": "bk_plugin/forms/1.0.0/form.js"}]


def test_version_to_module_name():
    assert version_to_module_name("1.2.3") == "v1_2_3.py"
```

- [ ] **Step 2: Run tests to verify they fail before implementation**

Run:

```bash
pytest tests/agent_kit/test_common.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'bk_plugin_agent_kit'`.

- [ ] **Step 3: Implement shared utility package**

Create `agent-kit/scripts/bk_plugin_agent_kit/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `agent-kit/scripts/bk_plugin_agent_kit/common.py`:

```python
import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9][a-z0-9]*$")
REQUIREMENT_RE = re.compile(r"^(bk-plugin-framework|bk-plugin-runtime)\s*==\s*([^;\s]+)")
PROJECT_MARKERS = (
    "bk_plugin/meta.py",
    "bk_plugin/versions",
    "bk_plugin/forms",
    "bin/manage.py",
    "requirements.txt",
)


def success(data: Optional[Dict[str, Any]] = None, message: str = "success", hints: Optional[List[str]] = None):
    return {"result": True, "code": "ok", "message": message, "data": data or {}, "hints": hints or []}


def error(code: str, message: str, data: Optional[Dict[str, Any]] = None, hints: Optional[List[str]] = None):
    return {"result": False, "code": code, "message": message, "data": data or {}, "hints": hints or []}


def print_json(payload: Dict[str, Any], pretty: bool = False) -> None:
    kwargs = {"ensure_ascii": False}
    if pretty:
        kwargs.update({"indent": 2, "sort_keys": True})
    print(json.dumps(payload, **kwargs))


def add_common_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", default=".", help="Generated plugin Demo project root")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")


def path_has_markers(path: Path) -> bool:
    return all((path / marker).exists() for marker in PROJECT_MARKERS)


def find_project_root(start: Path) -> Optional[Path]:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if path_has_markers(candidate):
            return candidate
    return None


def require_project_root(raw_root: str) -> Path:
    root = find_project_root(Path(raw_root))
    if root is None:
        raise ValueError("No cookiecutter-generated plugin Demo project found")
    return root


def relative_to_root(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def parse_dependency_versions(requirements_path: Path) -> Dict[str, str]:
    versions: Dict[str, str] = {}
    if not requirements_path.exists():
        return versions
    for line in requirements_path.read_text(encoding="utf-8").splitlines():
        match = REQUIREMENT_RE.match(line.strip())
        if match:
            versions[match.group(1)] = match.group(2)
    return versions


def module_name_to_version(filename: str) -> Optional[str]:
    stem = Path(filename).stem
    if not stem.startswith("v"):
        return None
    parts = stem[1:].split("_")
    if len(parts) < 3:
        return None
    version = ".".join(parts)
    return version if VERSION_RE.match(version) else None


def version_to_module_name(version: str) -> str:
    if not VERSION_RE.match(version):
        raise ValueError(f"Invalid plugin version: {version}")
    return "v%s.py" % version.replace(".", "_")


def discover_version_files(root: Path) -> List[Dict[str, str]]:
    version_dir = root / "bk_plugin" / "versions"
    items = []
    for path in sorted(version_dir.glob("v*.py")):
        version = module_name_to_version(path.name)
        if version:
            items.append({"version": version, "module": path.name, "path": relative_to_root(path, root)})
    return items


def discover_forms(root: Path) -> List[Dict[str, str]]:
    form_root = root / "bk_plugin" / "forms"
    items = []
    for path in sorted(form_root.glob("*/form.js")):
        version = path.parent.name
        if VERSION_RE.match(version):
            items.append({"version": version, "path": relative_to_root(path, root)})
    return items


def load_json_file(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_file(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_python_classes(path: Path) -> Iterable[ast.ClassDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            yield node


def base_names(class_node: ast.ClassDef) -> List[str]:
    names = []
    for base in class_node.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
        elif isinstance(base, ast.Attribute):
            names.append(base.attr)
    return names


def main_guard(func):
    try:
        func()
    except ValueError as exc:
        print_json(error("invalid_argument", str(exc)), pretty="--pretty" in sys.argv)
        raise SystemExit(1)
```

- [ ] **Step 4: Run common tests**

Run:

```bash
pytest tests/agent_kit/test_common.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit shared utilities**

```bash
git add agent-kit/scripts/bk_plugin_agent_kit tests/agent_kit/conftest.py tests/agent_kit/test_common.py
git commit -m "feat: add agent kit shared script utilities"
```

## Task 2: Demo Project Inspection CLI

**Files:**
- Create: `agent-kit/scripts/inspect_demo.py`
- Create: `tests/agent_kit/test_inspect_demo.py`

- [ ] **Step 1: Write tests for `inspect_demo.py`**

Create `tests/agent_kit/test_inspect_demo.py`:

```python
from tests.agent_kit.conftest import parse_json, run_script


def test_inspect_demo_success(demo_project):
    result = run_script("inspect_demo.py", "--project-root", str(demo_project))
    payload = parse_json(result.stdout)

    assert result.returncode == 0
    assert payload["result"] is True
    assert payload["data"]["project_root"] == str(demo_project)
    assert payload["data"]["dependency_versions"]["bk-plugin-framework"] == "2.3.12"
    assert payload["data"]["dependency_versions"]["bk-plugin-runtime"] == "2.1.9"
    assert payload["data"]["versions"][0]["version"] == "1.0.0"
    assert payload["data"]["forms"][0]["version"] == "1.0.0"
    assert payload["data"]["runtime"]["manage_py"] == "bin/manage.py"


def test_inspect_demo_failure_for_non_demo(tmp_path):
    result = run_script("inspect_demo.py", "--project-root", str(tmp_path))
    payload = parse_json(result.stdout)

    assert result.returncode == 1
    assert payload["result"] is False
    assert payload["code"] == "project_not_found"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/agent_kit/test_inspect_demo.py -v
```

Expected: FAIL because `agent-kit/scripts/inspect_demo.py` does not exist.

- [ ] **Step 3: Implement `inspect_demo.py`**

Create `agent-kit/scripts/inspect_demo.py`:

```python
#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bk_plugin_agent_kit.common import (  # noqa: E402
    add_common_flags,
    discover_forms,
    discover_version_files,
    error,
    find_project_root,
    parse_dependency_versions,
    print_json,
    relative_to_root,
    success,
)


def build_payload(root: Path):
    requirements = root / "requirements.txt"
    runtime_txt = root / "runtime.txt"
    tests_dir = root / "tests"
    test_files = [relative_to_root(path, root) for path in sorted(tests_dir.glob("test*.py"))]
    runtime_data = {
        "manage_py": "bin/manage.py",
        "runtime_txt": runtime_txt.read_text(encoding="utf-8").strip() if runtime_txt.exists() else "",
        "debug_server_command": "python bin/manage.py rundebugserver",
    }
    data = {
        "project_root": str(root),
        "dependency_versions": parse_dependency_versions(requirements),
        "versions": discover_version_files(root),
        "forms": discover_forms(root),
        "tests": test_files,
        "runtime": runtime_data,
    }
    hints = [
        "Use dependency_versions as the source of truth before consulting framework source code.",
        "Run validate_plugin.py before editing plugin logic.",
    ]
    return success(data, hints=hints)


def main():
    parser = argparse.ArgumentParser(description="Inspect a generated BlueKing plugin Demo project")
    add_common_flags(parser)
    args = parser.parse_args()

    root = find_project_root(Path(args.project_root))
    if root is None:
        print_json(
            error(
                "project_not_found",
                "No cookiecutter-generated plugin Demo project found",
                hints=["Run this command from the generated plugin project root."],
            ),
            pretty=args.pretty,
        )
        raise SystemExit(1)

    print_json(build_payload(root), pretty=args.pretty)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run inspection tests**

Run:

```bash
pytest tests/agent_kit/test_inspect_demo.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit inspection CLI**

```bash
git add agent-kit/scripts/inspect_demo.py tests/agent_kit/test_inspect_demo.py
git commit -m "feat: add plugin demo inspection script"
```

## Task 3: Static Plugin Validation CLI

**Files:**
- Create: `agent-kit/scripts/validate_plugin.py`
- Create: `tests/agent_kit/test_validate_plugin.py`

- [ ] **Step 1: Write validation tests**

Create `tests/agent_kit/test_validate_plugin.py`:

```python
from tests.agent_kit.conftest import parse_json, run_script


def test_validate_plugin_success(demo_project):
    result = run_script("validate_plugin.py", "--project-root", str(demo_project))
    payload = parse_json(result.stdout)

    assert result.returncode == 0
    assert payload["result"] is True
    assert payload["data"]["versions"][0]["version"] == "1.0.0"
    assert payload["data"]["versions"][0]["form_exists"] is True


def test_validate_plugin_reports_missing_form(demo_project):
    (demo_project / "bk_plugin" / "forms" / "1.0.0" / "form.js").unlink()

    result = run_script("validate_plugin.py", "--project-root", str(demo_project))
    payload = parse_json(result.stdout)

    assert result.returncode == 1
    assert payload["result"] is False
    assert payload["code"] == "form_missing"
    assert "1.0.0" in payload["message"]


def test_validate_plugin_reports_version_conflict(demo_project):
    extra = demo_project / "bk_plugin" / "versions" / "v1_0_1.py"
    extra.write_text(
        """
from bk_plugin_framework.kit import Plugin


class OtherPlugin(Plugin):
    class Meta:
        version = "1.0.0"

    def execute(self, inputs, context):
        return
""".lstrip(),
        encoding="utf-8",
    )

    result = run_script("validate_plugin.py", "--project-root", str(demo_project))
    payload = parse_json(result.stdout)

    assert result.returncode == 1
    assert payload["code"] == "version_conflict"
```

- [ ] **Step 2: Run validation tests to verify they fail**

Run:

```bash
pytest tests/agent_kit/test_validate_plugin.py -v
```

Expected: FAIL because `validate_plugin.py` does not exist.

- [ ] **Step 3: Implement `validate_plugin.py`**

Create `agent-kit/scripts/validate_plugin.py`:

```python
#!/usr/bin/env python3
import argparse
import ast
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bk_plugin_agent_kit.common import (  # noqa: E402
    VERSION_RE,
    add_common_flags,
    base_names,
    error,
    find_project_root,
    parse_python_classes,
    print_json,
    relative_to_root,
    success,
)


def meta_version(class_node: ast.ClassDef):
    for node in class_node.body:
        if isinstance(node, ast.ClassDef) and node.name == "Meta":
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "version":
                            if isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                                return item.value.value
    return None


def has_inner_class(class_node: ast.ClassDef, name: str) -> bool:
    return any(isinstance(node, ast.ClassDef) and node.name == name for node in class_node.body)


def collect_plugins(root: Path) -> List[Dict[str, object]]:
    plugins = []
    for path in sorted((root / "bk_plugin" / "versions").glob("v*.py")):
        for class_node in parse_python_classes(path):
            if "Plugin" not in base_names(class_node):
                continue
            version = meta_version(class_node)
            plugins.append(
                {
                    "class_name": class_node.name,
                    "version": version,
                    "path": relative_to_root(path, root),
                    "has_inputs": has_inner_class(class_node, "Inputs"),
                    "has_context_inputs": has_inner_class(class_node, "ContextInputs"),
                    "has_outputs": has_inner_class(class_node, "Outputs"),
                    "form_exists": bool(version and (root / "bk_plugin" / "forms" / version / "form.js").exists()),
                }
            )
    return plugins


def validate(root: Path):
    plugins = collect_plugins(root)
    if not plugins:
        return error(
            "version_not_found",
            "No Plugin subclass with Meta.version was found under bk_plugin/versions",
            hints=["Create a version file such as bk_plugin/versions/v1_0_0.py."],
        )

    seen = {}
    for plugin in plugins:
        version = plugin["version"]
        if not isinstance(version, str) or not VERSION_RE.match(version):
            return error(
                "version_not_found",
                f"Plugin {plugin['class_name']} in {plugin['path']} has no valid Meta.version",
                data={"plugin": plugin},
                hints=["Set Meta.version to a semantic version such as 1.0.0."],
            )
        if version in seen:
            return error(
                "version_conflict",
                f"Version {version} is defined by both {seen[version]} and {plugin['path']}",
                data={"version": version},
                hints=["Use one unique version per plugin class."],
            )
        seen[version] = plugin["path"]
        if not plugin["form_exists"]:
            return error(
                "form_missing",
                f"form.js for version {version} is missing",
                data={"version": version, "expected": f"bk_plugin/forms/{version}/form.js"},
                hints=["Create a version-matched form file for Standard Ops rendering."],
            )

    return success({"versions": plugins}, hints=["Static validation passed. Run simulate_invoke.py after starting the local runtime."])


def main():
    parser = argparse.ArgumentParser(description="Validate a generated BlueKing plugin Demo project")
    add_common_flags(parser)
    args = parser.parse_args()

    root = find_project_root(Path(args.project_root))
    if root is None:
        print_json(error("project_not_found", "No cookiecutter-generated plugin Demo project found"), args.pretty)
        raise SystemExit(1)

    payload = validate(root)
    print_json(payload, args.pretty)
    if not payload["result"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run validation tests**

Run:

```bash
pytest tests/agent_kit/test_validate_plugin.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit validation CLI**

```bash
git add agent-kit/scripts/validate_plugin.py tests/agent_kit/test_validate_plugin.py
git commit -m "feat: add static plugin validation script"
```

## Task 4: Version Generation CLI and Templates

**Files:**
- Create: `agent-kit/scripts/generate_version.py`
- Create: `agent-kit/templates/version.py.j2`
- Create: `agent-kit/templates/form.js.j2`
- Create: `agent-kit/templates/test_plugin.py.j2`
- Create: `tests/agent_kit/test_generate_version.py`

- [ ] **Step 1: Write generation tests**

Create `tests/agent_kit/test_generate_version.py`:

```python
from tests.agent_kit.conftest import parse_json, run_script


def test_generate_version_creates_files(demo_project):
    result = run_script(
        "generate_version.py",
        "--project-root",
        str(demo_project),
        "--version",
        "1.1.0",
        "--class-name",
        "EchoPlugin",
        "--description",
        "echo input",
    )
    payload = parse_json(result.stdout)

    assert result.returncode == 0
    assert payload["result"] is True
    assert (demo_project / "bk_plugin" / "versions" / "v1_1_0.py").exists()
    assert (demo_project / "bk_plugin" / "forms" / "1.1.0" / "form.js").exists()
    assert (demo_project / "tests" / "test_plugin_v1_1_0.py").exists()


def test_generate_version_refuses_to_overwrite(demo_project):
    run_script("generate_version.py", "--project-root", str(demo_project), "--version", "1.1.0")

    result = run_script("generate_version.py", "--project-root", str(demo_project), "--version", "1.1.0")
    payload = parse_json(result.stdout)

    assert result.returncode == 1
    assert payload["code"] == "file_exists"
```

- [ ] **Step 2: Run generation tests to verify they fail**

Run:

```bash
pytest tests/agent_kit/test_generate_version.py -v
```

Expected: FAIL because `generate_version.py` and templates do not exist.

- [ ] **Step 3: Add templates**

Create `agent-kit/templates/version.py.j2`:

```python
import logging

from bk_plugin_framework.kit import Context, ContextRequire, Field, InputsModel, OutputsModel, Plugin

logger = logging.getLogger("bk_plugin")


class {{ class_name }}(Plugin):
    class Meta:
        version = "{{ version }}"
        desc = "{{ description }}"

    class Inputs(InputsModel):
        hello: str = Field(title="输入内容", description="本地验证用输入")

    class Outputs(OutputsModel):
        world: str = Field(title="输出内容", description="本地验证用输出")

    class ContextInputs(ContextRequire):
        executor: str = Field(title="任务执行人")

    def execute(self, inputs: Inputs, context: Context):
        context.outputs["world"] = inputs.hello
```

Create `agent-kit/templates/form.js.j2`:

```javascript
var tag = [
  {
    tag_code: "hello",
    type: "input",
    attrs: {
      name: "输入内容",
      placeholder: "请输入内容",
      validation: [
        {
          type: "required"
        }
      ]
    }
  }
];
```

Create `agent-kit/templates/test_plugin.py.j2`:

```python
from bk_plugin.versions.{{ module_name }} import {{ class_name }}
from bk_plugin_framework.kit import Context, State


def test_{{ module_name }}_execute_success():
    plugin = {{ class_name }}()
    inputs = {{ class_name }}.Inputs(hello="world")
    context = Context(
        trace_id="localtrace",
        data={{ class_name }}.ContextInputs(executor="admin"),
        state=State.EMPTY,
        invoke_count=1,
        outputs={},
    )

    plugin.execute(inputs=inputs, context=context)

    assert context.outputs["world"] == "world"
```

- [ ] **Step 4: Implement `generate_version.py`**

Create `agent-kit/scripts/generate_version.py`:

```python
#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bk_plugin_agent_kit.common import (  # noqa: E402
    VERSION_RE,
    add_common_flags,
    error,
    find_project_root,
    print_json,
    success,
    version_to_module_name,
)


TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "templates"


def render_template(name: str, values):
    text = (TEMPLATE_ROOT / name).read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{ " + key + " }}", str(value))
    return text


def write_new(path: Path, content: str, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate a new BlueKing plugin version")
    add_common_flags(parser)
    parser.add_argument("--version", required=True, help="Plugin version such as 1.1.0")
    parser.add_argument("--class-name", default="MyPlugin", help="Python plugin class name")
    parser.add_argument("--description", default="generated plugin version", help="Meta.desc content")
    parser.add_argument("--force", action="store_true", help="Overwrite generated files")
    args = parser.parse_args()

    root = find_project_root(Path(args.project_root))
    if root is None:
        print_json(error("project_not_found", "No cookiecutter-generated plugin Demo project found"), args.pretty)
        raise SystemExit(1)
    if not VERSION_RE.match(args.version):
        print_json(error("invalid_version", f"Invalid version: {args.version}"), args.pretty)
        raise SystemExit(1)

    module_filename = version_to_module_name(args.version)
    module_name = Path(module_filename).stem
    values = {
        "version": args.version,
        "class_name": args.class_name,
        "description": args.description,
        "module_name": module_name,
    }
    targets = {
        root / "bk_plugin" / "versions" / module_filename: render_template("version.py.j2", values),
        root / "bk_plugin" / "forms" / args.version / "form.js": render_template("form.js.j2", values),
        root / "tests" / f"test_plugin_{module_name}.py": render_template("test_plugin.py.j2", values),
    }
    blocked = [path for path in targets if path.exists() and not args.force]
    if blocked:
        print_json(
            error(
                "file_exists",
                "Generated target already exists",
                data={"paths": [str(path) for path in blocked]},
                hints=["Use --force only when you intend to replace generated files."],
            ),
            args.pretty,
        )
        raise SystemExit(1)

    written = []
    for path, content in targets.items():
        write_new(path, content, args.force)
        written.append(str(path))

    print_json(success({"written": written}), args.pretty)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run generation tests**

Run:

```bash
pytest tests/agent_kit/test_generate_version.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit generation CLI and templates**

```bash
git add agent-kit/scripts/generate_version.py agent-kit/templates/version.py.j2 agent-kit/templates/form.js.j2 agent-kit/templates/test_plugin.py.j2 tests/agent_kit/test_generate_version.py
git commit -m "feat: add plugin version generation script"
```

## Task 5: Invoke Payload Rendering

**Files:**
- Create: `agent-kit/scripts/render_call_payload.py`
- Create: `agent-kit/templates/verify_payload.json.j2`
- Create: `tests/agent_kit/test_render_call_payload.py`

- [ ] **Step 1: Write payload rendering tests**

Create `tests/agent_kit/test_render_call_payload.py`:

```python
import json

from tests.agent_kit.conftest import parse_json, run_script


def test_render_call_payload_from_inputs_file(demo_project, tmp_path):
    inputs_file = tmp_path / "inputs.json"
    output_file = tmp_path / "payload.json"
    inputs_file.write_text(json.dumps({"hello": "world"}), encoding="utf-8")

    result = run_script(
        "render_call_payload.py",
        "--project-root",
        str(demo_project),
        "--inputs-file",
        str(inputs_file),
        "--output-file",
        str(output_file),
    )
    payload = parse_json(result.stdout)
    rendered = json.loads(output_file.read_text(encoding="utf-8"))

    assert result.returncode == 0
    assert payload["result"] is True
    assert rendered["inputs"] == {"hello": "world"}
    assert rendered["context"]["executor"] == "admin"
    assert rendered["context"]["task_name"] == "local verify"


def test_render_call_payload_rejects_invalid_inputs_json(demo_project, tmp_path):
    inputs_file = tmp_path / "inputs.json"
    inputs_file.write_text("{bad", encoding="utf-8")

    result = run_script("render_call_payload.py", "--project-root", str(demo_project), "--inputs-file", str(inputs_file))
    payload = parse_json(result.stdout)

    assert result.returncode == 1
    assert payload["code"] == "invalid_json"
```

- [ ] **Step 2: Run payload tests to verify they fail**

Run:

```bash
pytest tests/agent_kit/test_render_call_payload.py -v
```

Expected: FAIL because `render_call_payload.py` does not exist.

- [ ] **Step 3: Add default payload template**

Create `agent-kit/templates/verify_payload.json.j2`:

```json
{
  "inputs": {{ inputs_json }},
  "context": {
    "project_id": 1,
    "project_name": "local",
    "bk_biz_id": 2,
    "bk_biz_name": "local",
    "operator": "admin",
    "executor": "admin",
    "task_id": 1,
    "task_name": "local verify"
  }
}
```

- [ ] **Step 4: Implement `render_call_payload.py`**

Create `agent-kit/scripts/render_call_payload.py`:

```python
#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bk_plugin_agent_kit.common import add_common_flags, error, find_project_root, print_json, success, write_json_file  # noqa: E402


DEFAULT_CONTEXT = {
    "project_id": 1,
    "project_name": "local",
    "bk_biz_id": 2,
    "bk_biz_name": "local",
    "operator": "admin",
    "executor": "admin",
    "task_id": 1,
    "task_name": "local verify",
}


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def main():
    parser = argparse.ArgumentParser(description="Render a local Standard Ops-like plugin invoke payload")
    add_common_flags(parser)
    parser.add_argument("--inputs-file", required=True, help="JSON file containing plugin inputs")
    parser.add_argument("--context-file", help="JSON file containing context overrides")
    parser.add_argument("--output-file", help="Write payload to this file")
    args = parser.parse_args()

    root = find_project_root(Path(args.project_root))
    if root is None:
        print_json(error("project_not_found", "No cookiecutter-generated plugin Demo project found"), args.pretty)
        raise SystemExit(1)

    try:
        inputs = load_json(Path(args.inputs_file))
        context = dict(DEFAULT_CONTEXT)
        if args.context_file:
            context.update(load_json(Path(args.context_file)))
    except ValueError as exc:
        print_json(error("invalid_json", str(exc)), args.pretty)
        raise SystemExit(1)

    payload = {"inputs": inputs, "context": context}
    output_file = args.output_file or str(root / "reports" / "verify_payload.json")
    write_json_file(Path(output_file), payload)
    print_json(success({"payload_file": output_file, "payload": payload}), args.pretty)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run payload tests**

Run:

```bash
pytest tests/agent_kit/test_render_call_payload.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit payload rendering**

```bash
git add agent-kit/scripts/render_call_payload.py agent-kit/templates/verify_payload.json.j2 tests/agent_kit/test_render_call_payload.py
git commit -m "feat: add local invoke payload rendering"
```

## Task 6: HTTP Simulation and Trace Scripts

**Files:**
- Create: `agent-kit/scripts/bk_plugin_agent_kit/http.py`
- Create: `agent-kit/scripts/simulate_invoke.py`
- Create: `agent-kit/scripts/poll_schedule.py`
- Create: `agent-kit/scripts/collect_trace.py`
- Create: `tests/agent_kit/test_http_scripts.py`

- [ ] **Step 1: Write HTTP script tests**

Create `tests/agent_kit/test_http_scripts.py`:

```python
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

from tests.agent_kit.conftest import parse_json, run_script


class Handler(BaseHTTPRequestHandler):
    def _send(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/bk_plugin/meta/":
            self._send({"result": True, "data": {"versions": ["1.0.0"]}, "message": ""})
        elif self.path == "/bk_plugin/detail/1.0.0":
            self._send({"result": True, "data": {"version": "1.0.0"}, "message": ""})
        elif self.path == "/bk_plugin/schedule/trace123":
            self._send({"result": True, "data": {"state": 4, "outputs": {"world": "ok"}, "err": ""}, "message": ""})
        elif self.path == "/bk_plugin/logs/trace123":
            self._send({"result": True, "data": {"log": "trace log"}, "message": ""})
        else:
            self._send({"result": False, "message": "missing"}, status=404)

    def do_POST(self):
        if self.path == "/bk_plugin/invoke/1.0.0":
            self._send({"result": True, "trace_id": "trace123", "data": {"state": 4, "outputs": {"world": "ok"}, "err": ""}, "message": "success"})
        else:
            self._send({"result": False, "message": "missing"}, status=404)

    def log_message(self, format, *args):
        return


@pytest.fixture
def http_server():
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_simulate_invoke_success(demo_project, http_server, tmp_path):
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(json.dumps({"inputs": {"hello": "ok"}, "context": {"executor": "admin"}}), encoding="utf-8")

    result = run_script("simulate_invoke.py", "--base-url", http_server, "--version", "1.0.0", "--payload-file", str(payload_file))
    payload = parse_json(result.stdout)

    assert result.returncode == 0
    assert payload["result"] is True
    assert payload["data"]["trace_id"] == "trace123"
    assert payload["data"]["state"] == 4


def test_poll_schedule_success(http_server):
    result = run_script("poll_schedule.py", "--base-url", http_server, "--trace-id", "trace123", "--interval", "0", "--timeout", "1")
    payload = parse_json(result.stdout)

    assert result.returncode == 0
    assert payload["result"] is True
    assert payload["data"]["state"] == 4


def test_collect_trace_success(http_server):
    result = run_script("collect_trace.py", "--base-url", http_server, "--trace-id", "trace123")
    payload = parse_json(result.stdout)

    assert result.returncode == 0
    assert payload["data"]["log"] == "trace log"
```

- [ ] **Step 2: Run HTTP tests to verify they fail**

Run:

```bash
pytest tests/agent_kit/test_http_scripts.py -v
```

Expected: FAIL because HTTP scripts do not exist.

- [ ] **Step 3: Implement HTTP helper**

Create `agent-kit/scripts/bk_plugin_agent_kit/http.py`:

```python
import json
from typing import Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


def build_url(base_url: str, path: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def request_json(method: str, base_url: str, path: str, body: Optional[Dict] = None, headers: Optional[Dict[str, str]] = None, timeout: int = 10):
    data = None
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    request = Request(build_url(base_url, path), data=data, headers=request_headers, method=method.upper())
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"result": False, "message": raw}
        return exc.code, payload
    except URLError as exc:
        return 0, {"result": False, "message": str(exc)}
```

- [ ] **Step 4: Implement `simulate_invoke.py`**

Create `agent-kit/scripts/simulate_invoke.py`:

```python
#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bk_plugin_agent_kit.common import error, load_json_file, print_json, success  # noqa: E402
from bk_plugin_agent_kit.http import request_json  # noqa: E402


SCOPE_HEADERS = {"Bkplugin-Scope-Type": "space", "Bkplugin-Scope-Value": "local"}


def main():
    parser = argparse.ArgumentParser(description="Simulate Standard Ops remote_plugin invoke against a local runtime")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--payload-file", required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = load_json_file(Path(args.payload_file))
    meta_status, meta = request_json("GET", args.base_url, "/bk_plugin/meta/")
    if meta_status == 0:
        print_json(error("runtime_unreachable", meta["message"]), args.pretty)
        raise SystemExit(1)
    detail_status, detail = request_json("GET", args.base_url, f"/bk_plugin/detail/{args.version}")
    if detail_status >= 400:
        print_json(error("version_not_found", detail.get("message", "detail request failed"), data={"detail": detail}), args.pretty)
        raise SystemExit(1)
    invoke_status, invoke = request_json("POST", args.base_url, f"/bk_plugin/invoke/{args.version}", body=payload, headers=SCOPE_HEADERS)
    if invoke_status >= 400 or not invoke.get("result"):
        print_json(error("invoke_failed", invoke.get("message", "invoke failed"), data={"invoke": invoke}), args.pretty)
        raise SystemExit(1)

    invoke_data = invoke.get("data") or {}
    data = {
        "meta": meta,
        "detail": detail,
        "trace_id": invoke.get("trace_id"),
        "state": invoke_data.get("state"),
        "outputs": invoke_data.get("outputs"),
        "err": invoke_data.get("err"),
        "next_action": "poll_schedule" if invoke_data.get("state") in {2, 3} else "done",
    }
    print_json(success(data), args.pretty)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Implement `poll_schedule.py`**

Create `agent-kit/scripts/poll_schedule.py`:

```python
#!/usr/bin/env python3
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bk_plugin_agent_kit.common import error, print_json, success  # noqa: E402
from bk_plugin_agent_kit.http import request_json  # noqa: E402


TERMINAL_STATES = {4, 5}


def main():
    parser = argparse.ArgumentParser(description="Poll local plugin schedule state")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--trace-id", required=True)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    deadline = time.time() + args.timeout
    last_payload = None
    while time.time() <= deadline:
        status, payload = request_json("GET", args.base_url, f"/bk_plugin/schedule/{args.trace_id}")
        last_payload = payload
        if status == 0:
            print_json(error("runtime_unreachable", payload["message"]), args.pretty)
            raise SystemExit(1)
        if status >= 400 or not payload.get("result"):
            print_json(error("schedule_not_found", payload.get("message", "schedule request failed"), data={"schedule": payload}), args.pretty)
            raise SystemExit(1)
        data = payload.get("data") or {}
        if data.get("state") in TERMINAL_STATES:
            print_json(success(data), args.pretty)
            return
        time.sleep(args.interval)

    print_json(error("schedule_timeout", "Schedule did not reach a terminal state", data={"last": last_payload}), args.pretty)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Implement `collect_trace.py`**

Create `agent-kit/scripts/collect_trace.py`:

```python
#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bk_plugin_agent_kit.common import error, print_json, success  # noqa: E402
from bk_plugin_agent_kit.http import request_json  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Collect local trace logs")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--trace-id", required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    status, payload = request_json("GET", args.base_url, f"/bk_plugin/logs/{args.trace_id}")
    if status == 0:
        print_json(error("runtime_unreachable", payload["message"]), args.pretty)
        raise SystemExit(1)
    if status >= 400 or not payload.get("result"):
        print_json(error("trace_unavailable", payload.get("message", "trace logs unavailable"), data={"logs": payload}), args.pretty)
        raise SystemExit(1)
    print_json(success(payload.get("data") or {}), args.pretty)


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: Run HTTP script tests**

Run:

```bash
pytest tests/agent_kit/test_http_scripts.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit HTTP scripts**

```bash
git add agent-kit/scripts/bk_plugin_agent_kit/http.py agent-kit/scripts/simulate_invoke.py agent-kit/scripts/poll_schedule.py agent-kit/scripts/collect_trace.py tests/agent_kit/test_http_scripts.py
git commit -m "feat: add local protocol verification scripts"
```

## Task 7: Agent Workflows, Manifest, and Adapters

**Files:**
- Create: `agent-kit/AGENT.md`
- Create: `agent-kit/manifest.yaml`
- Create: `agent-kit/workflows/01-orient-demo-project.md`
- Create: `agent-kit/workflows/02-develop-plugin-requirement.md`
- Create: `agent-kit/workflows/03-verify-like-bksops.md`
- Create: `agent-kit/workflows/04-troubleshoot-failure.md`
- Create: `agent-kit/adapters/generic/prompt.md`
- Create: `agent-kit/adapters/codex/SKILL.md`
- Create: `tests/agent_kit/test_manifest_and_docs.py`

- [ ] **Step 1: Write docs presence tests**

Create `tests/agent_kit/test_manifest_and_docs.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "agent-kit"


def test_required_agent_kit_docs_exist():
    required = [
        "AGENT.md",
        "manifest.yaml",
        "workflows/01-orient-demo-project.md",
        "workflows/02-develop-plugin-requirement.md",
        "workflows/03-verify-like-bksops.md",
        "workflows/04-troubleshoot-failure.md",
        "adapters/generic/prompt.md",
        "adapters/codex/SKILL.md",
    ]

    missing = [path for path in required if not (KIT / path).exists()]

    assert missing == []


def test_manifest_names_all_scripts():
    manifest = (KIT / "manifest.yaml").read_text(encoding="utf-8")
    for script in [
        "inspect_demo.py",
        "validate_plugin.py",
        "generate_version.py",
        "render_call_payload.py",
        "simulate_invoke.py",
        "poll_schedule.py",
        "collect_trace.py",
    ]:
        assert script in manifest


def test_agent_entrypoint_mentions_version_source_priority():
    agent = (KIT / "AGENT.md").read_text(encoding="utf-8")

    assert "Do not infer behavior from the latest GitHub branch" in agent
    assert "requirements.txt" in agent
```

- [ ] **Step 2: Run docs tests to verify they fail**

Run:

```bash
pytest tests/agent_kit/test_manifest_and_docs.py -v
```

Expected: FAIL because docs and manifest do not exist.

- [ ] **Step 3: Create `AGENT.md`**

Create `agent-kit/AGENT.md`:

```markdown
# BK Standard Plugin Agent Kit

Use this kit when helping a user develop a BlueKing standard plugin from a cookiecutter-generated Demo project.

## Operating Rules

1. Treat the user's generated plugin Demo project as the source of truth.
2. Read `requirements.txt`, `runtime.txt`, existing `bk_plugin/versions/`, and existing `bk_plugin/forms/` before editing.
3. Do not infer behavior from the latest GitHub branch unless the user explicitly asks for that comparison.
4. Prefer creating a new plugin version for breaking changes.
5. Validate locally through `/bk_plugin/meta/`, `/bk_plugin/detail/<version>`, `/bk_plugin/invoke/<version>`, and `/bk_plugin/schedule/<trace_id>`.
6. Label verification results as local protocol simulation.

## Default Flow

1. Run `python agent-kit/scripts/inspect_demo.py --project-root <demo> --pretty`.
2. Run `python agent-kit/scripts/validate_plugin.py --project-root <demo> --pretty`.
3. Clarify inputs, context inputs, outputs, and sync or schedule behavior.
4. Edit or generate version files, form files, and tests.
5. Run project tests.
6. Start the local runtime with `python bin/manage.py rundebugserver`.
7. Render an invoke payload and run `simulate_invoke.py`.
8. If state is `2` or `3`, run `poll_schedule.py`.
9. On failure, run `collect_trace.py` and follow `workflows/04-troubleshoot-failure.md`.
```

- [ ] **Step 4: Create `manifest.yaml`**

Create `agent-kit/manifest.yaml`:

```yaml
name: bk-standard-plugin-agent-kit
version: 0.1.0
description: Agent-neutral local kit for BlueKing standard plugin development and local BK-SOPS-style verification.
requires:
  shell: optional
  python: ">=3.8"
workflows:
  orient:
    path: workflows/01-orient-demo-project.md
  develop:
    path: workflows/02-develop-plugin-requirement.md
  verify:
    path: workflows/03-verify-like-bksops.md
  troubleshoot:
    path: workflows/04-troubleshoot-failure.md
commands:
  inspect_demo:
    path: scripts/inspect_demo.py
    output: json
  validate_plugin:
    path: scripts/validate_plugin.py
    output: json
  generate_version:
    path: scripts/generate_version.py
    output: json
  render_call_payload:
    path: scripts/render_call_payload.py
    output: json
  simulate_invoke:
    path: scripts/simulate_invoke.py
    output: json
  poll_schedule:
    path: scripts/poll_schedule.py
    output: json
  collect_trace:
    path: scripts/collect_trace.py
    output: json
adapters:
  generic: adapters/generic/prompt.md
  codex: adapters/codex/SKILL.md
verification_scope: local_protocol_simulation
```

- [ ] **Step 5: Create workflow documents**

Create `agent-kit/workflows/01-orient-demo-project.md`:

```markdown
# Orient Demo Project

Run `inspect_demo.py` from the generated plugin Demo project. Confirm `bk_plugin/meta.py`, `bk_plugin/versions/`, `bk_plugin/forms/`, `bin/manage.py`, and `requirements.txt` exist. Use dependency pins from the Demo project before consulting framework source.
```

Create `agent-kit/workflows/02-develop-plugin-requirement.md`:

```markdown
# Develop Plugin Requirement

Clarify visible inputs, Standard Ops context inputs, outputs, state behavior, external calls, and examples. Use a new version for breaking changes. Keep business logic in `bk_plugin/versions/vX_Y_Z.py`, form definition in `bk_plugin/forms/X.Y.Z/form.js`, and focused tests in `tests/`.
```

Create `agent-kit/workflows/03-verify-like-bksops.md`:

```markdown
# Verify Like BK-SOPS Locally

Start the local runtime with `python bin/manage.py rundebugserver`. Render a payload with Standard Ops-like context. Call `meta`, `detail`, and `invoke` through `simulate_invoke.py`. If invoke returns state `2` or `3`, poll `schedule` by trace id. Report the result as local protocol simulation.
```

Create `agent-kit/workflows/04-troubleshoot-failure.md`:

```markdown
# Troubleshoot Failure

Use script error codes to pick the next action. For `project_not_found`, run from the Demo project root. For `form_missing`, create `bk_plugin/forms/<version>/form.js`. For validation failures, compare the payload with `Inputs` and `ContextInputs`. For schedule failures, confirm worker and broker setup when polling or callback behavior is used.
```

- [ ] **Step 6: Create adapters**

Create `agent-kit/adapters/generic/prompt.md`:

```markdown
# Generic Agent Adapter

Read `../../AGENT.md` first. Use `../../manifest.yaml` to find workflows and scripts. If shell access is available, run the listed Python scripts and parse JSON output. If shell access is unavailable, use the workflows to edit files and provide exact commands for the user to run.
```

Create `agent-kit/adapters/codex/SKILL.md`:

```markdown
---
name: bk-standard-plugin-agent-kit
description: Develop and locally verify BlueKing standard plugins from cookiecutter-generated Demo projects.
---

# BK Standard Plugin Agent Kit for Codex

Read `../../AGENT.md` and follow `../../manifest.yaml`. Before editing a plugin, run `inspect_demo.py` and `validate_plugin.py` when shell access is available. Use local protocol simulation for verification and do not treat it as a real BK-SOPS execution.
```

- [ ] **Step 7: Run docs tests**

Run:

```bash
pytest tests/agent_kit/test_manifest_and_docs.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit docs and adapters**

```bash
git add agent-kit/AGENT.md agent-kit/manifest.yaml agent-kit/workflows agent-kit/adapters tests/agent_kit/test_manifest_and_docs.py
git commit -m "docs: add agent kit workflows and adapters"
```

## Task 8: End-to-End Script Verification

**Files:**
- Modify: files created in Tasks 1-7 only if verification finds a specific failure.

- [ ] **Step 1: Run all agent kit tests**

Run:

```bash
pytest tests/agent_kit -v
```

Expected: PASS.

- [ ] **Step 2: Run framework tests that are cheap and local**

Run:

```bash
cd bk-plugin-framework && pytest tests/utils tests/kit -v
```

Expected: PASS.

- [ ] **Step 3: Run script smoke test against fixture-style generated files**

Run:

```bash
tmpdir="$(mktemp -d)"
mkdir -p "$tmpdir/demo_plugin/bin" "$tmpdir/demo_plugin/bk_plugin/versions" "$tmpdir/demo_plugin/bk_plugin/forms/1.0.0" "$tmpdir/demo_plugin/tests"
printf "print('manage')\n" > "$tmpdir/demo_plugin/bin/manage.py"
printf "description = 'demo'\nallow_scope = {}\n" > "$tmpdir/demo_plugin/bk_plugin/meta.py"
printf "bk-plugin-framework==2.3.12\nbk-plugin-runtime==2.1.9\n" > "$tmpdir/demo_plugin/requirements.txt"
printf "python-3.8.18\n" > "$tmpdir/demo_plugin/runtime.txt"
printf "" > "$tmpdir/demo_plugin/bk_plugin/versions/__init__.py"
printf "var tag = [];\n" > "$tmpdir/demo_plugin/bk_plugin/forms/1.0.0/form.js"
cat > "$tmpdir/demo_plugin/bk_plugin/versions/v1_0_0.py" <<'PY'
from bk_plugin_framework.kit import Context, ContextRequire, Field, InputsModel, OutputsModel, Plugin


class MyPlugin(Plugin):
    class Meta:
        version = "1.0.0"

    class Inputs(InputsModel):
        hello: str

    class Outputs(OutputsModel):
        world: str

    class ContextInputs(ContextRequire):
        executor: str = Field(title="任务执行人")

    def execute(self, inputs: Inputs, context: Context):
        context.outputs["world"] = inputs.hello
PY
python agent-kit/scripts/inspect_demo.py --project-root "$tmpdir/demo_plugin" --pretty
python agent-kit/scripts/validate_plugin.py --project-root "$tmpdir/demo_plugin" --pretty
```

Expected: both commands return `"result": true`.

- [ ] **Step 4: Commit verification fixes if any files changed**

If Step 1, 2, or 3 required changes, commit only the changed agent-kit files and tests:

```bash
git add agent-kit tests/agent_kit
git commit -m "fix: stabilize agent kit verification"
```

Expected: no commit is created when verification passed without file changes.

## Task 9: Final Review and Handoff

**Files:**
- Modify: none unless final review finds a concrete issue in created files.

- [ ] **Step 1: Check worktree scope**

Run:

```bash
git status --short
```

Expected: only `.serena/` may remain untracked from the pre-existing worktree state; no unintended framework runtime files are modified.

- [ ] **Step 2: Check no blocked marker text remains in plan-generated docs**

Run:

```bash
python - <<'PY'
from pathlib import Path

markers = ["TB" + "D", "TO" + "DO", "FIX" + "ME", "implement " + "later"]
paths = [Path("agent-kit"), Path("tests/agent_kit"), Path("docs/superpowers/plans/2026-05-26-bk-standard-plugin-agent-kit.md")]
matches = []
for base in paths:
    files = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
    for path in files:
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker in text:
                matches.append(f"{path}: contains {marker}")
print("\n".join(matches))
raise SystemExit(1 if matches else 0)
PY
```

Expected: no output.

- [ ] **Step 3: Summarize implementation**

Prepare a concise handoff with:

- created `agent-kit/` structure
- created script names and their purpose
- test commands run
- local protocol simulation scope
- note that `.serena/` was not touched

- [ ] **Step 4: Final commit if Task 9 changed files**

If final review required edits:

```bash
git add agent-kit tests/agent_kit docs/superpowers/plans/2026-05-26-bk-standard-plugin-agent-kit.md
git commit -m "docs: refine agent kit implementation plan"
```

Expected: commit only created agent-kit or plan files.

## Self-Review

Spec coverage:

- Agent-neutral local kit: Task 7 creates `AGENT.md`, manifest, workflows, and adapters.
- Generated Demo project source of truth: Tasks 1 and 2 implement project detection and dependency parsing.
- Local protocol simulation: Tasks 5 and 6 implement payload rendering, invoke simulation, schedule polling, and trace collection.
- No shared MCP deployment: Task 7 documents local-first behavior, and no service deployment files are planned.
- No framework source modification: File structure and Task 9 explicitly check this.
- Version priority: Task 2 exposes dependency pins, and Task 7 documents the rule.
- Tests: Tasks 1 through 8 add focused pytest coverage and smoke verification.

Marker scan:

- The red-flag marker scan is part of Task 9 and avoids matching its own command text.
- Each code-creating step includes complete file content for the planned first implementation.

Type consistency:

- Scripts import shared helpers from `bk_plugin_agent_kit.common` and `bk_plugin_agent_kit.http`.
- JSON envelopes use `result`, `code`, `message`, `data`, and `hints` consistently.
- Terminal plugin states use framework numeric states `4` for `SUCCESS` and `5` for `FAIL`; unfinished states use `2` and `3`.
