"""
测试配置文件
"""

import pytest
from pathlib import Path

# 测试数据目录
TEST_DATA_DIR = Path(__file__).parent / "data"
TEST_DATA_DIR.mkdir(exist_ok=True)