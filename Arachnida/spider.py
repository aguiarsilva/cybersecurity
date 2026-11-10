import argparse
import sys
import urllib.request
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from html.parser import HTMLParser

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
    Create an instance, feed the html and convert the the urls to the absolute url and returns it
    """
    img = ImageParser()
    img.feed(html)
    absolute_url = []
    for item in img.images:
        absolute_url.append(urllib.parse.urljoin(base_url, item))
    return absolute_url

def validate_img(url):
    """
    Function to check if the extension is a valid image file extension for the program
    (.jpg, .jpeg, .png, .gif, .bmp)
    Returns a boolean
    """
    #use urllib.parse.urlparse()
    clean_url = urllib.parse.urlparse(url).path
    if clean_url.lower().endswith((".jpg", ".bmp", ".jpeg", ".png", ".gif")):
        return True
    else:
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("-r", action="store_true")
    parser.add_argument("-l", type=int, default=None)
    parser.add_argument("-p", type=str, default='./data/')

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

if __name__ == "__main__":
    main()
