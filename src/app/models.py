"""数据模型定义"""
from typing import Optional, List
from pydantic import BaseModel


class Period(BaseModel):
    """课时信息"""
    课时: int
    课程: str
    教师: Optional[str] = None
    班主任: bool = False


class DaySchedule(BaseModel):
    """一天的课程安排"""
    星期: str
    课程列表: List[Period]


class ClassSchedule(BaseModel):
    """一个班级的课程表"""
    班级: str
    课程表: List[DaySchedule]


class TimetableResponse(BaseModel):
    """API响应模型"""
    成功: bool
    消息: str
    数据: Optional[List[ClassSchedule]] = None
    统计: Optional[dict] = None

