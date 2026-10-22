#!/usr/bin/env python3
"""Experimental AlleFolders page-image discovery.

Not a price scanner. Discovers publicly linked folder page images and offer-page
URLs, using standard library only. Subject to robots.txt/site permissions.
"""
import argparse
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

STORES = {
    "lidl": "https://www.allefolders.nl/lidl/folder-aanbiedingen",
    "albert-heijn": "https://www.allefolders.nl/nl/albert-heijn/folder-aanbiedingen",
    "jumbo": "https://www.allefolders.nl/jumbo/folder-aanbiedingen",
    "kruidvat": "https://www.allefolders.nl/kruidvat/folder-aanbiedingen",
}
IMAGE_RE = re.compile(r"^https://cdn\.jafolders\.com/pages/[^/?]+/(?:small|medium|large)\.webp(?:\?.*)?$")
FOLDER_RE = re.compile(r"^https://www\.allefolders\.nl/[^/?]+-aanbiedingen/[0-9a-f-]{36}/\d+(?:\?.*)?$")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "img":
            for k in ("src", "data-src"):
                if attrs.get(k):
                    self.images.append(attrs[k])


def fetch(url):
    request = Request(url, headers={"User-Agent": "KoopkrachtResearch/1.0 (manual research; no bulk download)"})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", "replace")


def parse(url, html):
    parser = Links()
    parser.feed(html)
    urls = [urljoin(url, item) for item in parser.links]
    images = [urljoin(url, item) for item in parser.images]
    # Canonical links to folder pages have stable UUID paths; all are kept,
    # not assumed to be the current week's folders.
    folder_links = sorted(set(x for x in urls if FOLDER_RE.match(x)))
    page_images = sorted(set(x for x in images + urls if IMAGE_RE.match(x)))
    return {"url": url, "folder_links": folder_links, "page_images": page_images}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--store", choices=STORES.keys(), required=True)
    cli.add_argument("--folder-url", help="Optional known folder detail page URL")
    args = cli.parse_args()
    url = args.folder_url or STORES[args.store]
    if urlparse(url).hostname != "www.allefolders.nl":
        cli.error("Only www.allefolders.nl pages are accepted")
    result = parse(url, fetch(url))
    result["store"] = args.store
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    result["limitations"] = [
        "No OCR or product extraction",
        "No offer validation, dates, or price verification",
        "No proof of original PDF existence",
        "Page may load links dynamically; empty results are not a success",
    ]
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
