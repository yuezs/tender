# TOOLS.md - 本地工具配置

技能定义工具的 _如何工作_。这个文件是 _你的_ 具体信息——对你的设置独特的内容。

## 存储位置

- 文件存储：`storage/tender/`
- 知识库：`storage/knowledge/`

## 数据库配置

- MySQL：用于知识库存储
- 表：`knowledge_documents`, `knowledge_chunks`

## API 端点

- 后端 API：`http://127.0.0.1:8000`
- 前端：`http://127.0.0.1:3000`

## 文件格式

支持解析的格式：
- txt（纯文本）
- docx（Word 文档）
- pdf（预留，暂未支持）

## 环境变量

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=xxx
MYSQL_DATABASE=tender
```

---

添加任何能帮助你工作的内容。这是你的速查表。