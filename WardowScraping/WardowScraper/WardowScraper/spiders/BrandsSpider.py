import scrapy


class BrandsspiderSpider(scrapy.Spider):
    name = "BrandsSpider"
    allowed_domains = ["wardow.com"]
    start_urls = ["https://www.wardow.com/marken"]

    def parse(self, response):
        """
        Parse the response from the brands page and extract brand names and URLs.
        :param response: The response object containing the HTML content of the brands page.
        :return: A generator yielding dictionaries with brand names and URLs.
        """

        # The Website Stores the brand names and URLs in a div with class "brand-group"
        # Extract all brand groups in the response
        brand_groups = response.css("div.brand-group")

        # Iterate through each brand group
        for brand_group in brand_groups:
            # In every brand group the brands stored in an ul element
            # and every brand in an li element
            brands = brand_group.css("ul li")

            # Iterate through each brand
            for brand in brands:
                # Extract the brand name and URL
                brand_name = brand.css("a::text").get().strip()
                brand_url = brand.css("a::attr(href)").get()

                # Yield the brand name and URL as a dictionary
                yield {
                    "brand_name": brand_name,
                    "brand_url": brand_url
                }

