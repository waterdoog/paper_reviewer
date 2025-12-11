import json
import logging
import os
import shutil
import subprocess
import time
from contextlib import closing
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urljoin, urlparse

import openreview
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


def configure_logger() -> logging.Logger:
    """Configure a simple stdout logger."""
    logger = logging.getLogger("agent4science")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


class Agent4ScienceScraper:
    SUBMISSIONS_URL = "https://agents4science.stanford.edu/submissions.html"
    OPENREVIEW_FORUM_URL = "https://openreview.net/forum?id={forum_id}"
    OPENREVIEW_PDF_URL = "https://api2.openreview.net/pdf/{pdf_id}"
    NETWORK_DELAY = 0.3

    METADATA_FIELDS = [
        "forum_id",
        "title",
        "authors",
        "status",
        "primary_topic",
        "secondary_topic",
        "human_review_score",
        "ai_reviewer_1_score",
        "ai_reviewer_2_score",
        "ai_reviewer_3_score",
        "hypothesis_development_label",
        "openreview_link",
        "supplementary_link",
        "code_link",
    ]

    HEADER_MAP = {
        "forumid": "forum_id",
        "forum": "forum_id",
        "title": "title",
        "authors": "authors",
        "status": "status",
        "primarytopic": "primary_topic",
        "secondarytopic": "secondary_topic",
        "humanreviewscore": "human_review_score",
        "aireviewer1score": "ai_reviewer_1_score",
        "aireviewer2score": "ai_reviewer_2_score",
        "aireviewer3score": "ai_reviewer_3_score",
        "hypothesisdevelopmentlabel": "hypothesis_development_label",
        "openreviewlink": "openreview_link",
        "openreview": "openreview_link",
        "supplementarylink": "supplementary_link",
        "supplementary": "supplementary_link",
        "codelink": "code_link",
        "code": "code_link",
    }

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.project_root = Path(__file__).resolve().parent.parent
        self.download_root = self.project_root / "downloads"
        self.metadata_path = self.download_root / "metadata.csv"
        self.pdf_dir = self.download_root / "pdfs"
        self.reviews_dir = self.download_root / "reviews"
        self.supp_dir = self.download_root / "supplementary"
        self.code_dir = self.download_root / "code"

        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Agent4ScienceScraper/1.0 (+https://openreview.net/)"}
        )

        username = os.getenv("OPENREVIEW_USERNAME")
        password = os.getenv("OPENREVIEW_PASSWORD")
        if not username or not password:
            self.logger.warning(
                "OPENREVIEW_USERNAME or OPENREVIEW_PASSWORD not set. "
                "Some features may not work without authentication."
            )
        
        self.client = openreview.api.OpenReviewClient(
            baseurl="https://api2.openreview.net",
            username=username,
            password=password,
        )

        self.counts = {
            "total_papers": 0,
            "pdfs": 0,
            "reviews": 0,
            "supplementary": 0,
            "repos": 0,
        }

    def run(self) -> None:
        self._prepare_directories()
        metadata = self._fetch_metadata()
        if not metadata:
            self.logger.error("No metadata rows retrieved; aborting run.")
            return

        self.counts["total_papers"] = len(metadata)
        self._save_metadata(metadata)
        self._process_papers(metadata)
        self._print_summary()

    def _prepare_directories(self) -> None:
        for path in [
            self.download_root,
            self.pdf_dir,
            self.reviews_dir,
            self.supp_dir,
            self.code_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def _fetch_metadata(self) -> List[Dict[str, str]]:
        self.logger.info("Fetching submissions table from %s", self.SUBMISSIONS_URL)
        response = self._safe_get(self.SUBMISSIONS_URL)
        if response is None:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        if not table:
            self.logger.error("Submissions table not found on the page.")
            return []
        return self._parse_table(table)

    def _parse_table(self, table) -> List[Dict[str, str]]:
        header_cells = table.find("thead")
        if header_cells:
            header_cells = header_cells.find_all("th")
        else:
            first_row = table.find("tr")
            header_cells = first_row.find_all("th") if first_row else []

        headers = [cell.get_text(strip=True) for cell in header_cells]
        column_targets = [self._map_header(header) for header in headers]

        # If no thead, skip the first row when reading body
        body_rows = table.find("tbody").find_all("tr") if table.find("tbody") else table.find_all("tr")[1:]

        records: List[Dict[str, str]] = []
        for row in body_rows:
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
            record = {field: "" for field in self.METADATA_FIELDS}
            for idx, cell in enumerate(cells):
                target = column_targets[idx] if idx < len(column_targets) else None
                if target is None:
                    continue
                record[target] = self._extract_cell_value(cell, target)

            if (
                not any(value for value in record.values())
                or (record["forum_id"] == "" and record["openreview_link"] == "")
            ):
                continue

            if not record["forum_id"] and record["openreview_link"]:
                record["forum_id"] = self._derive_forum_id(record["openreview_link"])

            records.append(record)
        self.logger.info("Parsed %d metadata rows from the table.", len(records))
        return records

    def _map_header(self, header: str) -> Optional[str]:
        normalized = "".join(char for char in header.lower() if char.isalnum())
        return self.HEADER_MAP.get(normalized)

    def _extract_cell_value(self, cell, target: str) -> str:
        link_fields = {"openreview_link", "supplementary_link", "code_link"}
        if target in link_fields:
            link = cell.find("a", href=True)
            if link and link["href"]:
                return link["href"].strip()
        text = cell.get_text(separator=" ", strip=True)
        return text

    def _derive_forum_id(self, openreview_link: str) -> str:
        """Extract forum_id from OpenReview URL.
        
        Supports multiple URL formats:
        - https://openreview.net/forum?id=xxx
        - https://openreview.net/forum?id=xxx&noteId=yyy
        - /forum?id=xxx
        """
        parsed = urlparse(openreview_link)
        query = parse_qs(parsed.query)
        forum_id = query.get("id", [""])[0]
        if not forum_id and parsed.path:
            # Try to extract from path if query param not found
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) >= 2 and path_parts[0] == "forum":
                # Handle /forum/xxx format if exists
                pass
        return forum_id

    def _save_metadata(self, data: List[Dict[str, str]]) -> None:
        df = pd.DataFrame(data, columns=self.METADATA_FIELDS)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.metadata_path, index=False)
        self.logger.info("Saved metadata CSV with %d rows to %s", len(df), self.metadata_path)

    def _process_papers(self, metadata: List[Dict[str, str]]) -> None:
        """Process each paper: download PDF, reviews, supplementary, and code."""
        for entry in tqdm(metadata, desc="Processing papers", unit="paper"):
            forum_id = (entry.get("forum_id") or "").strip()
            if not forum_id:
                self.logger.warning("Skipping row with missing forum_id.")
                continue

            # Fetch notes once and reuse for PDF and reviews
            notes = self._fetch_notes(forum_id)
            if notes:
                if self._save_reviews(forum_id, notes):
                    self.counts["reviews"] += 1
                if self._download_pdf(forum_id, notes):
                    self.counts["pdfs"] += 1
            else:
                self.logger.warning("No notes returned for forum %s", forum_id)

            # Download supplementary materials (pass code_link to check for duplicates)
            code_link = (entry.get("code_link") or "").strip()
            if self._download_supplementary(forum_id, code_link):
                self.counts["supplementary"] += 1

            # Clone code repository if applicable
            supp_link = (entry.get("supplementary_link") or "").strip()
            if self._clone_code_repo(forum_id, code_link, supp_link):
                self.counts["repos"] += 1

    def _fetch_notes(self, forum_id: str):
        try:
            notes = self.client.get_all_notes(forum=forum_id, details="all")
            time.sleep(self.NETWORK_DELAY)
            return notes
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.error("Failed to fetch notes for %s: %s", forum_id, exc)
            time.sleep(self.NETWORK_DELAY)
            return None

    def _save_reviews(self, forum_id, notes) -> bool:
        try:
            if not notes:
                self.logger.debug("No notes to save for forum %s", forum_id)
                return False
            notes_json = [note.to_json() for note in notes]
            review_path = self.reviews_dir / f"{forum_id}.json"
            with review_path.open("w", encoding="utf-8") as handle:
                json.dump(notes_json, handle, indent=2)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.error("Failed to save review history for %s: %s", forum_id, exc)
            return False

    def _download_pdf(self, forum_id: str, notes) -> bool:
        if not notes:
            self.logger.debug("No notes available for PDF download for forum %s", forum_id)
            return False
            
        pdf_note = next(
            (
                note
                for note in notes
                if getattr(note, "content", None)
                and isinstance(note.content, dict)
                and note.content.get("pdf")
            ),
            None,
        )
        if not pdf_note:
            self.logger.warning("PDF note not found for forum %s", forum_id)
            return False

        pdf_id = pdf_note.content.get("pdf")
        if not pdf_id:
            self.logger.warning("PDF id missing in note for %s", forum_id)
            return False

        pdf_path = self.pdf_dir / f"{forum_id}.pdf"
        if pdf_path.exists():
            self.logger.debug("PDF already exists for forum %s", forum_id)
            return True

        pdf_url = self.OPENREVIEW_PDF_URL.format(pdf_id=pdf_id)
        response = self._safe_get(pdf_url, stream=True)
        if response is None:
            return False

        try:
            with closing(response), pdf_path.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        handle.write(chunk)
            self.logger.debug("Successfully downloaded PDF for forum %s", forum_id)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.error("Failed to write PDF file for %s: %s", forum_id, exc)
            # Clean up partial file
            if pdf_path.exists():
                pdf_path.unlink()
            return False

    def _download_supplementary(self, forum_id: str, code_link: str = "") -> bool:
        """Download supplementary materials from forum HTML page.
        
        Args:
            forum_id: OpenReview forum ID
            code_link: Code link from metadata to check for duplicates
        """
        existing = next(self.supp_dir.glob(f"{forum_id}.*"), None)
        if existing:
            return True

        forum_url = self.OPENREVIEW_FORUM_URL.format(forum_id=forum_id)
        response = self._safe_get(forum_url)
        if response is None:
            return False
        soup = BeautifulSoup(response.text, "html.parser")
        attachment_link = self._find_supplementary_link(soup)
        if not attachment_link:
            self.logger.info("No supplementary attachment found for %s", forum_id)
            return False

        full_url = urljoin("https://openreview.net", attachment_link)
        
        # Check if this is the same as code_link to avoid duplicate download
        if code_link and self._urls_are_same_file(full_url, code_link):
            self.logger.info("Supplementary attachment matches code_link; skipping duplicate download for %s", forum_id)
            return False
        
        extension = self._guess_extension(full_url)
        supp_path = self.supp_dir / f"{forum_id}{extension}"
        if supp_path.exists():
            return True

        response = self._safe_get(full_url, stream=True)
        if response is None:
            return False

        try:
            with closing(response), supp_path.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        handle.write(chunk)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.error("Failed to download supplementary for %s: %s", forum_id, exc)
            if supp_path.exists():
                supp_path.unlink()
            return False

    def _find_supplementary_link(self, soup: BeautifulSoup) -> Optional[str]:
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            href_lower = href.lower()
            text_lower = (anchor.get_text(strip=True) or "").lower()
            if "attachment" in href_lower and "supp" in (href_lower + text_lower):
                return href
        return None

    def _guess_extension(self, url: str) -> str:
        path = urlparse(url).path
        if path.endswith(".tar.gz"):
            return ".tar.gz"
        if path.endswith(".tar"):
            return ".tar"
        extension = Path(path).suffix
        return extension if extension else ".bin"
    
    def _urls_are_same_file(self, url1: str, url2: str) -> bool:
        """Check if two URLs point to the same file.
        
        Compares normalized URLs to detect if code_link and supplementary
        attachment are the same file.
        """
        if not url1 or not url2:
            return False
        
        # Normalize URLs by extracting attachment IDs or comparing paths
        parsed1 = urlparse(url1)
        parsed2 = urlparse(url2)
        
        # If both are OpenReview attachment URLs, compare attachment IDs
        if "attachment" in parsed1.path and "attachment" in parsed2.path:
            q1 = parse_qs(parsed1.query)
            q2 = parse_qs(parsed2.query)
            id1 = q1.get("id", [""])[0]
            id2 = q2.get("id", [""])[0]
            if id1 and id2 and id1 == id2:
                return True
        
        # Compare full normalized URLs
        norm1 = f"{parsed1.netloc}{parsed1.path}"
        norm2 = f"{parsed2.netloc}{parsed2.path}"
        if norm1 == norm2:
            return True
        
        return False

    def _clone_code_repo(self, forum_id: str, code_link: str, supplementary_link: str) -> bool:
        if not code_link:
            return False
        if supplementary_link and code_link == supplementary_link:
            self.logger.info("Code link matches supplementary attachment; skipping clone for %s", forum_id)
            return False
        normalized_repo = self._normalize_github_repo_url(code_link)
        if not normalized_repo:
            self.logger.debug("Code link is not a GitHub repo for %s: %s", forum_id, code_link)
            return False

        target_dir = self.code_dir / forum_id
        if target_dir.exists():
            self.logger.debug("Code repo already exists for forum %s", forum_id)
            return True

        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", normalized_repo, str(target_dir)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300,  # 5 minute timeout
            )
            self.logger.debug("Successfully cloned repo for forum %s", forum_id)
            return True
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout while cloning repo for %s (%s)", forum_id, normalized_repo)
            # Clean up partial clone
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            return False
        except subprocess.CalledProcessError as exc:
            error_msg = exc.stderr.decode("utf-8", errors="ignore") if exc.stderr else str(exc)
            self.logger.error("Failed to clone repo for %s (%s): %s", forum_id, normalized_repo, error_msg)
            # Clean up partial clone
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            return False
        except FileNotFoundError:
            self.logger.error("Git not found. Please install git to clone repositories.")
            return False

    def _normalize_github_repo_url(self, url: str) -> Optional[str]:
        """Normalize GitHub repository URL to standard format.
        
        Supports:
        - https://github.com/owner/repo
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git
        - github.com/owner/repo (without protocol)
        """
        if not url:
            return None
            
        # Handle git@ format
        if url.startswith("git@") or url.startswith("ssh://git@"):
            # Extract owner/repo from git@github.com:owner/repo.git
            if ":" in url:
                parts = url.split(":")[-1].replace(".git", "").split("/")
                if len(parts) >= 2:
                    return f"https://github.com/{'/'.join(parts)}"
            return None
        
        parsed = urlparse(url if "://" in url else f"https://{url}")
        netloc = parsed.netloc.lower()
        if "github.com" not in netloc:
            return None
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2:
            return None
        owner, repo = parts[0], parts[1].replace(".git", "")
        base = f"https://github.com/{owner}/{repo}"
        return base

    def _print_summary(self) -> None:
        lines = [
            "========== SCRAPE SUMMARY ==========",
            f"Papers processed:     {self.counts['total_papers']}",
            f"PDFs downloaded:      {self.counts['pdfs']}",
            f"Review JSON files:    {self.counts['reviews']}",
            f"Supplementary files:  {self.counts['supplementary']}",
            f"GitHub repos cloned:  {self.counts['repos']}",
        ]
        print("\n".join(lines))

    def _safe_get(self, url: str, stream: bool = False, timeout: int = 30) -> Optional[requests.Response]:
        try:
            response = self.session.get(url, stream=stream, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            self.logger.error("Request failed for %s: %s", url, exc)
            return None
        finally:
            time.sleep(self.NETWORK_DELAY)


def main() -> None:
    """Main entry point for the scraper."""
    logger = configure_logger()
    logger.info("Starting Agent4Science scraper...")
    scraper = Agent4ScienceScraper(logger)
    try:
        scraper.run()
        logger.info("Scraper completed successfully.")
    except KeyboardInterrupt:
        logger.warning("Run interrupted by user.")
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Fatal error during scraping: %s", exc, exc_info=True)
        raise


if __name__ == "__main__":
    main()
