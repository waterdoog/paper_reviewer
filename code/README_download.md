# Agents4Science 2025 论文批量下载工具
# Agents4Science 2025 Paper Batch Download Tool

## 功能 / Features

这个脚本可以一次性下载 https://agents4science.stanford.edu/submissions.html 上的所有论文及其相关资源：

This script can batch download all papers and related resources from https://agents4science.stanford.edu/submissions.html:

- ✅ 论文PDF / Paper PDFs
- ✅ Review histories（评审历史）/ Review histories
- ✅ 代码链接信息 / Code link information
- ✅ 论文元数据（标题、作者、摘要等）/ Paper metadata (title, authors, abstract, etc.)
- ✅ **表格数据**（Status、Primary Topic、Secondary Topic、Human Review、AI Reviewer 1/2/3、Hypothesis Development）/ **Table data** (Status, Primary Topic, Secondary Topic, Human Review, AI Reviewer 1/2/3, Hypothesis Development)

## 安装依赖 / Installation

**使用虚拟环境 / Use virtual environment** (推荐 / Recommended):

```bash
# 激活虚拟环境 / Activate virtual environment
# Windows:
code\paper_review\Scripts\activate
# Linux/Mac:
source code/paper_review/bin/activate

# 安装依赖 / Install dependencies
pip install -r requirements.txt
```

**或者直接安装 / Or install directly**:

```bash
pip install -r requirements.txt
```

## 使用方法 / Usage

**在 `code/` 文件夹中运行 / Run in `code/` folder**:

```bash
cd code
python download_papers.py
```

**或者从项目根目录运行 / Or run from project root**:

```bash
python code/download_papers.py
```

脚本会自动：
The script will automatically:

1. 从网页提取所有论文的 OpenReview forum ID
   Extract all paper OpenReview forum IDs from the webpage
2. 使用 OpenReview API 获取每篇论文的详细信息
   Use OpenReview API to get detailed information for each paper
3. 下载论文PDF、保存reviews和元数据
   Download paper PDFs, save reviews and metadata
4. 将所有数据保存到 `downloads/` 目录
   Save all data to `downloads/` directory

## 输出目录结构 / Output Directory Structure

```
downloads/
├── papers/              # 论文PDF和完整数据 / Paper PDFs and complete data
│   └── {forum_id}_{title}/
│       ├── {forum_id}.pdf
│       └── {forum_id}_complete.json
├── reviews/             # Review histories / 评审历史
│   └── {forum_id}_reviews.json
├── code/                # 代码链接信息 / Code link information
│   └── {forum_id}_code_info.json
├── metadata/            # 论文元数据（包含表格数据）/ Paper metadata (including table data)
│   └── {forum_id}_metadata.json
├── forum_ids.txt        # 所有论文的forum ID列表（备份，从table_data.json自动生成）/ List of all paper forum IDs (backup, auto-generated from table_data.json)
└── table_data.json      # 表格数据（推荐，包含forum_id和对应表格信息）/ Table data (recommended, contains forum_id and corresponding table info)
```

**注意 / Note**: 
- `downloads/` 文件夹在项目根目录（不在 `code/` 文件夹内）
- `downloads/` folder is in project root (not inside `code/` folder)
- 代码在 `code/` 文件夹中运行
- Code runs in `code/` folder

## 注意事项 / Notes

- 脚本会在请求之间添加1秒延迟，以避免请求过快
  The script adds a 1-second delay between requests to avoid too many requests
- 如果文件已存在，会跳过下载（PDF除外，会检查是否存在）
  If files already exist, they will be skipped (except PDFs, which are checked)
- 所有数据都会保存为JSON格式，便于后续处理
  All data is saved in JSON format for easy processing

## 提取表格数据 / Extract Table Data

**重要 / Important**: 
网页使用 JavaScript 动态加载内容，表格数据需要从浏览器中提取。
The webpage uses JavaScript to dynamically load content, so table data needs to be extracted from the browser.

**数据格式 / Data Format**:
`table_data.json` 文件格式为：每个 forum_id 作为 key，包含对应的表格信息
`table_data.json` file format: each forum_id as key, containing corresponding table information

```json
{
  "7MPstNz66e": {
    "title": "BadScientist: Can a Research Agent...",
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
    ...
  }
}
```

**提取表格数据的步骤 / Steps to extract table data**:

1. 打开 https://agents4science.stanford.edu/submissions.html
   Open https://agents4science.stanford.edu/submissions.html

2. 按 F12 打开浏览器开发者工具
   Press F12 to open browser developer tools

3. 切换到 Console（控制台）标签
   Switch to Console tab

4. 复制并运行 `code/extract_table_data.js` 中的脚本
   Copy and run the script from `code/extract_table_data.js`

5. 脚本会自动将 JSON 数据复制到剪贴板（格式：{forum_id: {title, status, ...}}）
   The script will automatically copy JSON data to clipboard (format: {forum_id: {title, status, ...}})

6. 将内容保存到 `downloads/table_data.json` 文件
   Save the content to `downloads/table_data.json` file

7. 运行下载脚本时：
   When running the download script:
   - 脚本会优先从 `table_data.json` 读取 forum IDs
     The script will prioritize reading forum IDs from `table_data.json`
   - 表格数据会自动合并到每篇论文的元数据中
     Table data will be automatically merged into each paper's metadata

**表格数据包含的字段 / Table data includes**:
- `title`: 论文标题
- `status`: Accepted/Rejected
- `primary_topic`: 主要主题
- `secondary_topic`: 次要主题
- `human_review`: 人工评审分数
- `ai_reviewer_1`, `ai_reviewer_2`, `ai_reviewer_3`: AI 评审分数
- `hypothesis_development`: 假设发展评分

## 关于网页提取 / About Web Extraction

**问题 / Issue**: 
网页使用 JavaScript 动态加载内容，直接用 `requests` 可能无法提取到链接。
The webpage uses JavaScript to dynamically load content, so `requests` may not be able to extract links directly.

**解决方案 / Solution**:
1. ✅ **推荐方式**: 使用 `extract_table_data.js` 提取表格数据，会自动包含所有 forum ID
   **Recommended**: Use `extract_table_data.js` to extract table data, which automatically includes all forum IDs
   - 运行脚本后，将结果保存到 `downloads/table_data.json`
     After running the script, save the result to `downloads/table_data.json`
   - 脚本会自动从该文件读取 forum IDs
     The script will automatically read forum IDs from this file

2. **备用方式**: 如果只有 forum IDs，可以：
   **Alternative**: If you only have forum IDs, you can:
   - 手动创建 `downloads/forum_ids.txt`（每行一个 forum ID）
     Manually create `downloads/forum_ids.txt` (one forum ID per line)
   - 脚本会从该文件读取 forum IDs
     The script will read forum IDs from this file

## 故障排除 / Troubleshooting

如果遇到网络错误，脚本会自动重试3次
If you encounter network errors, the script will automatically retry 3 times

如果某些论文无法下载，会在最后显示成功和失败的数量
If some papers cannot be downloaded, the success and failure counts will be shown at the end

