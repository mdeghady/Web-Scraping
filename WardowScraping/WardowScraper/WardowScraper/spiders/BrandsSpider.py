import scrapy


class BrandsspiderSpider(scrapy.Spider):
    name = "BrandsSpider"
    allowed_domains = ["wardow.com"]
    start_urls = ["https://www.wardow.com/marken"]

    def parse(self, response):
        pass
