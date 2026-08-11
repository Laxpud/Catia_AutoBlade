# 技术文档索引

本目录保存实现约束、数据契约和设计说明。项目介绍与使用入口见[英文 README](../README.md)，中文入口见[中文 README](README.cn.md)，当前工作见 [TODO](../TODO.md)。

## 当前文档

- [架构说明](architecture.md)：模块边界、CATIA 建模流程、资源生命周期和当前限制。
- [设计原则](design-principles.md)：`create`、`batch`、未来 `sweep` 的职责，模型输入模式和任务边界。
- [CLI 参考](cli.md)：命令参数、交互模式、任务预览、覆盖规则、退出码和示例。
- [输入数据格式](input-formats.md)：坐标系、CSV schema、单位、点序以及多翼型扩展状态。
- [展向多翼型设计](multi-airfoil-design.md)：输入路径、文件命名、逐截面引用、兼容模式、批处理和 Loft 对齐策略。
- [运行时配置](configuration.md)：配置来源、路径解析基准、CLI 覆盖优先级和输出命名模板。
- [分发范围与支持策略](distribution-scope.md)：首个预览版本的目标用户、渠道、已验证环境、外部依赖和非目标。
- [自动化测试](testing.md)：无 CATIA 测试入口、覆盖范围、COM 隔离和真实几何回归边界。

## 内容归属

- `README.md`：公开项目入口、当前能力、环境要求和最短使用路径。
- `TODO.md`：活动里程碑、待办事项和可验证的完成标准。
- `docs/`：稳定的技术契约、设计理由和长篇实现说明。
- `docs/archive/`：已经完成或被当前架构取代的历史计划；现有记录见[截至 0.1.1 的已完成里程碑](archive/milestones-through-0.1.1.md)。

新增文档应优先补充现有主题。只有当内容具有独立维护边界时，才创建新的技术文档。
