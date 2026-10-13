# 通知路由、评分边界与证据生命周期修复

范围：共享下一次执行代码、CPU回归和只读历史审查。没有通知发送、仿真、
采样/PPO、重提训练、活动冻结代码迁移或旧证据改写。

## 通知为何到达这个会话

事件049380b3e0b264fdb053b97b的原始manifest、chain_submission和hapi_notification
都绑定`967b73ed-f83d-45b8-876c-ab80f515e51f`；发送记录status=sent/returncode0。
该链是此前通过显式--hapi-session提交的motion链，传输使用manifest目标，
当前环境也报告同一session。现有证据支持“提交时绑定到本会话并按该目标投递”，
没有证明HAPI随机投错。用户指出预期接收者不是本会话，但其预期session未在本条提供；
本轮不猜测、转发、删除原投递记录或重新发送。

下一次manifest增加notification_route，记录owner/target及显式参数来源；
notify核对冻结spec授权目标、manifest路由及链submission回执。
任一冲突记录notification_route_conflict并拒绝发送，保持at-most-once。
这能防记录错配，不能自动判断“当初显式选错会话”的人类意图；新提交应核对
接收者session。当前默认仍为执行worker会话，不根据终态读取者重定向通知。

## 已完成的修复

1. domain.evaluation_config把scoring、schedule、storage字段分开，未知字段仍拒绝。
   train source/额外source端点/milestone/final的standing_protocol调用都走scoring_configuration。
   evaluator入口也适配旧整evaluation对象。full_trace_updates不再混入本次新构建评分协议，
   历史PROTOCOL_FIELDS白名单保留兼容，旧评分/结果SHA不重写。
2. RiseHold/PhaseCoverage持久状态即使在inference_mode中创建，也分配普通可变tensor；
   重置、第二个rollout及普通训练生命周期CPU fixture通过。
3. min_height完整保持样本与终态成功分别检查：1000样本已完整时continuous为真，
   task失败由contact/姿态/terminal_certificate等具体项表达。
   evaluator标注hold_window_complete/hold_certificate_passed，完整失败终态为
   hold_certificate_failed，保留runtime fault和真实提前安全终止语义。
4. tools.evaluation_loader集中从registry引用读取raw JSON，核对manifest/spec/model/asset/SHA，
   拒绝越界路径和缺诊断字段。recovery_progress_baseline复用它；压缩registry仍只作摘要。
5. completion保留原认证排序，增加diagnostic_comparison并列contact、posture、hold-prefix
   最佳及数值，明确不是accepted或拼接能力。
6. min-height prepare/review同步登记tools.entrypoints，继续保留历史guard与内部执行组件。
7. tools.prepare_recovery_retry默认零写，显式失败run/ledger/session/新目录，核验FAILED或
   TERMINATED exact attempt、实际更新一致、冻结spec/source/asset/library SHA。
   --write复用experiment_preparation发布UNAUTHORIZED、零使用、零phase额度声明，
   记录历史实际消耗和差异，不转移余额、不自动重试、不自动修配方。

## 尚未完整实现的反馈项

|项|当前状态|
|---|---|
|评分/调度/保存分层|本轮调用边界已分开；完整统一保存计划仍待收敛profile和legacy flags|
|实际source/smoke/milestone/final参数测试|当前真实调用点AST检查＋evaluator fake/边界回归；不等于物理调用验证|
|公共时间轴|几何脚本已有index/recovery clock说明，仍未共用全仓库转换模块|
|reserved/actual/settled|现有ledger实际charge与progress/terminal分开；尚无统一三字段摘要|
|准备器复用|Motion通用准备器已完成；Recovery本轮新增有限失败重试器，专用配方工具尚未全部迁移|
|effective legacy披露|Motion已有；Recovery旧FSM/高度兼容字段完整参与清单仍待整理|
|冻结CPU验证工具/通用事件审计|已有组件分散，本轮没有再构造一个重复监督或审计框架|
|文档当前/历史|根导航添加本轮索引；其他任务历史章节保留，不顺手改其任务语义|

11.5s训练episode覆盖与R0来源0/8属于训练设计/证据问题，本轮不改reward、
episode、rehearsal或gate，也不把R0 rehearsal叫作已认证旧能力保护。

## 验证

全量CPU：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q --tb=short`
结果522 passed in21.25s。通知使用fake transport，冲突零调用且重复不发送；
真实历史23_04失败smoke的retry plan files_written0、旧ledger字节不变、新目录不存在。
测试覆盖raw保存→registry删控制摘要→身份loader→ProgressGuard，以及完整失败1000窗口。
真实运行尚未验证本轮新代码；活动任务仍使用其冻结副本，不宣称行为改善。

## 文件与入口

新增domain/evaluation_config.py、tools/evaluation_loader.py、tools/prepare_recovery_retry.py、
tests/test_notification_evidence_lifecycle.py及本文。
修改command_v6 train/completion/stand_chain、tools/evaluate_checkpoint/recovery_progress_baseline/entrypoints；
recovery min_height/recipe；tests/test_recovery_progress_baseline与根导航。
既有工作树修复保持，不清理无关dirty文件。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
/home/kellen/anaconda3/envs/issaclab/bin/python -m native_stand.command_v6.tools.prepare_recovery_retry \
 --run "$FAILED_RUN" --ledger "$OLD_LEDGER" --output-dir "$NEW_CONFIG_DIR" \
 --hapi-session "$HAPI_SESSION_ID"
```

默认只输出计划，--write发布未授权零额度准备；授权登记和真实提交仍走supervisor。
