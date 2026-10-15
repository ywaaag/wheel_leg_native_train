# v14评估存储修复及有界恢复

用户明确授权修复并恢复；本次承接wiring2原1000上限，已耗smoke12＋formal300＝312，新formal上限688/5636096samples，不重复smoke或warmup。旧09_37链另26次历史消耗仍保留，不混入该1000授权，也不删除旧FAILED/证书/账本。

## 确认错误和最小修复

students/training.evaluate_cases原将128MiB单评估额度当作atomic_result的phase累计cap。修改为：chain_max_bytes扣除其他phase实际占用和terminal reserve得到当前phase累计上限；另用artifact_cap_bytes限制本次NPZ＋实际JSON字节。保留4GiB全链限制、不提高原单评估128MiB。原子保存计算最终trace引用和带缩进JSON尺寸，JSON发布失败回滚新trace，已有证据不动。

## 恢复身份和限制

来源：runs/2026_10_14-10_16__standing034_survival_quality_v14_wiring2/formal/model_update_300.pt，SHA64f96ac10d5d870fe23d33018a81b558f9eeb0ebcac2496e605a60b39a17829f。
新声明：configs/experiments/2026_10_14-12_44__standing034_v14_storage_resume/spec.json，同名run及独立ledger；账本显式引用父账本SHA、已耗312与原1000。公开supervisor仍为唯一提交入口，不引入另一trainer或watcher。

受限student_v14_storage_resume_v1核验：父spec/已结算ledger/指定storage异常terminal/SHA绑定checkpoint、通过的原smoke、配方行为不变、剩余688、单父发布。通用工程恢复原只支持formal前错误，此次增量专门支持已训练v14存储故障，不使用通用任意override。

Actor、Critic49、Adam、std原样恢复，LR3e-5；CPU逐tensor核验一致、无optimizer step。update300未保存RNG，明确重新初始化seed20261010，非逐位复现；新物理环境reset、未恢复PhysX状态。后续v14checkpoint新增完整training_rng和累计recipe_updates。resume声明显式覆盖原基线recipe的新Critic/Adam初始化说明，实际初始化以resume/readback为准，不冒称新建或恢复旧RNG。

source_eval补齐update300三组各8环境同协议完整30秒证据，普通能力不通过不阻止formal；工程错误才阻止。formal新局部100/200/300/400/500/600/688评估，对应原formal400/500/600/700/800/900/988。逐update同时记录局部、父formal累计及含父smoke累计。末轮/重复通过选模协议保持，不宣称source或单次结果已accepted。

## 修改文件

- src/native_stand/recovery/handoff_evaluator.py：累计/增量上限分离及发布失败清理。
- src/native_stand/students/training.py：正确传入上限、恢复分派、RNG保存和累计计数。
- src/native_stand/students/storage_resume.py：受限证据及预算校验、真实训练状态恢复。
- src/native_stand/students/requests.py、command_v6/wiring.py：公共preflight与原smoke证据消费。
- command_v6/stand_chain.py：source→formal及累计结算报告。
- students/training_evidence.py：恢复不重复warmup的报告。
- scripts/prepare_student_storage_resume.py：新命名独立发布、单父claim，默认不运行。
- tests/test_student_storage_recovery.py：容量、清理、SHA/行为/预算拒绝回归。
- TOOL_INDEX、WORKFLOW、STATUS与本报告：当前入口/授权/运行导航。

## 验证

初次PORTABLE353pass/8skip，补充预算/身份和发布故障回归后定向22pass；最终公共validator/零写plan及实际学生恢复读回在artifacts/standing_survival_storage_resume_20261014。没有用legacy Adam参数名审计器假装兼容学生；真实学生assemble＋恢复对照Actor/Critic/optimizer完整张量，std不变、源权重不写。

运行：物理GPU0共享、CUDA0、UUID GPU-e704e7d4-2965-4712-9759-ba6b9910bd72，当前负责人191bacc3-e5c7-4b8f-ae3d-5677eada837b，自动通知沿用明确授权。只做一次有界握手，后台既有monitor管训练/评估/终态。TensorBoard只读接入6006。无自动追加/重试，不改reward/课程目标/PPO/物理，不进行Git提交。

## 实际首次提交握手

{
  "chain": "/home/kellen/wheel_leg_native_train/runs/2026_10_14-12_44__standing034_v14_storage_resume",
  "worker_pid": 278270,
  "submitted": true,
  "submission_verified": true,
  "run_state": "SOURCE_EVAL",
  "current_stage": "source_eval",
  "formal_first_update_verified": false,
  "started": false,
  "spec_sha256": "4d4493ed65eddf69292359f4dadecfaf5baccaffd2a589b057be8a2f3368cb02",
  "source_sha256": "64f96ac10d5d870fe23d33018a81b558f9eeb0ebcac2496e605a60b39a17829f",
  "parent_online_updates": 312,
  "new_formal_limit": 688,
  "original_online_limit": 1000
}

最终公共CPU30pass，schema[]，零写plan PASS、run未创建；提交READY。一次有界握手后结束交互，SOURCE_EVAL不等于formal首更新。TensorBoard6006 HTTP200，只读桥278657；当前会话通知已冻结启用。全部旧输入SHA提交后仍一致；未改旧FAILED/账本/checkpoint。
