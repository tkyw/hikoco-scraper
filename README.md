# Hikoco Product Scraper

A high-performance web scraper for extracting product information from Hikoco, a Korean beauty and skincare e-commerce store.

## Overview

This project provides tools to scrape product information from the Hikoco website, including product details, prices, and ingredients. It features multiple scraping approaches to handle different scenarios, from simple requests to dealing with JavaScript-rendered content.

## Features

- **Asynchronous scraping**: Fast, concurrent requests with aiohttp
- **JavaScript rendering**: Playwright integration for JS-heavy pages
- **Rate limit handling**: Smart retry mechanisms with exponential backoff
- **User-agent rotation**: Prevents detection and blocking
- **Progress tracking**: Visual feedback during scraping
- **Comprehensive error handling**: Robust extraction with fallbacks

## Requirements

- Python 3.7+
- Required packages:
  - requests
  - beautifulsoup4
  - pandas
  - aiohttp
  - tqdm
  - playwright (for JavaScript-rendered pages)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/hikoco-scraper.git
cd hikoco-scraper
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. If using the Playwright scraper:

```bash
pip install playwright
playwright install
```

## Usage

to access the project directory:

```bash
cd hikoco
```

To run the script and save it in json format:

```bash
scrapy crawl hikoco_spider -O {filename}.json
```

alternatively, you can run the script and save it in csv format:

```bash
scrapy crawl hikoco_spider -O {filename}.csv
```

alternatively, you can run the script and save it in xml format:

```bash
scrapy crawl hikoco_spider -O {filename}.xml
```

## Project Structure

```
hikoco/
├── hikoco/                  # Package directory
│   └── spiders/             # Spider implementations
│       └── hikoco_spider.py # Scrapy spider implementation
├── product-links.json       # Input file with product URLs
└── requirements.txt         # Project dependencies
```

## Configuration

You can adjust the following parameters in the scripts:

- `MAX_CONNECTIONS`: Control concurrent connection limit
- `TIMEOUT`: Set request timeout
- `USER_AGENTS`: Add or modify user agent strings
- `OUTPUT_FILE`: Change the output file path

## Handling Rate Limits

The scraper includes several strategies to avoid rate limiting:

1. **Random delays** between requests
2. **Exponential backoff** for 429 errors
3. **User-agent rotation**
4. **Request throttling** with connection limits

If you encounter persistent rate limiting:

- Increase the delay between requests
- Reduce concurrent connections
- Consider using proxies

## Output Format

The scraped data is saved in JSON format:

```json
[
  {
    "link": "https://hikoco.co.nz/products/example-product",
    "name": "Product Name",
    "price": "$29.00",
    "ingredients": "Water, Glycerin, etc."
  }
]
```

## Performance Tips

- For large datasets, use the async version (`mian.py`)
- Process links in batches when dealing with 1000+ products
- Run during off-peak hours to reduce server load
- Balance concurrency settings based on your network and target server capacity

## Troubleshooting

### Common Issues

1. **429 Too Many Requests**
   - Increase delay between requests
   - Reduce concurrent connections
   - Implement IP rotation

2. **Missing Data**
   - Check if website structure has changed
   - Update CSS selectors in the script
   - Use the Playwright version for JS-rendered content

3. **Script Crashes**
   - Check for rate limiting
   - Ensure all dependencies are installed
   - Verify input file format

## Ethical Considerations

This scraper is designed to be respectful of website resources:

- Uses appropriate delays between requests
- Limits concurrent connections
- Sets proper headers
- Implements backoff for errors

Always ensure you have permission to scrape the target website and comply with their terms of service.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a pull request.
