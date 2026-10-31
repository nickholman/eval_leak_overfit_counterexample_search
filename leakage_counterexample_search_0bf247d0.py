"""（AI芯片算力场景）输入分布改变后，评测集泄漏与过拟合的结论会不会失效？用泄漏与重复检测给出鲁棒性边界。

测量：泄漏与重复检测（overlap_rate）；协议：反例搜索。
仅依赖 Python 标准库。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

SEP = '\t'
MEASURE_FIELD = 'overlap_rate'
FAILURE_MODE = '版本漂移'


def _read_rows(path: str, limit: int = 0) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if SEP and SEP in line:
                label, _, payload = line.partition(SEP)
                rows.append((label.strip(), payload.strip()))
            else:
                rows.append(("", line.strip()))
            if limit and len(rows) >= limit:
                break
    return rows


def _nums(values: list[str]) -> list[float]:
    out: list[float] = []
    for v in values:
        try:
            out.append(float(v))
        except ValueError:
            continue
    return out


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac



def measure_leakage(rows: list[tuple[str, str]]) -> dict:
    """泄漏检测：精确匹配与近似匹配两种口径。"""
    out: dict = {"metric": "leakage", "unit": "比例"}
    groups: dict[str, set[str]] = {}
    for label, payload in rows:
        groups.setdefault(label or "all", set()).add(payload)
    names = sorted(groups)
    exact_pairs = 0
    near_pairs = 0
    compared = 0
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            compared += 1
            inter = groups[a] & groups[b]
            exact_pairs += len(inter)
            near_pairs += sum(
                1 for x in groups[a] - inter for y in groups[b]
                if x[:12] == y[:12] or x[-12:] == y[-12:])
    out["overlap_rate"] = round(exact_pairs / compared, 4) if compared else 0.0
    out["near_overlap_rate"] = round(near_pairs / compared, 4) if compared else 0.0
    out["leaked"] = bool(compared and exact_pairs / compared > 0.10)
    return out



def measure(rows: list[tuple[str, str]]) -> dict:
    """按测量族分派到具体测量函数。"""
    return measure_leakage(rows)



def run_protocol(measure, rows: list[tuple[str, str]], args: argparse.Namespace) -> dict:
    """反例搜索：逐条剔除样本，寻找让结论翻转的最小子集。"""
    baseline = measure(rows)
    threshold = float(args.threshold or 0)
    base_value = baseline.get('overlap_rate')
    counterexamples = []
    for idx, (label, payload) in enumerate(rows):
        subset = rows[:idx] + rows[idx + 1:]
        value = measure(subset).get('overlap_rate')
        if isinstance(base_value, (int, float)) and isinstance(value, (int, float)):
            if abs(value - base_value) > max(abs(base_value) * 0.1, threshold):
                counterexamples.append({"index": idx, "label": label,
                                        "removed_value": value,
                                        "delta": round(value - base_value, 6)})
    return {"protocol": "counterexample_search",
            "baseline": base_value,
            "counterexample_count": len(counterexamples),
            "counterexamples": counterexamples[:5]}



def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="（AI芯片算力场景）输入分布改变后，评测集泄漏与过拟合的结论会不会失效？用泄漏与重复检测给出鲁棒性边界。")
    ap.add_argument("--input", help="输入文件路径")
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 行")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    ap.add_argument("--threshold", type=float, default=0.0, help="判定阈值")
    ap.add_argument("--budget", type=int, default=50, help="预算条数")
    ap.add_argument("--bins", type=int, default=10, help="分桶数量")
    ap.add_argument("--components", default="", help="组件列表（逗号分隔）")
    args = ap.parse_args(argv)

    if not args.input:
        ap.print_help()
        return 0

    t0 = time.time()
    try:
        rows = _read_rows(args.input, args.limit)
    except OSError as exc:
        print(f"读取失败：{exc}", file=sys.stderr)
        return 2

    measured = measure(rows)
    result = run_protocol(measure, rows, args)
    result["measure"] = measured
    result["row_count"] = len(rows)
    result["failure_mode"] = FAILURE_MODE
    result["elapsed_seconds"] = round(time.time() - t0, 4)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        value = measured.get(MEASURE_FIELD)
        print(f"读取 1 个文件，共 {result['row_count']} 条记录")
        print(f"{MEASURE_FIELD} = {value}")
        print(f"处理完成，耗时 {result['elapsed_seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
