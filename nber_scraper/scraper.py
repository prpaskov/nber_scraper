"""
NBER Scraper - Extract working papers and abstracts from NBER website
"""

import requests
import json
import time
import os
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NBERScraper:
    def __init__(self, search_query="", base_url="https://www.nber.org", delay=1.0, 
                 start_date=None, end_date=None):
        self.search_query = search_query.lower() if search_query else ""
        self.base_url = base_url
        self.delay = delay
        self.start_date = start_date  # Format: "YYYY/MM/DD" or "YYYY-MM-DD"
        self.end_date = end_date      # Format: "YYYY/MM/DD" or "YYYY-MM-DD"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.papers = []
        
    def get_page(self, url, retries=3):
        """Fetch a page with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                time.sleep(self.delay)
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(self.delay * 2)
    
    def extract_paper_metadata(self, paper_number):
        """Extract metadata from a single working paper using meta tags"""
        url = f"{self.base_url}/papers/w{paper_number}"
        
        try:
            response = self.get_page(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if paper exists (404 or not found)
            if response.status_code == 404:
                return None
                
            # Extract data from meta tags
            paper_data = {
                'paper_id': f'w{paper_number}',
                'url': url,
                'title': None,
                'authors': [],
                'abstract': None,
                'pdf_url': None,
                'publication_date': None,
                'doi': None,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract title
            title_meta = soup.find('meta', attrs={'name': 'citation_title'})
            if title_meta:
                paper_data['title'] = title_meta.get('content', '').strip()
            
            # Extract authors
            author_metas = soup.find_all('meta', attrs={'name': 'citation_author'})
            paper_data['authors'] = [meta.get('content', '').strip() for meta in author_metas if meta.get('content')]
            
            # Extract DOI
            doi_meta = soup.find('meta', attrs={'name': 'citation_doi'})
            if doi_meta:
                paper_data['doi'] = doi_meta.get('content', '').strip()
            
            # Extract publication date
            date_meta = soup.find('meta', attrs={'name': 'citation_publication_date'})
            if date_meta:
                paper_data['publication_date'] = date_meta.get('content', '').strip()
            
            # Extract PDF URL
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                paper_data['pdf_url'] = pdf_meta.get('content', '').strip()
            
            # Extract abstract from page content
            abstract_selectors = [
                'div.page-header__intro',  # NBER's actual abstract container
                'div.page-header__intro--centered',
                'div.abstract-content',
                'div.abstract',
                'div[class*="abstract"]',
                'p.abstract',
                'section.abstract'
            ]
            
            for selector in abstract_selectors:
                abstract_elem = soup.select_one(selector)
                if abstract_elem:
                    abstract_text = abstract_elem.get_text().strip()
                    # Clean up abstract text
                    abstract_text = re.sub(r'^Abstract:?\s*', '', abstract_text, flags=re.IGNORECASE)
                    abstract_text = re.sub(r'\s+', ' ', abstract_text)  # Normalize whitespace
                    paper_data['abstract'] = abstract_text
                    break
            
            # If we still don't have an abstract, try to find it in the main content
            if not paper_data['abstract']:
                # Look for text that contains typical abstract patterns
                main_content = soup.find('main') or soup.find('body')
                if main_content:
                    text_content = main_content.get_text()
                    # Look for abstract section
                    abstract_match = re.search(r'Abstract:?\s*(.{100,2000}?)(?:\n\n|\r\n\r\n|JEL|Keywords|$)', 
                                            text_content, re.IGNORECASE | re.DOTALL)
                    if abstract_match:
                        paper_data['abstract'] = abstract_match.group(1).strip()
            
            logger.info(f"Extracted metadata for paper w{paper_number}: {paper_data.get('title', 'No title')}")
            return paper_data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching paper w{paper_number}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing paper w{paper_number}: {e}")
            return None
    
    def matches_search_query(self, paper_data):
        """
        Check if paper matches the search query.
        
        Searches in:
        1. Paper Title
        2. Abstract content
        
        For "AI" searches, also looks for related terms like "artificial intelligence",
        "machine learning", "deep learning", etc.
        """
        if not self.search_query:
            return True
            
        query_lower = self.search_query.lower().strip()
        
        # Prepare search terms
        search_terms = []
        
        if query_lower == "ai":
            # For AI searches, look for AI as whole word plus variations
            search_terms = [
                r'\bai\b',  # AI as whole word
                r'\bartificial intelligence\b',
                r'\bmachine learning\b',
                r'\bdeep learning\b',
                r'\bneural network\b',
                r'\balgorithm\b'
            ]
        else:
            # For other topic searches, use word boundaries to avoid partial matches
            escaped_query = re.escape(query_lower)
            search_terms = [rf'\b{escaped_query}\b']
        
        # Search in title
        title = (paper_data.get('title') or '').lower()
        for term in search_terms:
            if re.search(term, title, re.IGNORECASE):
                return True
                
        # Search in abstract
        abstract = (paper_data.get('abstract') or '').lower()
        for term in search_terms:
            if re.search(term, abstract, re.IGNORECASE):
                return True
                
        return False
    
    def matches_date_range(self, paper_data):
        """
        Check if paper's publication date falls within the specified date range.
        
        Returns True if:
        - No date range is specified
        - Paper has no date (we include it to be safe)
        - Paper date falls within the specified range
        """
        if not self.start_date and not self.end_date:
            return True
            
        pub_date = paper_data.get('publication_date')
        if not pub_date:
            return True  # Include papers without dates
            
        try:
            # Parse the publication date (NBER format is usually YYYY/MM/DD)
            if '/' in pub_date:
                paper_date = datetime.strptime(pub_date, '%Y/%m/%d')
            elif '-' in pub_date:
                paper_date = datetime.strptime(pub_date, '%Y-%m-%d')
            else:
                return True  # If we can't parse it, include it
            
            # Check start date
            if self.start_date:
                try:
                    if '/' in self.start_date:
                        start_dt = datetime.strptime(self.start_date, '%Y/%m/%d')
                    else:
                        start_dt = datetime.strptime(self.start_date, '%Y-%m-%d')
                    
                    if paper_date < start_dt:
                        return False
                except:
                    pass  # If start_date format is invalid, ignore it
            
            # Check end date
            if self.end_date:
                try:
                    if '/' in self.end_date:
                        end_dt = datetime.strptime(self.end_date, '%Y/%m/%d')
                    else:
                        end_dt = datetime.strptime(self.end_date, '%Y-%m-%d')
                    
                    if paper_date > end_dt:
                        return False
                except:
                    pass  # If end_date format is invalid, ignore it
            
            return True
            
        except:
            return True  # If any parsing fails, include the paper
    
    def download_pdf(self, pdf_url, paper_id, download_dir="downloads"):
        """Download a PDF file"""
        if not pdf_url:
            return False
            
        try:
            os.makedirs(download_dir, exist_ok=True)
            
            response = self.get_page(pdf_url)
            filename = f"{paper_id}.pdf"
            filepath = os.path.join(download_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded PDF: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading PDF {pdf_url}: {e}")
            return False
    
    def scrape_papers(self, max_papers=None, max_pages=None, start_number=None, download_pdfs=False):
        """
        Scrape NBER working papers starting from recent papers and working backwards
        
        Args:
            max_papers: Maximum number of matching papers to collect (None for unlimited)
            max_pages: Maximum number of papers to check (None for unlimited) 
            start_number: Working paper number to start from (None to auto-detect)
            download_pdfs: Whether to download PDF files
        """
        
        # Auto-detect the most recent paper number if not provided
        if start_number is None:
            logger.info("Auto-detecting most recent paper number...")
            # Start from a high number and work backwards to find the latest
            for test_num in range(33500, 33000, -10):  # Test every 10th number
                test_url = f"{self.base_url}/papers/w{test_num}"
                try:
                    response = self.session.head(test_url, timeout=10)
                    if response.status_code == 200:
                        start_number = test_num + 10  # Add buffer
                        logger.info(f"Starting from paper number w{start_number}")
                        break
                except:
                    continue
            
            if start_number is None:
                start_number = 33200  # Fallback
                logger.info(f"Using fallback start number w{start_number}")
        
        papers_checked = 0
        papers_found = 0
        consecutive_failures = 0
        max_consecutive_failures = 50  # Stop if we hit 50 consecutive 404s
        
        logger.info(f"Starting scrape from paper w{start_number}")
        logger.info(f"Search query: '{self.search_query}'" if self.search_query else "No search filter")
        logger.info(f"Max papers: {max_papers}")
        logger.info(f"Max to check: {max_pages}")
        
        current_number = start_number
        
        while True:
            # Check stopping conditions
            if max_papers and papers_found >= max_papers:
                logger.info(f"Reached maximum papers limit: {max_papers}")
                break
                
            if max_pages and papers_checked >= max_pages:
                logger.info(f"Reached maximum papers to check limit: {max_pages}")
                break
                
            if consecutive_failures >= max_consecutive_failures:
                logger.info(f"Reached {max_consecutive_failures} consecutive failures, stopping")
                break
                
            if current_number <= 0:
                logger.info("Reached paper number 0, stopping")
                break
            
            papers_checked += 1
            
            # Extract paper metadata
            paper_data = self.extract_paper_metadata(current_number)
            
            if paper_data is None:
                consecutive_failures += 1
                current_number -= 1
                continue
            else:
                consecutive_failures = 0  # Reset failure counter
            
            # Check if paper matches search criteria and date range
            if self.matches_search_query(paper_data) and self.matches_date_range(paper_data):
                self.papers.append(paper_data)
                papers_found += 1
                
                logger.info(f"Found matching paper {papers_found}: w{current_number} - {paper_data.get('title', 'No title')[:100]}")
                
                # Download PDF if requested
                if download_pdfs and paper_data.get('pdf_url'):
                    self.download_pdf(paper_data['pdf_url'], paper_data['paper_id'])
                
                # Save progress periodically
                if papers_found % 10 == 0:
                    self.save_to_json(f"nber_papers_progress_{papers_found}.json")
            
            current_number -= 1
            
            # Progress update
            if papers_checked % 50 == 0:
                logger.info(f"Progress: checked {papers_checked} papers, found {papers_found} matching papers")
        
        logger.info(f"Scraping completed: checked {papers_checked} papers, found {papers_found} matching papers")
        return self.papers
    
    def save_to_json(self, filename):
        """Save collected papers to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.papers, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.papers)} papers to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving to {filename}: {e}")
            return False