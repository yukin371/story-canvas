from __future__ import annotations

import multiprocessing
import queue
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "minimal_project"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from story_harness_cli.protocol.state import _project_write_lock, load_project_state, save_state


def _hold_project_write_lock(
    project_root: str,
    ready_event,
    release_event,
    error_queue,
) -> None:
    try:
        with _project_write_lock(Path(project_root), timeout_seconds=1.0):
            ready_event.set()
            release_event.wait(5.0)
    except BaseException as exc:  # pragma: no cover - child process path
        error_queue.put(str(exc))
        ready_event.set()


def _drain_queue(error_queue) -> list[str]:
    items: list[str] = []
    while True:
        try:
            items.append(error_queue.get_nowait())
        except queue.Empty:
            return items


class StateWriteGuardSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="story-harness-state-guard-"))
        self.project_root = self.temp_dir / "minimal_project"
        shutil.copytree(FIXTURE_ROOT, self.project_root)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_state_rejects_stale_snapshot(self) -> None:
        first_state = load_project_state(self.project_root)
        second_state = load_project_state(self.project_root)

        first_state["project"]["title"] = "第一次写入"
        save_state(self.project_root, first_state, timeout_seconds=0.5)

        second_state["project"]["title"] = "过期快照"
        with self.assertRaises(SystemExit) as context:
            save_state(self.project_root, second_state, timeout_seconds=0.5)

        self.assertIn("项目状态已被其他命令更新", str(context.exception))

    def test_save_state_times_out_when_project_is_locked(self) -> None:
        ctx = multiprocessing.get_context("spawn")
        ready_event = ctx.Event()
        release_event = ctx.Event()
        try:
            error_queue = ctx.Queue()
        except PermissionError as exc:
            self.skipTest(f"当前环境不允许创建 multiprocessing.Queue: {exc}")
        process = ctx.Process(
            target=_hold_project_write_lock,
            args=(str(self.project_root), ready_event, release_event, error_queue),
        )
        process.start()
        self.addCleanup(lambda: process.terminate() if process.is_alive() else None)

        self.assertTrue(ready_event.wait(3.0), msg="child process did not acquire the project lock in time")
        self.assertEqual(_drain_queue(error_queue), [], msg="child process failed while acquiring project lock")

        state = load_project_state(self.project_root)
        with self.assertRaises(SystemExit) as context:
            save_state(self.project_root, state, timeout_seconds=0.2)

        self.assertIn("项目状态正被其他命令写入", str(context.exception))

        release_event.set()
        process.join(timeout=3.0)
        self.assertFalse(process.is_alive(), msg="child process did not release the project lock")
        self.assertEqual(_drain_queue(error_queue), [], msg="child process reported error while holding lock")


if __name__ == "__main__":
    unittest.main()
