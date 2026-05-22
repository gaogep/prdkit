"""Hook 状态机与项目根目录校验（unittest + 子进程）。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def _run_hook(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "prdkit.hook_manager", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def _write_state(cwd: Path, stages: dict) -> None:
    memory = cwd / ".memory"
    memory.mkdir(exist_ok=True)
    (memory / "workflow_state.json").write_text(
        json.dumps({"current_stage": "init", "stages": stages}, ensure_ascii=False),
        encoding="utf-8",
    )


class HookManagerTests(unittest.TestCase):
    def test_clarify_without_memory_dir_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run_hook(["check", "clarify"], Path(tmp))
            self.assertEqual(result.returncode, 1)
            self.assertIn(".memory", result.stdout + result.stderr)

    def test_init_check_without_memory_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run_hook(["check", "init"], Path(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertIn("放行", result.stdout)

    def test_init_completed_creates_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = _run_hook(["transit", "init_completed"], cwd)
            self.assertEqual(result.returncode, 0)
            state_file = cwd / ".memory" / "workflow_state.json"
            self.assertTrue(state_file.is_file())
            state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(state["stages"]["init"], "completed")
            self.assertEqual(state["stages"]["clarify"], "pending")

    def test_clarify_after_init_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            _write_state(
                cwd,
                {
                    "init": "completed",
                    "clarify": "pending",
                    "create": "locked",
                    "modify": "locked",
                },
            )
            result = _run_hook(["check", "clarify"], cwd)
            self.assertEqual(result.returncode, 0)
            self.assertIn("放行", result.stdout)

    def test_create_before_clarify_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            _write_state(
                cwd,
                {
                    "init": "completed",
                    "clarify": "pending",
                    "create": "locked",
                    "modify": "locked",
                },
            )
            result = _run_hook(["check", "create"], cwd)
            self.assertEqual(result.returncode, 1)
            self.assertIn("clarify", result.stdout)

    def test_clarify_completed_unlocks_create(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            _write_state(
                cwd,
                {
                    "init": "completed",
                    "clarify": "pending",
                    "create": "locked",
                    "modify": "locked",
                },
            )
            result = _run_hook(["transit", "clarify_completed"], cwd)
            self.assertEqual(result.returncode, 0)
            state = json.loads((cwd / ".memory" / "workflow_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["stages"]["clarify"], "completed")
            self.assertEqual(state["stages"]["create"], "pending")


class PathsTests(unittest.TestCase):
    def test_list_resources_includes_core_keys(self) -> None:
        sys.path.insert(0, str(ROOT))
        from prdkit.paths import list_resources, resolve

        keys = list_resources()
        self.assertIn("reference/prd-writing-spec.md", keys)
        self.assertIn("assets/文档输出模板.html", keys)
        path = resolve("reference/prd-writing-spec.md")
        self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
