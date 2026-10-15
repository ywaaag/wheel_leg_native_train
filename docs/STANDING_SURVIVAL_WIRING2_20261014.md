# v14 工程 smoke 与能力验收分离

用户明确批准修订证书并新增1000次PPO更新。新声明：`configs/experiments/2026_10_14-10_16__standing034_survival_quality_v14_wiring2/spec.json`，独立同名run与budget。原09_37链FAILED、26更新及其证书/账本保留，旧974余额不用于本次授权；本次独立1000上限，历史加本次最大1026，不自动追加或重试。

## 唯一工程修订

`students.training_evidence.smoke_certificate`对v14输出schema_version=2。进入formal仍要求身份一致、预定实际更新、Critic warmup及随后Actor更新、非零奖励、真实episode结束/reset、固定std、BC关闭、checkpoint保存读回和无工程故障。不再要求随机探索smoke出现30秒normal timeout。

证书独立记录completed episodes、最长已完成episode、normal timeout次数与`ppo_timeout_bootstrap_observed`。未观察timeout明确标注未观察，不能从CPU正确公式推断已真实物理采集该路径。工程PASSED不授予能力accepted；30秒生存与末10秒低速、直立、几何质量仍在原v14独立评估中分别判定。

CPU回归覆盖：无timeout但有真实结束/reset可通过工程证书；没有Actor更新或真实episode事件必须失败；30秒质量不合格不等于physical failure；bootstrap只使用reset前terminal Critic值；真实storage接线及online/offline质量判定一致。

## 冻结训练选择

来源v13/u988：`runs/2026_10_13-22_14__standing034_zero_privileged49_v13/formal/model_update_988.pt`，SHA `2af573b318d7ebd6df7b1a5919c5ea58e873e5d24761905ba773f8ab02cc72cd`。恢复Actor/std，新Critic49、新Adam、固定seed；新物理环境reset。不从旧smoke/u26继续。

smoke12＋formal988，共1000更新/8192000原始sample；每阶段仍按原配方先5次Critic warmup。formal100～900每100评估，终点988评估并独立终态复核。source上限1800秒、smoke3600秒，formal无墙钟截止但有有限更新/4GiB存储上限。物理GPU0 UUID `GPU-e704e7d4-2965-4712-9759-ba6b9910bd72`，共享授权/CUDA0，不抢占。未改reward、std、LR、PPO、Actor/Critic结构、物理、动作尺度或独立质量门槛。

借鉴同事RMUC：完整episode计数、真实支撑和几何质量、训练允许普通任务失败；不复制其reward数值、外环或动作接口。只读核对（该报告已按文档整理删除，长期结论见 TRAINING_EXPERIENCE_REUSE.md §12）保留其证据限制。本轮不叠加受力平衡新reward，也不预称已解决站立。

## 验证与执行证据

定向CPU29通过；公共validator选定回归37通过；PORTABLE349通过/8跳过。公共validate_cpu结果与零写plan见`artifacts/standing_survival_wiring2_20261014/cpu/validation_result.json`。实际学生初始化另见`student_initialization.json`：Actor/std完全一致、Critic49、新Adam为空、LR3e-5、CPU optimizer更新0。

通用legacy checkpoint审计器需要旧Adam参数名映射，与本配方新Critic/Adam不适用；没有修改历史checkpoint或放宽完整恢复检查，改用实际`students.ppo.assemble`核验。

本轮代码修改：`students/training_evidence.py`、`scripts/prepare_standing_survival_quality.py`、`tests/test_standing_survival_training.py`；规则/流程/命令/状态分别在AGENTS/WORKFLOW/TOOL_INDEX/STATUS更新。旧证据SHA在`historical_evidence_sha.json`提交前后核对。授权、提交与单次握手保存在同一artifact目录；无Git提交，无人工训练轮询。

## 一次提交握手

公共supervisor提交成功，worker PID114813、attempt e0562c1911c548d09149d45b029f1166；SOURCE_EVAL，submitted/submission_verified=true，formal首更新未验证，started=false。spec SHA `b28f87acec36d77c33f06ee7d35072d89416ff942c18261c147f69bba64ed553`。自动通知冻结当前负责人191bacc3-e5c7-4b8f-ae3d-5677eada837b，终态at-most-once；未新增watcher或训练轮询。phase日志/run_state/progress/最终completion_report均在同名run下。

用户询问8ms：本次仍10ms、128步=1.28秒。8ms/64步只有.512秒；控制频率对照须另立实验，核验PD调度、dt与折扣，不在本次同时修改。
