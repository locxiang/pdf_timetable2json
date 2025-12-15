"""Flask API路由"""
import os
import tempfile
import time
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
from typing import Dict, Any

from .pdf_parser import PDFParser
from .csv_parser import CSVParser
from .logger_config import logger


def create_app() -> Flask:
    """创建Flask应用"""
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB限制
    app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
    
    ALLOWED_EXTENSIONS = {'pdf'}
    
    def allowed_file(filename: str) -> bool:
        """检查文件扩展名是否允许"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    @app.route('/health', methods=['GET'])
    def health():
        """健康检查"""
        logger.debug("健康检查请求")
        return jsonify({'status': 'ok'}), 200
    
    @app.route('/api/timetable/parse', methods=['POST'])
    def parse_timetable():
        """
        解析PDF课程表
        
        请求:
            - 文件字段名: file
            - Content-Type: multipart/form-data
            
        返回:
            {
                "成功": true,
                "消息": "解析成功",
                "数据": {
                    "班级列表": [
                        {
                            "班级": "初三.1班",
                            "课程表": {
                                "星期一": [
                                    {
                                        "课时": 1,
                                        "课程": "英语",
                                        "教师": "陈小华",
                                        "班主任": true
                                    },
                                    ...
                                ],
                                ...
                            }
                        },
                        ...
                    ]
                },
                "统计": {
                    "班级数": 15,
                    "总课时数": 540
                }
            }
        """
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("收到PDF解析请求")
        logger.info(f"请求IP: {request.remote_addr}")
        logger.info(f"请求方法: {request.method}")
        logger.info(f"Content-Type: {request.content_type}")
        
        # 检查文件是否存在
        if 'file' not in request.files:
            logger.warning("请求中未找到file字段")
            return jsonify({
                '成功': False,
                '消息': '未找到文件，请使用file字段上传PDF文件'
            }), 400
        
        file = request.files['file']
        logger.info(f"上传文件名: {file.filename}")
        logger.info(f"文件大小: {request.content_length / 1024:.2f} KB" if request.content_length else "未知")
        
        # 检查文件名
        if file.filename == '':
            logger.warning("文件名为空")
            return jsonify({
                '成功': False,
                '消息': '文件名为空'
            }), 400
        
        if not allowed_file(file.filename):
            logger.warning(f"不支持的文件格式: {file.filename}")
            return jsonify({
                '成功': False,
                '消息': '不支持的文件格式，请上传PDF文件'
            }), 400
        
        # 保存临时文件（使用UUID确保文件名唯一且安全）
        import uuid
        file_ext = os.path.splitext(file.filename)[1] or '.pdf'
        temp_filename = f"{uuid.uuid4().hex}{file_ext}"
        temp_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        logger.info(f"保存临时文件到: {temp_pdf_path}")
        file.save(temp_pdf_path)
        
        try:
            # 步骤1: PDF -> CSV
            logger.info("=" * 60)
            logger.info("步骤1: PDF转CSV")
            logger.info("=" * 60)
            step1_start = time.time()
            csv_path, parsing_report = PDFParser.extract_table(temp_pdf_path)
            step1_time = time.time() - step1_start
            logger.info(f"PDF转CSV耗时: {step1_time:.2f}秒")
            
            if csv_path is None:
                logger.error("PDF解析失败，无法提取表格")
                return jsonify({
                    '成功': False,
                    '消息': 'PDF解析失败，无法提取表格'
                }), 400
            
            # 步骤2: CSV -> JSON
            logger.info("=" * 60)
            logger.info("步骤2: CSV转JSON")
            logger.info("=" * 60)
            step2_start = time.time()
            timetable = CSVParser.parse_to_json(csv_path)
            step2_time = time.time() - step2_start
            logger.info(f"CSV转JSON耗时: {step2_time:.2f}秒")
            
            if timetable is None:
                logger.error("CSV解析失败，无法转换为JSON")
                return jsonify({
                    '成功': False,
                    '消息': 'CSV解析失败，无法转换为JSON'
                }), 400
            
            # 格式化数据
            logger.info("格式化数据...")
            format_start = time.time()
            formatted_data = _format_timetable(timetable)
            format_time = time.time() - format_start
            logger.info(f"数据格式化耗时: {format_time:.2f}秒")
            
            # 获取统计信息
            statistics = CSVParser.get_statistics(timetable)
            logger.info(f"统计信息: {statistics}")
            
            # 清理临时文件
            try:
                logger.debug(f"清理临时文件: {temp_pdf_path}")
                os.remove(temp_pdf_path)
                logger.debug(f"清理临时文件: {csv_path}")
                os.remove(csv_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
            
            total_time = time.time() - start_time
            logger.info("=" * 60)
            logger.info(f"请求处理完成，总耗时: {total_time:.2f}秒")
            logger.info(f"  - PDF转CSV: {step1_time:.2f}秒")
            logger.info(f"  - CSV转JSON: {step2_time:.2f}秒")
            logger.info(f"  - 数据格式化: {format_time:.2f}秒")
            logger.info("=" * 60)
            
            return jsonify({
                '成功': True,
                '消息': '解析成功',
                '数据': formatted_data,
                '统计': statistics,
                '解析报告': parsing_report
            }), 200
            
        except Exception as e:
            logger.error(f"处理失败: {e}", exc_info=True)
            # 清理临时文件
            try:
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
            except:
                pass
            
            return jsonify({
                '成功': False,
                '消息': f'处理失败: {str(e)}'
            }), 500
    
    return app


def _format_timetable(timetable: Dict[str, Any]) -> Dict[str, Any]:
    """格式化课表数据为更清晰的结构"""
    weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五']
    class_list = []
    
    for class_name, schedule in sorted(timetable.items()):
        class_data = {
            '班级': class_name,
            '课程表': {}
        }
        
        for weekday in weekdays:
            if weekday in schedule:
                class_data['课程表'][weekday] = schedule[weekday]
        
        class_list.append(class_data)
    
    return {
        '班级列表': class_list
    }

