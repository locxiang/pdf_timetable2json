"""PDF转CSV模块"""
import camelot
from pathlib import Path
from typing import Optional, Tuple
from .logger_config import logger


class PDFParser:
    """PDF表格解析器"""
    
    @staticmethod
    def extract_table(pdf_path: str) -> Tuple[Optional[str], Optional[dict]]:
        """
        从PDF提取表格并保存为CSV
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            (csv_path, parsing_report) 或 (None, None) 如果失败
        """
        logger.info(f"开始解析PDF文件: {pdf_path}")
        
        if not Path(pdf_path).exists():
            logger.error(f"PDF文件不存在: {pdf_path}")
            return None, None
        
        file_size = Path(pdf_path).stat().st_size
        logger.info(f"PDF文件大小: {file_size / 1024:.2f} KB")
        
        try:
            # 尝试lattice方法（适合有明确网格线的表格）
            logger.info("尝试使用lattice方法提取表格...")
            tables = camelot.read_pdf(pdf_path, flavor='lattice', pages='1')
            logger.info(f"Lattice方法找到 {len(tables)} 个表格")
            
            # 如果lattice失败，尝试stream方法
            if len(tables) == 0:
                logger.warning("Lattice方法未找到表格，尝试stream方法...")
                tables = camelot.read_pdf(pdf_path, flavor='stream', pages='1')
                logger.info(f"Stream方法找到 {len(tables)} 个表格")
            
            if len(tables) == 0:
                logger.error("未能从PDF中提取到表格")
                return None, None
            
            table = tables[0]
            parsing_report = table.parsing_report
            logger.info(f"表格形状: {table.shape}, 解析报告: {parsing_report}")
            
            # 保存为CSV
            csv_path = pdf_path.replace('.pdf', '_table.csv')
            logger.info(f"保存CSV文件到: {csv_path}")
            table.to_csv(csv_path)
            
            csv_size = Path(csv_path).stat().st_size
            logger.info(f"CSV文件大小: {csv_size / 1024:.2f} KB")
            logger.info(f"PDF转CSV成功完成")
            
            return csv_path, parsing_report
            
        except Exception as e:
            logger.error(f"PDF解析失败: {e}", exc_info=True)
            return None, None

