import os
import json
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

TARGET_URL = "https://www.lifehacker.jp/regular/regular_book_to_read/"
DATA_DIR = "data"
KNOWN_URLS_PATH = f"{DATA_DIR}/known_urls.json"
EXCLUDED_URLS_PATH = f"{DATA_DIR}/excluded_urls.json"
ENV_FILE_PATH = ".env"
CARD_CONTAINER_SELECTOR = '[class*="articles_pArticles_Cards"]'

ANCHOR_SPONSORED_KEYWORDS = ["sponsored", "sponsored by"]


def load_env_file(path=ENV_FILE_PATH):
    """`.env` に設定された環境変数を読み込む"""
    if not os.path.exists(path):
        return

    with open(path, "r") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


load_env_file()


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_json_list(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def save_json_list(path, items):
    ensure_data_dir()
    with open(path, "w") as f:
        json.dump(sorted(set(items)), f, indent=2, ensure_ascii=False)


def normalize_url(href):
    if not href:
        return ""
    href = href.strip()
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return urljoin(TARGET_URL, href)
    return ""


def looks_like_review_link(href):
    if not href.startswith("https://www.lifehacker.jp/"):
        return False
    if any(
        segment in href for segment in ["/tag/", "/category/", "/author/", "/video/"]
    ):
        return False
    if "regular_book_to_read" in href or "/article/" in href:
        return True
    return False


def anchor_contains_sponsor(anchor):
    text = " ".join(anchor.stripped_strings).lower()
    return any(keyword in text for keyword in ANCHOR_SPONSORED_KEYWORDS)


def fetch_article_links():
    """書評一覧ページから記事URL一覧を取得"""
    try:
        res = requests.get(TARGET_URL, timeout=10)
        res.raise_for_status()
    except requests.RequestException as exc:
        print(f"[WARN] 記事一覧の取得に失敗しました: {exc}")
        return []
    soup = BeautifulSoup(res.text, "html.parser")

    card_links = set()
    # 広告リンクは後段のJavaScriptがクライアント側で挿入している可能性が高く、静的なHTMLを取得するだけでは検出できない。
    for card in soup.select(CARD_CONTAINER_SELECTOR):
        for anchor in card.find_all("a", href=True):
            href = normalize_url(anchor.get("href", ""))
            if not href:
                continue
            if anchor_contains_sponsor(anchor):
                continue
            if looks_like_review_link(href):
                card_links.add(href)

    if not card_links:
        reason = "Card セレクタに一致する書評リンクを取得できませんでした。ページ構造が変わっていないか確認してください。"
        notify_slack_error(reason)
        raise RuntimeError(reason)

    return sorted(card_links)


def post_to_slack(payload):
    webhook = os.environ.get("SLACK_BOOKREVIEW_WEBHOOK_URL")
    if not webhook:
        raise RuntimeError(
            "環境変数 SLACK_BOOKREVIEW_WEBHOOK_URL が設定されていません。"
        )

    res = requests.post(webhook, json=payload, timeout=5)
    try:
        res.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Slack 通知に失敗しました: {exc}") from exc


def notify_slack(url):
    """Slack へ通知"""
    message = {
        "text": f"🆕 新しい書評記事が公開されました！\n{url}",
        "unfurl_links": True,
        "unfurl_media": True,
    }
    post_to_slack(message)


def notify_slack_error(reason):
    """Slack へエラー通知"""
    post_to_slack(
        {
            "text": f":warning: 書評一覧ページから記事リンクを取得できませんでした。\n{reason}",
            "unfurl_links": False,
            "unfurl_media": False,
        }
    )


def main():
    known_urls = set(load_json_list(KNOWN_URLS_PATH))
    current_urls = fetch_article_links()
    # print(f"Current URLs: {current_urls}")

    new_urls = [u for u in current_urls if u not in known_urls]

    print(f"Found {len(new_urls)} new URLs")

    for url in new_urls:
        print(f"Recording and notifying Slack: {url}")
        known_urls.add(url)
        notify_slack(url)

    save_json_list(KNOWN_URLS_PATH, list(known_urls))
    print("Done.")


if __name__ == "__main__":
    main()
