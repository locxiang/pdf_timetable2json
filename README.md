# PDF课程表转JSON API

将PDF格式的课程表转换为结构化JSON数据的Flask API服务。

## 功能说明

- 📄 接收PDF文件上传
- 🔄 自动提取PDF表格并转换为CSV
- 📊 解析CSV并转换为结构化的JSON数据
- ✅ 返回清晰的JSON数据结构

## 安装说明

### 方式一：使用Docker（推荐）

#### 1. 构建Docker镜像

```bash
docker build -t pdf-timetable2json .
```

#### 2. 运行Docker容器

```bash
docker run -d \
  --name pdf-timetable-api \
  -p 5001:5001 \
  -e FLASK_HOST=0.0.0.0 \
  -e FLASK_PORT=5001 \
  -e FLASK_DEBUG=false \
  pdf-timetable2json
```

#### 3. 查看日志

```bash
docker logs -f pdf-timetable-api
```

#### 4. 停止容器

```bash
docker stop pdf-timetable-api
docker rm pdf-timetable-api
```

### 方式二：本地安装

#### 1. 创建conda环境

```bash
conda env create -f environment.yml
conda activate pdf_timetable2json
```

#### 2. 安装项目依赖

```bash
pip install -e .
```

#### 3. 安装Camelot依赖（可选）

如果需要使用lattice方法，可能需要安装Ghostscript：

**macOS:**
```bash
brew install ghostscript
```

**Ubuntu:**
```bash
apt install ghostscript
```

## 环境变量配置

应用支持以下环境变量配置：

| 环境变量 | 说明 | 默认值 | 示例 |
|---------|------|--------|------|
| `FLASK_HOST` | 服务监听的主机地址 | `0.0.0.0` | `0.0.0.0` |
| `FLASK_PORT` | 服务监听的端口 | `5001` | `5001` |
| `FLASK_DEBUG` | 是否启用调试模式 | `False` | `true` 或 `false` |

**注意：** 所有上传的文件在处理完成后会自动删除，不会保留在服务器上。

## 运行说明

### 启动服务

```bash
python -m src.app.main
```

或使用环境变量：

```bash
FLASK_PORT=8080 FLASK_DEBUG=false python -m src.app.main
```

服务将在 `http://localhost:5001` 启动（或您配置的端口）。

### 在线API文档 (Swagger)

启动服务后，访问以下地址查看完整的Swagger API文档：

```
http://localhost:5001/docs
```

Swagger文档提供：
- 交互式API测试界面
- 完整的API端点说明
- 请求/响应Schema定义
- 在线测试功能
- OpenAPI规范导出

### API使用

#### 1. 健康检查

```bash
GET /health
```

#### 2. 解析课程表

```bash
POST /api/timetable/parse
Content-Type: multipart/form-data
```

**请求参数：**
- `file`: PDF文件

**响应示例：**
```json
{
  "success": true,
  "message": "解析成功",
  "data": {
    "classes": [
      {
        "class_name": "初三.1班",
        "schedule": {
          "monday": [
            {
              "period": 1,
              "course": "英语",
              "teacher": "陈小华",
              "is_class_teacher": true
            }
          ],
          "tuesday": [],
          "wednesday": [],
          "thursday": [],
          "friday": []
        }
      }
    ]
  },
  "statistics": {
    "total_classes": 15,
    "total_periods": 540
  },
  "parsing_report": {
    "accuracy": 85.77,
    "whitespace": 12.4,
    "order": 1,
    "page": 1
  }
}
```

**使用curl测试：**
```bash
curl -X POST http://localhost:5001/api/timetable/parse \
  -F "file=@课表样例.pdf"
```

## 代码架构

```
src/app/
├── __init__.py          # 包初始化
├── main.py              # 应用入口
├── api.py               # Flask API路由
├── pdf_parser.py        # PDF转CSV模块
├── csv_parser.py        # CSV转JSON模块
└── models.py            # 数据模型定义
```

### 处理流程

```
接收PDF文件 → PDF转CSV → CSV转JSON → 返回JSON
```

### 模块说明

- **api.py**: 处理HTTP请求，接收文件上传，返回JSON响应
- **pdf_parser.py**: 使用Camelot提取PDF表格，转换为CSV
- **csv_parser.py**: 解析CSV文件，转换为结构化JSON数据
- **models.py**: 定义数据模型（Pydantic）

## 测试

运行函数测试：

```bash
python test_function.py
```

## 项目依赖

- Flask: Web框架
- flasgger: Swagger/OpenAPI文档生成
- camelot-py: PDF表格提取
- pandas: CSV数据处理
- pydantic: 数据验证

## 许可证

MIT License
