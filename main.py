import asyncio
import aiohttp
import pandas as pd
from bs4 import BeautifulSoup as bs
import time
import random
from tqdm import tqdm
import json
import logging
from aiohttp import ClientTimeout, TCPConnector

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('hikoco_scraper')

# Configure constants
MAX_CONNECTIONS = 5  # Limit concurrent connections to avoid overloading server
TIMEOUT = 30  # Request timeout in seconds
OUTPUT_FILE = "product_details.json"
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]


async def fetch_product_data(session, link, semaphore):
    """Fetch and parse data for a single product"""
    async with semaphore:
        try:
            # Add jitter to prevent rate limiting
            await asyncio.sleep(random.uniform(0.5, 2.0))

            # Prepare headers with random user agent
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://hikoco.co.nz/',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            # Make the request
            async with session.get(link, headers=headers, allow_redirects=False) as response:
                if response.status == 429:
                    logger.warning(f"Rate limited for {link}. Waiting and retrying...")
                    await asyncio.sleep(5 + random.uniform(1, 5))
                    return await fetch_product_data(session, link, semaphore)

                if response.status >= 400:
                    logger.error(f"Error {response.status} for {link}")
                    return None

                content = await response.text()

                # Parse with BeautifulSoup
                soup = bs(content, "html.parser")

                # Extract data with error handling for each field
                try:
                    name_element = soup.select_one(".h1.product-single__title")
                    name = name_element.text.strip() if name_element else "Name not found"
                except Exception as e:
                    logger.error(f"Error extracting name from {link}: {e}")
                    name = "Error extracting name"

                try:
                    price_element = soup.select_one(".visually-hidden")
                    price = price_element.text.strip() if price_element else "Price not found"
                except Exception as e:
                    logger.error(f"Error extracting price from {link}: {e}")
                    price = "Error extracting price"

                try:
                    ingredients_element = soup.select_one(".collapsible-content__inner.rte span.metafield-multi_line_text_field")
                    ingredients = ingredients_element.text.strip() if ingredients_element else "Ingredients not found"
                except Exception as e:
                    logger.error(f"Error extracting ingredients from {link}: {e}")
                    ingredients = "Error extracting ingredients"

                logger.info(f"Successfully scraped: {name}")

                return {
                    "link": link,
                    "name": name,
                    "price": price,
                    "ingredients": ingredients
                }

        except Exception as e:
            logger.error(f"Error processing {link}: {e}")
            return None


async def main():
    """Main function to process all links asynchronously"""
    start_time = time.time()

    # Load product links
    try:
        links = pd.read_json("product-links.json")["link"].to_list()
        logger.info(f"Loaded {len(links)} product links")
    except Exception as e:
        logger.error(f"Error loading product links: {e}")
        return

    # Create a semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(MAX_CONNECTIONS)

    # Configure client session with connection pooling and timeout
    connector = TCPConnector(limit=MAX_CONNECTIONS, force_close=True)
    timeout = ClientTimeout(total=TIMEOUT)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Create tasks for all links
        tasks = [fetch_product_data(session, link, semaphore) for link in links]

        # Execute all tasks with progress bar
        results = []
        for task in tqdm(asyncio.as_completed(tasks), total=len(links), desc="Scraping products"):
            result = await task
            if result:
                results.append(result)

        # Save results to file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        elapsed_time = time.time() - start_time
        logger.info(f"Scraped {len(results)} products in {elapsed_time:.2f} seconds")
        logger.info(f"Results saved to {OUTPUT_FILE}")

        # Print sample of results
        print(f"\nSample of {min(3, len(results))} results:")
        for i, item in enumerate(results[:3]):
            print(f"{i+1}. {item['name']} - {item['price']}")


if __name__ == "__main__":
    asyncio.run(main())
