"""Swagger API文档配置"""
from typing import Dict, Any


def get_swagger_config() -> Dict[str, Any]:
    """获取Swagger配置"""
    return {
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


def get_swagger_template() -> Dict[str, Any]:
    """获取Swagger模板"""
    return {
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
        "produces": ["application/json", "text/csv"]
    }

