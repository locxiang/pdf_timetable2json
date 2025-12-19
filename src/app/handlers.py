"""API路由处理函数"""
import os
import time
from flask import Flask, request, jsonify, send_file, g
from werkzeug.utils import secure_filename

from .pdf_parser import PDFParser
from .file_utils import validate_file_upload, save_temp_file, ALLOWED_EXTENSIONS_PDF, ALLOWED_EXTENSIONS_CSV
from .formatters import csv_to_json_internal
from .logger_config import logger


def register_health_route(app: Flask) -> None:
    """注册健康检查路由"""
    
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


def register_pdf_to_json_route(app: Flask) -> None:
    """注册PDF转JSON路由"""
    
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
        
        # 验证文件上传
        file, error_response, status_code = validate_file_upload('file', ALLOWED_EXTENSIONS_PDF)
        if error_response:
            return error_response
        
        # 保存临时文件
        temp_pdf_path = save_temp_file(file, app.config['UPLOAD_FOLDER'], '.pdf')
        
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
            
            # 步骤2: CSV -> JSON（复用代码）
            step2_start = time.time()
            formatted_data, statistics, error_response = csv_to_json_internal(csv_path)
            step2_time = time.time() - step2_start
            
            if error_response:
                return error_response
            
            total_time = time.time() - start_time
            logger.info("=" * 60)
            logger.info(f"请求处理完成，总耗时: {total_time:.2f}秒")
            logger.info(f"  - PDF转CSV: {step1_time:.2f}秒")
            logger.info(f"  - CSV转JSON: {step2_time:.2f}秒")
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


def register_pdf_to_csv_route(app: Flask) -> None:
    """注册PDF转CSV路由"""
    
    @app.route('/api/pdf/to-csv', methods=['POST'])
    def pdf_to_csv():
        """
        PDF转CSV
        ---
        tags:
          - PDF转换
        summary: 将PDF文件中的表格转换为CSV格式
        description: |
          上传PDF文件，提取其中的表格数据并转换为CSV格式文件返回。
          
          该接口使用Camelot库进行PDF表格提取，支持两种提取方法：
          - **lattice方法**: 适用于有明确网格线的表格（默认方法）
          - **stream方法**: 当lattice方法失败时自动尝试，适用于无网格线的表格
          
          **使用场景**:
          - 需要将PDF中的表格数据提取为CSV格式进行进一步处理
          - 需要查看PDF表格的原始数据结构
          - 作为PDF转JSON流程的中间步骤
          
          **注意事项**:
          - 仅支持PDF格式文件，最大文件大小为16MB
          - 仅提取PDF第一页的表格
          - 返回的CSV文件使用UTF-8编码
        consumes:
          - multipart/form-data
        parameters:
          - in: formData
            name: file
            type: file
            required: true
            description: PDF格式的文件（最大16MB），必须包含表格数据
        produces:
          - text/csv
        responses:
          200:
            description: 转换成功，返回CSV文件
            schema:
              type: file
            headers:
              Content-Type:
                type: string
                example: text/csv; charset=utf-8
              Content-Disposition:
                type: string
                example: attachment; filename="table.csv"
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
        examples:
          - title: 成功示例
            description: 成功转换PDF为CSV
            value:
              file: (binary PDF file)
          - title: 错误示例
            description: 文件格式错误
            value:
              success: false
              message: "不支持的文件格式，请上传PDF文件"
        """
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("收到PDF转CSV请求")
        logger.info(f"请求IP: {request.remote_addr}")
        logger.info(f"请求方法: {request.method}")
        logger.info(f"Content-Type: {request.content_type}")
        
        # 验证文件上传
        file, error_response, status_code = validate_file_upload('file', ALLOWED_EXTENSIONS_PDF)
        if error_response:
            return error_response
        
        # 保存临时文件
        temp_pdf_path = save_temp_file(file, app.config['UPLOAD_FOLDER'], '.pdf')
        
        csv_path = None
        
        try:
            # PDF -> CSV
            logger.info("=" * 60)
            logger.info("开始PDF转CSV转换")
            logger.info("=" * 60)
            conversion_start = time.time()
            csv_path, parsing_report = PDFParser.extract_table(temp_pdf_path)
            conversion_time = time.time() - conversion_start
            logger.info(f"PDF转CSV耗时: {conversion_time:.2f}秒")
            
            if csv_path is None:
                logger.error("PDF解析失败，无法提取表格")
                # 设置文件清理
                g.temp_files_to_clean = [temp_pdf_path]
                return jsonify({
                    'success': False,
                    'message': 'PDF解析失败，无法提取表格。请确保PDF文件包含表格数据。'
                }), 400
            
            if not os.path.exists(csv_path):
                logger.error(f"CSV文件不存在: {csv_path}")
                # 设置文件清理
                g.temp_files_to_clean = [temp_pdf_path]
                return jsonify({
                    'success': False,
                    'message': 'CSV文件生成失败'
                }), 500
            
            # 获取CSV文件信息
            csv_size = os.path.getsize(csv_path)
            logger.info(f"CSV文件大小: {csv_size / 1024:.2f} KB")
            logger.info(f"解析报告: {parsing_report}")
            
            total_time = time.time() - start_time
            logger.info("=" * 60)
            logger.info(f"PDF转CSV完成，总耗时: {total_time:.2f}秒")
            logger.info("=" * 60)
            
            # 生成下载文件名
            original_name = os.path.splitext(secure_filename(file.filename))[0]
            download_filename = f"{original_name}_table.csv"
            
            # 将需要清理的文件路径存储到g对象中，由after_request钩子清理
            g.temp_files_to_clean = [temp_pdf_path]
            if csv_path:
                g.temp_files_to_clean.append(csv_path)
            
            # 返回CSV文件
            return send_file(
                csv_path,
                mimetype='text/csv',
                as_attachment=True,
                download_name=download_filename,
                etag=False
            )
            
        except Exception as e:
            logger.error(f"处理失败: {e}", exc_info=True)
            # 将需要清理的文件路径存储到g对象中，由after_request钩子清理
            g.temp_files_to_clean = [temp_pdf_path]
            if csv_path and os.path.exists(csv_path):
                g.temp_files_to_clean.append(csv_path)
            
            return jsonify({
                'success': False,
                'message': f'处理失败: {str(e)}'
            }), 500


def register_csv_to_json_route(app: Flask) -> None:
    """注册CSV转JSON路由"""
    
    @app.route('/api/csv/to-json', methods=['POST'])
    def csv_to_json():
        """
        CSV转JSON
        ---
        tags:
          - CSV转换
        summary: 将CSV格式的课程表转换为JSON格式
        description: |
          上传CSV文件，解析其中的课程表数据并转换为结构化的JSON格式返回。
          
          该接口是PDF转JSON流程中的第二步，也可以独立使用。
          
          **使用场景**:
          - 已有CSV格式的课程表文件，需要转换为JSON格式
          - 作为PDF转JSON流程的中间步骤
          - 对CSV文件进行格式验证和结构化处理
          
          **注意事项**:
          - 仅支持CSV格式文件，最大文件大小为16MB
          - CSV文件必须符合课程表格式要求（包含星期列和班级行）
          - 返回的JSON数据包含格式化后的课程表结构和统计信息
        consumes:
          - multipart/form-data
        parameters:
          - in: formData
            name: file
            type: file
            required: true
            description: CSV格式的课程表文件（最大16MB），必须符合课程表格式要求
        responses:
          200:
            description: 转换成功，返回JSON数据
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                message:
                  type: string
                  example: 转换成功
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
                  example: CSV解析失败，无法转换为JSON
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
        examples:
          - title: 成功示例
            description: 成功转换CSV为JSON
            value:
              file: (binary CSV file)
          - title: 错误示例
            description: 文件格式错误
            value:
              success: false
              message: "不支持的文件格式，请上传CSV文件"
        """
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("收到CSV转JSON请求")
        logger.info(f"请求IP: {request.remote_addr}")
        logger.info(f"请求方法: {request.method}")
        logger.info(f"Content-Type: {request.content_type}")
        
        # 验证文件上传
        file, error_response, status_code = validate_file_upload('file', ALLOWED_EXTENSIONS_CSV)
        if error_response:
            return error_response
        
        # 保存临时文件
        temp_csv_path = save_temp_file(file, app.config['UPLOAD_FOLDER'], '.csv')
        
        try:
            # CSV -> JSON（复用代码）
            formatted_data, statistics, error_response = csv_to_json_internal(temp_csv_path)
            
            if error_response:
                g.temp_files_to_clean = [temp_csv_path]
                return error_response
            
            total_time = time.time() - start_time
            logger.info("=" * 60)
            logger.info(f"CSV转JSON完成，总耗时: {total_time:.2f}秒")
            logger.info("=" * 60)
            
            # 将需要清理的文件路径存储到g对象中，由after_request钩子清理
            g.temp_files_to_clean = [temp_csv_path]
            
            return jsonify({
                'success': True,
                'message': '转换成功',
                'data': formatted_data,
                'statistics': statistics
            }), 200
            
        except Exception as e:
            logger.error(f"处理失败: {e}", exc_info=True)
            # 将需要清理的文件路径存储到g对象中，由after_request钩子清理
            g.temp_files_to_clean = [temp_csv_path]
            
            return jsonify({
                'success': False,
                'message': f'处理失败: {str(e)}'
            }), 500

