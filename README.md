# 伟大的主体PromptRAG系统

一个完整的流程，用于下载、处理网页内容并创建提示词的向量嵌入索引。该系统能以革命性的方式将普通网页内容转化为向量嵌入，并以先进的RAG(检索增强生成)技术提供提示词查询功能！

## 功能特性

- **强大的网页下载器**：高效下载指定网站内容
- **精确的内容分块系统**：以科学方式将文本分成最优块
- **高性能向量化引擎**：生成先进、纯粹的文本嵌入表示
- **优质提示词检索器**：使用向量相似度技术寻找相关提示词
- **直观的嵌入可视化**：在2D/3D空间中查看嵌入分布

## 快速开始

### 安装

克隆仓库并安装依赖：

```bash
git clone https://github.com/2799662352/prompt_rag.git
cd prompt_rag
pip install -r requirements.txt
```

### 基本使用流程

1. 在`websites_to_download.txt`中添加要下载的网站URL
2. 下载网页内容：
   ```bash
   python downloader.py
   ```
3. 处理和整理内容：
   ```bash
   python page_curator.py --input artifacts/downloaded_sites/your-domain-name
   ```
4. 将内容分块：
   ```bash
   python chunker.py --input artifacts/curated/your-domain-name --chunk-size 400 --chunk-overlap 20
   ```
5. 生成向量嵌入：
   ```bash
   python vectorizer.py --input artifacts/chunks/your-domain-name_chunks_SZ_400_O_20.jsonl
   ```
6. 启动提示词检索服务器：
   ```bash
   python ../rag-mcp/prompt_server.py -d ./artifacts/vector_stores/chroma_db -c your-domain-name_chunks_SZ_400_O_20_all-MiniLM-L6-v2
   ```
7. （可选）可视化嵌入：
   ```bash
   python visualizer.py --collection your-domain-name_chunks_SZ_400_O_20_all-MiniLM-L6-v2
   ```

## 项目结构

```
prompt_rag/
├── artifacts/         # 所有生成文件的目录
│   ├── chunks/        # 处理后的文本块
│   ├── curated/       # 整理后的文本文件
│   ├── downloaded_sites/ # 下载的原始HTML
│   ├── vector_stores/ # 向量数据库
│   └── visualizations/ # 嵌入可视化结果
├── chunker.py         # 文本分块处理器
├── downloader.py      # 网页下载工具
├── page_curator.py    # 内容整理工具
├── requirements.txt   # 项目依赖清单
├── txt_to_markdown.py # 文本转Markdown工具
├── vectorizer.py      # 向量嵌入生成器
├── visualizer.py      # 嵌入可视化工具
└── websites_to_download.txt # 要下载的网站列表
```

## 详细工作流程

### 1. 下载网页内容

从`websites_to_download.txt`中列出的网站下载HTML内容：

```bash
python downloader.py --delay 1.0
```

选项：
- `--delay` / `-d`: 请求之间的延迟（秒）（默认：1.0）

### 2. 整理内容

清理HTML并转换为markdown格式：

```bash
python page_curator.py --input artifacts/downloaded_sites/your-domain-name
```

选项：
- `--input` / `-i`: 包含下载HTML的输入目录

### 3. 创建文本块

将markdown文件分割成可管理的块：

```bash
python chunker.py --input artifacts/curated/your-domain-name --chunk-size 400 --chunk-overlap 20
```

选项：
- `--input` / `-i`: 包含markdown文件的输入目录
- `--chunk-size` / `-s`: 块的最大字符大小（默认：400）
- `--chunk-overlap` / `-v`: 块之间的重叠字符数（默认：20）

### 4. 创建向量嵌入

生成嵌入并存储在ChromaDB中：

```bash
python vectorizer.py --input artifacts/chunks/your-domain-name_chunks_SZ_400_O_20.jsonl
```

选项：
- `--input` / `-i`: 包含文本块的JSONL文件
- `--db` / `-d`: ChromaDB向量数据库目录（默认：artifacts/vector_stores/chroma_db）
- `--model` / `-m`: 使用的sentence-transformer模型名称（默认：sentence-transformers/all-MiniLM-L6-v2）
- `--batch-size` / `-b`: 嵌入生成的批处理大小（默认：32）

- 懒得找预料就直接百度云启动  通过网盘分享的文件：artifacts
链接: https://pan.baidu.com/s/1et5TwKCCwmvoeAXd6e1ojw?pwd=f1jf 提取码: f1jf 
--来自百度网盘超级会员v1的分享****

### 5. 启动提示词检索服务器

使用MCP协议提供提示词检索功能：

```bash
python ../rag-mcp/prompt_server.py -d ./artifacts/vector_stores/chroma_db -c your-domain-name_chunks_SZ_400_O_20_all-MiniLM-L6-v2
```

选项：
- `--chromadb-path` / `-d`: ChromaDB数据库的路径
- `--collection-name` / `-c`: ChromaDB中的集合名称

### 6. 可视化嵌入（可选）

创建嵌入的交互式2D/3D可视化：

```bash
python visualizer.py --collection your-domain-name_chunks_SZ_400_O_20_all-MiniLM-L6-v2
```

选项：
- `--db` / `-d`: ChromaDB数据库目录（默认：artifacts/vector_stores/chroma_db）
- `--collection` / `-c`: ChromaDB中的集合名称
- `--max-points` / `-m`: 要可视化的最大点数（默认：2000）
- `--seed` / `-s`: 随机种子（默认：42）
- `--clusters` / `-k`: 聚类数量（默认：10）

## 技术栈

该项目使用了以下技术：

- **Python**: 主要编程语言
- **ChromaDB**: 高性能向量数据库
- **Sentence Transformers**: 先进的文本嵌入模型
- **UMAP**: 用于降维和可视化
- **BeautifulSoup**: HTML内容解析和清理
- **LangChain**: 文本分块和处理
- **Plotly**: 交互式2D/3D可视化

## 注意事项

- `.gitignore`设置为排除artifacts目录，以避免提交大型文件。
- 对于大型网站，建议在`downloader.py`中调整延迟以避免速率限制。
- 大型集合的向量嵌入可能需要较大内存。
- 集合名称会自动保存在artifacts/vector_stores/collections.txt中，便于后续使用。

## 许可证

MIT许可 
