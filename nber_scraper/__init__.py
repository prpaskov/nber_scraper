"""
NBER Papers Scraper

A production-ready Python package for scraping NBER working papers,
extracting abstracts, and downloading PDFs.
"""

__version__ = "1.0.0"
__author__ = "Patricia Paskov"
__email__ = "patriciarosepaskov@gmail.com"

from .scraper import NBERScraper
from .analysis import PaperAnalyzer
from .config import Config

__all__ = ["NBERScraper", "PaperAnalyzer", "Config"] 