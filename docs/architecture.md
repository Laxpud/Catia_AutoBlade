# 架构说明

## 系统边界

CATIA AutoBlade 是运行在 Windows 上的 Python CLI。Python 负责读取输入、计算截面变换和编排流程；实际几何创建、Loft、实体封闭和格式导出由 CATIA V5 COM 对象完成。

项目不包含独立几何内核。除少量坐标变换外，离开 CATIA 环境无法生成最终模型。

## 调用链

```text
Typer CLI
  -> commands：参数选择、交互提示、文件存在性检查
  -> core：CSV 解析、CATIA COM 调用、建模与导出
  -> CATIA V5：CATPart 文档、HybridShape、Loft、CloseSurface
```

主要模块职责：

- `catia_autoblade.cli`：注册 `create`、`batch`、`list` 和 `config` 子命令。
- `catia_autoblade.commands`：把 CLI 输入转换为核心函数参数，不应包含 CATIA 几何规则。
- `catia_autoblade.core.create_blade`：单叶片建模主流程和 CATIA COM 操作。
- `catia_autoblade.core.batch`：组合翼型与参数文件，逐个调用单叶片流程。
- `catia_autoblade.config`：配置模型和 TOML 持久化；目前尚未接入主要建模路径。
- `catia_autoblade.utils.file_scanner`：发现输入目录中的 CSV 文件。

## 单叶片建模流程

1. 初始化 COM，连接或启动 `CATIA.Application`，创建空 `Part` 文档。
2. 读取以 m 表示、弦长为 1 m 的基准翼型点，将弦向坐标反向并平移，使 X 轴成为 1/4 弦线。
3. 在 `airfoil` 几何集中创建点和样条；钝后缘额外增加封口直线和 Join。
4. 读取所有截面参数，对同一基准翼型依次执行绕 X 轴旋转、相对原点缩放和三维平移。
5. 从每条实际截面曲线提取前缘点，按输入端点变换生成后缘点，并用它们建立纵向导引样条。
6. 以变换后的截面为 Loft 截面，以前缘和后缘样条为导引线生成叶片曲面。
7. 使用 `CloseSurface` 将封闭曲面转换为实体。
8. 隐藏辅助几何，保存 `.CATPart`，并导出 `.stp`。
9. 退出 CATIA 并释放 COM。

## 批处理模型

批处理对选中的翼型文件和截面参数文件执行笛卡尔积。每个组合都会重新进入完整的单叶片流程，并输出到以翼型名称命名的子目录。

当前没有共享 CATIA 会话、失败重试、事务式输出或断点续跑。某一组合失败会记录失败结果，然后继续处理其他组合。

## 几何约束

- 所有输入翼型都位于 Y-Z 平面，因此输入点的 X 坐标应为 0。
- 输入及 Python 领域计算统一使用 m；基准翼型弦长为 1 m，前缘弦向坐标为 0 m，后缘弦向坐标为 1 m。
- CATIA Automation 的长度参数固定使用 mm，因此只有 COM 调用边界负责将 m 换算为 mm；界面显示单位不会改变该接口契约。
- 变换后的 X 轴是展向和旋转轴，正方向指向翼尖。
- `scale/m` 表示最终弦长；传给 CATIA 的无量纲缩放因子为 `scale/m / 1 m`。
- Loft 截面的对应点依靠前缘点定位，前缘及后缘样条用于约束展向走向。
- 前缘闭合点不能使用独立的理论坐标点。程序沿截面扭转后的弦向正方向计算曲线 `Extremum`；若 CATIA 对密集曲线返回多个非连通极值，再以理论前缘为 `Near` 选择器取得唯一曲线点。Loft 和前缘导引样条只引用这个实际曲线点。

## CATIA 特征树命名

程序创建的几何特征使用英文 `snake_case` 语义名称，避免依赖 CATIA 自动生成且会随操作顺序变化的 `Point.N`、`Translate.N` 等名称。点云点使用补零序号，例如 `airfoil_cloud_point_0001`；截面相关特征使用截面 `idx` 后缀，例如 `section_rotation_1`、`leading_edge_1` 和 `trailing_edge_1`。公共辅助特征按用途命名，例如 `section_rotation_axis`、`leading_edge_guide`、`blade_loft_surface` 和 `blade_closed_solid`。

更完整的字段与点序约束见[输入数据格式](input-formats.md)。

## 当前实现限制

- 一片叶片只能复用一个基准翼型，截面参数中的 `airfoil` 扩展列会被忽略。
- 尖后缘通过首尾坐标精确相等判断，没有浮点容差。
- CSV 解析主要依赖列位置，缺少启动 CATIA 前的完整 schema 校验。
- `config.toml` 尚未成为扫描、输出或命名逻辑的运行时来源。
- COM 清理只位于成功路径，异常可能遗留隐藏的 CATIA 进程。
- 建模核心直接依赖动态 COM 对象，尚未形成便于单元测试的适配器边界。
