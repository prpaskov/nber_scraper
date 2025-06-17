"""
Analysis utilities for NBER papers data
"""

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    from wordcloud import WordCloud
    ANALYSIS_DEPS_AVAILABLE = True
except ImportError:
    ANALYSIS_DEPS_AVAILABLE = False
    logger.warning("Analysis dependencies not available. Install pandas, matplotlib, seaborn, and wordcloud for full functionality.")


class PaperAnalyzer:
    """Analyzer for NBER papers data with summary statistics and visualizations."""
    
    def __init__(self, data_source: Optional[str] = None):
        """
        Initialize the analyzer.
        
        Args:
            data_source: Path to JSON file or None to use empty dataset
        """
        self.papers_data: List[Dict[str, Any]] = []
        
        if data_source:
            self.load_data(data_source)
    
    def load_data(self, filepath: str) -> None:
        """
        Load papers data from JSON file.
        
        Args:
            filepath: Path to JSON file containing papers data
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.papers_data = json.load(f)
            logger.info(f"Loaded {len(self.papers_data)} papers from {filepath}")
        except Exception as e:
            logger.error(f"Error loading data from {filepath}: {e}")
            raise
    
    def add_data(self, papers: List[Dict[str, Any]]) -> None:
        """
        Add papers data directly.
        
        Args:
            papers: List of paper dictionaries
        """
        self.papers_data.extend(papers)
        logger.info(f"Added {len(papers)} papers to analyzer")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive summary statistics.
        
        Returns:
            Dictionary containing summary statistics
        """
        if not self.papers_data:
            return {"total_papers": 0}
        
        # Basic counts
        stats = {
            "total_papers": len(self.papers_data),
            "papers_with_abstracts": sum(1 for p in self.papers_data if p.get('abstract')),
            "papers_with_pdf_urls": sum(1 for p in self.papers_data if p.get('pdf_url')),
            "papers_with_authors": sum(1 for p in self.papers_data if p.get('authors')),
            "papers_with_jel_codes": sum(1 for p in self.papers_data if p.get('jel_codes')),
            "papers_with_dates": sum(1 for p in self.papers_data if p.get('date')),
        }
        
        # Author statistics
        all_authors = []
        for paper in self.papers_data:
            if paper.get('authors'):
                all_authors.extend(paper['authors'])
        
        stats.update({
            "total_authors": len(all_authors),
            "unique_authors": len(set(all_authors)),
            "avg_authors_per_paper": len(all_authors) / len(self.papers_data) if self.papers_data else 0
        })
        
        # Abstract statistics
        abstracts = [p.get('abstract', '') for p in self.papers_data if p.get('abstract')]
        if abstracts:
            abstract_lengths = [len(abstract.split()) for abstract in abstracts]
            stats.update({
                "avg_abstract_length": sum(abstract_lengths) / len(abstract_lengths),
                "min_abstract_length": min(abstract_lengths),
                "max_abstract_length": max(abstract_lengths)
            })
        
        # JEL codes statistics
        all_jel_codes = []
        for paper in self.papers_data:
            if paper.get('jel_codes'):
                all_jel_codes.extend(paper['jel_codes'])
        
        stats.update({
            "total_jel_codes": len(all_jel_codes),
            "unique_jel_codes": len(set(all_jel_codes))
        })
        
        # Data collection info
        scrape_dates = [p.get('scraped_at') for p in self.papers_data if p.get('scraped_at')]
        if scrape_dates:
            stats.update({
                "earliest_scrape": min(scrape_dates),
                "latest_scrape": max(scrape_dates)
            })
        
        return stats
    
    def analyze_by_year(self) -> Dict[str, int]:
        """
        Analyze papers by publication year.
        
        Returns:
            Dictionary mapping years to paper counts
        """
        year_counts = defaultdict(int)
        
        for paper in self.papers_data:
            date_str = paper.get('date', '')
            if date_str:
                # Extract year from various date formats
                year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
                if year_match:
                    year = year_match.group()
                    year_counts[year] += 1
        
        return dict(sorted(year_counts.items()))
    
    def get_top_authors(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Get most prolific authors.
        
        Args:
            top_n: Number of top authors to return
            
        Returns:
            List of (author_name, paper_count) tuples
        """
        author_counts = Counter()
        
        for paper in self.papers_data:
            if paper.get('authors'):
                for author in paper['authors']:
                    author_counts[author] += 1
        
        return author_counts.most_common(top_n)
    
    def get_top_jel_codes(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Get most common JEL codes.
        
        Args:
            top_n: Number of top JEL codes to return
            
        Returns:
            List of (jel_code, count) tuples
        """
        jel_counts = Counter()
        
        for paper in self.papers_data:
            if paper.get('jel_codes'):
                for code in paper['jel_codes']:
                    jel_counts[code] += 1
        
        return jel_counts.most_common(top_n)
    
    def extract_keywords(self, top_n: int = 20, min_length: int = 4) -> List[Tuple[str, int]]:
        """
        Extract common keywords from abstracts.
        
        Args:
            top_n: Number of top keywords to return
            min_length: Minimum word length to consider
            
        Returns:
            List of (keyword, frequency) tuples
        """
        # Common stop words to exclude
        stop_words = {
            'the', 'this', 'that', 'with', 'from', 'they', 'have', 'been', 'their',
            'are', 'was', 'were', 'will', 'would', 'could', 'should', 'may', 'might',
            'can', 'does', 'did', 'has', 'had', 'also', 'more', 'most', 'some', 'any',
            'and', 'but', 'for', 'not', 'you', 'all', 'each', 'one', 'two', 'both',
            'between', 'among', 'within', 'without', 'through', 'during', 'before',
            'after', 'above', 'below', 'into', 'onto', 'upon', 'over', 'under',
            'paper', 'study', 'research', 'analysis', 'data', 'results', 'find',
            'found', 'show', 'shows', 'using', 'used', 'use', 'based', 'approach'
        }
        
        word_counts = Counter()
        
        for paper in self.papers_data:
            abstract = paper.get('abstract', '')
            if abstract:
                # Clean and extract words
                words = re.findall(r'\b[a-zA-Z]+\b', abstract.lower())
                for word in words:
                    if len(word) >= min_length and word not in stop_words:
                        word_counts[word] += 1
        
        return word_counts.most_common(top_n)
    
    def to_dataframe(self) -> 'pd.DataFrame':
        """
        Convert papers data to pandas DataFrame.
        
        Returns:
            DataFrame containing papers data
            
        Raises:
            ImportError: If pandas is not available
        """
        if not ANALYSIS_DEPS_AVAILABLE:
            raise ImportError("pandas is required for DataFrame functionality")
        
        # Flatten the data for DataFrame
        df_data = []
        for paper in self.papers_data:
            row = {
                'paper_id': paper.get('paper_id'),
                'title': paper.get('title'),
                'abstract': paper.get('abstract'),
                'url': paper.get('url'),
                'pdf_url': paper.get('pdf_url'),
                'date': paper.get('date'),
                'scraped_at': paper.get('scraped_at'),
                'num_authors': len(paper.get('authors', [])),
                'num_jel_codes': len(paper.get('jel_codes', [])),
                'has_abstract': bool(paper.get('abstract')),
                'has_pdf': bool(paper.get('pdf_url')),
                'abstract_length': len(paper.get('abstract', '').split()) if paper.get('abstract') else 0
            }
            
            # Add authors as comma-separated string
            if paper.get('authors'):
                row['authors'] = ', '.join(paper['authors'])
            else:
                row['authors'] = None
            
            # Add JEL codes as comma-separated string
            if paper.get('jel_codes'):
                row['jel_codes'] = ', '.join(paper['jel_codes'])
            else:
                row['jel_codes'] = None
            
            df_data.append(row)
        
        return pd.DataFrame(df_data)
    
    def create_word_cloud(self, output_path: str = "wordcloud.png", 
                         width: int = 800, height: int = 400) -> None:
        """
        Create a word cloud from abstracts.
        
        Args:
            output_path: Path to save the word cloud image
            width: Width of the image
            height: Height of the image
            
        Raises:
            ImportError: If wordcloud is not available
        """
        if not ANALYSIS_DEPS_AVAILABLE:
            raise ImportError("wordcloud is required for word cloud functionality")
        
        # Combine all abstracts
        all_text = ' '.join([
            paper.get('abstract', '') for paper in self.papers_data 
            if paper.get('abstract')
        ])
        
        if not all_text:
            logger.warning("No abstracts available for word cloud generation")
            return
        
        # Create word cloud
        wordcloud = WordCloud(
            width=width, 
            height=height, 
            background_color='white',
            max_words=100,
            colormap='viridis'
        ).generate(all_text)
        
        # Save to file
        wordcloud.to_file(output_path)
        logger.info(f"Word cloud saved to {output_path}")
    
    def plot_papers_by_year(self, output_path: str = "papers_by_year.png") -> None:
        """
        Create a bar plot of papers by year.
        
        Args:
            output_path: Path to save the plot
            
        Raises:
            ImportError: If matplotlib/seaborn is not available
        """
        if not ANALYSIS_DEPS_AVAILABLE:
            raise ImportError("matplotlib and seaborn are required for plotting")
        
        year_counts = self.analyze_by_year()
        
        if not year_counts:
            logger.warning("No year data available for plotting")
            return
        
        plt.figure(figsize=(12, 6))
        years = list(year_counts.keys())
        counts = list(year_counts.values())
        
        sns.barplot(x=years, y=counts)
        plt.title('NBER Papers by Year')
        plt.xlabel('Year')
        plt.ylabel('Number of Papers')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Plot saved to {output_path}")
    
    def generate_report(self, output_dir: str = "analysis_report") -> str:
        """
        Generate a comprehensive analysis report.
        
        Args:
            output_dir: Directory to save report files
            
        Returns:
            Path to the main report file
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate summary statistics
        stats = self.get_summary_stats()
        
        # Create report content
        report_lines = [
            "# NBER Papers Analysis Report",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary Statistics",
            f"- Total papers: {stats.get('total_papers', 0)}",
            f"- Papers with abstracts: {stats.get('papers_with_abstracts', 0)}",
            f"- Papers with PDF URLs: {stats.get('papers_with_pdf_urls', 0)}",
            f"- Papers with authors: {stats.get('papers_with_authors', 0)}",
            f"- Unique authors: {stats.get('unique_authors', 0)}",
            f"- Average authors per paper: {stats.get('avg_authors_per_paper', 0):.1f}",
            "",
            "## Top Authors",
        ]
        
        top_authors = self.get_top_authors(10)
        for i, (author, count) in enumerate(top_authors, 1):
            report_lines.append(f"{i}. {author}: {count} papers")
        
        report_lines.extend([
            "",
            "## Top JEL Codes",
        ])
        
        top_jel = self.get_top_jel_codes(10)
        for i, (code, count) in enumerate(top_jel, 1):
            report_lines.append(f"{i}. {code}: {count} papers")
        
        report_lines.extend([
            "",
            "## Common Keywords",
        ])
        
        keywords = self.extract_keywords(20)
        for i, (keyword, count) in enumerate(keywords, 1):
            report_lines.append(f"{i}. {keyword}: {count} occurrences")
        
        # Save text report
        report_path = os.path.join(output_dir, "analysis_report.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        # Generate visualizations if possible
        if ANALYSIS_DEPS_AVAILABLE:
            try:
                self.plot_papers_by_year(os.path.join(output_dir, "papers_by_year.png"))
                self.create_word_cloud(os.path.join(output_dir, "abstract_wordcloud.png"))
            except Exception as e:
                logger.warning(f"Error generating visualizations: {e}")
        
        # Save DataFrame if possible
        if ANALYSIS_DEPS_AVAILABLE:
            try:
                df = self.to_dataframe()
                df.to_csv(os.path.join(output_dir, "papers_data.csv"), index=False)
                logger.info("Saved papers data to CSV")
            except Exception as e:
                logger.warning(f"Error saving CSV: {e}")
        
        logger.info(f"Analysis report generated in {output_dir}")
        return report_path 