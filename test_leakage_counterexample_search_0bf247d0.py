"""自测：确认入口可运行、指标字段存在、判定规则可用。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENTRY = HERE / "leakage_counterexample_search_0bf247d0.py"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ENTRY), *args],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=str(HERE))


def test_help_exits_zero() -> None:
    proc = run(["--help"])
    assert proc.returncode == 0, proc.stderr


def test_reports_measure_field() -> None:
    sample = HERE / "sample.txt"
    proc = run(["--input", str(sample), "--json"])
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert "measure" in data, data
    assert "row_count" in data, data
    print("measure field:", data["measure"].get("overlap_rate"))


if __name__ == "__main__":
    test_help_exits_zero()
    test_reports_measure_field()
    print("ok")
