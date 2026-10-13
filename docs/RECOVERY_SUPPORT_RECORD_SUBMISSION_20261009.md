# Recovery支撑纪录单变量短训：提交交付

2026-10-09用户明确“授权下一步”。通过现有supervisor提交，唯一问题是平滑支撑纪录奖励能否促进合法Swing恢复，同时保住DrawBack/R0。

## 声明与预算

spec：`configs/experiments/2026_10_9-08_59__recovery_swing_support_record_from_b25/spec.json`；独立budget、approval_request、authorization_receipt、preparation_manifest、poses及publication_complete同目录。新run：`runs/2026_10_9-08_59__recovery_swing_support_record_from_b25`。

来源认证RecoveryB25：`runs/2026_10_8-10_48__recovery_p2_wheel_std_ab_from_new50/B/formal/model_update_25.pt`，SHA `8c3f74f98c0605fad084f6e1fa547bf305bc1a4aa162025767d485b0efbcfd44`。smoke/formal各自严格继承该来源actor/critic及Adam，来源std不再乘旧B系数；不从aux退化分支或smoke末尾接棒。

单变量：Swing受控pre_entry的support_record_reward_v1，beta=.3、short=.15m、width=.225m；exactprecontrolbaseline，失败当步0、无dt/heightgate/terminal释放。关闭meanaux及std初始化干预，保留新USD、150D、6D控制、原reward、DrawBack/R0和v2完整10秒协议。固定64env槽位26/25/13，原始姿态只调整采样权重。

独立来源评估≤900秒、smoke10≤900秒、formal≤25≤3600秒；更新合计≤35、样本≤286720，整链≤5460秒含60秒收尾余量。更新10/25完整三组评估，来源/早期/末尾候选保留。旧两组连续完整失败由既有StandingRegression保护；缺字段不能通过、不放宽Swinggate、不拼模型、不自动续训/调beta/加std制动。未进行100秒耐久。

GPU0 UUID `GPU-e704e7d4-2965-4712-9759-ba6b9910bd72` → cuda0，shared明确CLI授权；resource默认exclusive准备模板不等于实际执行资源，实际effective policy已冻结为shared。没有停止其他任务。

## 工程验证与真实握手

- 修复train.RolloutMetrics缺新增reward字段登记；公共course request支持严格版本support_record_reward，不允许同时meanaux。
- smoke除原真实episode/各family初始化事件外，必须从实际metrics.jsonl证明support_record_progress非负有限且至少一次正reward；否则wiring_certificate失败，formal阻断。前次PPO0通过不能替代本次smoke证书。
- 新PolicyReadback只消费真实ppo.act已产生的mean/std/sample，按受控Swingpre_entry报告两轮mean/std/实际sampleclip，不额外forward/采样、不改cache/RNG/optimizer；full geometry原raw评估继续保留。
- 全CPU660 passed；最终冻结PORTABLE13 passed，schema/plan/来源完整初始化通过。CPU产物`artifacts/recovery_support_record_train_frozen_final_cpu_20261009/validation_result.json`。
- 公开supervisor零写plan PASS；一次check-submission READY、current session/UUID/新output/账本/容量核验；提交时重复核验资源。
- 一次5秒握手：submitted=true、submission_verified=true，worker 952753、链attempt `d0602d233a344c389611baf9480468d4`，SOURCE_EVAL。formal_first_update_verified=false；不能称正式PPO已开始。回执`configs/experiments/2026_10_9-08_59__recovery_swing_support_record_from_b25/chain_submission.json`。
- 通知冻结负责人session7bbabd67-183d-4185-b686-1aefcd55781b，enabled=true；后台生成终态报告、结算并按at-most-once通知。交互不轮询、不新建watcher。

## 本轮改动

源码`src/native_stand/command_v6/domain/recovery_course.py`、`tools/prepare_recovery_course.py`、`train.py`、`wiring.py`，以及`src/native_stand/recovery/support_record_proposal.py`；新增`scripts/prepare_recovery_support_record.py`，扩展`tests/test_recovery_support_record_proposal.py`。更新STATUS、RECOVERY_STANDING_PLAN、TOOL_INDEX、ARCHITECTURE及本报告。旧run/冻结代码/checkpoint/ledger不修改；保留其他dirty changes，无commit/push。

## 终态判断

首先检查Swing的入口/完整保持是否净改善，再看两旧组完整能力；几何quality或总reward更高不独立构成接受理由。beta信号较小、双侧平均允许单侧改善、record未显式输入150D的critic别名及mean轮越界仍是公开风险。结果不好就保留B25并复盘，不能自动提高权重或延长训练。
