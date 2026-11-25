import asyncio
from collections import Counter
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

from app.utils.validators import WebsiteError, public_target

MAX_BYTES = 4_000_000
REDIRECTS = {301, 302, 303, 307, 308}


async def fetch_html(url: str, origin: tuple[str, str] | None = None) -> tuple[str, bytes]:
    async with asyncio.timeout(10):
        for _ in range(5):
            if origin is not None and urlsplit(url)[:2] != origin:
                raise WebsiteError("The related page redirected outside the website.")
            target, authority, hostname = await public_target(url)
            async with httpx.AsyncClient(trust_env=False, timeout=5) as client:
                async with client.stream(
                    "GET", target,
                    headers={"Host": authority, "User-Agent": "LinkAnalysis/1.0",
                             "Accept-Encoding": "identity"},
                    extensions={"sni_hostname": hostname},
                ) as response:
                    if response.status_code in REDIRECTS and "location" in response.headers:
                        try:
                            url = urljoin(url, response.headers["location"])
                        except ValueError as exc:
                            raise WebsiteError("The website returned an invalid redirect.") from exc
                        continue
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "").split(";")[0]
                    if content_type.lower().strip() not in {"text/html", "application/xhtml+xml"}:
                        raise WebsiteError("The website did not return an HTML page.")
                    if response.headers.get("content-encoding", "identity").lower() != "identity":
                        raise WebsiteError("The website did not return an uncompressed page.")
                    body = bytearray()
                    async for chunk in response.aiter_raw():
                        body.extend(chunk)
                        if len(body) > MAX_BYTES:
                            raise WebsiteError("The HTML page exceeds the download limit.")
                    return url, bytes(body)
    raise WebsiteError("The website exceeded the redirect limit.")


def extract_page(url: str, body: bytes) -> tuple[dict, list[str]]:
    soup = BeautifulSoup(body, "html.parser")
    description = soup.find("meta", attrs={"name": "description"})
    site_name = soup.find("meta", attrs={"property": "og:site_name"})
    links = []
    origin = urlsplit(url)[:2]
    keywords = ("about", "service", "product", "solution", "industr", "pricing")
    for anchor in soup.find_all("a", href=True):
        try:
            link = urljoin(url, anchor["href"]).split("#", 1)[0]
            parsed = urlsplit(link)
        except ValueError:
            continue
        if (parsed[:2] == origin and not parsed.query and link != url
                and any(word in parsed.path.lower() for word in keywords)):
            links.append(link)
    for tag in soup(["script", "style", "noscript", "nav", "footer", "aside", "template", "svg"]):
        tag.decompose()
    content = soup.find("main") or soup.find("article") or soup.body or soup
    lines = [" ".join(line.split()) for line in content.stripped_strings]
    return {
        "url": url,
        "title": soup.title.get_text(" ", strip=True)[:250] if soup.title else "",
        "description": description.get("content", "")[:500] if description else "",
        "site_name": site_name.get("content", "")[:250] if site_name else "",
        "headings": [heading.get_text(" ", strip=True)[:160]
                     for heading in content.find_all(["h1", "h2", "h3"], limit=20)],
        "text": "\n".join(dict.fromkeys(lines))[:9000],
    }, list(dict.fromkeys(links))[:2]


async def optional_page(url: str, origin: tuple[str, str]) -> dict | None:
    try:
        final_url, body = await fetch_html(url, origin)
        page, _ = extract_page(final_url, body)
        return page if page["text"] else None
    except (WebsiteError, httpx.HTTPError, TimeoutError):
        pass
    return None


async def extract_website(url: str) -> tuple[str, list[dict]]:
    final_url, body = await fetch_html(url)
    home, links = extract_page(final_url, body)
    pages = [home]
    origin = urlsplit(final_url)[:2]
    related = await asyncio.gather(*(optional_page(link, origin) for link in links))
    pages.extend(page for page in related if page)
    if not any(page["text"] for page in pages):
        raise WebsiteError("No readable website text was found.")
    repeated = Counter(line for page in pages for line in page["text"].splitlines())
    for index, page in enumerate(pages):
        if index:
            page["text"] = "\n".join(line for line in page["text"].splitlines()
                                     if repeated[line] == 1)[:3500]
    return final_url, pages
