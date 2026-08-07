# 输入数据目录

本目录保存可以随仓库版本化、用于命令行示例或 CATIA 回归的输入数据，不保存生成结果或测试临时文件。

- `airfoils/` 保存规范化翼型点云 CSV。
- `section_params/` 保存一片叶片的展向截面定义。
- 文件名统一使用 ASCII 小写字母、数字、连字符和下划线；CSV 内的 `airfoil` 值只引用 `airfoils/` 下的精确文件名。
- 当前里程碑依赖的样例必须与实现一起纳入版本控制，避免参数文件引用仅存在于某台开发机的翼型。
- 私有、客户或大体量数据应通过 `config.toml` 把输入目录指向仓库外位置，不应放入本目录。

完整字段、单位和点序约束见 [`docs/input-formats.md`](../docs/input-formats.md)，多翼型路径和兼容策略见 [`docs/multi-airfoil-design.md`](../docs/multi-airfoil-design.md)。
