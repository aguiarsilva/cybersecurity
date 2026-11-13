import argparse
import sys
import os
import re
import urllib.request
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse, unquote, quote
from html.parser import HTMLParser
from pathlib import Path

class ImageParser(HTMLParser):
    """
    Class to parse the HTML and filter for the tag and attribute of the images
    """
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            result = [attr[1] for attr in attrs if attr[0] == 'src']
            for item in result:
                self.images.append(item)

class LinkParser(HTMLParser):
    """
    Class to parse the HTML and filter for the tag and attributes of the links
    """
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            result = [attr[1] for attr in attrs if attr[0] == 'href']
            for item in result:
                self.links.append(item)

def fetch_page(url):
    """
    Fetch a webpage and return its HTML content.
    """
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            encoding = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(encoding, errors='replace')
    except (TimeoutError, HTTPError, URLError, UnicodeDecodeError) as e:
        print(f"Could not fetch {url}: {e}")
        return None

def extract_images(html, base_url):
    """
    Extract valid, absolute image URLs from the page HTML.
    """
    img = ImageParser()
    img.feed(html)
    absolute_urls = []
    visited_urls = set()

    for item in img.images:
        if not isinstance(item, str):
            continue

        src = item.strip()
        if not src or src.startswith("#"):
            continue

        try:
            source_url = urlparse(src)
            if source_url.scheme and source_url.scheme not in ("http", "https"):
                continue

            absolute_url = urljoin(base_url, src)
            parsed_url = urlparse(absolute_url)
            absolute_url = parsed_url._replace(
                path=quote(parsed_url.path, safe="/%:@!$&'()*+,;=-._~"),
                query=quote(parsed_url.query, safe=";/?:@&=+$,-_.!~*'()%"),
            ).geturl()
            parsed_url = urlparse(absolute_url)
        except ValueError:
            continue

        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            continue

        if absolute_url not in visited_urls:
            visited_urls.add(absolute_url)
            absolute_urls.append(absolute_url)

    return absolute_urls

def extract_links(html, base_url):
    """
    Extract valid, absolute links URLs from the page HTML.
    """
    lnk = LinkParser()
    lnk.feed(html)
    absolute_urls = []
    visited_urls = set()

    for item in lnk.links:
        if not isinstance(item, str):
            continue

        href = item.strip()
        if not href or href.startswith("#"):
            continue

        try:
            source_url = urlparse(href)
            if source_url.scheme and source_url.scheme not in ("http", "https"):
                continue

            absolute_url = urljoin(base_url, href)
            parsed_url = urlparse(absolute_url)
            absolute_url = parsed_url._replace(
                fragment="",
                path=quote(parsed_url.path, safe="/%:@!$&'()*+,;=-._~"),
                query=quote(parsed_url.query, safe=";/?:@&=+$,-_.!~*'()%"),
            ).geturl()
            parsed_url = urlparse(absolute_url)
        except ValueError:
            continue

        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            continue

        if absolute_url not in visited_urls:
            visited_urls.add(absolute_url)
            absolute_urls.append(absolute_url)

    return absolute_urls

def process_page(url, output_path):
    """
    Function to process the page, extract images and download them
    """
    html = fetch_page(url)
    if html is None:
        return

    image_urls = extract_images(html, url)
    for img_url in image_urls:
        if validate_img(img_url):
            try:
                download_image(img_url, output_path)
            except (HTTPError, URLError, OSError, TimeoutError) as e:
                print(f"Failed to download {img_url}: {e}")

def validate_img(url):
    """
    Function to check if the extension is a valid image file extension for the program
    (.jpg, .jpeg, .png, .gif, .bmp)
    Returns a boolean
    """
    clean_url = urllib.parse.urlparse(url).path
    if clean_url.lower().endswith((".jpg", ".bmp", ".jpeg", ".png", ".gif")):
        return True
    else:
        return False

def download_image(url, path):
    """
    Function to download the image, define filename and save the image scraped to the disk
    """
    with urllib.request.urlopen(url, timeout=10) as response:
        data = response.read()
        decoded_path = unquote(urlparse(response.url).path)
        filename = os.path.basename(decoded_path) or "downloaded_img"
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f]', "_", filename)
        filename = filename.strip(" .") or "downloaded_img"

        output_dir = Path(path)
        output_dir.mkdir(parents=True, exist_ok=True)
        candidate = output_dir / filename
        counter = 1
        while True:
            try:
                with candidate.open("xb") as image_file:
                    image_file.write(data)
                break
            except FileExistsError:
                stem = Path(filename).stem
                suffix = Path(filename).suffix
                candidate = output_dir / f"{stem}_{counter}{suffix}"
                counter += 1

def crawl(url, output_path, current_depth, max_depth, visited_urls, downloaded_images, domain):
    """
    Function to crawl the website recursively and download images from each page.
    """
    if current_depth > max_depth or url in visited_urls:
        return

    visited_urls.add(url)
    html = fetch_page(url)

    if html is None:
        return

    image_urls = extract_images(html, url)
    for image_url in image_urls:
        if validate_img(image_url) and image_url not in downloaded_images:
            downloaded_images.add(image_url)
            try:
                download_image(image_url, output_path)
            except (HTTPError, URLError, OSError, TimeoutError, ValueError) as e:
                print(f"Failed to download {image_url}: {e}")

    links = extract_links(html, url)
    for link in links:
        parsed_link = urlparse(link)
        if parsed_link.netloc == domain:
            crawl(link, output_path, current_depth + 1, max_depth, visited_urls, downloaded_images, domain)

def main():
    """
    Main function to parse command line arguments and initiate the crawling process.
    """
    parser = argparse.ArgumentParser(
        description="Download images from a webpage, optionally crawling linked pages."
    )
    parser.add_argument("url", help="URL of the webpage to scrape")
    parser.add_argument(
        "-r",
        action="store_true",
        help="recursively crawl pages on the same domain",
    )
    parser.add_argument(
        "-l",
        type=int,
        default=None,
        metavar="DEPTH",
        help="maximum crawl depth when used with -r (default: 5)",
    )
    parser.add_argument(
        "-p",
        type=str,
        default='./data/',
        metavar="PATH",
        help="directory where images are saved (default: ./data/)",
    )

    list_args = sys.argv[1:]
    if "-l" in list_args:
        index = list_args.index("-l")
        if index + 1 < len(list_args):
            next_arg = list_args[index + 1]
        else:
            next_arg = None

        if next_arg is None:
            list_args.insert(index + 1, "5")
        else:
            try:
                value = int(next_arg)
            except ValueError:
                if next_arg.startswith("-") or next_arg.startswith("http://") or next_arg.startswith("https://"):
                    list_args.insert(index + 1, "5")
                else:
                    parser.error("Error: Invalid recursion depth. Expected an integer.")

    args = parser.parse_args(list_args)

    depth = args.l if args.l is not None else 5

    if depth < 0:
        parser.error("Recursion depth cannot be negative")

    if args.l is not None and not args.r:
        parser.error('Recursion flag [-r] mandatory to use [-l] flag')

    if not args.r:
        process_page(args.url, args.p)
    else:
        visited_urls = set()
        downloaded_images = set()
        domain = urlparse(args.url).netloc
        crawl(args.url, args.p, 0, depth, visited_urls, downloaded_images, domain)

if __name__ == "__main__":
    main()
