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
│   ├── airfoils/              # 翼型数据 CSV
│   │   ├── sc1095.csv
│   │   ├── sc1095_sharp.csv
│   │   └── sd7032_sharp.csv
│   └── section_params/        # 截面参数 CSV
│       └── section_params-*.csv
├── src/catia_autoblade/
│   ├── __init__.py
│   ├── create_blade.py        # 单叶片创建逻辑
│   └── batch_create_blade.py  # 批量创建逻辑
├── output/                    # 生成的文件输出目录
├── pyproject.toml
└── README.md
```

## 安装依赖

使用 uv 管理依赖，推荐使用以下命令安装依赖：

```bash
uv sync
```

## 使用方法

### 单桨叶创建

```bash
catblade --airfoil sc1095.csv --section section_params-1.csv --output ./output
```

### 批量创建

```bash
# 列出所有可用的翼型和截面参数文件
catblade-batch --list

# 批量创建所有组合的桨叶
catblade-batch --output ./output

# 指定特定文件
catblade-batch --airfoil sc1095.csv --section section_params-1.csv
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

## 环境要求

- Python >= 3.10
- Windows 系统
- CATIA v5 （本人环境为 CATIA P3 V5-6R2020）
- pywin32

## License

MIT
