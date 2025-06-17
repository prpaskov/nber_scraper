# NBER Papers Scraper

[[work in progress]] - a simple Python script for scraping NBER working papers. 

## Quick Start

### 1. Setup (one-time)

```bash
# Clone the repository
git clone <your-repo-url>
cd nber_scraper

# Create a virtual environment  
python -m venv nber_env
source nber_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the scraper

**Easy way:** Edit `run_scraper.py` and run it:

```python
# Edit these settings in run_scraper.py:
SEARCH_QUERY = "machine learning"    # What to search for
MAX_PAGES = 10                       # How many pages (each page ≈ 100 papers)  
DOWNLOAD_PDFS = False                # True if you want PDF files
OUTPUT_FILENAME = None               # Custom filename or None for auto-generated
```

Then run:
```bash
python run_scraper.py
```

**Command line way (alternative):**
```bash
python -m nber_scraper scrape --query "AI" --pages 5
python -m nber_scraper scrape --query "climate change" --pages 3 --output my_papers.json
```

> **Note:** Both methods do exactly the same thing. The `run_scraper.py` script is simpler - just edit the settings and run. The command line interface is more flexible for one-off runs without editing files.

### 3. Analyze results

```bash
python -m nber_scraper analyze nber_ai_papers.json
```

## Search Details

**What fields are searched:**
- **Paper Title**
- **Abstract content**

**Search behavior:**
- Uses whole-word matching to avoid false positives (e.g., "AI" won't match "rain" or "available")
- For "AI" searches, also finds related terms: "artificial intelligence", "machine learning", "deep learning", "neural network", "algorithm"
- Case-insensitive matching
- **Note:** NBER doesn't provide JEL codes or keywords in the accessible metadata

**Date filtering:**
- Optional start/end date filtering (format: "2023/01/01" or "2023-01-01")
- Papers without dates are included when date filters are active (to be safe)

## What You Get

- **JSON file** in `data/` folder with all paper metadata
- **PDF files** in `downloads/` folder (if you set `DOWNLOAD_PDFS = True`)
- **Analysis charts** when you run the analyze command

## Example Output

```json
[
  {
    "paper_id": "w12345",
    "title": "Artificial Intelligence and Economic Growth",
    "authors": ["Jane Smith", "John Doe"],
    "abstract": "This paper examines...",
    "url": "https://www.nber.org/papers/w12345",
    "pdf_url": "https://www.nber.org/system/files/working_papers/w12345/w12345.pdf",
    "date": "2023-01-15",
    "scraped_at": "2024-01-15T10:30:00"
  }
]
```

## Project Structure

```
nber_scraper/
├── run_scraper.py          # ← MAIN SCRIPT - Edit and run this!
├── requirements.txt        # Python dependencies  
├── nber_env/              # Virtual environment (you create this)
├── nber_scraper/          # Package code
├── data/                  # Output JSON files
└── downloads/             # PDF files (if downloaded)
```

## Commands Reference

- `python run_scraper.py` - Main way to run (edit the file first)
- `python -m nber_scraper scrape --help` - See all command line options
- `python -m nber_scraper test` - Test if everything works
- `python -m nber_scraper analyze <file.json>` - Analyze scraped data

## Python API (Advanced)

If you want to use this in your own code:

```python
from nber_scraper import NBERScraper

scraper = NBERScraper()
papers = scraper.crawl_papers("machine learning", max_pages=3)
scraper.save_to_json("my_papers.json")
```