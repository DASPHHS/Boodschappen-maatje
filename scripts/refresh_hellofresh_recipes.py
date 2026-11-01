#!/usr/bin/env python3
"""Bounded, rights-conscious HelloFresh NL recipe-link discovery.

This index stores canonical recipe URLs and factual title/ingredient-family tags.
It does NOT republish recipes, ingredients, instructions, photographs or nutrition.
Only public category pages linked to public recipe pages are inspected; robots
rules, host restrictions and HTTP refusal are respected. Errors leave old data.
"""
import datetime as dt
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from refresh_publisher_recipes import families_of, VEG, LEGUMES, EXCLUDE

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "docs/data/publisher-recipes.json"
BASE = "https://www.hellofresh.nl"
CATEGORIES = (
    "/recipes/indonesische-recepten",
    "/recipes/traditionele-recepten",
    "/recipes/vlees-recepten/gehakt",
    "/recipes/vegetarische-recepten",
    "/recipes/vis-recepten",
    "/recipes",
)
USER_AGENT = "Boodschappenmaatje/1.0 (small publisher link-metadata catalog)"
RECIPE_PATH = re.compile(r"^/recipes/([a-z0-9][a-z0-9_-]{5,180})-([0-9a-f]{24})$")
REJECT = re.compile(r"\b(ontbijt|dessert|nagerecht|smoothie|babyvoeding|"
                    r"kant-en-klaar|ready to eat|opwarmmaaltijd|maaltijdbox voor)\b", re.I)

def canonical(url):
    """Allowlist exact Dutch publisher hostname, recipe-only paths, no queries."""
    parsed = urllib.parse.urlsplit(urllib.parse.urljoin(BASE, url))
    if parsed.scheme != "https" or parsed.hostname != "www.hellofresh.nl":
        return None
    match = RECIPE_PATH.fullmatch(parsed.path.rstrip("/"))
    if not match or parsed.username or parsed.password or parsed.port:
        return None
    return BASE + parsed.path.rstrip("/")

class PublicPage(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self._href = None
        self._parts = []
        self._h1 = False
        self.title = ""
        self.description = ""
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a":
            self._href = a.get("href", "")
            self._parts = []
        if tag == "h1":
            self._h1 = True
        if tag == "meta" and a.get("name", "").lower() == "description":
            self.description = html.unescape(a.get("content", ""))[:350]
        if tag == "meta" and a.get("property", "").lower() == "og:description" and not self.description:
            self.description = html.unescape(a.get("content", ""))[:350]
    def handle_data(self, data):
        if self._href is not None:
            self._parts.append(data)
        if self._h1 and not self.title:
            value = " ".join(data.split())
            if len(value) >= 8:
                self.title = value[:155]
    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            url = canonical(self._href)
            if url:
                title = " ".join(" ".join(self._parts).split())
                self.links.append((url, title))
            self._href = None
            self._parts = []
        if tag == "h1":
            self._h1 = False

def allowed_robots(fetcher):
    """Fail closed when robots file cannot be retrieved."""
    body = fetcher(BASE + "/robots.txt", 150_000)
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(body.splitlines())
    return parser

def fetch(url, max_bytes=1_000_000):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "www.hellofresh.nl":
        raise ValueError("HelloFresh host allowlist")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
        "Accept": "text/html,text/plain;q=0.8"})
    with urllib.request.urlopen(req, timeout=16) as response:
        if response.status != 200:
            raise OSError("Publisher response is not 200")
        # Read only a bounded prefix of large Next.js pages. The source may
        # include multi-megabyte hydration scripts; we need only public <a>
        # links on category pages and the original <h1> on detail pages.
        # A partial parser is acceptable; it must never invent a record.
        payload = response.read(max_bytes)
        return payload.decode("utf-8", "replace")

def record_from_page(url, page_html, stamp):
    parser = PublicPage()
    parser.feed(page_html)
    title = parser.title.strip()
    if len(title) < 9 or len(title) > 150 or REJECT.search(title) or EXCLUDE.search(title):
        return None
    # Tags are candidate food families from public title/short description only;
    # never misrepresent them as the publisher's actual ingredient list.
    families = families_of(title, parser.description)
    if not families:
        return None
    method = next((m for m in ("hachee","rendang","stoof","curry","lasagne","dahl",
        "stamppot","oven","pasta","rijst","bowl","salade","noedels","roerbak","tajine",
        "soep") if m in title.casefold()), "anders")
    if method == "soep" and not (VEG.intersection(families) or LEGUMES.intersection(families)):
        return None
    # This is a link to a real, individually opened page, not a copy of its recipe.
    return {
        "id":"hf-page-"+hashlib.sha256(url.encode()).hexdigest()[:14],
        "source":"HelloFresh","title":title,"url":url,"families":families,
        "minutes":None,"servings":None,"course":"niet_gecontroleerd",
        "method":method,"vegetable_families":len(VEG.intersection(families)),
        "has_legumes":bool(LEGUMES.intersection(families)),
        "review_status":"publisher_page_title_verified","last_checked":stamp
    }

def discover(max_pages=12, day=None, fetcher=fetch, pause=0.3):
    day = day or dt.date.today()
    data = json.loads(TARGET.read_text("utf-8"))
    existing = {r["url"]:r for r in data["recipes"]}
    try:
        rules=allowed_robots(fetcher)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        print("HelloFresh robots unavailable; retaining previous data:",str(exc)[:160])
        return 0
    choices=[]
    for path in CATEGORIES:
        category=BASE+path
        if not rules.can_fetch(USER_AGENT, category):
            print("HelloFresh category disallowed by robots:",path)
            continue
        try:
            parser=PublicPage()
            parser.feed(fetcher(category, 6_000_000))
            choices.extend(url for url,_ in parser.links)
        except (OSError,ValueError,urllib.error.URLError) as exc:
            print("HelloFresh category unavailable:",path,str(exc)[:130])
        time.sleep(pause)
    choices=sorted(set(url for url in choices if url not in existing))
    # Bounded stable weekly rotation, no preference for bulk copying.
    week=day.isocalendar().week
    choices.sort(key=lambda url: hashlib.sha1((url+str(week)).encode()).hexdigest())
    checked=0
    added=0
    for url in choices:
        if checked >= max_pages or sum(r.get("source")=="HelloFresh" for r in existing.values())>=120:
            break
        if not rules.can_fetch(USER_AGENT, url):
            continue
        checked += 1
        try:
            record=record_from_page(url, fetcher(url), day.isoformat())
        except urllib.error.HTTPError as exc:
            if exc.code in (401,403,429):
                print("HelloFresh refused request; stop immediately:",exc.code)
                break
            continue
        except (OSError,ValueError,urllib.error.URLError):
            continue
        if record:
            existing[url]=record
            added+=1
        time.sleep(pause)
    if added:
        data["recipes"]=list(existing.values())
        data["generated_at"]=day.isoformat()
        TARGET.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n","utf-8")
    print("HelloFresh index:",checked,"checked,",added,"new,",len(existing),"total")
    return added

if __name__ == "__main__":
    discover()
