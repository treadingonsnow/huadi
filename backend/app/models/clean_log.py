from sqlalchemy import Column, Integer, String, DateTime, Text
from ..database import Base
from datetime import datetime


class CleanLog(Base):
    """数据清洗日志模型 - 对应 clean_log 表"""

    __tablename__ = "clean_log"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="日志ID")
    task_name = Column(String(200), nullable=False, comment="任务名称")
    stage = Column(String(50), nullable=True, comment="清洗阶段")
    level = Column(String(20), nullable=False, default="INFO", comment="日志级别")
    message = Column(Text, nullable=False, comment="日志内容")
    record_count = Column(Integer, nullable=True, comment="影响记录数")
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")

    __table_args__ = {"comment": "数据清洗日志表"}

    def to_dict(self):
        return {
            "id": self.id,
            "task_name": self.task_name,
            "stage": self.stage,
            "level": self.level,
            "message": self.message,
            "record_count": self.record_count,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
        }
