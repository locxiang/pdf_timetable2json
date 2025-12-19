"""数据格式化函数"""
import time
from typing import Dict, Any, Tuple, Optional
from flask import jsonify

from .csv_parser import CSVParser
from .logger_config import logger


def format_timetable(timetable: Dict[str, Any]) -> Dict[str, Any]:
    """格式化课表数据为更清晰的结构"""
    weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五']
    class_list = []
    
    for class_name, schedule in sorted(timetable.items()):
        class_data = {
            'class_name': class_name,
            'schedule': {}
        }
        
        for weekday in weekdays:
            if weekday in schedule:
                weekday_en = CSVParser.WEEKDAY_EN_MAP.get(weekday, weekday.lower())
                class_data['schedule'][weekday_en] = schedule[weekday]
        
        class_list.append(class_data)
    
    return {
        'classes': class_list
    }


def csv_to_json_internal(csv_path: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[dict]]:
    """
    内部函数：将CSV转换为JSON（复用代码）
    
    Args:
        csv_path: CSV文件路径
        
    Returns:
        (formatted_data, statistics, error_response) 元组
    """
    # CSV -> JSON
    logger.info("=" * 60)
    logger.info("开始CSV转JSON转换")
    logger.info("=" * 60)
    conversion_start = time.time()
    timetable = CSVParser.parse_to_json(csv_path)
    conversion_time = time.time() - conversion_start
    logger.info(f"CSV转JSON耗时: {conversion_time:.2f}秒")
    
    if timetable is None:
        logger.error("CSV解析失败，无法转换为JSON")
        return None, None, jsonify({
            'success': False,
            'message': 'CSV解析失败，无法转换为JSON'
        }), 400
    
    # 格式化数据
    logger.info("格式化数据...")
    format_start = time.time()
    formatted_data = format_timetable(timetable)
    format_time = time.time() - format_start
    logger.info(f"数据格式化耗时: {format_time:.2f}秒")
    
    # 获取统计信息
    statistics = CSVParser.get_statistics(timetable)
    logger.info(f"统计信息: {statistics}")
    
    return formatted_data, statistics, None

