# CLI 和实验包装器

公开运行入口使用 `native_stand.command_v6.supervisor`，源码算法与物理控制位于 `src/native_stand/`。
本目录包含配方准备、CPU分析、报告和薄兼容包装；准确参数只维护于 [TOOL_INDEX](../TOOL_INDEX.md)。

查询入口分类：

```bash
PYTHONPATH=src python -m native_stand.command_v6.tools.entrypoints --include-historical
```

`CURRENT` 是当前工具；`HISTORICAL` 用于冻结历史配方；`RETIRED/DEPRECATED` 不用于新提交。
日期型脚本可能依赖本地 checkpoint、资产或证据目录，保留它们用于复现，不作为跨机器默认值。
CPU检查可以先执行 `python scripts/test_portable_cpu.py`；它只选择显式 PORTABLE fixture。
