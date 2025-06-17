#!/usr/bin/env python3
"""
Simple NBER Scraper
Edit the settings below and run this script to scrape NBER papers.
"""

# =============================================================================
# EDIT THESE SETTINGS
# =============================================================================
SEARCH_QUERY = "AI"  # Search for papers containing this term (title, abstract, or authors)
MAX_PAPERS = 50     # Maximum number of matching papers to collect (None for unlimited)
MAX_TO_CHECK = 500  # Maximum number of papers to check (None for unlimited)
DOWNLOAD_PDFS = False  # Set to True to download PDF files
OUTPUT_FILENAME = None  # Output filename (None for auto-generated)

# Date range filters (optional - leave as None to search all dates)
START_DATE = None   # Format: "2023/01/01" or "2023-01-01" (papers from this date onwards)
END_DATE = None     # Format: "2024/12/31" or "2024-12-31" (papers up to this date)

# =============================================================================
# DON'T EDIT BELOW THIS LINE UNLESS YOU KNOW WHAT YOU'RE DOING
# =============================================================================

import os
import sys
from datetime import datetime

# Add the nber_scraper directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'nber_scraper'))

from scraper import NBERScraper

def main():
    print("=" * 60)
    print("NBER Papers Scraper")
    print("=" * 60)
    print(f"Search query: '{SEARCH_QUERY}'" if SEARCH_QUERY else "No search filter (all papers)")
    print(f"Max papers to collect: {MAX_PAPERS}")
    print(f"Max papers to check: {MAX_TO_CHECK}")
    print(f"Download PDFs: {DOWNLOAD_PDFS}")
    if START_DATE or END_DATE:
        date_range = f"{START_DATE or 'earliest'} to {END_DATE or 'latest'}"
        print(f"Date range: {date_range}")
    print("=" * 60)
    
    # Create scraper
    scraper = NBERScraper(search_query=SEARCH_QUERY, start_date=START_DATE, end_date=END_DATE)
    
    try:
        # Scrape papers
        papers = scraper.scrape_papers(
            max_papers=MAX_PAPERS,
            max_pages=MAX_TO_CHECK,
            download_pdfs=DOWNLOAD_PDFS
        )
        
        # Generate output filename if not specified
        if OUTPUT_FILENAME:
            filename = OUTPUT_FILENAME
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_part = f"_{SEARCH_QUERY.replace(' ', '_')}" if SEARCH_QUERY else ""
            filename = f"nber_papers{query_part}_{timestamp}.json"
        
        # Save results
        if scraper.save_to_json(filename):
            print(f"\n✅ Successfully saved {len(papers)} papers to {filename}")
            
            # Print summary
            print("\n📊 Summary:")
            print(f"Papers found: {len(papers)}")
            print(f"Papers with abstracts: {sum(1 for p in papers if p.get('abstract'))}")
            print(f"Papers with PDF URLs: {sum(1 for p in papers if p.get('pdf_url'))}")
            print(f"Papers with authors: {sum(1 for p in papers if p.get('authors'))}")
            
            # Show first few papers
            if papers:
                print(f"\n📄 First few papers:")
                for i, paper in enumerate(papers[:3], 1):
                    title = paper.get('title', 'No title')[:80]
                    authors = ', '.join(paper.get('authors', [])[:2])
                    if len(paper.get('authors', [])) > 2:
                        authors += f" (+ {len(paper.get('authors', [])) - 2} more)"
                    abstract = paper.get('abstract', 'No abstract available')[:200]
                    
                    print(f"  {i}. {title}{'...' if len(paper.get('title', '')) > 80 else ''}")
                    if authors:
                        print(f"     Authors: {authors}")
                    print(f"     Paper ID: {paper.get('paper_id', 'Unknown')}")
                    if paper.get('publication_date'):
                        print(f"     Date: {paper.get('publication_date')}")
                    print(f"     Abstract: {abstract}{'...' if len(paper.get('abstract', '')) > 200 else ''}")
                    print()
        else:
            print("❌ Failed to save results")
            
    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted by user")
        # Try to save partial results
        if scraper.papers:
            emergency_filename = f"nber_papers_interrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            if scraper.save_to_json(emergency_filename):
                print(f"💾 Saved {len(scraper.papers)} partial results to {emergency_filename}")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        # Try to save partial results
        if scraper.papers:
            error_filename = f"nber_papers_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            if scraper.save_to_json(error_filename):
                print(f"💾 Saved {len(scraper.papers)} partial results to {error_filename}")

if __name__ == "__main__":
    main() 