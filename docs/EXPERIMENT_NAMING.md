# 新实验命名规则

适用范围：此规则加入后新建的实验和实验根目录。创建时间采用Asia/Shanghai。
已有、已准备或已冻结的实验保持原名，禁止为满足命名规范搬移历史证据。

格式：`YYYY_M_D-HH_MM__用途`，例如：

```text
2026_10_7-14_27__motion_width_ab
2026_10_7-15_08__recovery_coverage
```

日期不强制补零，小时和分钟使用两位数字。名称应简短表达任务与唯一实验变量；
不要只用test、new、latest等无法区分用途的名称。

同一实验使用同一个完整名称：

- 配置根目录：`configs/experiments/2026_10_7-14_27__motion_width_ab/`。
- 运行根目录：`runs/2026_10_7-14_27__motion_width_ab/`。
- `spec.experiment`及存在时的`artifacts.run_name`与根目录名一致。

source_eval、smoke、formal以及A/B等阶段或对照臂子目录保留职责名称，
不逐个添加时间。跨日运行也不改名：前缀表示创建时间，不表示当前更新时间。
同一分钟重名时追加`_01`、`_02`，或追加秒数；仍必须使用fresh/exclusive-create，
不得覆盖旧目录、spec、checkpoint、evaluation或ledger。

Linux shell可以只读生成时间前缀：

```bash
date '+%Y_%-m_%-d-%H_%M'
```

旧日期准备器是历史复现工具，不得直接改路径后当作通用新实验入口。
新实验准备时应明确冻结目标名称，再完成身份核验、spec和独立账本。
命名规范不授权创建预算、启动仿真/PPO或复用历史授权。

本轮将规则写入AGENTS和当前入口文档，未对历史spec实施追溯schema校验。
共享命名接口为domain.experiment_naming；公开coverage准备器的CLI及prepare
函数均校验新根目录名称。历史复现工具保持冻结名称，不做追溯修改。
新增公开准备器必须复用new_experiment_name/validate_new_experiment_name，
不能自行硬编码日期。未迁移的历史工具仍由执行者遵守其复现边界；
避免仅因目录名合法就推断其配置、证据或权限有效。
