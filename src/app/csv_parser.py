"""CSV转JSON模块"""
import pandas as pd
import re
from typing import List, Dict, Any, Optional, Tuple
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
    # 每个星期对应的课程数（固定为9节）
    PERIODS_PER_DAY = 9
    
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
            
            # 步骤1: 识别星期列位置
            logger.info("步骤1: 识别星期列位置...")
            header_row = df.iloc[0]
            weekday_start_cols = CSVParser._find_weekday_start_columns(header_row)
            logger.info(f"星期列起始位置: {weekday_start_cols}")
            
            if not weekday_start_cols:
                logger.error("未找到任何星期列")
                return None
            
            # 步骤2: 确定每个星期对应的列范围
            logger.info("步骤2: 确定每个星期对应的列范围...")
            weekday_column_ranges = CSVParser._calculate_weekday_ranges(
                weekday_start_cols, len(header_row)
            )
            logger.info(f"星期列范围: {weekday_column_ranges}")
            
            # 步骤3: 解析每个班级的数据
            logger.info("步骤3: 开始解析班级数据...")
            timetable = {}
            class_count = 0
            
            for row_idx in range(2, len(df)):
                row = df.iloc[row_idx]
                class_name = str(row.iloc[0]).strip() if len(row) > 0 else ''
                
                # 判断是否是班级行：第1列非空且符合班级命名格式
                if not CSVParser._is_class_row(row, class_name):
                    logger.debug(f"跳过第{row_idx}行（不是班级行）: {class_name}")
                    continue
                
                logger.info(f"解析班级: {class_name} (第{row_idx}行)")
                timetable[class_name] = CSVParser._parse_class_schedule(
                    row, weekday_column_ranges
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
    def _find_weekday_start_columns(header_row: pd.Series) -> Dict[str, int]:
        """
        找出每个星期第一次出现的列索引（起始列）
        
        Args:
            header_row: CSV第一行（标题行）
            
        Returns:
            字典，键为星期名，值为该星期第一次出现的列索引
        """
        weekday_start_cols = {}
        for weekday in CSVParser.WEEKDAYS:
            for col_idx in range(len(header_row)):
                cell = str(header_row.iloc[col_idx])
                if weekday in cell:
                    weekday_start_cols[weekday] = col_idx
                    logger.debug(f"找到 {weekday} 在第 {col_idx} 列")
                    break
        return weekday_start_cols
    
    @staticmethod
    def _calculate_weekday_ranges(
        weekday_start_cols: Dict[str, int], 
        total_columns: int
    ) -> Dict[str, Tuple[int, int]]:
        """
        计算每个星期对应的列范围
        
        Args:
            weekday_start_cols: 每个星期起始列索引
            total_columns: 总列数
            
        Returns:
            字典，键为星期名，值为(起始列, 结束列)元组
        """
        weekday_ranges = {}
        
        for i, weekday in enumerate(CSVParser.WEEKDAYS):
            if weekday not in weekday_start_cols:
                continue
            
            start_col = weekday_start_cols[weekday]
            
            # 找到下一个星期的起始列作为结束列
            end_col = total_columns
            for j in range(i + 1, len(CSVParser.WEEKDAYS)):
                next_weekday = CSVParser.WEEKDAYS[j]
                if next_weekday in weekday_start_cols:
                    end_col = weekday_start_cols[next_weekday]
                    break
            
            weekday_ranges[weekday] = (start_col, end_col)
            logger.debug(f"{weekday}: 列范围 {start_col} 到 {end_col} (共 {end_col - start_col} 列)")
        
        return weekday_ranges
    
    @staticmethod
    def _is_class_row(row: pd.Series, first_cell: str) -> bool:
        """
        判断是否是班级行
        
        Args:
            row: 数据行
            first_cell: 第一列的值
            
        Returns:
            如果是班级行返回True，否则返回False
        """
        # 第1列必须非空
        if not first_cell or first_cell == '' or first_cell == 'nan':
            return False
        
        # 检查是否符合班级命名格式（如：初一.1班、初二.2班、初三.3班等）
        # 支持：初一、初二、初三、初四等，以及可能的其他格式
        # 格式：年级 + 分隔符（.或·） + 数字 + 班
        class_pattern = r'^[初高][一二三四五六七八九十\d]+[\.·]?\d+班'
        if re.match(class_pattern, first_cell):
            return True
        
        # 也支持更简单的格式，如：初一1班、初二2班等（无分隔符）
        class_pattern_simple = r'^[初高][一二三四五六七八九十\d]+\d+班'
        if re.match(class_pattern_simple, first_cell):
            return True
        
        # 如果第1列有值，且该行在星期列范围内有非空数据，也认为是班级行
        # 这是一个兜底策略，处理可能的格式变化
        if len(row) > 1:
            # 检查第2列之后是否有非空数据
            for col_idx in range(1, min(len(row), 10)):  # 只检查前10列
                cell_value = str(row.iloc[col_idx]).strip()
                if cell_value and cell_value != '' and cell_value != 'nan':
                    return True
        
        return False
    
    @staticmethod
    def _parse_class_schedule(
        row: pd.Series, 
        weekday_column_ranges: Dict[str, Tuple[int, int]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        解析一个班级的课程表
        
        Args:
            row: 班级数据行
            weekday_column_ranges: 每个星期对应的列范围字典
            
        Returns:
            该班级的课程表字典
        """
        schedule = {}
        
        for weekday in CSVParser.WEEKDAYS:
            schedule[weekday] = []
            
            if weekday not in weekday_column_ranges:
                logger.debug(f"  {weekday}: 未找到列范围")
                continue
            
            start_col, end_col = weekday_column_ranges[weekday]
            
            # 每个星期对应9节课，按列顺序对应第1-9节
            # 根据CSV结构：星期标题列在标题行中，但在数据行中该列就是第一节课的数据
            # 所以数据列从 start_col 开始，共9列
            data_start_col = start_col
            
            # 计算实际的数据列范围（最多9列，或到下一个星期之前）
            max_cols = min(data_start_col + CSVParser.PERIODS_PER_DAY, end_col, len(row))
            
            logger.debug(f"  {weekday}: 数据列范围 {data_start_col}-{max_cols}，解析9节课")
            
            # 用于标记已处理的 period（避免重复处理）
            processed_periods = set()
            
            # 按列顺序解析为第1-9节课
            for period in range(1, CSVParser.PERIODS_PER_DAY + 1):
                # 如果已经处理过，跳过
                if period in processed_periods:
                    continue
                
                col_idx = data_start_col + period - 1
                
                # 如果超出范围，跳过
                if col_idx >= max_cols or col_idx >= len(row):
                    break
                
                cell_value = str(row.iloc[col_idx]).strip()
                
                # 空单元格表示该节课为空（正常现象）
                if not cell_value or cell_value == '' or cell_value == 'nan':
                    continue
                
                # 检查是否需要拆分：先检查下一个 period 是否为空
                next_period = period + 1
                should_split = False
                split_courses = None
                
                if next_period <= CSVParser.PERIODS_PER_DAY:
                    next_col_idx = data_start_col + next_period - 1
                    if next_col_idx < max_cols and next_col_idx < len(row):
                        next_cell_value = str(row.iloc[next_col_idx]).strip()
                        # 如果下一个单元格为空，检查当前单元格是否有重复模式
                        if not next_cell_value or next_cell_value == '' or next_cell_value == 'nan':
                            # 先解析当前单元格获取课程名
                            temp_period_data = CSVParser._parse_cell(cell_value, period)
                            if temp_period_data:
                                course = temp_period_data['course']
                                # 检测是否有重复模式
                                split_result = CSVParser._detect_and_split_duplicate_course(course)
                                if split_result:
                                    should_split = True
                                    split_courses = split_result
                                    logger.debug(f"    检测到需要拆分: 第{period}节 '{course}' -> 第{period}节 '{split_result[0]}' + 第{next_period}节 '{split_result[1]}'")
                
                # 如果需要拆分
                if should_split and split_courses:
                    # 解析当前单元格获取教师信息
                    temp_period_data = CSVParser._parse_cell(cell_value, period)
                    if temp_period_data:
                        teacher = temp_period_data.get('teacher')
                        is_class_teacher = temp_period_data.get('is_class_teacher', False)
                        
                        # 创建两个 period 的数据
                        # 第一个 period
                        period_data_1 = {
                            'period': period,
                            'course': split_courses[0],
                            'teacher': teacher,
                            'is_class_teacher': is_class_teacher
                        }
                        schedule[weekday].append(period_data_1)
                        processed_periods.add(period)
                        logger.debug(f"    第{period}节: {period_data_1['course']} - {period_data_1.get('teacher', '无')}")
                        
                        # 第二个 period
                        period_data_2 = {
                            'period': next_period,
                            'course': split_courses[1],
                            'teacher': teacher,  # 两个 period 使用相同的教师信息
                            'is_class_teacher': is_class_teacher
                        }
                        schedule[weekday].append(period_data_2)
                        processed_periods.add(next_period)
                        logger.debug(f"    第{next_period}节: {period_data_2['course']} - {period_data_2.get('teacher', '无')}")
                else:
                    # 正常解析单元格
                    period_data = CSVParser._parse_cell(cell_value, period)
                    if period_data:
                        schedule[weekday].append(period_data)
                        processed_periods.add(period)
                        logger.debug(f"    第{period}节: {period_data['course']} - {period_data.get('teacher', '无')}")
            
            logger.debug(f"  {weekday}: 共 {len(schedule[weekday])} 节课")
        
        return schedule
    
    @staticmethod
    def _detect_and_split_duplicate_course(course: str) -> Optional[Tuple[str, str]]:
        """
        检测课程名是否有重复模式，如果有则拆分
        
        Args:
            course: 课程名称
            
        Returns:
            如果检测到重复模式，返回拆分后的两部分元组 (第一部分, 第二部分)；
            否则返回 None
        """
        if not course or len(course) < 2:
            return None
        
        # 检测完全重复模式：如 "选修课选修课" -> ("选修课", "选修课")
        # 使用正则表达式匹配：课程名是否为某个子串的完全重复
        match = re.match(r'^(.+)\1$', course)
        if match:
            base_course = match.group(1)
            logger.debug(f"检测到重复课程名: '{course}' -> '{base_course}' + '{base_course}'")
            return (base_course, base_course)
        
        return None
    
    @staticmethod
    def _parse_cell(cell_value: str, period: int) -> Optional[Dict[str, Any]]:
        """
        解析单个单元格
        
        Args:
            cell_value: 单元格内容
            period: 课时编号（1-9）
            
        Returns:
            解析后的课时数据字典，如果解析失败返回None
        """
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
        if teacher:
            # 处理（班）标识
            if '（班）' in teacher:
                teacher = teacher.replace('（班）', '')
                is_class_teacher = True
            elif '(班)' in teacher:
                teacher = teacher.replace('(班)', '')
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

