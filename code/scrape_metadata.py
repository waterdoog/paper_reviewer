#!/usr/bin/env python3
"""
Metadata Scraper for Agent4Science 2025
Scrapes submission metadata from the submissions table and saves to CSV.
"""

import re
import time
import random
import logging
from pathlib import Path
from urllib.parse import urljoin
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('downloads/metadata_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
SUBMISSIONS_URL = "https://agents4science.stanford.edu/submissions.html"
OPENREVIEW_BASE = "https://openreview.net"
DOWNLOAD_DIR = Path("downloads")
METADATA_CSV = DOWNLOAD_DIR / "metadata.csv"

# Request delays (in seconds)
MIN_DELAY = 0.3
MAX_DELAY = 1.0


def setup_directories():
    """Create necessary directories."""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Directories created/verified")


def polite_delay():
    """Add a random delay between requests."""
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def extract_forum_id(openreview_link: str) -> Optional[str]:
    """Extract forum_id from OpenReview link."""
    if not openreview_link:
        return None
    # Match patterns like: https://openreview.net/forum?id=XXXXX
    match = re.search(r'forum\?id=([^&\s]+)', openreview_link)
    if match:
        return match.group(1)
    # Also try direct ID patterns
    match = re.search(r'/([a-zA-Z0-9_-]{20,})', openreview_link)
    if match:
        return match.group(1)
    return None


def parse_submissions_table() -> pd.DataFrame:
    """Parse submissions table from the CSV data file (loaded by JavaScript)."""
    # The table is dynamically loaded from data/papers.csv via JavaScript
    # So we need to fetch the CSV directly instead of parsing HTML
    csv_url = "https://agents4science.stanford.edu/data/papers.csv"
    logger.info(f"Fetching data from {csv_url}")
    polite_delay()
    
    try:
        # Add User-Agent header to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(csv_url, headers=headers, timeout=30)
        response.raise_for_status()
        logger.debug(f"Response status: {response.status_code}, Content length: {len(response.content)}")
        
        # Parse CSV directly
        csv_text = response.text
        lines = csv_text.strip().split('\n')
        if len(lines) < 2:
            logger.error("CSV file is empty or has no data rows")
            return pd.DataFrame()
        
        # Parse CSV manually (handling quoted fields)
        rows = []
        headers_line = lines[0]
        
        # Simple CSV parser (handles quoted fields)
        def parse_csv_line(line):
            values = []
            current = ''
            in_quotes = False
            for char in line:
                if char == '"':
                    in_quotes = not in_quotes
                elif char == ',' and not in_quotes:
                    values.append(current.strip())
                    current = ''
                else:
                    current += char
            values.append(current.strip())
            return values
        
        # Parse header
        headers = [h.strip().strip('"') for h in parse_csv_line(headers_line)]
        logger.debug(f"CSV headers: {headers}")
        
        # Parse data rows
        for i, line in enumerate(lines[1:], 1):
            if not line.strip():
                continue
            values = parse_csv_line(line)
            if len(values) < len(headers):
                logger.warning(f"Row {i} has fewer values than headers, skipping")
                continue
            
            row_data = {}
            for j, header in enumerate(headers):
                value = values[j].strip().strip('"') if j < len(values) else ''
                row_data[header] = value
            
            rows.append(row_data)
        
        df = pd.DataFrame(rows)
        logger.info(f"Parsed {len(df)} submissions from CSV")
        
        # Map CSV columns to our expected format
        # CSV columns: title, link, airev1_score, airev2_score, airev3_score, human_score, 
        #              status, hypothesis_development, experimental_design, data_analysis, writing, 
        #              primary_topic, secondary_topic
        if 'link' in df.columns:
            df['openreview_link'] = df['link']
            df['forum_id'] = df['link'].apply(extract_forum_id)
        
        # Rename columns to match expected format
        column_mapping = {
            'airev1_score': 'ai_reviewer_1_score',
            'airev2_score': 'ai_reviewer_2_score',
            'airev3_score': 'ai_reviewer_3_score',
            'human_score': 'human_review_score',
            'hypothesis_development': 'hypothesis_development_label'
        }
        df = df.rename(columns=column_mapping)
        
        # Add missing columns with default values
        if 'authors' not in df.columns:
            df['authors'] = ''
        if 'supplementary_link' not in df.columns:
            df['supplementary_link'] = ''
        if 'code_link' not in df.columns:
            df['code_link'] = ''
        
        # Filter out rows without valid forum_id
        initial_count = len(df)
        df = df[df['forum_id'].notna() & (df['forum_id'] != '')]
        if len(df) < initial_count:
            logger.warning(f"Filtered out {initial_count - len(df)} rows without valid forum_id")
        
        return df
    
    except Exception as e:
        logger.error(f"Error fetching/parsing CSV data: {e}", exc_info=True)
        return pd.DataFrame()
        
        # Extract rows from tbody (skip thead rows)
        rows = []
        tbody = table.find('tbody')
        
        # Debug: log table structure
        thead = table.find('thead')
        logger.debug(f"Table structure - has thead: {thead is not None}, has tbody: {tbody is not None}")
        
        if not tbody:
            # If no tbody, get all rows and skip header rows in thead
            all_rows = table.find_all('tr')
            thead_rows = table.find('thead')
            skip_count = len(thead_rows.find_all('tr')) if thead_rows else 1
            data_rows = all_rows[skip_count:]
            logger.debug(f"No tbody found, using all rows (skip {skip_count} header rows)")
        else:
            # Get all rows from tbody (no need to skip, thead is separate)
            data_rows = tbody.find_all('tr')
            logger.debug(f"Found tbody with {len(data_rows)} rows")
        
        logger.info(f"Found {len(data_rows)} data rows to process")
        
        # Debug: check first row if exists
        if data_rows:
            first_row_cells = data_rows[0].find_all('td')
            logger.debug(f"First data row has {len(first_row_cells)} cells")
            if first_row_cells:
                logger.debug(f"First cell text: {first_row_cells[0].get_text(strip=True)[:50]}")
        
        for tr in data_rows:
            cells = tr.find_all('td')  # Only get td, not th (th is for headers)
            if not cells or len(cells) < 4:
                continue
            
            row_data = {}
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # Extract links from all cells
            links = {}
            for cell in cells:
                for a in cell.find_all('a', href=True):
                    href = a['href']
                    text = a.get_text(strip=True).lower()
                    if 'openreview.net' in href.lower() or 'openreview' in href.lower():
                        links['openreview'] = href if href.startswith('http') else urljoin(OPENREVIEW_BASE, href)
                    if 'github.com' in href.lower():
                        links['code'] = href
                    if 'supp' in text or 'supplementary' in text or 'supp' in href.lower():
                        links['supplementary'] = href if href.startswith('http') else urljoin(OPENREVIEW_BASE, href)
            
            # Map columns based on actual table structure:
            # 0: Title (with OpenReview link)
            # 1: Status
            # 2: Primary Topic
            # 3: Secondary Topic
            # 4: Human Review Score
            # 5: AI Reviewer 1 Score
            # 6: AI Reviewer 2 Score
            # 7: AI Reviewer 3 Score
            # 8: Hypothesis Development
            # 9: Experimental Design
            # 10: Data Analysis
            # 11: Writing
            # 12: Overall
            # 13: Code Audit Result
            
            row_data['title'] = cell_texts[0] if len(cell_texts) > 0 else ''
            row_data['status'] = cell_texts[1] if len(cell_texts) > 1 else ''
            row_data['primary_topic'] = cell_texts[2] if len(cell_texts) > 2 else ''
            row_data['secondary_topic'] = cell_texts[3] if len(cell_texts) > 3 else ''
            
            # Extract forum_id from openreview link (usually in title cell)
            openreview_link = links.get('openreview', '')
            row_data['forum_id'] = extract_forum_id(openreview_link)
            row_data['openreview_link'] = openreview_link
            
            # Extract scores (columns 4-7)
            try:
                row_data['human_review_score'] = float(cell_texts[4]) if len(cell_texts) > 4 and cell_texts[4] else None
            except (ValueError, TypeError):
                row_data['human_review_score'] = None
            
            try:
                row_data['ai_reviewer_1_score'] = float(cell_texts[5]) if len(cell_texts) > 5 and cell_texts[5] else None
            except (ValueError, TypeError):
                row_data['ai_reviewer_1_score'] = None
            
            try:
                row_data['ai_reviewer_2_score'] = float(cell_texts[6]) if len(cell_texts) > 6 and cell_texts[6] else None
            except (ValueError, TypeError):
                row_data['ai_reviewer_2_score'] = None
            
            try:
                row_data['ai_reviewer_3_score'] = float(cell_texts[7]) if len(cell_texts) > 7 and cell_texts[7] else None
            except (ValueError, TypeError):
                row_data['ai_reviewer_3_score'] = None
            
            # Extract hypothesis development label (column 8)
            row_data['hypothesis_development_label'] = cell_texts[8] if len(cell_texts) > 8 else ''
            
            # Authors - not in table, will be empty or could be extracted from title/OpenReview
            row_data['authors'] = ''
            
            # Links
            row_data['supplementary_link'] = links.get('supplementary', '')
            row_data['code_link'] = links.get('code', '')
            
            # Only add row if we have a forum_id (valid OpenReview link)
            if row_data['forum_id']:
                rows.append(row_data)
            else:
                logger.warning(f"Skipping row without valid forum_id: {row_data.get('title', 'Unknown')[:50]}")
        
        df = pd.DataFrame(rows)
        logger.info(f"Parsed {len(df)} submissions from table")
        return df
    
    except Exception as e:
        logger.error(f"Error parsing submissions table: {e}", exc_info=True)
        return pd.DataFrame()


def main():
    """Main function to scrape metadata and save to CSV."""
    logger.info("=" * 60)
    logger.info("Agent4Science Metadata Scraper - Starting")
    logger.info("=" * 60)
    
    # Setup directories
    setup_directories()
    
    # Parse submissions table
    df = parse_submissions_table()
    
    if df.empty:
        logger.error("No submissions found. Exiting.")
        return
    
    # Save metadata
    df.to_csv(METADATA_CSV, index=False, encoding='utf-8')
    logger.info(f"Saved metadata to {METADATA_CSV} ({len(df)} papers)")
    
    # Log missing fields
    missing_fields = []
    for col in ['forum_id', 'title', 'status']:
        missing_count = df[col].isna().sum() + (df[col] == '').sum()
        if missing_count > 0:
            missing_fields.append(f"{col}: {missing_count} missing")
    
    if missing_fields:
        logger.warning(f"Missing fields: {', '.join(missing_fields)}")
    
    # Print summary
    logger.info("=" * 60)
    logger.info("Metadata Scraping Summary")
    logger.info("=" * 60)
    logger.info(f"Total papers found: {len(df)}")
    logger.info(f"Accepted: {len(df[df['status'].str.lower() == 'accepted']) if 'status' in df.columns else 0}")
    logger.info(f"Rejected: {len(df[df['status'].str.lower() == 'rejected']) if 'status' in df.columns else 0}")
    logger.info(f"Metadata saved to: {METADATA_CSV}")
    logger.info("=" * 60)
    logger.info("Metadata scraping complete!")
    logger.info(f"Next step: Run 'python code/main.py' to download PDFs, reviews, and code.")


if __name__ == "__main__":
    main()

