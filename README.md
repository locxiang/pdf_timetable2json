# PDF课程表转JSON API

将PDF格式的课程表转换为结构化JSON数据的Flask API服务。

## 功能说明

- 📄 接收PDF文件上传
- 🔄 自动提取PDF表格并转换为CSV
- 📊 解析CSV并转换为结构化的JSON数据
- ✅ 返回清晰的JSON数据结构

## 安装说明

### 1. 创建conda环境

```bash
conda env create -f environment.yml
conda activate pdf_timetable2json
```

### 2. 安装项目依赖

```bash
pip install -e .
```

### 3. 安装Camelot依赖（可选）

如果需要使用lattice方法，可能需要安装Ghostscript：

**macOS:**
```bash
brew install ghostscript
```

**Ubuntu:**
```bash
apt install ghostscript
```

## 运行说明

### 启动服务

```bash
python -m src.app.main
```

服务将在 `http://localhost:5001` 启动。

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
            }
          ]
        }
      }
    ]
  },
  "统计": {
    "班级数": 15,
    "总课时数": 540
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
- camelot-py: PDF表格提取
- pandas: CSV数据处理
- pydantic: 数据验证

## 许可证

MIT License
