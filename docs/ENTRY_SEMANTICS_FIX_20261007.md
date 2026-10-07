# 入口与运行语义局部修复

本轮仅修共享接口和 CPU fixture；未启动 Isaac、在线 PPO 或新训练，未停止、
修改或清理其他进程。开始时已有大量未提交的 Motion/Recovery 改动，本轮保留并
在其基础上增量整理，不将这些既有配方改动计为本轮新训练收益。

## 反馈核验与处理

| 反馈 | 处理 |
| --- | --- |
| NoMachine 被当作 GPU 独占任务，靠名称豁免 | 删除两入口的名称白名单；统一 exclusive/shared。默认 exclusive；共享需要显式批准说明，并保存资源策略和现场 owner 信息。 |
| 来源最佳被登记为新最佳 | 增加 canonical source/latest/best_new/best_overall/accepted。来源及同 SHA 的来源副本不能成为 best_new，但可以成为 best_overall 或原有 accepted fallback。 |
| timeout、成功 reset、完整窗口验收混杂 | 增加 terminated/truncated/certificate_passed/runtime_fault/task_mode；旧 handover/autonomous_hold 语义保留，显式 continuous_holding 单独表达。 |
| smoke 固定更新数不足覆盖事件 | 从待验证时长、初始化 offset、policy dt、rollout steps 计算最低更新和样本量，预算不足在 reserve 前拒绝；不自动增加预算，仍需真实事件证据。 |
| certificate 重复写入 | run_phase 为共享 chain 的唯一生成 owner；worker、preflight、ledger 只校验持久化证据。独立对照 supervisor 保留其自己的 owner，不由 reader 重写。 |
| 240秒等待误称启动失败 | 默认最多5秒读取 owned worker 的首个阶段事件；提交成功、当前阶段、formal 首更新验证分开。可选有界等待，不轮询 progress/log。 |
| 样本固定8192 | chain 和当前准备工具从冻结 ppo.envs×steps_per_env 计算；旧日期脚本不批量改写。 |
| 窗口失败只有总数 | holding episode 结束时 GPU 汇总逐 gate 失败数和关键指标，正常 timeout、证书失败、物理失败、fault 分开，update末传回摘要。 |

## 资源接口

声明示例（仅接口示例，不是对任何 GPU 的使用授权）：

```json
{
  "resources": {
    "mode": "shared",
    "sharing_authorized": true,
    "authorization_note": "用户明确允许本次任务与已核对任务共享指定 GPU"
  }
}
```

公共 supervisor 支持 `--resource-mode exclusive|shared`，以及
`--sharing-authorization <本次批准范围与理由>`。CLI 可显式补充本次授权；
shared 缺理由或批准字段直接拒绝。exclusive 对全部 compute owner 一视同仁，
包括桌面进程；shared 不自动抢占、不停止其他任务，GPU UUID、会话、来源和账本
检查仍执行。训练与 PPO0 evaluation 两条公共入口共用同一检查。

资源模式、共享理由和一次 GPU snapshot 写入 submission/manifest/握手记录。
模式允许共存，不保证显存余量、速度或物理吞吐，不等于训练预算授权。
未知 GPU 状态不因 shared 被视为可用。

## 模型角色与 episode 结果

`model_roles` 是新统一登记对象；原有字段和 `best_observed_candidate` alias
保留原分支含义，以免历史工具突然读成另一模型。新工具应明确读
`best_overall_candidate` 或 `best_new_evaluated_candidate`，而不是猜 alias。
latest 可以未评估；accepted 的原验收规则没有放宽。不同课程阶段仍分别登记。

episode flags 为证据接口，不改变 reward/GAE/reset 的判断。正常 horizon timeout
可 `truncated=true, certificate_passed=false`；窗口未通过不等于物理跌倒。
runtime fault 必须 terminated 且不能通过证书。训练随机采样结果与独立确定性
评估分别标记，不能把训练窗口计数当8/8独立验收。

continuous_holding 无 handover，跳过未参与控制的 STAND forward。新声明可以在
所有 STAND dependency 字段都缺失时省略它；声明任何一项就继续要求完整身份。
旧 spec 仍核验其原冻结 STAND。source-retention teacher 是另一依赖，保持不变。
原 FSM、奖励、物理及已声明 horizon/timeout/bootstrap 不在本轮修改范围。

逐窗口摘要包含：正常 timeout、证书通过/失败、物理终止、runtime fault、
steady样本、高度、接触、mean/peak pitch/roll、tilt、闭链、限幅及逐gate失败计数。
没有采集的 teacher comparison 标为 null/not_applicable，不能伪装真实零。

## 提交与 smoke

新字段 `submitted`、`submission_verified`、`current_stage`、
`formal_first_update_verified` 分别说明后台提交身份和训练阶段。
`SUBMITTED` 不宣称 formal 已更新；只有 trainer/monitor/attempt/spec/progress
验证成功才 `started=true`。UNKNOWN 保持 false。

`--handshake-wait-s` 可指定0–600秒，等待仅消费 owned event pipe。
当前会话结束或管道关闭不终止后台训练；事件投递失败不等于训练失败。
后台 monitor/worker 仍负责固定评估、budget、terminal和通知，禁止人工轮询长训。

`wiring_smoke` 可以声明 required_event、required_event_duration_s、event_offset_s
与minimum_event_count。holding默认依据 training_episode；没有必需事件的旧
smoke仍按原接线检查。最低更新量只是采样可达性下界，不是能力证明，不能替代
真实完成episode证据。preflight 输出 wiring_smoke_plan，证书再检查实际记录。

## 公共入口与历史工具

新提交统一 `python -m native_stand.command_v6.supervisor`，默认 plan-only。
两个 compatibility wrappers 保留但在 stderr 输出 DEPRECATED：

- `scripts/submit_motion_high_speed_formal.py`
- `scripts/continue_motion_high_speed_submission.py`

文件名不再表示另一个提交路径，也不接受旧 PID 自动续链。没有删除文件，因为
外部调用不可凭本地搜索证明不存在。`prepare_standing_yaw.py`、
`prepare_standing_long.py` 和下方日期实验索引归为历史入口；相关测试和旧文档
保留。`recovery/chain.py`、`recovery/train_stages.py`、launcher 和 monitor 不删除。

## 验证与边界

CPU命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q --tb=short
```

最终结果与精确文件 SHA 存在新本地目录
`isolated/entry_semantics_fix_20261007/verification.json`。
本轮检查结果：387项CPU测试通过，113个Python文件语法检查通过；572项历史
输入SHA核验无变化。plan-only返回BUDGET_EXHAUSTED，拒绝耗尽的旧额度，
没有创建输出目录或改写账本。该验证文件记录检查时刻身份；后续文档更新和
Git提交以对应commit tree为准，不覆盖旧验证记录。
新增fixture覆盖共享资源授权、来源/新模型角色、timeout证书分离、无teacher
forward、逐gate计数、event-sized smoke、单一owner、提交事件与formal验证。
mock subprocess 和 toy optimizer 是CPU证据，不是新 Isaac/在线 PPO。

一次只读身份核验确认现有 Recovery trainer/worker 使用自己的冻结
`runs/recovery_r0_hold10_from50_20261007/source_snapshot/`；本轮未改其文件。
没有恢复、重试、停止该任务，也没有把其历史启动事实当作当前能力。
新接口仍缺一次明确授权的新 runtime 验证，尤其资源共享与GPU采集吞吐。

本轮增量文件：AGENTS.md、README.md、STATUS.md、ARCHITECTURE.md、TOOL_INDEX.md、本文；
domain/{resource_policy,candidate_roles,episode_result,execution_plan}.py；
completion.py、config.py、launcher.py、supervisor.py、stand_chain.py、wiring.py、train.py；
tools/{health_check,preflight}.py；recovery/{preflight,recipe,runtime,holding,validation}.py；
scripts/{prepare_recovery_hold,prepare_motion_course_plan,submit_motion_high_speed_formal,
continue_motion_high_speed_submission}.py；
tests/{test_resource_candidate_interfaces,test_chain_interfaces,test_episode_semantics_interface,
test_recovery_holding,test_stand_chain}.py。工作树中其它先前修改保留，不归入本轮。
