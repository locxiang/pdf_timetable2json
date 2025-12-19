"""Flask API路由"""
import tempfile
from flask import Flask
from flasgger import Swagger

from .swagger_config import get_swagger_config, get_swagger_template
from .middleware import register_cleanup_middleware
from .handlers import (
    register_health_route,
    register_pdf_to_json_route,
    register_pdf_to_csv_route,
    register_csv_to_json_route
)


def create_app() -> Flask:
    """创建Flask应用"""
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB限制
    app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
    
    # 配置Swagger
    swagger_config = get_swagger_config()
    swagger_template = get_swagger_template()
    Swagger(app, config=swagger_config, template=swagger_template)
    
    # 注册中间件
    register_cleanup_middleware(app)
    
    # 注册路由
    register_health_route(app)
    register_pdf_to_json_route(app)
    register_pdf_to_csv_route(app)
    register_csv_to_json_route(app)
    
    return app
