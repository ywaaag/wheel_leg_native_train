# 当前工程状态与交接入口

更新日期：2026-10-07。本页汇总当前共享源码的工程能力，不替代run的
manifest、冻结源码、原始评估、terminal或ledger，也不判断进程当前是否存活。

## 当前公共入口

- 新提交：`native_stand.command_v6.supervisor`，默认零写入plan-only。
- 只读核查：health_check、preflight、entrypoints。
- 离线证据：correct_evidence、audit_recovery_survival.py。
- 受限工程恢复：engineering_recovery，默认零写入；显式发布仍UNAUTHORIZED。
- 终态报告/通知：tools.completion；notify-only只消费已有就绪报告。

精确CLI和历史工具分类见[TOOL_INDEX](../TOOL_INDEX.md)。launcher、monitor、
stand_chain保留内部职责；已退役watch不替代后台owner。

## 已实现与验证范围

| 工程项 | 当前状态 | 限制 |
| --- | --- | --- |
| shared/exclusive资源与模型角色 | CPU验证；来源与best_new分开 | 不自动授权共享，不以PID猜测任务 |
| RunState | 共享标准chain统一记录，握手为证据投影 | 独立旧A/B及历史链不追溯迁移 |
| Motion/Recovery请求schema | 独立validator，拒绝跨task字段 | 标准Recovery batch仍固定10秒；rising按显式独立协议路径 |
| 冻结源码重定位 | 声明根/实际根分开，receipt/逐文件SHA严格核验 | 真实冻结preflight为CPU证据，无新GPU执行认证 |
| EpisodeSummary | 版本1，兼容completed/旧alias，冲突拒绝 | 不重写历史metrics |
| per-family/pose smoke | GPU张量汇总，声明组分别核验 | 新真实runtime覆盖与吞吐尚未验证 |
| holding/rising | 明确任务身份与窗口对齐，legacy adapter保留行为 | standing_task共享字段尚未彻底拆除 |
| 受限证书恢复 | 指定completed reader错误白名单、SHA计划、exact-ID去重 | 仅发布未授权新配置；非通用预算转移或自动恢复 |
| 后台通知 | 现有owner终态hook、报告SHA、事件去重与当前session校验 | 本轮mock验证，未实际发送HAPI通知 |
| 报告 | Markdown压缩数组，链接原始证据 | JSON/原始轨迹不删减，旧报告不覆盖 |
| 新实验命名 | 集中Asia/Shanghai日期时间前缀 | 旧/已冻结实验不重命名 |

## 最近验证

最近全量CPU：435 passed（18.61秒），127个Python文件AST语法通过。
后续冻结schema记录的针对性回归：43 passed（2.18秒）。
一次历史起身smoke只读恢复plan绑定15项输入，source_eval1/smoke10/formal0
及原limits保留，未创建目标目录或publication receipt；检查输入SHA未变化。
Git提交前的再次验证另记于提交说明，不覆盖上述历史检查。

没有启动Isaac/AppLauncher、PPO、续训或新预算；没有修改活动run冻结副本。
CPU/mock成功不能证明运动、起身或高速度能力改善。

## 任务事实的阅读边界

Motion当前推荐来源为B250，依据[最终同协议复核](MOTION_ENGINEERING_RECHECK_20261007.md)。
Recovery coverage A/B已完成，起身链的准确运行状态读
[起身实施记录](RECOVERY_RISE_LOW_20261007.md)及其run终态。
STATUS中的PID、RUNNING和首更新是对应握手时刻事实，不作为现在存活证明。
本次文档整理没有轮询任务，不更新或推断其最新训练结果。

## 下一步工程优先项

1. 在另有授权的新运行中验证per-pose摘要、分组smoke与通知投递；仅一次握手。
2. 准备器的共享身份/exclusive-create/账本事务封装，防止中途留下可误用配置。
3. 逐步拆除holding/rising的legacy字段，先有兼容证据再退役旧接口。

不扩大工程恢复白名单，不因旧额度或终态通知自动续训。长训detached后结束交互，
后台owner负责终态通知；Codex禁止亲自周期性查日志、进程或GPU。

详细交付：[状态接口](STATE_REQUEST_FIX_20261007.md)、
[episode/身份/恢复](EPISODE_IDENTITY_RECOVERY_FIX_20261007.md)、
[后台唤醒规则](DETACHED_TRAINING_POLICY.md)、[命名](EXPERIMENT_NAMING.md)、
[Git边界](GIT_WORKFLOW.md)。
