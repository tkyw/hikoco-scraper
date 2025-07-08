import scrapy


class HikocoSpiderSpider(scrapy.Spider):
    name = "hikoco_spider"
    custom_settings = {
            'CONCURRENT_REQUESTS': 20,  # Lower concurrency
            'DOWNLOAD_DELAY': 1,       # 3 seconds delay between requests
            'RANDOMIZE_DOWNLOAD_DELAY': True,
            'AUTOTHROTTLE_ENABLED': True,
            'AUTOTHROTTLE_START_DELAY': 3,
            'AUTOTHROTTLE_MAX_DELAY': 30,
            'AUTOTHROTTLE_TARGET_CONCURRENCY': 5.0,
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
        yield scrapy.Request(url=url, callback=self.parse, meta=HikocoSpiderSpider.meta)

    def parse(self, response):
        for url in response.css(".main-content .table-wrapper a::attr(href)").getall():
            yield scrapy.Request(url=url, callback=self.parse_product_page)

    def parse_product_page(self, response):
        for url in response.css(".new-grid.product-grid.collection-grid .grid-item .grid-item__content a.grid-item__link::attr(href)").getall():
            url = response.urljoin(url)
            yield scrapy.Request(url=url, callback=self.parse_product_details)
        yield from response.follow_all(css=".next a", callback=self.parse_product_page)

    def parse_product_details(self, response):
        try:
            price = response.css(".product__price .visually-hidden::text").get().strip()
        except AttributeError:
            price = response.css(".product__price span::text").get().strip()
        yield {
            "link": response.url,
            'name': response.css(".h1.product-single__title::text").get().strip(),
            'price': price,
            'ingredients': response.css(".collapsible-content__inner.rte span.metafield-multi_line_text_field::text").get()
        }
