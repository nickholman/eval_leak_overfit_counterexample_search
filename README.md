# eval_leak_overfit_counterexample_search

（AI芯片算力场景）输入分布改变后，评测集泄漏与过拟合的结论会不会失效？用泄漏与重复检测给出鲁棒性边界。

## 要回答的问题

- 子问题：评测集泄漏与过拟合
- 提问角度：robustness
- 测量方式：泄漏与重复检测（指标字段 `overlap_rate`，单位 比例）
- 实验协议：反例搜索 —— 按约束逐条筛出反例，并说明违反的是哪一条
- 重点排查的失败模式：版本漂移

## 快速开始

仅依赖 Python 标准库。

```bash
python eval_leak_overfit_counterexample_search.py --help
python eval_leak_overfit_counterexample_search.py --input sample.txt
python eval_leak_overfit_counterexample_search.py --input sample.txt --json
```

输入文件按行解析。协议「反例搜索」使用分隔符 `（无）` 区分标签与载荷。

## 用法

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--input` | 输入文件路径 | 无（必填） |
| `--limit` | 只处理前 N 行 | 0 表示不限 |
| `--json` | 以 JSON 输出结果 | 关闭 |
| `--threshold` | 判定阈值 | 0 |
| `--budget` | 预算条数 | 50 |
| `--bins` | 分桶数量 | 10 |
| `--components` | 组件列表（逗号分隔） | 无 |

## 输出

```text
读取 1 个文件，共 3 条记录
处理完成，耗时 0.002s
```

## 判定规则

训练与评测样本重叠率超过 10% 视为泄漏。

同时报告精确匹配与近似匹配两种口径。

## 复现步骤

1. 按上面的分隔符准备输入文件，每行一条样本；
2. 运行 `python eval_leak_overfit_counterexample_search.py --input sample.txt --json`；
3. 记录运行环境、输入文件与完整输出；
4. **未运行的指标不要引用**：本仓库只提供测量方法与判定规则，
   不预填任何实测数字。填入实测值前请确认对应命令与输入一致。

## 适用与不适用

- 适用：需要可脚本化、可离线复核的「评测集泄漏与过拟合」测量。
- 不适用：需要真实线上流量回放或分布式压测的场景。

## 与同类方案的区别

同类脚本通常只输出一个总数，无法回答「哪一段出的问题」。
这个实现把 overlap_rate 拆成可核对的分量，并明确给出判定规则与反例，
让人能追问结论是怎么来的，而不是接受一个无法追问来源的数字。

## 来源与参考

- Python 官方文档 argparse：<https://docs.python.org/3/library/argparse.html>
- Python 官方文档 statistics：<https://docs.python.org/3/library/statistics.html>
