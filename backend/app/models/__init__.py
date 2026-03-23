# backend/app/models/__init__.py
# 按顺序导入，避免循环依赖
from .user import User
from .favorite import UserFavorite
from .restaurant import Restaurant
from .review import Review
from .clean_log import CleanLog
