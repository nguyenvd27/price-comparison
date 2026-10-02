import re

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0 Safari/537.36 iphone-checker-web/1.0"
    ),
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en;q=0.8",
}
TIMEOUT = 30


def new_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def describe_block(response: requests.Response) -> str:
    """Ai trả lỗi (server, CDN) và tiêu đề trang lỗi, để biết bị chặn kiểu gì."""
    parts = [f"{key}={response.headers[key]}" for key in ("Server", "X-Cache") if key in response.headers]
    title = re.search(r"<title[^>]*>(.*?)</title>", response.text[:5000], re.S | re.I)
    if title:
        parts.append(f"title={' '.join(title.group(1).split())[:100]}")
    return ", ".join(parts)


def get_text(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=TIMEOUT)
    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        raise requests.HTTPError(f"{error} ({describe_block(response)})", response=response) from None
    if not response.encoding or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding
    return response.text
