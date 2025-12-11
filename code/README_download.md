# Agents4Science 2025 论文批量下载工具
# Agents4Science 2025 Paper Batch Download Tool

一个用于批量下载 Agents4Science 2025 会议论文、评审历史和表格数据的自动化工具。

An automated tool for batch downloading Agents4Science 2025 conference papers, review histories, and table data.

## 📋 目录 / Table of Contents

- [功能特性](#功能特性--features)
- [快速开始](#快速开始--quick-start)
- [详细使用说明](#详细使用说明--detailed-usage)
- [数据格式](#数据格式--data-format)
- [输出结构](#输出结构--output-structure)
- [常见问题](#常见问题--faq)

## ✨ 功能特性 / Features

这个工具可以一次性下载 https://agents4science.stanford.edu/submissions.html 上的所有论文及其相关资源：

This tool can batch download all papers and related resources from https://agents4science.stanford.edu/submissions.html:

- ✅ **论文PDF** / Paper PDFs
- ✅ **评审历史** / Review histories（包含所有评审意见和评分）
- ✅ **代码链接** / Code link information（GitHub、代码仓库等）
- ✅ **论文元数据** / Paper metadata（标题、作者、摘要、关键词等）
- ✅ **表格数据** / Table data（Status、Primary Topic、Secondary Topic、Human Review、AI Reviewer 1/2/3、Hypothesis Development）

## 🚀 快速开始 / Quick Start

### 1. 安装依赖 / Installation

**使用虚拟环境（推荐）/ Use virtual environment (Recommended)**:

```bash
# Windows
cd code
code\paper_review\Scripts\activate
pip install -r requirements.txt

# Linux/Mac
cd code
source paper_review/bin/activate
pip install -r requirements.txt
```

**或直接安装 / Or install directly**:

```bash
pip install -r requirements.txt
```

### 2. 提取表格数据（推荐）/ Extract Table Data (Recommended)

由于网页使用 JavaScript 动态加载，需要先从浏览器提取表格数据：

Since the webpage uses JavaScript to dynamically load content, you need to extract table data from the browser first:

1. 打开 https://agents4science.stanford.edu/submissions.html
2. 按 `F12` 打开开发者工具，切换到 Console 标签
3. 复制 `code/extract_table_data.js` 中的脚本并运行
4. 将输出的 JSON 数据保存到 `downloads/table_data.json`

**详细步骤见下方 [提取表格数据](#提取表格数据--extract-table-data) 章节**

### 3. 运行下载脚本 / Run Download Script

```bash
# 在 code/ 文件夹中运行
cd code
python download_papers.py

# 或从项目根目录运行
python code/download_papers.py
```

## 📖 详细使用说明 / Detailed Usage

### 提取表格数据 / Extract Table Data

**为什么需要提取表格数据？/ Why extract table data?**

网页使用 JavaScript 动态加载内容，Python 的 `requests` 库无法直接获取动态内容。因此需要从浏览器中提取表格数据。

The webpage uses JavaScript to dynamically load content, so Python's `requests` library cannot directly get dynamic content. Therefore, we need to extract table data from the browser.

**步骤 / Steps**:

1. **打开网页** / Open webpage:
   - 访问 https://agents4science.stanford.edu/submissions.html
   - 等待页面完全加载（确保所有论文都显示在表格中）

2. **打开开发者工具** / Open developer tools:
   - 按 `F12` 或右键选择"检查" / Press `F12` or right-click "Inspect"
   - 切换到 **Console（控制台）** 标签 / Switch to **Console** tab

3. **运行提取脚本** / Run extraction script:
   - 打开 `code/extract_table_data.js` 文件
   - 复制全部内容
   - 粘贴到浏览器控制台并按 `Enter`

4. **保存数据** / Save data:
   - 脚本会自动将 JSON 数据复制到剪贴板
   - 创建 `downloads/table_data.json` 文件
   - 将剪贴板内容粘贴到文件中并保存

**数据格式示例 / Data Format Example**:

```json
{
  "7MPstNz66e": {
    "title": "BadScientist: Can a Research Agent Write Convincing but Unsound Papers that Fool LLM Reviewers?",
    "status": "Accepted",
    "primary_topic": "Computer & Data Sciences",
    "secondary_topic": "Artificial Intelligence & Machine Learning",
    "human_review": "5",
    "ai_reviewer_1": "3",
    "ai_reviewer_2": "6",
    "ai_reviewer_3": "5",
    "hypothesis_development": "B"
  },
  "G5jK2OMT2q": {
    "title": "Co-Alignment: Rethinking Alignment as Bidirectional Human-AI Cognitive Adaptation",
    "status": "Accepted",
    "primary_topic": "Computer & Data Sciences",
    "secondary_topic": "Human-Computer Interaction",
    "human_review": "5",
    "ai_reviewer_1": "3",
    "ai_reviewer_2": "6",
    "ai_reviewer_3": "3",
    "hypothesis_development": "B"
  }
}
```

**表格数据字段说明 / Table Data Fields**:

- `title`: 论文标题
- `status`: 论文状态（Accepted/Rejected）
- `primary_topic`: 主要研究主题
- `secondary_topic`: 次要研究主题
- `human_review`: 人工评审分数（1-6）
- `ai_reviewer_1`, `ai_reviewer_2`, `ai_reviewer_3`: 三个 AI 评审员的分数（1-6）
- `hypothesis_development`: 假设发展评分（A/B/C）

### 运行下载脚本 / Run Download Script

脚本会按以下优先级获取 forum IDs：

The script will get forum IDs in the following priority order:

1. **优先** / **Priority**: 从 `downloads/table_data.json` 读取（推荐，包含所有 forum ID 和表格数据）
2. **备用** / **Alternative**: 尝试从网页或 API 提取 forum IDs（不推荐，无法获取表格数据）

**运行示例 / Run Example**:

```bash
cd code
python download_papers.py
```

**输出示例 / Output Example**:

```
============================================================
🚀 Agents4Science 2025 论文批量下载工具
🚀 Agents4Science 2025 Paper Batch Download Tool
============================================================
✅ 从 table_data.json 读取到 247 个 forum ID / Read 247 forum IDs from table_data.json
✅ 加载了 247 条表格数据 / Loaded 247 table data entries

[1/247] 处理论文ID / Processing paper ID: 7MPstNz66e
📄 处理论文 / Processing: BadScientist: Can a Research Agent...
  📥 下载PDF... / Downloading PDF...
  ✓ 包含表格数据 / Includes table data
  ✓ 保存了 3 条review / Saved 3 reviews
...
```

## 📁 输出结构 / Output Structure

下载完成后，所有数据将保存在 `downloads/` 目录中：

After downloading, all data will be saved in the `downloads/` directory:

```
downloads/
├── papers/                          # 论文PDF和完整数据
│   └── {forum_id}_{title}/          # 每篇论文一个文件夹
│       ├── {forum_id}.pdf           # 论文PDF
│       └── {forum_id}_complete.json # 完整的OpenReview数据
│
├── reviews/                         # 评审历史
│   └── {forum_id}_reviews.json      # 每篇论文的所有评审
│
├── code/                            # 代码链接信息
│   └── {forum_id}_code_info.json    # 代码仓库链接等
│
├── metadata/                        # 论文元数据（包含表格数据）
│   └── {forum_id}_metadata.json     # 元数据（标题、作者、摘要、表格数据等）
│
└── table_data.json                  # 表格数据（包含所有forum_id和表格信息）
```

**重要说明 / Important Notes**:

- `downloads/` 文件夹位于**项目根目录**（不在 `code/` 文件夹内）
- `downloads/` folder is in the **project root** (not inside `code/` folder)
- 代码在 `code/` 文件夹中运行
- Code runs in `code/` folder

## 📊 数据格式 / Data Format

### 元数据文件格式 / Metadata File Format

`downloads/metadata/{forum_id}_metadata.json`:

```json
{
  "forum_id": "7MPstNz66e",
  "title": "BadScientist: Can a Research Agent...",
  "authors": ["Author 1", "Author 2"],
  "abstract": "Paper abstract...",
  "keywords": ["keyword1", "keyword2"],
  "openreview_url": "https://openreview.net/forum?id=7MPstNz66e",
  "created": "2025-01-01T00:00:00.000Z",
  "status": "Accepted",
  "primary_topic": "Computer & Data Sciences",
  "secondary_topic": "Artificial Intelligence & Machine Learning",
  "human_review": "5",
  "ai_reviewer_1": "3",
  "ai_reviewer_2": "6",
  "ai_reviewer_3": "5",
  "hypothesis_development": "B"
}
```

### 评审文件格式 / Review File Format

`downloads/reviews/{forum_id}_reviews.json`:

```json
[
  {
    "review_id": "review_id_1",
    "content": {
      "summary": "Review summary...",
      "strengths": "...",
      "weaknesses": "..."
    },
    "rating": "5",
    "confidence": "4",
    "created": "2025-01-01T00:00:00.000Z"
  }
]
```

## ⚙️ 配置说明 / Configuration

### 脚本行为 / Script Behavior

- **请求延迟** / **Request Delay**: 每次请求之间延迟 1 秒，避免请求过快
- **自动重试** / **Auto Retry**: 网络错误时自动重试 3 次
- **跳过已存在** / **Skip Existing**: 如果文件已存在，会跳过下载（PDF 会检查是否存在）

### 自定义配置 / Custom Configuration

可以在 `download_papers.py` 中修改以下配置：

You can modify the following configurations in `download_papers.py`:

```python
# 修改下载目录
BASE_DIR = Path("your_custom_downloads_folder")

# 修改请求延迟（秒）
time.sleep(2)  # 改为 2 秒延迟
```

## ❓ 常见问题 / FAQ

### Q1: 为什么需要提取表格数据？/ Why do I need to extract table data?

**A**: 网页使用 JavaScript 动态加载内容，Python 的 `requests` 库无法直接获取。从浏览器提取是最可靠的方法。

**A**: The webpage uses JavaScript to dynamically load content, so Python's `requests` library cannot directly get it. Extracting from the browser is the most reliable method.

### Q2: 如果没有表格数据可以下载吗？/ Can I download without table data?

**A**: 可以，但不推荐。如果没有 `table_data.json`，脚本会尝试从网页/API 提取 forum IDs。但表格数据（status、topics、scores 等）将无法获取。建议先运行 `extract_table_data.js` 提取表格数据。

**A**: Yes, but not recommended. If there's no `table_data.json`, the script will try to extract forum IDs from the webpage/API. However, table data (status, topics, scores, etc.) will not be available. It's recommended to run `extract_table_data.js` first to extract table data.

### Q3: 下载中断了怎么办？/ What if download is interrupted?

**A**: 重新运行脚本即可。脚本会跳过已存在的文件，只下载缺失的部分。

**A**: Just run the script again. The script will skip existing files and only download missing parts.

### Q4: 如何只下载特定论文？/ How to download specific papers only?

**A**: 编辑 `downloads/table_data.json`，只保留需要的 forum ID 条目。脚本会自动从该文件读取 forum IDs。

**A**: Edit `downloads/table_data.json`, keeping only the forum ID entries you need. The script will automatically read forum IDs from this file.

### Q5: 遇到网络错误怎么办？/ What if I encounter network errors?

**A**: 脚本会自动重试 3 次。如果仍然失败，会在最后显示失败列表。可以稍后重新运行脚本。

**A**: The script will automatically retry 3 times. If it still fails, it will show a failure list at the end. You can run the script again later.

## 🔧 故障排除 / Troubleshooting

### 问题：无法连接到 OpenReview API

**解决方案** / **Solution**:
- 检查网络连接
- 确认 OpenReview API 是否可访问
- 尝试使用 VPN（如果在某些地区）

### 问题：提取表格数据时控制台报错

**解决方案** / **Solution**:
- 确保页面完全加载（等待所有论文显示）
- 刷新页面后重试
- 检查浏览器控制台是否有其他错误

### 问题：下载的 PDF 文件损坏

**解决方案** / **Solution**:
- 删除损坏的文件，重新运行脚本
- 检查磁盘空间是否充足
- 检查网络连接是否稳定

## 📝 更新日志 / Changelog

### v1.0.0 (Latest)
- ✅ 支持批量下载论文 PDF
- ✅ 支持提取和保存评审历史
- ✅ 支持提取表格数据（Status、Topics、Scores 等）
- ✅ 支持代码链接提取
- ✅ 自动重试机制
- ✅ 智能跳过已下载文件

## 📄 许可证 / License

本项目仅供学习和研究使用。

This project is for learning and research purposes only.

## 🤝 贡献 / Contributing

欢迎提交 Issue 和 Pull Request！

Issues and Pull Requests are welcome!

---

**Happy Downloading! 🎉**
