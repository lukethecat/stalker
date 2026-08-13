"""Subprocess adapter for garak (NVIDIA, Apache-2.0) -- breadth baseline scanning.

garak is a tool, not the body of this repo (see docs/architecture.md's
"工具三件套" section): this module only knows how to run a given garak
invocation safely and read back whatever JSONL report it produced. It does
not hardcode probe names, detector names, or garak's exact report schema --
those vary across garak versions/config, so callers pass the full argv and
an optional row filter/mapper instead of this module guessing.

Safety: argv is always a list (never shell=True), so no shell injection
regardless of what's embedded in target/probe strings.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 1800.0


@dataclass(frozen=True)
class GarakRunConfig:
    argv: list[str]
    report_jsonl: Path
    cwd: Path | None = None
    timeout_seconds: float | None = DEFAULT_TIMEOUT_SECONDS
    row_filter: Callable[[dict[str, Any]], bool] = field(default=lambda row: "probe" in row)


@dataclass(frozen=True)
class GarakRunResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    rows: list[dict[str, Any]]


def parse_garak_report(path: Path, row_filter: Callable[[dict[str, Any]], bool]) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and row_filter(row):
                rows.append(row)
    return rows


def run_garak(config: GarakRunConfig) -> GarakRunResult:
    """Run garak via subprocess and parse whatever report it wrote.

    Non-zero exit or a subprocess timeout does not raise -- a red-team scan
    finding vulnerabilities, crashing on a hostile target, or running past
    its timeout are all *outcomes*, not adapter bugs. Callers inspect
    `returncode`/`timed_out`/`stderr` to decide what happened.
    """
    timed_out = False
    try:
        completed = subprocess.run(
            config.argv,
            cwd=config.cwd,
            capture_output=True,
            text=True,
            timeout=config.timeout_seconds,
            check=False,
        )
        returncode, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = -1
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""

    rows = parse_garak_report(config.report_jsonl, config.row_filter)
    return GarakRunResult(returncode=returncode, stdout=stdout, stderr=stderr, timed_out=timed_out, rows=rows)
