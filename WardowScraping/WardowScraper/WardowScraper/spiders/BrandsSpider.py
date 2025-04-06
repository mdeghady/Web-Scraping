import scrapy


class BrandsspiderSpider(scrapy.Spider):
    name = "BrandsSpider"
    allowed_domains = ["wardow.com"]
    start_urls = ["https://www.wardow.com/en/brands"]

    def parse(self, response):
        """
        Parse the response from the brands page and extract brand names and URLs.
        :param response: The response object containing the HTML content of the brands page.
        :return: None
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

                # Follow the brand URL to get all products for the brand
                yield response.follow(brand_url ,
                                      callback=self.parse_brand,
                                      meta={"brand_name": brand_name})

    def parse_brand(self, response):
        """
        Parse the response from the brand page and extract product URLs.
        :param response: The response object containing the HTML content of the brand page.
        :return: Generator yielding product URLs and brand name.
        """
        # The Website Stores the products in a div with class "category-products"
        # and ul element with class "products-grid products-grid--max-4-col"
        # then every product is in an li element with data-id attribute
        cur_page_products = response.css('div.category-products\
                        ul.products-grid.products-grid--max-4-col li[data-id]')

        # Iterate through each product in the page
        for product in cur_page_products:
            # In every product the product URL is stored in a div with class "product-tile"
            # then in another div with class "product-tile__visual"
            # and finally in an "a" element with class "product-tile__img"
            product_url = product.css('div.product-tile\
                                        div.product-tile__visual\
                                         a.product-tile__img::attr(href)').get()

            # Yield the product name and URL
            yield {
                "brand_name": response.meta["brand_name"],
                "product_url": product_url
            }

        # Check if there is a next page
        next_page = response.css('button.button.btn-subtle.next::attr(value)').get()

        if next_page:
            # If there is a next page, follow the link to the next page
            next_page_url = response.urljoin(next_page)
            yield response.follow(next_page_url,
                                  callback=self.parse_brand,
                                  meta={"brand_name": response.meta["brand_name"]})
