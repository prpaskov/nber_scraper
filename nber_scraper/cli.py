#!/usr/bin/env python3
"""
Command-line interface for NBER Papers Scraper
"""

import os
import sys
import click
from pathlib import Path

from .scraper import NBERScraper
from .analysis import PaperAnalyzer  
from .config import Config


@click.group()
@click.version_option()
def cli():
    """NBER Papers Scraper - Command-line interface for scraping NBER working papers."""
    pass


@cli.command()
@click.option('--query', '-q', default="AI", help='Search query (default: AI)')
@click.option('--pages', '-p', default=None, type=int, help='Maximum pages to scrape (default: all pages)')
@click.option('--output', '-o', default=None, help='Output JSON filename')
@click.option('--no-pdfs', is_flag=True, help='Skip PDF downloads')
@click.option('--delay', '-d', default=1.5, help='Delay between requests in seconds (default: 1.5)')
@click.option('--per-page', default=100, help='Papers per page (default: 100)')
@click.option('--output-dir', default="data", help='Output directory (default: data)')
def scrape(query, pages, output, no_pdfs, delay, per_page, output_dir):
    """Scrape NBER papers for the given search query."""
    
    click.echo(f"Starting NBER scraper...")
    click.echo(f"Search query: '{query}'")
    click.echo(f"Max pages: {pages if pages else 'ALL (unlimited)'}")
    click.echo(f"Download PDFs: {not no_pdfs}")
    click.echo(f"Output directory: {output_dir}")
    click.echo("-" * 50)
    
    # Setup configuration
    config = Config()
    config.update(
        request_delay=delay,
        papers_per_page=per_page,
        default_output_dir=output_dir,
        download_pdfs=not no_pdfs
    )
    
    # Initialize scraper
    click.echo("Initializing scraper...")
    scraper = NBERScraper(config)
    click.echo("Scraper initialized successfully!")
    
    try:
        # Scrape papers
        click.echo(f"\nStarting crawl for '{query}'...")
        papers = scraper.crawl_papers(
            search_query=query,
            max_pages=pages,
            download_pdfs=not no_pdfs
        )
        
        click.echo(f"Crawling completed! Found {len(papers)} papers total.")
        
        # Generate output filename if not provided
        if not output:
            safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_query = safe_query.replace(' ', '_').lower()
            output = f"nber_{safe_query}_papers.json"
        
        # Save results
        click.echo(f"Saving results to {output}...")
        output_path = scraper.save_to_json(output, output_dir)
        
        # Show results
        stats = scraper.get_summary_stats()
        click.echo("\nResults:")
        click.echo(f"  Total papers: {stats['total_papers']}")
        click.echo(f"  Papers with abstracts: {stats['papers_with_abstracts']}")
        click.echo(f"  Papers with PDFs: {stats['papers_with_pdf_urls']}")
        click.echo(f"  Saved to: {output_path}")
        
        if papers:
            click.echo(f"\nFirst paper: {papers[0].get('title', 'No title')}")
            click.echo(f"Has abstract: {'Yes' if papers[0].get('abstract') else 'No'}")
        
    except KeyboardInterrupt:
        click.echo("\nScraping interrupted by user.")
        if scraper.papers_data:
            emergency_file = f"nber_{query.lower()}_interrupted.json"
            emergency_path = scraper.save_to_json(emergency_file, output_dir)
            click.echo(f"Partial data saved to: {emergency_path}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"ERROR: {e}", err=True)
        click.echo(f"Error type: {type(e).__name__}", err=True)
        import traceback
        click.echo("Full traceback:", err=True)
        traceback.print_exc()
        if scraper.papers_data:
            emergency_file = f"nber_{query.lower()}_error.json"
            emergency_path = scraper.save_to_json(emergency_file, output_dir)
            click.echo(f"Partial data saved to: {emergency_path}")
        sys.exit(1)


@cli.command()
@click.argument('input_file')
@click.option('--output-dir', default="analysis", help='Output directory for analysis results')
@click.option('--top-n', default=10, help='Number of top items to show (default: 10)')
def analyze(input_file, output_dir, top_n):
    """Analyze scraped NBER papers data."""
    
    if not os.path.exists(input_file):
        click.echo(f"Error: Input file '{input_file}' not found.", err=True)
        sys.exit(1)
    
    click.echo(f"Analyzing papers from: {input_file}")
    click.echo(f"Output directory: {output_dir}")
    click.echo("-" * 50)
    
    try:
        # Create analyzer
        analyzer = PaperAnalyzer()
        analyzer.load_from_json(input_file)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Basic statistics
        stats = analyzer.get_summary_stats()
        click.echo("\nBasic Statistics:")
        for key, value in stats.items():
            click.echo(f"  {key.replace('_', ' ').title()}: {value}")
        
        # Top authors
        click.echo(f"\nTop {top_n} Authors:")
        top_authors = analyzer.get_top_authors(top_n)
        for i, (author, count) in enumerate(top_authors, 1):
            click.echo(f"  {i:2d}. {author}: {count} papers")
        
        # Top keywords
        click.echo(f"\nTop {top_n} Keywords:")
        keywords = analyzer.extract_keywords(top_n)
        for i, (keyword, count) in enumerate(keywords, 1):
            click.echo(f"  {i:2d}. {keyword}: {count} occurrences")
        
        # Generate visualizations if possible
        try:
            click.echo(f"\nGenerating visualizations...")
            
            # Year distribution
            year_plot = os.path.join(output_dir, "papers_by_year.png")
            analyzer.plot_papers_by_year(year_plot)
            click.echo(f"  Saved year distribution: {year_plot}")
            
            # Top authors
            authors_plot = os.path.join(output_dir, "top_authors.png")
            analyzer.plot_top_authors(authors_plot, top_n)
            click.echo(f"  Saved top authors: {authors_plot}")
            
            # Keywords word cloud
            wordcloud_plot = os.path.join(output_dir, "keywords_wordcloud.png")
            analyzer.create_wordcloud(wordcloud_plot)
            click.echo(f"  Saved word cloud: {wordcloud_plot}")
            
        except ImportError:
            click.echo("  Skipping visualizations (matplotlib/seaborn not available)")
        except Exception as e:
            click.echo(f"  Warning: Could not generate some visualizations: {e}")
            
    except Exception as e:
        click.echo(f"Error during analysis: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--query', '-q', default="test", help='Test search query')
def test(query):
    """Test the scraper with a simple query."""
    
    click.echo("Running scraper test...")
    click.echo(f"Test query: '{query}'")
    click.echo("-" * 30)
    
    try:
        # Quick test with minimal settings
        config = Config()
        config.update(request_delay=0.5, download_pdfs=False)
        
        scraper = NBERScraper(config)
        
        # Test basic functionality
        click.echo("Testing page retrieval...")
        response = scraper.get_page(f"{config.base_url}/papers")
        click.echo(f"  Base URL accessible: {response.status_code == 200}")
        
        # Test search
        click.echo("Testing search functionality...")
        papers = scraper.crawl_papers(
            search_query=query,
            max_pages=1,
            download_pdfs=False
        )
        
        click.echo(f"  Found {len(papers)} papers")
        
        if papers:
            click.echo("  Sample paper:")
            sample = papers[0]
            click.echo(f"    Title: {sample.get('title', 'No title')[:100]}...")
            click.echo(f"    Authors: {', '.join(sample.get('authors', [])[:3])}")
            click.echo(f"    Has abstract: {'Yes' if sample.get('abstract') else 'No'}")
        
        click.echo("\nTest completed successfully!")
        
    except Exception as e:
        click.echo(f"Test failed: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli() 