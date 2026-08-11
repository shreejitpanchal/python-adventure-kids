"""Executes a child's Python code safely: static check, then an isolated subprocess with a timeout."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.sandbox.safety import SafetyViolation, check_code_safety

WORKER_PATH = Path(__file__).parent / "worker.py"
DEFAULT_TIMEOUT_SECONDS = 5.0


@dataclass
class ExecutionResult:
    success: bool
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    blocked: bool = False
    blocked_message: str = ""


class RunHandle:
    """Lets the UI cancel a run that's in progress (e.g. an infinite loop)."""

    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self.cancelled = False

    def _attach(self, process: subprocess.Popen) -> None:
        with self._lock:
            self._process = process
            if self.cancelled:
                process.kill()

    def cancel(self) -> None:
        with self._lock:
            self.cancelled = True
            if self._process is not None:
                self._process.kill()


def run_code(
    code: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    handle: Optional[RunHandle] = None,
    stdin_text: Optional[str] = None,
) -> ExecutionResult:
    try:
        check_code_safety(code)
    except SafetyViolation as violation:
        return ExecutionResult(success=False, blocked=True, blocked_message=violation.message)

    with tempfile.TemporaryDirectory(prefix="pyadventure_") as tmp_dir:
        code_file = Path(tmp_dir) / "child_code.py"
        code_file.write_text(code, encoding="utf-8")

        process = subprocess.Popen(
            [sys.executable, "-I", str(WORKER_PATH), str(code_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=tmp_dir,
        )
        if handle is not None:
            handle._attach(process)

        try:
            # Always feed (and close) stdin -- even "" -- so an unexpected
            # input() call in a lesson that doesn't use one fails fast with
            # EOFError instead of hanging until the timeout.
            stdout, stderr = process.communicate(input=stdin_text or "", timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            return ExecutionResult(success=False, timed_out=True)

    if handle is not None and handle.cancelled:
        return ExecutionResult(success=False, timed_out=True)

    return ExecutionResult(success=process.returncode == 0, stdout=stdout, stderr=stderr)
