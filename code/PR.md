📄 Agent4Science Dataset Builder — 需求文档
🧭 项目目标

构建一个自动化数据抓取 pipeline，从 Agent4Science 2025 网站与 OpenReview API v2 获取并整理完整论文数据集，包括：

投稿元数据（metadata）

论文 PDF

Review History（完整 JSON）

Supplementary Materials

Code（仅真实仓库）

标准化 dataset 目录结构

可复现的 Python 脚本（位于 code/）

所有输出文件必须放置在 downloads/ 目录。

📁 最终文件结构要求
downloads/
│
├── metadata.csv
│
├── pdfs/
│   └── {forum_id}.pdf
│
├── reviews/
│   └── {forum_id}.json
│
├── supplementary/
│   └── {forum_id}.{ext}        # zip / pdf / png / others （只保存一次）
│
└── code/
    └── {forum_id}/             # 仅存在真实 GitHub 仓库时

🔧 开发目录结构（必须遵守）
PAPER_REVIEWER/
│
├── code/
│   └── main.py                 # 所有 Python 代码
│
├── downloads/                  # 所有抓取结果（脚本自动创建）
│
└── paper_review/               # 现有虚拟环境（不要修改）

📌 功能需求说明
1. 抓取 submissions.html 中的表格数据

来源：
https://agents4science.stanford.edu/submissions.html

需提取：

字段	描述
forum_id	OpenReview ID，从 openreview 链接取得
title	论文标题
authors	作者字符串
status	Accepted / Rejected
primary_topic	表格内容
secondary_topic	表格内容
human_review_score	数值
ai_reviewer_1_score	数值
ai_reviewer_2_score	数值
ai_reviewer_3_score	数值
hypothesis_development_label	标签
openreview_link	指向 forum 的链接
supplementary_link	如有，OpenReview 附件
code_link	GitHub 或附件

保存为：

downloads/metadata.csv

2. 下载 PDF（OpenReview API v2）

步骤：

使用 openreview-py 官方 client：

import openreview

client = openreview.api.OpenReviewClient(
    baseurl="https://api2.openreview.net",
    username=os.getenv("OPENREVIEW_USERNAME"),
    password=os.getenv("OPENREVIEW_PASSWORD"),
)


获取所有 notes：

notes = client.get_all_notes(forum=forum_id, details="all")


找到 submission note：

pdf_id = note.content["pdf"]


下载 PDF：

GET https://api2.openreview.net/pdf/{pdf_id}


保存：

downloads/pdfs/{forum_id}.pdf

3. 下载 Review History（完整 JSON）

继续使用：

notes = client.get_all_notes(forum=forum_id, details="all")


每条 note 用：

note_json = note.to_json()


保存整个列表为：

downloads/reviews/{forum_id}.json


该文件包含：

submission note

meta-review

decision

human reviews

AI reviews

comments

edits

是完整的 review timeline。

4. 下载 Supplementary Materials

访问：

https://openreview.net/forum?id={forum_id}


用 BeautifulSoup 查找：

<a href="…attachment…">

href 或文本包含 "supp" 或 "Supplementary"

例如：

/attachment?id=XXXX&name=supplementary_material


下载一次即可，保存为：

downloads/supplementary/{forum_id}.{ext}


如果 supplementary.zip 与 code_link 指向的 zip 相同，则不要重复下载。

5. 下载 Code（仅真实仓库）
A. 如果 code_link 是 GitHub 仓库：
git clone <repo> downloads/code/{forum_id}

B. 如果 code_link 是 OpenReview ZIP：

不重复下载

supplementary 已保存即可

C. 如果无 code：

跳过

⚙️ 技术与实现要求

使用 openreview-py（API v2）

使用 pandas、requests、BeautifulSoup4、tqdm

网络请求间隔 0.3–1.0 秒

添加错误处理（某篇失败不能终止整个程序）

生成详细日志与处理统计

程序结束输出 summary：

Total papers processed: X
PDFs downloaded: X
Review histories saved: X
Supplementary files saved: X
GitHub repos cloned: X

🧪 脚本执行方式

脚本必须放在：

code/main.py


执行方式：

python code/main.py


在虚拟环境 paper_review 中运行。