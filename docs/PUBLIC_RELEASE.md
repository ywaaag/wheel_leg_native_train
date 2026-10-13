# GitHub 发布说明

## 仓库内容与边界

发布项目源码、CPU测试、工具、接口协议、现有实验说明与历史配置。
训练模型、USD/mesh资产、运行账本、原始轨迹、CPU冻结副本和授权回执保留本地。
不删除本地证据，不批量替换历史 SHA、绝对路径或历史结论。

当前项目有三种显式策略接口：legacy150D、multiskill_student_v1、multiskill_mcu_v2。
它们共享 native 6D 实体关节/Plane/1–5–10ms/腿40Nm轮5.5Nm边界，但策略输入并不通用。
CPU契约通过、脚本能执行、流程COMPLETED与物理能力accepted分别报告。

## 依赖与外部输入

Python 3.12；项目实测依赖为 Torch 2.10.0+cu128、RSL-RL 5.0.1、TensorDict 0.14.0、
Isaac Lab 6.1.14、Isaac Sim 6.0.1.0、Gymnasium 1.2.1、NumPy 2.5.2。
这些是现场环境记录，不是所有硬件/版本兼容承诺。
CPU依赖列表在根 requirements-cpu.txt；Torch CPU构建可用于纯域及tensor fixture测试。

真实运行依赖外部 `agent_world.assets.rmuc_wheel_leg` 模块、闭链USD、来源checkpoint和冻结配置。
机器人资产、参考仓库和 checkpoint 未随仓库提供。配置中的本机路径需要在新声明中明确提供；
先检查身份/资源和零写plan，再按权限运行。Isaac runtime导入必须位于AppLauncher之后。
人工工作台的本地编辑引擎与模型目录也未发布；其包装器不能冒充完整可运行资产包。

## 许可证

按仓库拥有者本轮选择，暂不添加 LICENSE。
公开可见不等于已授予第三方开源使用/修改/分发许可；正式开源前应确定项目许可证。
依赖、第三方代码和资产遵守各自许可，项目文档不授予它们的再分发权。
用户保存的第三方长篇摘录《开源文档.md》仅留本地，不加入这次提交。

## 验证范围

GitHub CPU工作流仅执行显式 PORTABLE tests，不加载Isaac或训练资产，不查询后台任务。
PROJECT_DATA/未分类测试可能依赖本机历史证据；不能为了公开CI通过而降低其SHA检查。
已有 Motion 历史证书冲突单独报告，CPU回归不覆盖真实GPU行为。

## 历史与安全

本轮不改写Git历史、不更换remote、不自动push。既有历史提交可能已包含本机身份和路径；
发布前可用 `git log` 和 `git ls-files`复核历史。未来若发现真实凭据，须撤销凭据后另行处理历史，
不通过普通删除提交假装从Git历史移除。

## 本次公开提交验证（2026-10-13）

从Git暂存区导出干净源码副本（没有runs/artifacts/isolated/资产及模型），同一便携入口结果为
269 passed、8 skipped、4 warnings / 9.22秒。skip是原测试已有的可选/证据条件，不修改断言。
该验证使用本机已安装的依赖；新加GitHub workflow尚未在GitHub runner执行，不能称远程CI已通过。
对当前拟提交文件检查常见token/private-key/Bearer凭据格式，未发现匹配；单文件没有超过5MiB，
没有模型/USD/数值轨迹等二进制候选。此检查不代表完整Git历史审计或所有格式的凭据检测。
既有本机路径和SHA作为历史身份保留；未篡改旧运行证据，也未运行任何仿真/训练。
