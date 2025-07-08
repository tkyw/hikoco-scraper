import asyncio
import random
import time
import json
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("abib_scraper")

# Target URL
TARGET_URL = "https://hikoco.co.nz/collections/abib"

# Output filename
OUTPUT_FILE = "abib_products.json"


async def extract_text_with_fallbacks(element, selectors):
    """Extract text using multiple fallback selectors"""
    for selector in selectors:
        found = element.select_one(selector)
        if found:
            return found.get_text(strip=True)
    return None


async def extract_link_with_fallbacks(element, selectors):
    """Extract href attribute using multiple fallback selectors"""
    for selector in selectors:
        found = element.select_one(selector)
        if found and found.get('href'):
            return found.get('href')
    return None


async def extract_image_with_fallbacks(element, selectors):
    """Extract image src using multiple fallback selectors"""
    for selector in selectors:
        found = element.select_one(selector)
        if found:
            for attr in ['src', 'data-src', 'data-lazy-src', 'srcset']:
                img_src = found.get(attr)
                if img_src:
                    return img_src
    return None


async def clean_price(price_text):
    """Clean and normalize price text"""
    if not price_text:
        return None

    # Remove extra whitespace and newlines
    price_text = ' '.join(price_text.split())

    return price_text


async def parse_products_with_bs4(soup, url):
    """Parse products using BeautifulSoup"""
    results = []

    # Multiple selectors to find products
    product_selectors = [
        '.grid-product',
        '.product-item',
        '.product-card',
        '[class*="product"]',
        '.collection-product'
    ]

    products = []
    for selector in product_selectors:
        products = soup.select(selector)
        if products:
            logger.info(f"Found {len(products)} products using selector: {selector}")
            break

    if not products:
        logger.warning("No products found with any selector")
        return results

    for product in products:
        try:
            # Extract product details with multiple fallback selectors
            title = await extract_text_with_fallbacks(product, [
                '.grid-product__title',
                '.product-title',
                '.product-name',
                'h3',
                'h2',
                '[class*="title"]'
            ])

            price = await extract_text_with_fallbacks(product, [
                '.grid-product__price',
                '.product-price',
                '.price',
                '[class*="price"]'
            ])

            # Clean up price
            price = await clean_price(price)

            # Extract link
            link = await extract_link_with_fallbacks(product, [
                'a',
                '[href]'
            ])

            if link and not link.startswith('http'):
                link = urljoin(url, link)

            # Extract image
            image = await extract_image_with_fallbacks(product, [
                '.grid-product__image img',
                '.product-image img',
                'img'
            ])

            # Extract brand (if available)
            brand = await extract_text_with_fallbacks(product, [
                '.brand',
                '.product-brand',
                '[class*="brand"]'
            ]) or 'Abib'

            # Extract reviews/rating
            reviews = await extract_text_with_fallbacks(product, [
                '.reviews',
                '.rating',
                '[class*="review"]'
            ])

            # Extract availability
            availability = await extract_text_with_fallbacks(product, [
                '.availability',
                '.stock',
                '[class*="stock"]'
            ])

            # Extract sale/discount info
            sale_info = await extract_text_with_fallbacks(product, [
                '.sale',
                '.discount',
                '[class*="sale"]',
                '[class*="discount"]'
            ])

            if title and title.strip():
                results.append({
                    'title': title.strip(),
                    'price': price,
                    'link': link,
                    'image': image,
                    'brand': brand.strip() if brand else 'Abib',
                    'reviews': reviews.strip() if reviews else None,
                    'availability': availability.strip() if availability else None,
                    'sale_info': sale_info.strip() if sale_info else None,
                    'source_url': url
                })

        except Exception as e:
            logger.error(f"Error extracting product: {e}")
            continue

    return results


async def get_next_page_link(soup, url):
    """Extract the next page link using BeautifulSoup"""
    # Multiple selectors for pagination
    next_page_selectors = [
        'a[aria-label="Next"]',
        'a.next',
        'li.next a',
        '.pagination a[rel="next"]',
        '.pagination-next a',
        'a[rel="next"]',
        '.next a'
    ]

    for selector in next_page_selectors:
        next_page = soup.select_one(selector)
        if next_page and next_page.get('href'):
            next_url = next_page.get('href')
            if next_url:
                if not next_url.startswith('http'):
                    next_url = urljoin(url, next_url)
                return next_url

    return None


async def scrape_with_playwright(url, retry_count=0):
    """Scrape page with Playwright and parse with BeautifulSoup"""
    if retry_count >= 5:
        logger.error(f"Maximum retries reached for {url}")
        return []

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor'
            ]
        )

        try:
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0',
                    'Referer': 'https://hikoco.co.nz/'
                }
            )

            # Add cookies to seem more like a real browser
            await context.add_cookies([
                {
                    'name': 'visited',
                    'value': 'true',
                    'domain': 'hikoco.co.nz',
                    'path': '/'
                }
            ])

            page = await context.new_page()

            # Remove webdriver flag and add other evasions
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });

                // Override the permissions
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
                );
            """)

            # Add random delay before visiting
            delay = random.uniform(2, 5)
            logger.info(f"Waiting {delay:.2f}s before visiting {url}")
            await asyncio.sleep(delay)

            try:
                logger.info(f"Loading page: {url}")
                response = await page.goto(url, wait_until='networkidle', timeout=60000)

                if response.status == 429:
                    # Exponential backoff
                    wait_time = min(60, 2 ** retry_count + random.uniform(5, 15))
                    logger.warning(f"Rate limited (429), waiting {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                    await browser.close()
                    return await scrape_with_playwright(url, retry_count + 1)

                if response.status >= 400:
                    logger.error(f"HTTP Error {response.status}: {url}")
                    await browser.close()
                    if response.status in [500, 502, 503, 504]:
                        wait_time = random.uniform(5, 15)
                        logger.info(f"Server error, waiting {wait_time:.2f}s before retry")
                        await asyncio.sleep(wait_time)
                        return await scrape_with_playwright(url, retry_count + 1)
                    return []

                # Wait for page to fully render
                await page.wait_for_load_state('networkidle')

                # Human-like behavior
                await asyncio.sleep(random.uniform(1, 3))
                await page.mouse.move(random.randint(100, 700), random.randint(100, 700))
                await asyncio.sleep(random.uniform(0.1, 0.5))

                # Scroll down slowly to trigger lazy loading
                await page.evaluate("""
                    const scrollHeight = document.body.scrollHeight;
                    const viewportHeight = window.innerHeight;
                    const scrollSteps = 4;

                    for (let i = 0; i <= scrollSteps; i++) {
                        window.scrollTo(0, i * (scrollHeight / scrollSteps));
                    }
                """)

                await asyncio.sleep(random.uniform(2, 4))

                # Wait for common product selectors
                try:
                    await page.wait_for_selector(".grid-product, .product-item, .product-card", timeout=10000)
                except:
                    logger.warning("Couldn't find product selectors, continuing anyway")

                # Get page content and parse with BeautifulSoup
                html_content = await page.content()
                soup = BeautifulSoup(html_content, 'html.parser')

                # Extract products
                page_results = await parse_products_with_bs4(soup, url)
                results.extend(page_results)

                # Check for next page
                next_page_url = await get_next_page_link(soup, url)
                if next_page_url:
                    logger.info(f"Found next page: {next_page_url}")

                    # Add delay before going to next page
                    await asyncio.sleep(random.uniform(3, 7))

                    # Get results from next page
                    next_page_results = await scrape_with_playwright(next_page_url)
                    results.extend(next_page_results)

            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                if retry_count < 4:  # Retry with incremental backoff
                    wait_time = 2 ** retry_count + random.uniform(2, 10)
                    logger.info(f"Retrying in {wait_time:.2f}s (attempt {retry_count + 1})")
                    await asyncio.sleep(wait_time)
                    await browser.close()
                    return await scrape_with_playwright(url, retry_count + 1)

        finally:
            await browser.close()

    return results


async def main():
    """Main entry point for the scraper"""
    start_time = time.time()
    logger.info(f"Starting scraper for URL: {TARGET_URL}")

    try:
        results = await scrape_with_playwright(TARGET_URL)

        # Save results to file
        if results:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"Scraped {len(results)} products. Data saved to {OUTPUT_FILE}")
        else:
            logger.warning("No products were scraped!")

    except Exception as e:
        logger.error(f"Error in main process: {e}")

    finally:
        elapsed_time = time.time() - start_time
        logger.info(f"Scraping completed in {elapsed_time:.2f} seconds")


# Entry point
if __name__ == "__main__":
    asyncio.run(main())
