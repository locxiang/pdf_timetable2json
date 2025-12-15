"""CSV转JSON模块"""
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from .logger_config import logger


class CSVParser:
    """CSV表格解析器"""
    
    WEEKDAYS = ['星期一', '星期二', '星期三', '星期四', '星期五']
    WEEKDAY_EN_MAP = {
        '星期一': 'monday',
        '星期二': 'tuesday',
        '星期三': 'wednesday',
        '星期四': 'thursday',
        '星期五': 'friday'
    }
    
    @staticmethod
    def parse_to_json(csv_path: str) -> Optional[Dict[str, Any]]:
        """
        解析CSV文件并转换为JSON格式
        
        Args:
            csv_path: CSV文件路径
            
        Returns:
            解析后的课表数据字典，失败返回None
        """
        logger.info(f"开始解析CSV文件: {csv_path}")
        
        if not Path(csv_path).exists():
            logger.error(f"CSV文件不存在: {csv_path}")
            return None
        
        try:
            # 读取CSV
            logger.info("读取CSV文件...")
            df = pd.read_csv(csv_path, header=None, keep_default_na=False)
            logger.info(f"CSV文件维度: {df.shape[0]} 行 x {df.shape[1]} 列")
            
            if len(df) < 3:
                logger.error(f"CSV文件行数不足，至少需要3行，实际: {len(df)}")
                return None
            
            # 找出每个星期在哪些列
            logger.info("识别星期列...")
            header_row = df.iloc[0]
            weekday_columns = CSVParser._find_weekday_columns(header_row)
            logger.info(f"星期列分布: {weekday_columns}")
            
            # 解析每个班级的数据
            logger.info("开始解析班级数据...")
            timetable = {}
            class_count = 0
            
            for row_idx in range(2, len(df)):
                row = df.iloc[row_idx]
                class_name = str(row.iloc[0]).strip() if len(row) > 0 else ''
                
                if not class_name or '初三' not in class_name:
                    logger.debug(f"跳过第{row_idx}行（不是班级行）: {class_name}")
                    continue
                
                logger.info(f"解析班级: {class_name} (第{row_idx}行)")
                timetable[class_name] = CSVParser._parse_class_schedule(
                    row, weekday_columns
                )
                class_count += 1
                
                # 记录每个班级的课程数
                total_periods = sum(len(periods) for periods in timetable[class_name].values())
                logger.debug(f"  班级 {class_name} 总课时数: {total_periods}")
            
            logger.info(f"CSV解析完成，共解析 {class_count} 个班级")
            return timetable
            
        except Exception as e:
            logger.error(f"CSV解析失败: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _find_weekday_columns(header_row: pd.Series) -> Dict[str, List[int]]:
        """找出每个星期对应的列索引"""
        weekday_columns = {}
        for weekday in CSVParser.WEEKDAYS:
            weekday_columns[weekday] = []
            for col_idx in range(len(header_row)):
                cell = str(header_row.iloc[col_idx])
                if weekday in cell:
                    weekday_columns[weekday].append(col_idx)
        return weekday_columns
    
    @staticmethod
    def _parse_class_schedule(
        row: pd.Series, 
        weekday_columns: Dict[str, List[int]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """解析一个班级的课程表"""
        schedule = {}
        
        for weekday in CSVParser.WEEKDAYS:
            schedule[weekday] = []
            
            weekday_cols = weekday_columns[weekday]
            if not weekday_cols:
                logger.debug(f"  {weekday}: 未找到列")
                continue
            
            # 确定列范围
            start_col = weekday_cols[0]
            next_weekday_idx = (CSVParser.WEEKDAYS.index(weekday) + 1) % len(CSVParser.WEEKDAYS)
            if (next_weekday_idx < len(CSVParser.WEEKDAYS) and 
                weekday_columns[CSVParser.WEEKDAYS[next_weekday_idx]]):
                end_col = weekday_columns[CSVParser.WEEKDAYS[next_weekday_idx]][0]
            else:
                end_col = len(row)
            
            logger.debug(f"  {weekday}: 列范围 {start_col}-{end_col}")
            
            # 解析课程
            period = 1
            for col_idx in range(start_col, min(end_col, len(row))):
                cell_value = str(row.iloc[col_idx]).strip() if col_idx < len(row) else ''
                
                if not cell_value or cell_value == '' or cell_value == 'nan':
                    continue
                
                # 解析单元格
                period_data = CSVParser._parse_cell(cell_value, period)
                if period_data:
                    schedule[weekday].append(period_data)
                    logger.debug(f"    第{period}节: {period_data['course']} - {period_data.get('teacher', '无')}")
                    period += 1
                    
                    if period > 9:  # 每天最多9节课
                        break
            
            logger.debug(f"  {weekday}: 共 {len(schedule[weekday])} 节课")
        
        return schedule
    
    @staticmethod
    def _parse_cell(cell_value: str, period: int) -> Optional[Dict[str, Any]]:
        """解析单个单元格"""
        # 特殊活动
        if '班会' in cell_value:
            return {
                'period': period,
                'course': '班会',
                'teacher': None,
                'is_class_teacher': False
            }
        
        if '阳光体育' in cell_value:
            return {
                'period': period,
                'course': '阳光体育',
                'teacher': None,
                'is_class_teacher': False
            }
        
        # 解析课程和教师（用换行符分隔）
        parts = cell_value.split('\n')
        course = parts[0].strip() if len(parts) > 0 else ''
        teacher = parts[1].strip() if len(parts) > 1 else None
        
        if not course:
            return None
        
        # 清理教师名字
        is_class_teacher = False
        if teacher and '（班）' in teacher:
            teacher = teacher.replace('（班）', '')
            is_class_teacher = True
        
        return {
            'period': period,
            'course': course,
            'teacher': teacher,
            'is_class_teacher': is_class_teacher
        }
    
    @staticmethod
    def get_statistics(timetable: Dict[str, Any]) -> Dict[str, Any]:
        """获取统计信息"""
        total_classes = len(timetable)
        total_periods = sum(
            len(periods) 
            for class_data in timetable.values() 
            for periods in class_data.values()
        )
        
        return {
            'total_classes': total_classes,
            'total_periods': total_periods
        }

