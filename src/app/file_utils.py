"""文件处理工具函数"""
import os
import uuid
from flask import request, jsonify
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage

from .logger_config import logger

# 允许的文件扩展名
ALLOWED_EXTENSIONS_PDF = {'pdf'}
ALLOWED_EXTENSIONS_CSV = {'csv'}


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def validate_file_upload(
    file_field_name: str = 'file', 
    allowed_extensions: set = None
) -> Tuple[Optional[FileStorage], Optional[dict], Optional[int]]:
    """
    验证文件上传请求
    
    Args:
        file_field_name: 文件字段名，默认为'file'
        allowed_extensions: 允许的文件扩展名集合
        
    Returns:
        (file, error_response, status_code) 元组，如果验证失败error_response不为None
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS_PDF
    
    # 检查文件是否存在
    if file_field_name not in request.files:
        logger.warning(f"请求中未找到{file_field_name}字段")
        return None, jsonify({
            'success': False,
            'message': f'未找到文件，请使用{file_field_name}字段上传文件'
        }), 400
    
    file = request.files[file_field_name]
    logger.info(f"上传文件名: {file.filename}")
    logger.info(f"文件大小: {request.content_length / 1024:.2f} KB" if request.content_length else "未知")
    
    # 检查文件名
    if file.filename == '':
        logger.warning("文件名为空")
        return None, jsonify({
            'success': False,
            'message': '文件名为空'
        }), 400
    
    if not allowed_file(file.filename, allowed_extensions):
        ext_str = ', '.join(allowed_extensions)
        logger.warning(f"不支持的文件格式: {file.filename}")
        return None, jsonify({
            'success': False,
            'message': f'不支持的文件格式，请上传{ext_str.upper()}文件'
        }), 400
    
    return file, None, None


def save_temp_file(file: FileStorage, upload_folder: str, default_ext: str = '.pdf') -> str:
    """
    保存上传的文件为临时文件
    
    Args:
        file: Flask文件对象
        upload_folder: 上传文件夹路径
        default_ext: 默认文件扩展名
        
    Returns:
        临时文件路径
    """
    file_ext = os.path.splitext(file.filename)[1] or default_ext
    temp_filename = f"{uuid.uuid4().hex}{file_ext}"
    temp_path = os.path.join(upload_folder, temp_filename)
    logger.info(f"保存临时文件到: {temp_path}")
    file.save(temp_path)
    return temp_path

