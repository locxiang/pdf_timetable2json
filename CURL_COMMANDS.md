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

## 健康检查

```bash
curl -X GET http://localhost:5001/health
```
