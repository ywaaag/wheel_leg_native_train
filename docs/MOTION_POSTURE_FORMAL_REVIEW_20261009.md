# B250姿态formal结果与通知故障

集中报告及逐环境证据：`isolated/2026_10_09-12_03_09__motion_posture_terminal_review/README.md`、`comparison.json`。raw和原terminal保持不变。

formal50/409600样本，3953.345472秒，STOPPED_BOUNDED。update25九命令完整但+2误差.3413，0/8；九命令姿态成本改善11.54%，不足20%。update50七命令完整均8/8，共同七命令姿态成本改善33.30%；+2在23.97秒预算中断、-2未执行，完整保留和重复通过不成立。B250仍为回退来源，不认证new50。

通知未发送不是传输故障证据：completion_error记录当前共享config.py SHA不符合恢复证书绑定；monitor先finalize_report再notify，报告失败后没有执行notify。report_ready、completion_report均未生成。应修冻结报告身份消费，不应靠改旧证书SHA解决；本轮未重发通知或修代码。

累计消耗9788.174916秒，原3小时余1011.825084秒，smoke1/formal50更新额度均已消耗。后续仅可提议独立PPO0补齐new50±2、核对全部命令，无新PPO/升速；需明确授权且预算累计不重置。完整新候选前不接new50训练。
