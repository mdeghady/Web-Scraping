from locale import currency

import scrapy
import re


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
        :return: None
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

            # Follow the product URL to get the product details
            yield response.follow(product_url,
                                  callback=self.parse_product,
                                  meta={"brand_name": response.meta["brand_name"]})

        # Check if there is a next page
        next_page = response.css('button.button.btn-subtle.next::attr(value)').get()

        if next_page:
            # If there is a next page, follow the link to the next page
            next_page_url = response.urljoin(next_page)
            yield response.follow(next_page_url,
                                  callback=self.parse_brand,
                                  meta={"brand_name": response.meta["brand_name"]})

    def parse_product(self, response):
        """
        Parse the response from the product page and extract product details.
        :param response: The response object containing the HTML content of the product page.
        :return: None
        """
        # Every color for the same product may have different price
        # So I will deal with every color as a different product
        # The Website Stores the product colors in a div with class "product-shop"
        # and div element with class "colors"
        cur_product_colors = response.css('div.product-shop div.colors ul li')

        # Iterate through each color
        for product_color in cur_product_colors:
            # Check if the current color is checked or not
            # if the current color is the color displayed in the product page
            # It won't have url to direct to the product color page
            color_url = product_color.css('a::attr(href)').get()

            if color_url is None:
                # If the color URL is None, it means this is the current color
                # Which is displayed in the product page
                yield self.extract_product_data(response)
            else:
                # If the color URL is not None, it means this is a different color
                # Follow the color URL to get the product details
                yield response.follow(color_url,
                                      callback=self.extract_product_data,
                                      meta={"brand_name": response.meta["brand_name"]})


    def extract_product_data(self, response):
        """
        Extract product details from the response.
        :param response: The response object containing the HTML content of the product page.
        :return: A dictionary containing product details.
        """
        # Extract the first image URL & number of available images
        all_product_images = response.css('img.gallery-image::attr(src)').getall()
        first_image_url = all_product_images[0]
        number_of_images = len(all_product_images)

        # The Website Stores the product details in a div with class "product-essential"
        product_details = response.css('div.product-essential')

        # Get Brand Name
        brand_name = response.meta["brand_name"]

        # Get Product URL
        product_url = response.url

        # Product Shop Details [Name, Price, Color]
        product_shop  = product_details.css('div.product-shop')
        product_name  = product_shop.css('span.product-name::text').get() # Extract Product Name
        product_color = product_shop.css('div.colors p.headline span::text').get() # Extract Product Color

        # Extract Product Price
        price_data = product_shop.css('div.price-info')
        old_price, new_price, price_currency , discount_amount = self._parse_price_data(price_data)

        # Extract description Section
        description_details = product_details.css('div.description-details li::text').getall()
        description_details = self._clean_strings(description_details) # Remove \n and every multiple spaces

        description_inside = product_details.css('div.description-inside li::text').getall()
        description_inside = self._clean_strings(description_inside) # Remove \n and every multiple spaces

        description_general_keys = product_details.css('div.description-general li strong::text').getall()
        description_general_keys = self._clean_strings(description_general_keys) # Remove \n and every multiple spaces
        description_general_values = product_details.css('div.description-general li:not([class])::text').getall()
        description_general_values = self._clean_strings(description_general_values) # Remove \n and every multiple spaces

        # Combine the description general keys and values in a dictionary
        description_general = {key:value for key, value in zip(description_general_keys, description_general_values)}

        # Extract SKU Code
        sku_code = product_details.css('div.description-general li.sku span[itemprop="sku"]::text').get()

        # Extract Web Code
        web_code = product_details.css('div.description-general li.sku::text').getall()
        web_code = self._clean_strings(web_code)[-1] # Remove \n and every multiple spaces

        # Extract Product Tags
        product_tags = product_details.css('div.more-links ul li a::text').getall()

        result_set = {
            "brand_name": brand_name,
            "product_name": product_name,
            "product_url": product_url,
            "first_image_url" :  first_image_url,
            "number_of_images" : number_of_images,
            "product_color": product_color,
            "product_tags": product_tags,
            "old_price": old_price,
            "new_price": new_price,
            "discount_amount" : discount_amount,
            "price_currency": price_currency,
            "description_details": description_details,
            "description_inside": description_inside,
            "sku_code": sku_code,
            "web_code": web_code
        }
        # Add the description general dictionary to the result set
        result_set.update(description_general)

        # Return the result set
        return result_set



    def _clean_strings(self, strings):
        """
        Clean the strings by removing leading , trailing spaces and \n character.
        Then remove empty strings.
        :param strings: A list of strings to be cleaned.
        :return: A list of cleaned strings.
        """

        return [
                ' '.join([word for word in re.sub(r'[\s:]+', ' ', text).strip().split(' ') if word])
                for text in strings
                if text.strip()  # Remove entirely empty strings
            ]

    def _parse_price_data(self , price_data):
        """
        Parse the price data from the response.
        :param price_data: The price data extracted from the response.
        :return: A tuple containing old price, new price, and currency.
        """
        # Extract Product Price
        # if the product has discount it will have "p" element
        # with class "old-price" & another "p" element with class "special-price"
        # else it will have only one "p" element with class "regular-price"
        old_price = price_data.css('p.old-price span.price::text').get()
        if old_price:
            # If the product has discount, extract the old price and the new price
            old_price = self._clean_price_string(old_price)
            new_price = price_data.css('p.special-price span.price meta[itemprop="price"]::attr(content)').get()
            new_price = self._clean_price_string(new_price)
            price_currency = price_data.css('meta[itemprop="priceCurrency"]::attr(content)').get()
            # Extract the discount amount
            discount_amount =  price_data.css('div.price-info__sale span.price::text').get()
            discount_amount = self._clean_price_string(discount_amount)
        else:
            # If the product doesn't have discount, extract the regular price
            # No old price or discount amount
            old_price = 0
            discount_amount = 0
            new_price = price_data.css('span.regular-price span.price::text').get()
            new_price = self._clean_price_string(new_price)
            price_currency = price_data.css('meta[itemprop="priceCurrency"]::attr(content)').get()

        return old_price, new_price, price_currency , discount_amount

    def _clean_price_string(self , price_string):
        """
        Clean the price string to delete the currency symbol and return the price as float type
        :param price_string:
        :return:
        """
        # Remove any non-digit, non-dot, and non-comma characters (e.g., currency symbols)
        cleaned = re.sub(r'[^\d,.-]', '', price_string)

        # If the number uses comma as thousands separator, remove it
        # and if dot is used for decimals, keep it
        if ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace(',', '')  # remove comma (thousands separator)
        elif ',' in cleaned:
            # assume European format: e.g., '3.384,30' => '3384.30'
            cleaned = cleaned.replace('.', '').replace(',', '.')

        return float(cleaned)


