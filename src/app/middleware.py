"""Flask中间件和钩子"""
import os
from flask import g
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask, Response

from .logger_config import logger


def register_cleanup_middleware(app: 'Flask') -> None:
    """注册临时文件清理中间件"""
    
    @app.after_request
    def cleanup_temp_files(response: 'Response') -> 'Response':
        """在响应后清理临时文件"""
        if hasattr(g, 'temp_files_to_clean'):
            for file_path in g.temp_files_to_clean:
                try:
                    if os.path.exists(file_path):
                        logger.debug(f"清理临时文件: {file_path}")
                        os.remove(file_path)
                        logger.debug(f"成功删除文件: {file_path}")
                except Exception as e:
                    logger.warning(f"清理临时文件失败 {file_path}: {e}")
        return response

