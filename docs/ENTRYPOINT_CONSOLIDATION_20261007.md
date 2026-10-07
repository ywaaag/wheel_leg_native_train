# 公开入口与历史工具收敛

本轮只整理入口、文档和防误用接口，不修改reward、课程、PPO、物理或历史证据。
没有启动AppLauncher、Isaac、在线PPO或续训；没有执行任何准备器生成spec/ledger。

## 已确认问题与修复

- 旧run_motion_high_speed_preparation.py固定GPU1、旧spec/run、会话与smoke10，
  会写旧账本且直接调用run_phase。当前CLI在读取证据前拒绝，退出码2，
  即使传历史复现确认也不允许启动；旧实现可从Git和冻结snapshot追溯。
- 三旧Motion声明准备器默认拒绝零参数执行，要求显式--historical-replay。
  该参数仅确认历史工具用途，不是当前运行授权。
- prepare_motion_high_speed_course.py原来在检查ledger前写spec，有覆盖旧spec
  的风险。现在先拒绝已存在的整个目标目录，再读取来源；不改其历史配方公式。
- TOOL_INDEX首页原来夹杂多个历史current入口与授权文本。完整旧清单原文移至
  根TOOL_INDEX_HISTORY.md，保持根目录相对路径语义；首页仅展示当前入口和决策。
- Motion报告早期new250推荐加明确更正：最终同协议复核推荐B250。

## 接口与兼容性

只读catalog：python -m native_stand.command_v6.tools.entrypoints。
加--include-historical列出CURRENT/INTERNAL/DEPRECATED/HISTORICAL/RETIRED。
新提交唯一公开入口是supervisor；launcher、monitor、stand_chain保留内部职责。
tools/completion.py是CLI，completion.py是实现，均保留。A/B流程和日期工具不删除。

两个已弃用高速wrapper继续转发supervisor，保护未知外部调用兼容性。
旧runtime CLI不再兼容执行；三个旧准备器需要新增显式确认。这是有意的防误用
行为变更，不适用于旧run中的冻结副本。新准备、提交应使用当前明确spec和授权。

prepare_motion_course_plan.py会生成特定halfstep课程并修改课程/宽度字段，
不是仅复制身份的通用工具；Recovery和recheck准备器也各有冻结实验逻辑。
catalog明确标为历史配方工具，未引入新的包装器或泛化配方生成算法。

## 验证

CPU fixture核验catalog路径唯一且存在、仅supervisor公开提交、历史确认、
旧runtime不可启动、拒绝前零文件访问，以及已有spec不覆盖。
全量CPU回归命令见AGENTS；本轮399项通过（17.10秒），其中新增12项入口fixture。
只读catalog CLI已实际运行，输出零simulation/PPO/files_written。未进行物理验证。
6个新增/修改Python文件AST语法检查通过。prepared v4的supervisor plan-only返回
READY_NEEDS_AUTH/AUTHORIZATION_MISSING，output未创建，输入spec和ledger的
SHA检查前后一致。该plan只是只读工程验证，不是提交或追加预算。

仍未处理的独立工作：跨trainer/evaluator冻结一次effective配置、通用报告
吸收一次性Motion报告功能、执行依赖SHA与全项目SHA分层。这些本轮只核查到
反馈与现有实现，未宣称已修；需要按真实依赖做后续小范围变更，不能把入口
整理说成这些架构问题已经消失。未删除历史run、snapshot、checkpoint或ledger。

改动文件：AGENTS.md、README.md、STATUS.md、ARCHITECTURE.md、TOOL_INDEX.md、
TOOL_INDEX_HISTORY.md、本文、MOTION_ENGINEERING_RECHECK_20261007.md；
tools/entrypoints.py、tests/test_entrypoint_catalog.py；
scripts/run_motion_high_speed_preparation.py、prepare_motion_high_speed_course.py、
prepare_motion_overnight_20261005.py、prepare_motion_endpoint_20261005.py。
