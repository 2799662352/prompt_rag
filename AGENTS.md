# AGENTS

## Project: PromptRAG - 提示词检索增强生成系统

### 概述

一个完整的流程，用于下载、处理网页内容并创建提示词的向量嵌入索引。
通过 ChromaDB MCP Server 在 AI IDE 中提供向量检索功能。

### 工作流

1. `downloader.py` - 下载网页内容
2. `page_curator.py` - 清理 HTML 转为 Markdown
3. `chunker.py` - 文本分块
4. `vectorizer.py` - 生成向量嵌入
5. `chroma_mcp_server_minimal.py` - MCP 检索服务

### MCP 工具

| 工具 | 功能 |
|------|------|
| `query` | 向量相似度查询（支持艺术家分析工作流） |
| `batch_query` | 批量向量查询 |
| `remember` | 存储记忆到向量数据库 |
| `search_memory` | 搜索用户记忆 |
| `list_collections` | 列出所有集合 |
| `get_performance_stats` | 性能统计信息 |

### 嵌入后端

- **local**: 本地 GPU/CPU 推理（sentence-transformers）
- **jina-api**: Jina Cloud API（jina-embeddings-v3）

### 开发规范

- Python 3.8+，遵循 PEP 8
- 使用 type hints 标注
- 错误返回格式: `{"success": False, "error": "..."}`
- 使用 logging 模块记录日志
