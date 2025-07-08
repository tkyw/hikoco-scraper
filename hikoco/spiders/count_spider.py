import scrapy

class CountSpider(scrapy.Spider):
    name = 'count'
    custom_settings = {
            'CONCURRENT_REQUESTS': 25,  # Lower concurrency
            'DOWNLOAD_DELAY': 0.7,       # 3 seconds delay between requests
            'RANDOMIZE_DOWNLOAD_DELAY': True,
            'AUTOTHROTTLE_ENABLED': True,
            'AUTOTHROTTLE_START_DELAY': 3,
            'AUTOTHROTTLE_MAX_DELAY': 30,
            'AUTOTHROTTLE_TARGET_CONCURRENCY': 25,
            'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }
    allowed_domains = ['hikoco.co.nz']
    meta = {
        "playwright": True,
        'playwright_page_kwargs': {
                                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
                            }
    }

    async def start(self):
        url = "https://hikoco.co.nz/pages/brand"
        yield scrapy.Request(url=url, callback=self.parse, meta=CountSpider.meta)

    def parse(self, response):
        for url in response.css(".main-content .table-wrapper a::attr(href)").getall():
            yield scrapy.Request(url=url, callback=self.parse_product_page)

    def parse_product_page(self, response):
        yield {
            "page": response.url,
            "Total products": response.css(".collection-filter__item.collection-filter__item--count.small--hide::text").re(r"(\d+) product")[0]
        }
