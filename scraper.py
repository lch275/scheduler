#!/usr/bin/env python3
"""
정부24 & 건강보험공단 공지사항 스크래퍼
- 수집한 공지를 매 실행마다 전부 Telegram으로 전송
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# ─── 설정 ───────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


# ─── 스크래핑 ────────────────────────────────────────────


def scrape_gov24():
    """정부24 공지사항 - plus.gov.kr JSON API (POST)"""
    notices = []
    api_url = "https://plus.gov.kr/api/portal/v1.0/ntcmttr"
    params = {
        "pageNo": 1,
        "srchClsf": "whol",
        "srchCn": "",
        "pageSz": 10,
    }

    try:
        resp = requests.post(api_url, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        items = []
        for key in data.get("pstInfo"):
            items.append(key)
        if not items:
            print(f"[정부24] API 응답에서 목록을 찾지 못함. 키: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            print(f"[정부24] 응답 샘플: {json.dumps(data, ensure_ascii=False)[:500]}")
            return notices

        for item in items:
            title = (
                item.get("pstTtl") or item.get("title") or item.get("ttl")
                or item.get("ntcmttrSj") or item.get("sj") or ""
            ).strip()

            post_sn = (
                item.get("pstSn") or item.get("ntcmttrSn")
                or item.get("articleNo") or item.get("id") or item.get("sn") or ""
            )

            if not title:
                continue

            detail_url = (
                f"https://plus.gov.kr/portal/ntcmttr/ntcmttrdtl/?pstSn={post_sn}"
                if post_sn else "https://plus.gov.kr/portal/ntcmttr/"
            )

            notices.append({"title": title, "url": detail_url, "source": "정부24"})

        print(f"[정부24] API에서 {len(notices)}건 수집 성공")

    except Exception as e:
        print(f"[정부24] 스크래핑 실패: {e}")

    return notices


def scrape_nhis():
    """
    국민건강보험공단 공지사항 스크래핑
    메인 페이지(index.do) #newsTabpanel01 내 a.tit 수집
    """
    notices = []
    base = "https://www.nhis.or.kr"
    url = f"{base}/nhis/index.do"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        links = soup.select("#newsTabpanel01 a.tit")

        for link in links:
            title = link.get_text(strip=True)
            href = link.get("href", "")

            if not title:
                continue
            if href.startswith("javascript") or href == "#":
                continue

            if href.startswith("http"):
                full_url = href
            elif href.startswith("/"):
                full_url = f"{base}{href}"
            else:
                full_url = f"{base}/nhis/together/{href}"

            notices.append({"title": title, "url": full_url, "source": "건강보험공단"})

        if notices:
            print(f"[건강보험공단] #newsTabpanel01 a.tit에서 {len(notices)}건 수집 성공")
        else:
            print("[건강보험공단] #newsTabpanel01 a.tit 요소를 찾지 못함")

    except Exception as e:
        print(f"[건강보험공단] 스크래핑 실패: {e}")

    return notices


# ─── 텔레그램 전송 ────────────────────────────────────────


def send_telegram_message(message):
    """Telegram 봇으로 메시지 전송"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] 토큰 또는 채팅 ID 미설정 - 콘솔에만 출력")
        print(message)
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        print("[Telegram] 메시지 전송 성공")
        return True
    except Exception as e:
        print(f"[Telegram] 메시지 전송 실패: {e}")
        return False


def format_all_notices(notices):
    """수집한 전체 공지를 Telegram 메시지로 변환"""
    now = datetime.now().astimezone(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M")
    lines = [f"📋 <b>공지사항 목록</b> ({now})\n"]

    by_source = {}
    for n in notices:
        by_source.setdefault(n["source"], []).append(n)

    for source, items in by_source.items():
        lines.append(f"\n📌 <b>{source}</b> ({len(items)}건)")
        for i, item in enumerate(items, 1):
            lines.append(f'  {i}. <a href="{item["url"]}">{item["title"]}</a>')

    lines.append(f"\n총 {len(notices)}건")
    return "\n".join(lines)


# ─── 메인 ────────────────────────────────────────────────


def main():
    print(f"=== 공지사항 스크래핑 시작 ({datetime.now().isoformat()}) ===\n")

    all_notices = []
    all_notices.extend(scrape_gov24())
    all_notices.extend(scrape_nhis())

    print(f"\n총 {len(all_notices)}건 수집됨")

    if all_notices:
        message = format_all_notices(all_notices)

        # Telegram 메시지 길이 제한(4096자) 대응: 초과 시 분할 전송
        if len(message) <= 4096:
            send_telegram_message(message)
        else:
            by_source = {}
            for n in all_notices:
                by_source.setdefault(n["source"], []).append(n)

            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            for source, items in by_source.items():
                lines = [f"📋 <b>{source} 공지사항</b> ({now})\n"]
                for i, item in enumerate(items, 1):
                    lines.append(f'  {i}. <a href="{item["url"]}">{item["title"]}</a>')
                lines.append(f"\n총 {len(items)}건")
                send_telegram_message("\n".join(lines))
    else:
        send_telegram_message("⚠️ 공지사항 수집 실패 - 사이트 구조 변경 확인 필요")

    print("=== 완료 ===")


if __name__ == "__main__":
    main()
