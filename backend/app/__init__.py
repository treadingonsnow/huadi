# backend/app/utils/__init__.py
# 空文件，用于包导入
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[2]
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)
