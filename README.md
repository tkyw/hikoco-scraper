# Hikoco Product Scraper

A web scraper for extracting product information from Hikoco, a Korean beauty and skincare e-commerce store.

## Overview

This project provides tools to scrape product information from the Hikoco website, including product details, prices, and ingredients.

## Features

- Extract product names, prices, and ingredients
- Handle rate limiting and retries
- Async support for faster scraping
- BeautifulSoup and Playwright integration

## Installation

1. Clone the repository:

```bash
git clone https://github.com/tkyw/hikoco-scraper.git
cd hikoco-scraper
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Create a `product-links.json` file with product URLs (see `product-links.json.sample`)
2. first, change directory to the project folder

```bash
cd hikoco
```

3. run the scraper and output to json Format

```bash
scrapy crawl hikoco -O {filename}.json
```

4. Alternative (csv)

```bash
scrapy crawl hikoco -O {filename}.csv
```

## Input Format

Create a `product-links.json` file with this structure:

```json
{
  "link": [
    "https://hikoco.co.nz/products/product-1",
    "https://hikoco.co.nz/products/product-2"
  ]
}
```

## Output Format

The scraper outputs a JSON file with product data:

```json
[
  {
    "link": "https://hikoco.co.nz/products/example",
    "name": "Product Name",
    "price": "$29.00",
    "ingredients": "Water, Glycerin, etc."
  }
]
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a pull request.
