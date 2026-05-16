# Catia_AutoBlade

CATIA 桨叶自动化建模工具。通过读取翼型数据 CSV 和截面参数 CSV，在 CATIA 中自动创建三维桨叶模型。

## 功能特性

- 读取翼型点云数据（CSV 格式）并生成样条曲线
- 支持桨叶截面参数配置（缩放、位移、旋转）
- 支持尖后缘翼型和钝后缘翼型
- 批量创建多个桨叶模型
- 基于 pywin32 与 CATIA COM 接口通信

## 项目结构

```
Catia_AutoBlade/
├── input/
│   ├── airfoils/                 # 翼型数据 CSV
│   └── section_params/           # 截面参数 CSV
├── src/catia_autoblade/
│   ├── cli.py                    # CLI 入口（typer）
│   ├── core/                     # 核心建模逻辑
│   │   ├── create_blade.py       # 单叶片创建
│   │   └── batch.py              # 批量创建
│   ├── commands/                 # CLI 命令实现
│   ├── interactive/              # 交互式提示
│   ├── utils/                    # 工具函数
│   └── config/                   # 配置管理
├── output/                       # 生成的文件输出目录
├── pyproject.toml
└── README.md
```

## 安装

### 环境要求

- Windows 系统
- Python >= 3.14
- CATIA v5（本人环境为 CATIA P3 V5-6R2020）

### 使用 uv 安装

推荐使用 [uv](https://docs.astral.sh/uv/) 管理 Python 环境和依赖。

```bash
# 1. 克隆仓库
git clone https://github.com/Laxpud/catia-autoblade.git
cd catia-autoblade

# 2. 创建虚拟环境并安装依赖
uv sync

# 3. 以可编辑模式安装项目（使 CLI 命令可用）
uv pip install -e .
```

安装后可用的 CLI 命令：

| 命令 | 说明 |
|------|------|
| `autoblade` | 主入口，包含所有子命令 |
| `autoblade-create` | 快捷方式：创建单个桨叶 |
| `autoblade-batch` | 快捷方式：批量创建桨叶 |

## 使用方法

### 列出可用文件

```bash
autoblade batch --list
```

### 创建单个桨叶

```bash
# 指定翼型和截面参数
autoblade create --airfoil sc1095.csv --section section_params-1.csv

# 指定输出目录
autoblade create --airfoil sc1095.csv --section section_params-1.csv --output ./output

# 交互模式（手动选择文件）
autoblade create --interactive
```

### 批量创建

```bash
# 列出所有可用的翼型和截面参数文件
autoblade batch --list

# 批量创建所有组合的桨叶
autoblade batch

# 指定某个翼型，使用所有截面参数
autoblade batch --airfoil sc1095.csv

# 指定翼型和截面参数
autoblade batch --airfoil sc1095.csv --section section_params-1.csv

# 交互模式（手动选择翼型和截面）
autoblade batch --interactive

# 指定输出目录
autoblade batch --airfoil sc1095.csv --output ./output
```

### 配置管理

```bash
# 查看当前配置
autoblade config show

# 设置配置项
autoblade config set --key <key> --value <value>

# 重置为默认值
autoblade config reset
```

### 输入文件格式

要求：
- 翼型前缘点为原点，弦长为 1，并置于 Y-Z 平面上
- 翼型点云顺序从后缘（上端）开始，沿着上表面经过前缘，再沿着下表面返回后缘（下端）
- 生成的 3d 模型以 x 轴作为基准 1/4 弦线，x 轴指向翼尖，翼型前缘指向 y 轴正向

**翼型数据 CSV** (`input/airfoils/`):

```csv
x,y,z
0,1,0.00173
0,0.99628,0.00202
...
```

**截面参数 CSV** (`input/section_params/`):

```csv
idx,scale/mm,translate_x/mm,translate_y/mm,translate_z/mm,rotate/deg
1,70.94,160.0,0.0,0.0,15.0
2,80.28,200.0,0.0,0.0,13.9
...
```

## License

MIT
