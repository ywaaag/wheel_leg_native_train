# B250 姿态实验存储修复后准备

本轮授权为准备、CPU检查及来源复用核验；运行需要新的明确授权。没有启动Isaac、PPO、通知或续训，未创建run或预留attempt。

## 新声明

配置目录：`configs/experiments/2026_10_8-22_51__motion_b250_posture_storage_retry/`。命名为实际准备时间，不因跨日继续验证而重命名。

来源：`runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt`；SHA256 `5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e`。

新spec SHA256：`8f6f5fb63fad3140638d07887e16b18e0edcc223da51f3167dc487b18b1dfc5d`。授权状态UNAUTHORIZED；独立budget.json使用量为0，历史终态/账本路径与SHA明确保存。来源actor/critic严格加载、17项Adam状态、实际LR3e-5及CPU/CUDA RNG字段核验通过。

保持前次冻结reward、姿态成本、采样课程、时相、网络、PPO、动作、物理及评估配置完全一致。姿态有界成本权重-.5，轮心错位/腿长差/roll死区分别.02m/.005m/.02rad，误差平方分母分别.01m²/.01m²/.04rad²。运动保护0、±.5、±1、±1.5、±2，不解锁更高速度。

## 累计预算

原上限10800秒，两个历史链已消耗3806.672207秒，剩6993.327793秒。
smoke最多1次、formal最多50次，共最多417792训练样本。来源2500秒、smoke300秒、formal4013.327793秒、尾部180秒；链整体先到即停。实际评估耗时较高，不能保证在剩余墙钟内完成50次及两轮验收；不得因未完成而追加预算。

## 存储与复用

已核验现有storage_budget在preflight和reserve接入，summary压缩在trainer/chain/completion接入，原始几何诊断仍保存。准备快照可用约24.7GiB；source/smoke/formal各阶段容量要求约1.458/1.464/3.191GiB，均PASS，包括原子临时峰值和512MiB终态余量。容量不是锁，其他任务可继续消耗。

前一次v2来源九命令raw完整，但source_evidence严格检查CONFLICTING。有效配方差异仅为`motion_posture.chain_wall_s`预算元数据，执行代码整体SHA也变更（包括metrics修复、存储/摘要接线及无关Recovery模块）。当前证书不支持审核后代码等价迁移，不能宣称REUSABLE。本spec不填写source_evidence_reference，默认重新来源评估且计入剩余预算；不使用最新失败重试的半写-2。若希望省掉来源采集，必须先完成独立、严格的执行依赖等价核验工具，不在本轮绕过身份门槛。

## 验证和改动

证据：`artifacts/motion_posture_storage_preparation_20261008/`中preparation.json、source_reuse_check.json、plan_only.json、cpu_tests.txt。plan对三阶段未创建run、未修改配置文件或ledger；source READY_NEEDS_AUTH，其余阶段缺授权及真实前置证书，符合顺序执行语义。

本轮修正两个测试文件的历史数据依赖：`tests/test_motion_absolute_recheck.py`在临时目录使用保留B250构造batch请求；`tests/test_motion_cohort_width_ab.py`使用保留的历史配置声明。没有恢复已删除run、跳过测试、修改历史spec或放宽评分。

命令：`PYTHONPATH=src /home/kellen/anaconda3/envs/issaclab/bin/python -m pytest -q`。专项37项及存储/姿态13项通过；全量642 passed（25.77秒），结果见cpu_tests.txt。相关文件py_compile与本轮测试diff检查通过。

后续只能在明确授权后用公共supervisor提交，GPU1当时资源和当前负责人session需再次核验。只做一次有界握手，后台负责25/50评估与结算；未知握手不称训练已启动。

## 用户授权后的提交

2026-10-09用户明确同意并授权，使用register_authorization登记后spec SHA为`1951dc1e27a3c11498bdd0542d338df56308564c345784b41906c0f1862b2d0d`；原准备SHA仍代表授权前声明。GPU1一次快照无compute进程，check-submission READY/submit_ready=true，未抢占或切GPU0。

公共supervisor --launch --handshake-wait-s 5提交成功，worker931944、chain attempt `c18f058434b94ec39efb6e36aa828796`，CUDA_VISIBLE_DEVICES=1，逻辑cuda:0。一次握手核验argv/start/output/spec/attempt/session/GPU通过，SOURCE_EVAL，formal_first_update_verified=false；不宣称正式PPO已开始或姿态改善。后台负责后续source/smoke/formal/25与50评估及累计预算结算。

run：`runs/2026_10_8-22_51__motion_b250_posture_storage_retry/`；日志`chain.log`，阶段日志为source_eval.log/smoke.log/formal.log，状态`chain_progress.json`，终态`chain_terminal_report.json`和`completion_report.md`。授权/提交证据见artifacts目录的authorization_request.json、submission_preflight.json、launch_receipt.json。通知负责人为当前HAPI session `191bacc3-e5c7-4b8f-ae3d-5677eada837b`。本次提交后结束交互，不查询进度或追加尝试。
