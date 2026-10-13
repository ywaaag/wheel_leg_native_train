# Recovery历史运行数据清理

用户明确授权仅清理不再使用Recovery记录；按当前任务、来源/资产/pose/STAND依赖闭包及一次进程路径清点，保留本日各Recovery块和完整祖先，被Motion引用路径同时保护。

删除37个Recovery历史run目录，文件合计15.18GiB；删除后根分区可用24.78GiB（并发其他任务写盘，free差值不视为独立精确释放量）。

删除清单与逐文件尺寸：isolated/recovery_storage_cleanup_20261008/plan.json；执行回执execution.json，保留验证verification.json，小型身份/终态归档metadata/。配置和ledger、代码、assets、Motion未删除，未停止进程或运行仿真。来源B25和Motion B250 checkpoint SHA实际核验通过。

旧文档中指向删除run的链接现为历史索引：raw/checkpoint已经不可用，不冒称原始结果仍可复核。终态小文件归档仅保留身份/消耗，不替代大轨迹证据。

## 删除目录

- 2026_10_7-15_46__recovery_rise_source_locator（0.009GiB）
- 2026_10_7-15_51__recovery_rise_low_from50（0.001GiB）
- 2026_10_7-15_58__recovery_rise_low_from50（2.106GiB）
- 2026_10_7-16_18__recovery_rise_formal_from50（0.333GiB）
- 2026_10_7-17_21__recovery_level2_drawback_from1000（3.323GiB）
- 2026_10_7-20_17__recovery_update50_geometry_ppo0（0.066GiB）
- 2026_10_7-20_42__recovery_level2_alignment_from50（0.002GiB）
- 2026_10_7-20_55__recovery_level2_alignment_from50（5.386GiB）
- 2026_10_7-22_10__recovery_min_height_p1_from_s50（0.002GiB）
- 2026_10_7-23_04__recovery_min_height_p1_resetfix_from_s50（1.955GiB）
- recovery_capture_20261003_220525（0.000GiB）
- recovery_capture_20261003_223302（0.000GiB）
- recovery_capture_20261003_224152（0.000GiB）
- recovery_capture_20261003_233646（0.000GiB）
- recovery_capture_max_extension_20261003_234541（0.000GiB）
- recovery_capture_probe_20261003（0.000GiB）
- recovery_checkpoint_review_20261005（0.000GiB）
- recovery_checkpoint_sweep_20261004（0.247GiB）
- recovery_coverage_ab_20261007（0.865GiB）
- recovery_dense_corrected_initial_20261004（0.001GiB）
- recovery_dense_curriculum_20261004_chain（0.000GiB）
- recovery_dense_curriculum_20261004_chain_retry1（0.002GiB）
- recovery_dense_curriculum_20261004_formal_direct（0.007GiB）
- recovery_diagnostic433_20261002（0.035GiB）
- recovery_eval_update900_20261005_170935（0.010GiB）
- recovery_knee_stop_pitch_20261004_chain（0.000GiB）
- recovery_knee_stop_pitch_20261004_initial（0.000GiB）
- recovery_pose_capture_20261002_170621（0.000GiB）
- recovery_r0_hold10_from50_20261007（0.272GiB）
- recovery_settle_from433_chain_20261002（0.000GiB）
- recovery_settle_from433_chain_20261002b（0.019GiB）
- recovery_settle_from433_retry2_chain_20261002（0.000GiB）
- recovery_standing_balance_20261006_chain_1140（0.080GiB）
- recovery_standing_yaw_20261006（0.046GiB）
- recovery_static_pose_20261003_224308（0.000GiB）
- recovery_survival_level_from50_20261006（0.316GiB）
- recovery_symmetry_from1500_20261006（0.098GiB）
