# Authorization/session 提交契约修复与后续工程清单

日期：2026-10-07。范围：共享入口与 CPU 验证；不变更训练配方，不启动仿真。
本轮按用户要求只提交文档，下面的代码/测试修复留在工作树，尚未进入 Git commit。
只 checkout HEAD 时不能假定这些新接口已存在，先查 `git status` 与 `--help`。

## 两处已修复的接口缺口

静态核对确认：历史 spec 同时使用字符串与字典 authorization；旧训练链对其
直接调用 `.get()`。默认 supervisor plan 没有验证完整 session/GPU 提交元数据。
本轮未重跑旧提交，也没有修改当前运行的冻结副本。

1. 新增纯域接口 `domain.submission_contract.authorization(spec)`。
   接受旧 AUTHORIZED/UNAUTHORIZED 字符串，返回字典；字典保持原字段，
   缺 status 的旧字典标 UNKNOWN。非法类型/status/session 明确拒绝。
   不原位改写 spec，不改变文件 SHA，不把兼容解析当作新授权。
2. config.validate 校验类型；stand_chain 用规范化接口读取绑定 session。
3. supervisor 的训练与 PPO0 评估计划都输出 `submission_contract`；
   launch 复用同一判断，在 ledger reserve/启动子进程之前拒绝不完整提交。
4. 新增 `--check-submission`：执行一次只读资源/提交检查，不写 run 或预算。
   不能与 `--launch` 同用，避免“检查命令”实际启动。

账本仍是授权与累计预算的必要证据。UNKNOWN 兼容旧声明不跳过 ledger preflight；
spec 明确 UNAUTHORIZED 则拒绝提交。旧 AUTHORIZED、历史会话或剩余额度
不代表当前用户授权。代码修复不新增训练预算。

## Plan 与可提交检查的区别

| 字段/状态 | 含义 |
| --- | --- |
| preflight.status | 原有当前 phase 的配置、身份、账本与前置证据检查，保留兼容 |
| submission_contract.configuration_status | 原 preflight 是否 PASS；不是单独的 schema 验收 |
| NOT_READY | 元数据、原 preflight 或资源检查有阻塞；列出 errors/reason_code |
| READY_METADATA | 元数据完整，但未做资源核验；submit_ready=false |
| READY | 当前检查时刻前置条件及资源已核验；submit_ready=true，未启动 |
| resource_verified | 是否实际获得一次资源核验；不代表未来 GPU 永远可用 |

默认 plan 不读取进程/GPU，不把 PASS 宣称成可以提交。
`--check-submission` 在未就绪时返回退出码 2，成功返回 0；仍保持零写入。
核对当前 session、spec 绑定 session、物理 GPU/index/UUID、共享模式、输出路径
及重复 chain receipt。原 preflight 的预算/身份错误继续保留。
resource review 拒绝或未知为 MISSING_EVIDENCE，UUID 冲突为 IDENTITY_ERROR；
authorization/session 缺失为 AUTHORIZATION_MISSING，其余元数据错误为 CONFIG_ERROR。
这是当前 phase 的提交检查，不承诺未来阶段预算、能力验收或训练一定成功。

## 用法

先设置实际 `SPEC_PATH`、全新 `RUN_PATH`，确认本次会话的 `HAPI_SESSION_ID`，
并明确指定本次允许的 `PHYSICAL_GPU`。不从历史 spec 自动继承会话目标。

```bash
cd /home/kellen/wheel_leg_native_train
export PYTHONPATH=src
PYTHON=/home/kellen/anaconda3/envs/issaclab/bin/python
# 默认计划：不读取资源，不写文件，不启动
"$PYTHON" -m native_stand.command_v6.supervisor \
  --spec "$SPEC_PATH" --output-dir "$RUN_PATH"
# 一次只读可提交检查；评估任务另加 --evaluation-only
"$PYTHON" -m native_stand.command_v6.supervisor \
  --spec "$SPEC_PATH" --output-dir "$RUN_PATH" --check-submission \
  --hapi-session "$HAPI_SESSION_ID" --physical-gpu "$PHYSICAL_GPU"
```

不要循环执行检查等待 GPU 空闲。实际 launch 仍须明确授权、前置检查与独立
exact attempt；一次握手后结束交互，由后台 owner 结算并通知当前会话。

## 精确代码与测试范围

留在工作树，不纳入本次文档提交：

- `src/native_stand/command_v6/domain/submission_contract.py`：规范化与纯元数据判断。
- `src/native_stand/command_v6/config.py`：schema 入口类型校验。
- `src/native_stand/command_v6/stand_chain.py`：兼容读取 authorization session。
- `src/native_stand/command_v6/supervisor.py`：共享 readiness、只读检查与启动前拒绝。
- `tests/test_submission_contract.py`：旧类型、非法类型、session/GPU/UUID、
  输出冲突、重复提交、预算拒绝、资源未知、零写入及训练/评估入口回归。

CPU 命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q --tb=short
```

结果记录见本页末尾。GPU 可用性使用 fixture，不做真实资源快照；没有历史提交
重放、真实子进程启动或物理验证，不能声称物理/PPO 能力改善。

## 后续建议：不混入本轮修复

按收益顺序推进，复用 supervisor，不新增 trainer 或第二套历史分类：

1. 通用 Motion 准备器：父 spec/checkpoint、已通过与新端点、宽度/槽位、
   预算、检查点、GPU/session 显式输入；集中命名/SHA/exclusive-create，
   生成 requested/effective 对照与未授权独立账本。先实现 CPU fixture。
2. 跨实验预算只读审计：账本清单、exact-ID 去重、计数冲突、累计已用/剩余，
   授权范围不同则分开汇总；不得凭工具输出授予额度。
3. 来源评估决策与通用比较报告：同协议逐环境指标、双向偏置/增益、旧端点变化，
   区分普通能力不足、运行故障与证据缺失；任何自动分支只在已有明确授权内。
4. 实验标签中的控制逻辑拆成显式字段，但保留旧快照语义；此项尚未改。
5. batch 前置回归改为 request 分组判定，替代现有第 3 项位置假设；此项尚未改。
6. 报告同时显示累计新增 updates 与 formal updates，不混淆 smoke/formal 初始化。

deprecated 包装器、日期型 prepare/report 暂不删除；等通用替代覆盖且调用引用
迁移后再退役。supervisor 公开；stand_chain、launcher、monitor 内部职责保留。
本轮没有删除脚本、改变标签/评分/采样、追加预算或迁移任何活动任务。

## 验证记录

第一轮针对性回归：48 passed / 0.88s；全量 CPU：464 passed / 18.38s。
之后增加只读检查与 launch 互斥、评估缺 session 用例；最终全量复验：
466 passed / 18.45s。五个修改/新增 Python 文件 AST 通过，supervisor --help
包含新参数；文档链接与 git diff --check 通过。
历史 run、checkpoint、evaluation、ledger 均未写入。
