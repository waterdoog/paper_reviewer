"""
批量下载 Agents4Science 2025 会议的所有论文、review histories 和代码
Batch download all papers, review histories, and code from Agents4Science 2025 conference
"""

import openreview
import requests
import os
import json
import re
import csv
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import time

# 配置 / Configuration
# 代码在code文件夹运行，downloads在父目录（根目录）
# Code runs in code folder, downloads in parent directory (root)
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent / "downloads"
PAPERS_DIR = BASE_DIR / "papers"
REVIEWS_DIR = BASE_DIR / "reviews"
CODE_DIR = BASE_DIR / "code"
METADATA_DIR = BASE_DIR / "metadata"

# 创建目录 / Create directories
for dir_path in [PAPERS_DIR, REVIEWS_DIR, CODE_DIR, METADATA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 初始化 OpenReview 客户端 / Initialize OpenReview client
client = openreview.api.OpenReviewClient(
    baseurl="https://api2.openreview.net"
)

def extract_table_data_from_page(url):
    """
    从网页提取表格数据（包括forum ID和表格中的所有信息）
    Extract table data from webpage (including forum IDs and all table information)
    返回: dict {forum_id: {status, primary_topic, secondary_topic, human_review, ai_reviewer_1, ai_reviewer_2, ai_reviewer_3, hypothesis_development}}
    Returns: dict {forum_id: {status, primary_topic, secondary_topic, human_review, ai_reviewer_1, ai_reviewer_2, ai_reviewer_3, hypothesis_development}}
    """
    print(f"📄 正在从网页提取表格数据... / Extracting table data from webpage...")
    try:
        # 设置 User-Agent 模拟浏览器
        # Set User-Agent to simulate browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        table_data = {}
        
        # 提取所有包含openreview链接的行，并尝试提取对应的表格数据
        # Extract all rows containing openreview links and try to extract corresponding table data
        # 使用正则表达式匹配表格行和forum ID
        # Use regex to match table rows and forum IDs
        
        # 匹配包含forum ID的链接
        # Match links containing forum IDs
        link_pattern = r'openreview\.net/forum\?id=([a-zA-Z0-9]+)'
        forum_ids = list(set(re.findall(link_pattern, response.text)))
        
        # 对于每个forum ID，尝试提取同一行或附近行的表格数据
        # For each forum ID, try to extract table data from the same row or nearby rows
        # 由于网页是动态加载的，我们使用一个简化的方法：提取所有可能的数据模式
        # Since the webpage is dynamically loaded, we use a simplified approach: extract all possible data patterns
        
        # 尝试提取Status（Accepted/Rejected）
        # Try to extract Status (Accepted/Rejected)
        status_pattern = r'(Accepted|Rejected)'
        
        # 尝试提取Primary Topic和Secondary Topic
        # Try to extract Primary Topic and Secondary Topic
        topic_patterns = [
            r'Computer & Data Sciences',
            r'Life & Health Sciences',
            r'Natural Sciences',
            r'Engineering & Technology',
            r'Social Sciences',
            r'Artificial Intelligence & Machine Learning',
            r'Human-Computer Interaction',
            # 可以添加更多主题
            # Can add more topics
        ]
        
        print(f"✅ 找到 {len(forum_ids)} 个forum ID / Found {len(forum_ids)} forum IDs")
        print("⚠️  注意：表格数据需要JavaScript渲染，将从已保存的数据中读取 / Note: Table data requires JavaScript rendering, will read from saved data")
        
        return forum_ids, table_data
    except Exception as e:
        print(f"❌ 从网页提取失败 / Failed to extract from webpage: {e}")
        return [], {}

def extract_forum_ids_from_page(url):
    """
    从网页提取所有论文的 forum ID（简化版，主要用于获取ID列表）
    Extract all paper forum IDs from the webpage (simplified version, mainly for getting ID list)
    """
    forum_ids, _ = extract_table_data_from_page(url)
    return forum_ids

def get_all_papers_from_api(invitation_pattern=None):
    """
    通过OpenReview API获取所有论文（如果知道invitation pattern）
    Get all papers via OpenReview API (if invitation pattern is known)
    """
    print(f"📡 正在通过API获取所有论文... / Getting all papers via API...")
    try:
        # 尝试获取所有submission notes
        # Try to get all submission notes
        # 注意：需要知道具体的invitation pattern
        # Note: Need to know the specific invitation pattern
        
        # Agents4Science 2025 可能的invitation格式
        # Possible invitation format for Agents4Science 2025
        possible_invitations = [
            "Agents4Science.stanford.edu/2025/Conference/-/Submission",
            "Agents4Science.stanford.edu/2025/-/Submission",
            "Agents4Science/2025/Conference/-/Submission",
        ]
        
        for invitation in possible_invitations:
            try:
                notes = client.get_all_notes(
                    invitation=invitation,
                    details="all",
                    limit=10000
                )
                
                if notes and len(notes) > 0:
                    forum_ids = [note.forum for note in notes if hasattr(note, 'forum')]
                    forum_ids = list(set(forum_ids))
                    print(f"✅ 通过API找到 {len(forum_ids)} 篇论文 / Found {len(forum_ids)} papers via API")
                    return forum_ids
            except:
                continue
        
        print("⚠️  API方法未找到论文，将使用网页提取方法 / API method found no papers, will use webpage extraction")
        return []
    except Exception as e:
        print(f"⚠️  API方法失败 / API method failed: {e}")
        print("将使用网页提取方法 / Will use webpage extraction method")
        return []

def download_file(url, filepath, max_retries=3):
    """
    下载文件，带重试机制
    Download file with retry mechanism
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  ⚠️  重试 {attempt + 1}/{max_retries}... / Retry {attempt + 1}/{max_retries}...")
                time.sleep(2)
            else:
                print(f"  ❌ 下载失败 / Download failed: {e}")
                return False
    return False

def get_paper_details(forum_id):
    """
    获取论文的详细信息
    Get detailed information about a paper
    """
    try:
        # 获取论文主note
        # Get main paper note
        notes = client.get_notes(forum=forum_id, details="all", limit=1000)
        
        if not notes:
            return None
        
        main_note = notes[0]  # 第一个是主论文 / First one is the main paper
        
        # 获取所有reviews
        # Get all reviews
        reviews = [note for note in notes if 'Review' in note.invitation or 'review' in note.invitation.lower()]
        
        # 获取所有代码附件
        # Get all code attachments
        code_attachments = []
        if hasattr(main_note, 'content') and main_note.content:
            for key, value in main_note.content.items():
                if isinstance(value, str) and ('code' in key.lower() or 'github' in value.lower() or 'git' in value.lower()):
                    code_attachments.append({'key': key, 'value': value})
        
        return {
            'main_note': main_note,
            'reviews': reviews,
            'code_attachments': code_attachments,
            'all_notes': notes
        }
    except Exception as e:
        print(f"  ❌ 获取论文详情失败 / Failed to get paper details: {e}")
        return None

def load_table_data():
    """
    从保存的表格数据文件加载表格信息（支持 CSV 格式）
    Load table data from saved table data file (supports CSV format)
    格式: {forum_id: {title, status, primary_topic, ...}}
    Format: {forum_id: {title, status, primary_topic, ...}}
    """
    # 优先尝试 CSV 格式
    # Priority: try CSV format
    table_data_path_csv = BASE_DIR / "table_data.csv"
    if table_data_path_csv.exists():
        try:
            table_data = {}
            with open(table_data_path_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    forum_id = row.get('forum_id', '').strip()
                    if forum_id:
                        table_data[forum_id] = {
                            'title': row.get('title', '').strip(),
                            'status': row.get('status', '').strip(),
                            'primary_topic': row.get('primary_topic', '').strip(),
                            'secondary_topic': row.get('secondary_topic', '').strip(),
                            'human_review': row.get('human_review', '').strip(),
                            'ai_reviewer_1': row.get('ai_reviewer_1', '').strip(),
                            'ai_reviewer_2': row.get('ai_reviewer_2', '').strip(),
                            'ai_reviewer_3': row.get('ai_reviewer_3', '').strip(),
                            'hypothesis_development': row.get('hypothesis_development', '').strip(),
                        }
            if table_data:
                return table_data
        except Exception as e:
            print(f"⚠️  加载 CSV 表格数据失败 / Failed to load CSV table data: {e}")
    
    # 备用：尝试 JSON 格式（向后兼容）
    # Fallback: try JSON format (backward compatibility)
    table_data_path_json = BASE_DIR / "table_data.json"
    if table_data_path_json.exists():
        try:
            with open(table_data_path_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 确保数据格式正确：forum_id 作为 key
                # Ensure data format is correct: forum_id as key
                if isinstance(data, dict):
                    return data
                else:
                    print("⚠️  表格数据格式不正确，应为 {forum_id: {...}} / Table data format incorrect, should be {forum_id: {...}}")
                    return {}
        except Exception as e:
            print(f"⚠️  加载 JSON 表格数据失败 / Failed to load JSON table data: {e}")
            return {}
    
    return {}

def download_paper(forum_id, paper_info, table_data=None):
    """
    下载单篇论文的所有资源
    Download all resources for a single paper
    """
    main_note = paper_info['main_note']
    title = main_note.content.get('title', 'Untitled') if hasattr(main_note, 'content') else 'Untitled'
    
    # 清理文件名中的非法字符 / Clean illegal characters from filename
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)[:100]
    paper_folder = PAPERS_DIR / f"{forum_id}_{safe_title}"
    paper_folder.mkdir(exist_ok=True)
    
    print(f"\n📄 处理论文 / Processing: {title[:60]}...")
    
    # 1. 下载论文PDF / Download paper PDF
    if hasattr(main_note, 'content') and 'pdf' in main_note.content:
        pdf_url = main_note.content['pdf']
        pdf_path = paper_folder / f"{forum_id}.pdf"
        if not pdf_path.exists():
            print(f"  📥 下载PDF... / Downloading PDF...")
            download_file(pdf_url, pdf_path)
        else:
            print(f"  ✓ PDF已存在 / PDF already exists")
    
    # 2. 保存论文元数据（包含表格数据）/ Save paper metadata (including table data)
    metadata_path = METADATA_DIR / f"{forum_id}_metadata.json"
    metadata = {
        'forum_id': forum_id,
        'title': title,
        'authors': main_note.content.get('authors', []) if hasattr(main_note, 'content') else [],
        'abstract': main_note.content.get('abstract', '') if hasattr(main_note, 'content') else '',
        'keywords': main_note.content.get('keywords', []) if hasattr(main_note, 'content') else [],
        'openreview_url': f"https://openreview.net/forum?id={forum_id}",
        'created': str(main_note.cdate) if hasattr(main_note, 'cdate') else None,
    }
    
    # 添加表格数据（如果可用）/ Add table data (if available)
    # 表格数据格式: {title, status, primary_topic, secondary_topic, human_review, ai_reviewer_1, ai_reviewer_2, ai_reviewer_3, hypothesis_development}
    # Table data format: {title, status, primary_topic, secondary_topic, human_review, ai_reviewer_1, ai_reviewer_2, ai_reviewer_3, hypothesis_development}
    if table_data and forum_id in table_data and table_data[forum_id]:
        # 直接将表格数据合并到元数据中（而不是嵌套在 table_data 字段下）
        # Directly merge table data into metadata (instead of nesting under table_data field)
        table_info = table_data[forum_id]
        if isinstance(table_info, dict):
            metadata.update(table_info)
            print(f"  ✓ 包含表格数据 / Includes table data")
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # 3. 下载并保存所有reviews / Download and save all reviews
    reviews_data = []
    for i, review in enumerate(paper_info['reviews']):
        review_data = {
            'review_id': review.id,
            'content': review.content if hasattr(review, 'content') else {},
            'rating': review.content.get('rating', '') if hasattr(review, 'content') else '',
            'confidence': review.content.get('confidence', '') if hasattr(review, 'content') else '',
            'created': str(review.cdate) if hasattr(review, 'cdate') else None,
        }
        reviews_data.append(review_data)
    
    reviews_path = REVIEWS_DIR / f"{forum_id}_reviews.json"
    with open(reviews_path, 'w', encoding='utf-8') as f:
        json.dump(reviews_data, f, indent=2, ensure_ascii=False)
    
    if reviews_data:
        print(f"  ✓ 保存了 {len(reviews_data)} 条review / Saved {len(reviews_data)} reviews")
    
    # 4. 保存代码链接信息 / Save code link information
    if paper_info['code_attachments']:
        code_info_path = CODE_DIR / f"{forum_id}_code_info.json"
        with open(code_info_path, 'w', encoding='utf-8') as f:
            json.dump(paper_info['code_attachments'], f, indent=2, ensure_ascii=False)
        print(f"  ✓ 找到代码链接 / Found code links")
    
    # 5. 保存完整的note数据（包含所有信息）/ Save complete note data
    complete_data_path = paper_folder / f"{forum_id}_complete.json"
    try:
        # 将note对象转换为可序列化的字典
        # Convert note objects to serializable dictionaries
        complete_data = {
            'main_note': {
                'id': main_note.id,
                'content': dict(main_note.content) if hasattr(main_note, 'content') else {},
                'invitation': main_note.invitation,
                'cdate': str(main_note.cdate) if hasattr(main_note, 'cdate') else None,
            },
            'reviews': [
                {
                    'id': r.id,
                    'content': dict(r.content) if hasattr(r, 'content') else {},
                    'invitation': r.invitation,
                }
                for r in paper_info['reviews']
            ]
        }
        with open(complete_data_path, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  ⚠️  保存完整数据时出错 / Error saving complete data: {e}")
    
    return True

def main():
    """
    主函数：批量下载所有论文
    Main function: batch download all papers
    """
    print("=" * 60)
    print("🚀 Agents4Science 2025 论文批量下载工具")
    print("🚀 Agents4Science 2025 Paper Batch Download Tool")
    print("=" * 60)
    
    # 方法0：优先从 table_data.csv 获取 forum IDs（推荐方式）
    # Method 0: Priority: get forum IDs from table_data.csv (recommended)
    table_data = load_table_data()
    forum_ids = []
    
    if table_data:
        forum_ids = list(table_data.keys())
        print(f"✅ 从 table_data.csv 读取到 {len(forum_ids)} 个 forum ID / Read {len(forum_ids)} forum IDs from table_data.csv")
    
    # 方法1：如果 table_data.json 不存在，检查是否已有forum_ids.txt文件
    # Method 1: If table_data.json doesn't exist, check if forum_ids.txt exists
    if not forum_ids:
        forum_ids_path = BASE_DIR / "forum_ids.txt"
        if forum_ids_path.exists():
            print(f"📄 发现已有forum_ids.txt文件，正在读取... / Found existing forum_ids.txt, reading...")
            try:
                with open(forum_ids_path, 'r', encoding='utf-8') as f:
                    forum_ids = [line.strip() for line in f if line.strip()]
                if forum_ids:
                    print(f"✅ 从文件读取到 {len(forum_ids)} 个forum ID / Read {len(forum_ids)} forum IDs from file")
            except Exception as e:
                print(f"⚠️  读取文件失败 / Failed to read file: {e}")
    
    # 方法2：如果文件不存在或为空，尝试通过API获取
    # Method 2: If file doesn't exist or is empty, try to get via API
    if not forum_ids:
        forum_ids = get_all_papers_from_api()
    
    # 方法3：如果API失败，从网页提取
    # Method 3: If API fails, extract from webpage
    if not forum_ids:
        submissions_url = "https://agents4science.stanford.edu/submissions.html"
        forum_ids = extract_forum_ids_from_page(submissions_url)
    
    if not forum_ids:
        print("❌ 未找到任何论文 / No papers found")
        print("💡 提示：请运行 extract_table_data.js 提取表格数据（会生成 CSV 格式），或手动编辑 forum_ids.txt 文件")
        print("💡 Tip: Please run extract_table_data.js to extract table data (will generate CSV format), or manually edit forum_ids.txt file")
        return
    
    # 如果没有表格数据，尝试从 forum_ids.txt 生成空的表格数据结构
    # If no table data, try to generate empty table data structure from forum_ids.txt
    if not table_data:
        print("⚠️  未找到表格数据，将使用空的表格数据结构 / No table data found, will use empty table data structure")
        table_data = {fid: {} for fid in forum_ids}
    
    # 保存forum ID列表（作为备份）
    # Save forum ID list (as backup)
    forum_ids_path = BASE_DIR / "forum_ids.txt"
    with open(forum_ids_path, 'w', encoding='utf-8') as f:
        for fid in forum_ids:
            f.write(f"{fid}\n")
    print(f"✓ 已保存forum ID列表到 / Saved forum ID list to: {forum_ids_path}")
    
    # 下载每篇论文
    # Download each paper
    total = len(forum_ids)
    success_count = 0
    failed_count = 0
    
    for idx, forum_id in enumerate(forum_ids, 1):
        print(f"\n[{idx}/{total}] 处理论文ID / Processing paper ID: {forum_id}")
        
        try:
            # 获取论文详情
            # Get paper details
            paper_info = get_paper_details(forum_id)
            
            if paper_info:
                # 下载论文资源（传入表格数据）
                # Download paper resources (pass table data)
                if download_paper(forum_id, paper_info, table_data):
                    success_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
                print(f"  ❌ 无法获取论文信息 / Unable to get paper information")
        
        except Exception as e:
            failed_count += 1
            print(f"  ❌ 处理失败 / Processing failed: {e}")
        
        # 添加延迟以避免请求过快
        # Add delay to avoid too many requests
        time.sleep(1)
    
    # 打印总结
    # Print summary
    print("\n" + "=" * 60)
    print("📊 下载完成 / Download Complete")
    print("=" * 60)
    print(f"✅ 成功 / Success: {success_count}")
    print(f"❌ 失败 / Failed: {failed_count}")
    print(f"📁 下载目录 / Download directory: {BASE_DIR.absolute()}")
    print("=" * 60)

if __name__ == "__main__":
    main()

