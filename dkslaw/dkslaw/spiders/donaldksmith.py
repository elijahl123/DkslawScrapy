import os
import re
import scrapy
from urllib.parse import urlparse, unquote, urljoin


class DonaldKSmithSpider(scrapy.Spider):
    name = "donaldksmith"
    allowed_domains = ["donaldksmith.us"]
    start_urls = ["https://donaldksmith.us/"]
    base_directory = "downloaded_files"  # Base directory for downloaded files

    def parse(self, response):

        image_urls = [
            "images/logo.jpg",
            "images/nav_blue.jpg",
            "images/nav_green.jpg",
            "images/nav_yellow.jpg",
            "images/blue_photo.jpg",
            "images/yellow_photo.jpg",
            "images/green_photo.jpg",
            "images/navigation_background.jpg",
            "images/nav_menu.jpg",
            "images/nav_menu2.jpg",
            "images/body1_background.jpg",
            "images/body2_background.jpg",
            "images/body3_background.jpg",
            "images/body4_background.jpg",
            "images/body5_background2.jpg",
            "images/col_seperator3.jpg",
            "images/bottom_nav.jpg"
        ]

        for img_url in image_urls:
            absolute_url = urljoin(self.start_urls[0], img_url)
            yield scrapy.Request(absolute_url, callback=self.save_file)

        # Extract all links and follow them
        for href in response.css('a::attr(href)').getall():
            url = response.urljoin(href)
            # Debugging: print the URL to check its correctness
            print("Resolved URL:", url)
            if url.endswith('.htm') or url.endswith('.html') or url == self.start_urls[0]:
                yield scrapy.Request(url, callback=self.parse_htm)

    def parse_htm(self, response):
        # Save the .htm file
        self.save_file(response)

        # Extract and download images, stylesheets, js, etc.
        for src in response.css('img::attr(src), link::attr(href), script::attr(src)').getall():
            url = response.urljoin(src)
            yield scrapy.Request(url, callback=self.save_file)

    def save_file(self, response, filename=None):
        # Parse the file and save it
        path = urlparse(unquote(response.url)).path
        directory, file_name = os.path.split(path)

        if file_name == '':
            file_name = 'index.htm'

        if filename is None:
            filename = file_name

        # Adjust the directory path to be relative to base_directory
        directory = os.path.join(self.base_directory, directory.lstrip('/'))

        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)

        # Save the file
        file_path = os.path.join(directory, filename)
        with open(file_path, 'wb') as file:
            file.write(response.body)

        # Additional handling for CSS files
        if filename.endswith('.css'):
            self.parse_css(response, file_path)

    def parse_css(self, response, css_file_path):
        # Find URLs in CSS file
        css_content = response.text
        urls = re.findall(r'url\(([^)]+)\)', css_content)

        for url in urls:
            # Clean and join the URL
            url = url.strip('\'"')
            absolute_url = urljoin(response.url, url)

            # Download the asset
            yield scrapy.Request(absolute_url, callback=self.save_file)
