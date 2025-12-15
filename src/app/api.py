"""Flask API路由"""
import os
import tempfile
import time
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
from typing import Dict, Any
from flasgger import Swagger

from .pdf_parser import PDFParser
from .csv_parser import CSVParser
from .logger_config import logger


def create_app() -> Flask:
    """创建Flask应用"""
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB限制
    app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
    
    # 配置Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "PDF课程表转JSON API",
            "description": "将PDF格式的课程表转换为结构化JSON数据的RESTful API",
            "version": "0.1.0",
            "contact": {
                "name": "API Support"
            }
        },
        "host": "localhost:5001",
        "basePath": "/",
        "schemes": ["http"],
        "consumes": ["multipart/form-data", "application/json"],
        "produces": ["application/json"]
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)
    
    ALLOWED_EXTENSIONS = {'pdf'}
    
    def allowed_file(filename: str) -> bool:
        """检查文件扩展名是否允许"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    @app.route('/health', methods=['GET'])
    def health():
        """
        健康检查端点
        ---
        tags:
          - 系统
        summary: 健康检查
        description: 检查API服务是否正常运行
        responses:
          200:
            description: 服务正常
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: ok
        """
        logger.debug("健康检查请求")
        return jsonify({'status': 'ok'}), 200
    
    @app.route('/api/timetable/parse', methods=['POST'])
    def parse_timetable():
        """
        解析PDF课程表
        ---
        tags:
          - 课程表
        summary: 解析PDF课程表
        description: 上传PDF格式的课程表文件，返回结构化的JSON数据
        consumes:
          - multipart/form-data
        parameters:
          - in: formData
            name: file
            type: file
            required: true
            description: PDF格式的课程表文件（最大16MB）
        responses:
          200:
            description: 解析成功
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                message:
                  type: string
                  example: 解析成功
                data:
                  type: object
                  properties:
                    classes:
                      type: array
                      items:
                        type: object
                        properties:
                          class_name:
                            type: string
                            example: 初三.1班
                          schedule:
                            type: object
                            properties:
                              monday:
                                type: array
                                items:
                                  type: object
                                  properties:
                                    period:
                                      type: integer
                                      example: 1
                                    course:
                                      type: string
                                      example: 英语
                                    teacher:
                                      type: string
                                      example: 陈小华
                                    is_class_teacher:
                                      type: boolean
                                      example: true
                statistics:
                  type: object
                  properties:
                    total_classes:
                      type: integer
                      example: 15
                    total_periods:
                      type: integer
                      example: 540
                parsing_report:
                  type: object
                  properties:
                    accuracy:
                      type: number
                      format: float
                      example: 85.77
                    whitespace:
                      type: number
                      format: float
                      example: 12.4
                    order:
                      type: integer
                      example: 1
                    page:
                      type: integer
                      example: 1
          400:
            description: 请求错误（文件缺失、格式错误或解析失败）
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: false
                message:
                  type: string
                  example: PDF解析失败，无法提取表格
          500:
            description: 服务器内部错误
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: false
                message:
                  type: string
                  example: "处理失败: 错误信息"
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
                'success': False,
                'message': '未找到文件，请使用file字段上传PDF文件'
            }), 400
        
        file = request.files['file']
        logger.info(f"上传文件名: {file.filename}")
        logger.info(f"文件大小: {request.content_length / 1024:.2f} KB" if request.content_length else "未知")
        
        # 检查文件名
        if file.filename == '':
            logger.warning("文件名为空")
            return jsonify({
                'success': False,
                'message': '文件名为空'
            }), 400
        
        if not allowed_file(file.filename):
            logger.warning(f"不支持的文件格式: {file.filename}")
            return jsonify({
                'success': False,
                'message': '不支持的文件格式，请上传PDF文件'
            }), 400
        
        # 保存临时文件（使用UUID确保文件名唯一且安全）
        import uuid
        file_ext = os.path.splitext(file.filename)[1] or '.pdf'
        temp_filename = f"{uuid.uuid4().hex}{file_ext}"
        temp_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        logger.info(f"保存临时文件到: {temp_pdf_path}")
        file.save(temp_pdf_path)
        
        csv_path = None
        
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
                    'success': False,
                    'message': 'PDF解析失败，无法提取表格'
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
                    'success': False,
                    'message': 'CSV解析失败，无法转换为JSON'
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
            
            total_time = time.time() - start_time
            logger.info("=" * 60)
            logger.info(f"请求处理完成，总耗时: {total_time:.2f}秒")
            logger.info(f"  - PDF转CSV: {step1_time:.2f}秒")
            logger.info(f"  - CSV转JSON: {step2_time:.2f}秒")
            logger.info(f"  - 数据格式化: {format_time:.2f}秒")
            logger.info("=" * 60)
            
            return jsonify({
                'success': True,
                'message': '解析成功',
                'data': formatted_data,
                'statistics': statistics,
                'parsing_report': parsing_report
            }), 200
            
        except Exception as e:
            logger.error(f"处理失败: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': f'处理失败: {str(e)}'
            }), 500
        
        finally:
            # 确保所有临时文件都被清理
            files_to_clean = [temp_pdf_path]
            if csv_path:
                files_to_clean.append(csv_path)
            
            for file_path in files_to_clean:
                try:
                    if os.path.exists(file_path):
                        logger.debug(f"清理临时文件: {file_path}")
                        os.remove(file_path)
                        logger.debug(f"成功删除文件: {file_path}")
                except Exception as e:
                    logger.warning(f"清理临时文件失败 {file_path}: {e}")
    
    return app


def _format_timetable(timetable: Dict[str, Any]) -> Dict[str, Any]:
    """格式化课表数据为更清晰的结构"""
    from .csv_parser import CSVParser
    
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

