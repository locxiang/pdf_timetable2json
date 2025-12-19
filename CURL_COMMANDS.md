# Curl测试命令

## 最简单的命令（一行）

```bash
curl -X POST http://localhost:5001/api/timetable/parse -F "file=@课表样例.pdf"
```

## 格式化输出（推荐，显示中文）

```bash
curl -X POST http://localhost:5001/api/timetable/parse -F "file=@课表样例.pdf" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=2))"
```

## 只查看关键信息

```bash
curl -X POST http://localhost:5001/api/timetable/parse -F "file=@课表样例.pdf" | python3 -c "import sys, json; d=json.load(sys.stdin); print('成功:', d['成功']); print('消息:', d['消息']); print('统计:', d['统计'])"
```

## 保存到文件

```bash
curl -X POST http://localhost:5001/api/timetable/parse -F "file=@课表样例.pdf" -o response.json
```

## PDF转CSV接口

### 下载CSV文件（推荐，直接保存）

```bash
curl -X POST http://localhost:5001/api/pdf/to-csv -F "file=@课表样例.pdf" -o output_table.csv
```

### 查看CSV内容（不保存文件）

```bash
curl -X POST http://localhost:5001/api/pdf/to-csv -F "file=@课表样例.pdf"
```

### 指定输出文件名

```bash
curl -X POST http://localhost:5001/api/pdf/to-csv -F "file=@课表样例.pdf" -o "我的课表.csv"
```

### 显示下载进度

```bash
curl -X POST http://localhost:5001/api/pdf/to-csv -F "file=@课表样例.pdf" -o output_table.csv --progress-bar
```

## 健康检查

```bash
curl -X GET http://localhost:5001/health
```
