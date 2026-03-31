# API 设计说明

## 一、基础约定

* 所有接口返回 JSON
* 所有错误返回统一格式：

```json
{
  "success": false,
  "message": "error message"
}
```

* 所有成功返回统一格式：

```json
{
  "success": true,
  "data": {}
}
```

---

## 二、健康检查

### GET /api/health

**用途：**

服务健康检查

**返回：**

```json
{
  "success": true,
  "data": {
    "status": "ok"
  }
}
```

---

## 三、招标文件相关

### 1. 上传招标文件

#### POST /api/tender/upload

**用途：**

上传招标文件

**form-data：**

* file
* source_type（upload / url，可先预留）
* source_url（可选）

**返回：**

```json
{
  "success": true,
  "data": {
    "file_id": "uuid",
    "file_name": "tender.docx"
  }
}
```

---

### 2. 解析招标文件

#### POST /api/tender/parse

**用途：**

解析招标文件并提取纯文本

**请求：**

```json
{
  "file_id": "uuid"
}
```

**返回：**

```json
{
  "success": true,
  "data": {
    "text": "..."
  }
}
```

---

### 3. 抽取核心字段

#### POST /api/tender/extract

**用途：**

抽取核心字段

**请求：**

```json
{
  "file_id": "uuid"
}
```

**返回：**

```json
{
  "success": true,
  "data": {
    "project_name": "",
    "tender_company": "",
    "budget": "",
    "deadline": "",
    "qualification_requirements": []
  }
}
```

---

### 4. 判断是否投标

#### POST /api/tender/judge

**用途：**

判断是否建议投标

**请求：**

```json
{
  "file_id": "uuid"
}
```

**返回：**

```json
{
  "success": true,
  "data": {
    "should_bid": true,
    "reason": "",
    "risks": []
  }
}
```

---

### 5. 生成标书初稿

#### POST /api/tender/generate

**用途：**

生成标书初稿

**请求：**

```json
{
  "file_id": "uuid"
}
```

**返回：**

```json
{
  "success": true,
  "data": {
    "company_intro": "",
    "project_cases": "",
    "implementation_plan": "",
    "business_response": ""
  }
}
```

---

## 四、知识库相关

### 1. 上传知识文档

#### POST /api/knowledge/documents/upload

**用途：**

上传知识文档

**form-data：**

* file
* title
* category
* tags
* industry

**返回：**

```json
{
  "success": true,
  "data": {
    "document_id": "uuid",
    "title": "公司介绍2026版",
    "category": "company_profile"
  }
}
```

---

### 2. 获取知识文档列表

#### GET /api/knowledge/documents

**用途：**

获取知识文档列表

**查询参数：**

* category
* status

**返回：**

```json
{
  "success": true,
  "data": {
    "items": []
  }
}
```

---

### 3. 查看知识文档详情

#### GET /api/knowledge/documents/{document_id}

**用途：**

查看知识文档详情

---

### 4. 文档解析与切块

#### POST /api/knowledge/documents/{document_id}/process

**用途：**

解析并切块

**返回：**

```json
{
  "success": true,
  "data": {
    "document_id": "uuid",
    "chunk_count": 8
  }
}
```

---

### 5. 知识检索

#### POST /api/knowledge/retrieve

**用途：**

检索知识片段

**请求：**

```json
{
  "category": "project_cases",
  "query": "智慧园区 项目经验",
  "tags": ["案例"],
  "industry": ["政务"],
  "limit": 5
}
```

**返回：**

```json
{
  "success": true,
  "data": {
    "chunks": [
      {
        "id": "uuid",
        "section_title": "项目成果",
        "content": "..."
      }
    ]
  }
}
```
