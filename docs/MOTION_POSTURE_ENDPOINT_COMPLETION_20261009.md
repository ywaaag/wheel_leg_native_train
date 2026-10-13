# 姿态formal更正报告与update50端点PPO0补评

用户明确同意下一步：修收尾、保留历史、新GPU1 PPO0补评，不续训。

## 收尾修复

completion.finalize_report的历史来源迁移原先调用新运行validate，绑定当前共享src，结束后无关/工程修改会使报告失败且notify未执行。本轮增加historical_report_certificate：核验原证书SHA、冻结spec、运行manifest执行依赖、PPO/软件依赖、已归档文件字节及非源码证据；源码输入以原运行modules记录绑定，未归档模块仅是manifest追溯，不宣称完整字节快照。新运行validate仍严格核验当前代码，不能用报告接口获得执行许可。

新增tools.completion --corrected-output，要求全新且位于原run之外，禁止与通知/ack合用。生成的更正分析、候选选择、报告和report_ready均写独立目录。旧completion_error、run及账本不改。

已生成`isolated/2026_10_9-12_08__motion_posture_corrected_completion/`，未补发通知。原formal50验收不完整、accepted为空结论不变。

改动：command_v6/completion.py、tools/completion.py、tools/motion_recovery_certificate.py、tests/test_motion_historical_completion.py、tests/test_motion_engineering_recovery_certificate.py（历史报告专项）、TOOL_INDEX及本文/STATUS。38项报告回归通过；18项接口/窗口/分布专项通过，py_compile/diff检查通过。

旧工程恢复PROJECT_DATA测试22项setup错误：当前其他worker的learning.py和learning_distribution.py新增分布分支使原等价审核拒绝。未放宽审核或重新发原运行证书。此诊断未设置action_distribution，固定CPU输入对比原归档learning构造和当前构造，update50 actor最大输出差0，证据actor_compatibility.json；不证明全状态/动力学等价。

## 独立物理补评

新配置`configs/experiments/2026_10_9-12_08__motion_posture_update50_endpoints_ppo0/`。来源仍保留B250声明，只评估formal/model_update_50.pt，SHA `cee3a4315c3de66527d56f5170bc7da7723ec13014b869778f020949d336ae41`。两请求+2/-2，各8scored环境、seed104、完整30秒原motion_absolute_v3协议及[10,18]保持/原回零窗口，新诊断声明移除训练工程恢复许可；不转移旧运行授权。

物理GPU1独占，公共supervisor evaluation-only --launch --wait；exact attempt `aba886431d384d5b9b2c23c8a48d4929`，monitor1076430。新预算900秒，原累计余1011.825084秒，不做online/offline optimizer更新，不追加训练额度。已有process wait是用户授权前台有界诊断等待，不读取日志/进度守候长训。

证据索引：`artifacts/motion_posture_endpoint_completion_20261009/`的plan、declaration、submission_check、测试文本和后续终态复盘。raw及monitor日志在新run/相邻monitor.log。终态结果在验证结束后追加，不把提交通知当通过。

## 终态与实际结果

COMPLETED，exact attempt已结算，online/offline optimizer更新0。实际426.311984秒，原累计10214.486900秒，剩585.513100秒（9.76分钟），更新预算已用完，不续训/自动加额。

| command | 完整环境 | mean vx | MAE均值/最差环境 | 接触 | 轮心错位 | 腿长差 | abs roll |
|---|---|---:|---:|---:|---:|---:|---:|
| +2 | 8/8，30秒 | 2.28961 | .29046/.29085 | 1 | 8.286cm | 13.003cm | .28069rad |
| -2 | 8/8，30秒 | -2.06432 | .08197/.08385 | 1 | 11.664cm | 8.130cm | .17325rad |

高度均值.37106/.38258m，峰tilt均值.30364/.17830rad，closure最大量级3.57e-5/2.94e-5m，100Hz末端限矩饱和比例.000333，无runtime fault；所有逐gate通过。结果针对单评估seed104，不能称多训练seed。

按同一update50七项原raw与本次两项补测汇总，仅作诊断比较：九命令姿态cost .228566 vs B250 .286189，下降20.1347%；三bounded component宏均值均降低。+2轮心错位比来源7.41cm恶化至8.29cm；-2 roll由.16795略升至.17325，几何改善非处处一致。原update25 +2失败且姿态总改善11.54%，因此不存在两次完整通过，不授予accepted。

此补测代码版本与原formal评估不同，协议/seed/checkpoint绑定相同、固定CPU构造输出一致，但完整依赖等价认证未补齐；不拼接为严格全能力证书、不修改原registry。新完整端点证据和逐环境结果见result_review.json。当前结论是update50有局部姿态改善、端点补测通过，但未通过原重复验收。

本轮未重发终态通知。更正report_ready只存在独立报告目录，原run的completion_error和缺报告状态保留。下一步仅建议先用update50进行明确授权的GUI/独立sim2sim姿态对比，保留B250回退；不能宣称新模型已正式接受或恢复高速训练。额外物理验证应明确预算，当前原余额仅9.76分钟。
