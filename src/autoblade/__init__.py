from ._distribution import ensure_no_legacy_distribution
from .core.create_blade import create_single_blade
from .core.batch import batch_create_blades
from .utils.file_scanner import get_available_files


__version__ = "0.2.0"

# 新旧 distribution 共存时，两套相同 console entry 会由安装顺序决定，无法安全
# 判断用户实际启动了哪一份代码。因此包初始化返回前必须拒绝这种环境。
ensure_no_legacy_distribution()

__all__ = ["create_single_blade", "batch_create_blades", "get_available_files"]
