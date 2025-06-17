"""
Configuration settings for NBER Papers Scraper
"""

class Config:
    """Configuration settings with sensible defaults."""
    
    def __init__(self):
        # Scraping settings
        self.base_url = "https://www.nber.org"
        self.request_delay = 1.5  # Seconds between requests
        self.max_retries = 3
        self.timeout = 30
        
        # Output settings  
        self.default_output_dir = "data"
        self.download_pdfs = True
        self.papers_per_page = 100
        
        # Search settings
        self.default_search_query = "AI"
        self.default_max_pages = None  # None = all pages
        
        # Logging
        self.log_level = "INFO"
        
        # User agent for requests
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    def update(self, **kwargs):
        """Update configuration with new values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration option: {key}")
    
    def __repr__(self):
        attrs = [f"{k}={v}" for k, v in self.__dict__.items()]
        return f"Config({', '.join(attrs)})" 