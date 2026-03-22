#!/usr/bin/env python3
"""
정부24 & 건강보험공단 공지사항 모니터링 스크래퍼
- GitHub Actions 스케줄러 기반
- Telegram 봇으로 신규 공지 알림
"""

import os
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ─── 설정 ───────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
DATA_FILE = "data/known_notices.json"

# User-Agent 설정 (봇 차단 방지)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

# ─── 스크래핑 대상 사이트 정의 ─────────────────────────────


def scrape_gov24():
    """
    정부24 공지사항 스크래핑
    URL: https://www.gov.kr/portal/ntcItm
    - 구버전(www.gov.kr)과 신버전(plus.gov.kr) 두 가지가 있음
    - 둘 다 시도하여 성공하는 쪽 사용
    """
    notices = []

    # 방법 1: 기존 gov.kr
    urls_to_try = [
        "https://www.gov.kr/portal/ntcItm",
        "https://plus.gov.kr/portal/ntcmttr/",
    ]

    for url in urls_to_try:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            # gov.kr 구버전 파싱
            if "gov.kr/portal/ntcItm" in url:
                # 테이블 또는 리스트 형태의 공지사항 파싱
                rows = soup.select("table tbody tr")
                if not rows:
                    rows = soup.select(".board_list li, .list_item, .notice_list li")
                if not rows:
                    # 일반적인 링크 기반 파싱
                    links = soup.select("a[href*='ntcItm']")
                    for link in links[:20]:
                        title = link.get_text(strip=True)
                        href = link.get("href", "")
                        if title and len(title) > 5:
                            full_url = href if href.startswith("http") else f"https://www.gov.kr{href}"
                            notices.append({
                                "title": title,
                                "url": full_url,
                                "source": "정부24",
                            })
                else:
                    for row in rows[:20]:
                        link = row.select_one("a")
                        if link:
                            title = link.get_text(strip=True)
                            href = link.get("href", "")
                            full_url = href if href.startswith("http") else f"https://www.gov.kr{href}"
                            notices.append({
                                "title": title,
                                "url": full_url,
                                "source": "정부24",
                            })

            # plus.gov.kr 신버전 파싱
            elif "plus.gov.kr" in url:
                rows = soup.select("table tbody tr, .board-list li, .list-item")
                if not rows:
                    links = soup.select("a[href*='ntcmttr']")
                    for link in links[:20]:
                        title = link.get_text(strip=True)
                        href = link.get("href", "")
                        if title and len(title) > 5:
                            full_url = href if href.startswith("http") else f"https://plus.gov.kr{href}"
                            notices.append({
                                "title": title,
                                "url": full_url,
                                "source": "정부24",
                            })
                else:
                    for row in rows[:20]:
                        link = row.select_one("a")
                        if link:
                            title = link.get_text(strip=True)
                            href = link.get("href", "")
                            full_url = href if href.startswith("http") else f"https://plus.gov.kr{href}"
                            notices.append({
                                "title": title,
                                "url": full_url,
                                "source": "정부24",
                            })

            if notices:
                print(f"[정부24] {url}에서 {len(notices)}건 수집 성공")
                break

        except Exception as e:
            print(f"[정부24] {url} 스크래핑 실패: {e}")
            continue

    if not notices:
        print("[정부24] 모든 URL에서 스크래핑 실패 - HTML 구조 변경 가능성 있음")

    return notices


def scrape_nhis():
    """
    국민건강보험공단 공지사항 스크래핑
    URL: https://www.nhis.or.kr/nhis/together/wbhaea01600m01.do
    """
    notices = []

    urls_to_try = [
        "https://www.nhis.or.kr/nhis/together/wbhaea01600m01.do",
        "https://www.nhis.or.kr/nhis/index.do",
    ]

    for url in urls_to_try:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            # 공지사항 테이블/리스트 파싱
            rows = soup.select("table tbody tr")
            if not rows:
                rows = soup.select(".board_list li, .list_wrap li, .bbsList li")

            if rows:
                for row in rows[:20]:
                    link = row.select_one("a")
                    if link:
                        title = link.get_text(strip=True)
                        href = link.get("href", "")
                        if title and len(title) > 3:
                            if href.startswith("http"):
                                full_url = href
                            elif href.startswith("/"):
                                full_url = f"https://www.nhis.or.kr{href}"
                            else:
                                full_url = f"https://www.nhis.or.kr/nhis/together/{href}"
                            notices.append({
                                "title": title,
                                "url": full_url,
                                "source": "건강보험공단",
                            })
            else:
                # 대안: 모든 링크에서 공지 패턴 찾기
                links = soup.select("a")
                for link in links:
                    href = link.get("href", "")
                    title = link.get_text(strip=True)
                    if ("wbhaea" in href or "board" in href.lower()) and title and len(title) > 5:
                        full_url = href if href.startswith("http") else f"https://www.nhis.or.kr{href}"
                        notices.append({
                            "title": title,
                            "url": full_url,
                            "source": "건강보험공단",
                        })

            if notices:
                print(f"[건강보험공단] {url}에서 {len(notices)}건 수집 성공")
                break

        except Exception as e:
            print(f"[건강보험공단] {url} 스크래핑 실패: {e}")
            continue

    if not notices:
        print("[건강보험공단] 모든 URL에서 스크래핑 실패 - HTML 구조 변경 가능성 있음")

    return notices


# ─── 데이터 관리 ─────────────────────────────────────────


def load_known_notices():
    """이전에 수집한 공지 ID 목록 로드"""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"notices": {}, "last_updated": ""}


def save_known_notices(data):
    """공지 ID 목록 저장"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def make_notice_id(notice):
    """공지의 고유 ID 생성 (제목 + URL 해시)"""
    raw = f"{notice['source']}:{notice['title']}:{notice['url']}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


# ─── 알림 ────────────────────────────────────────────────


def send_telegram_message(message):
    """Telegram 봇으로 메시지 전송"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] 토큰 또는 채팅 ID 미설정 - 콘솔에만 출력합니다.")
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


def format_notification(new_notices):
    """신규 공지를 Telegram 메시지 형식으로 변환"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"🔔 <b>신규 공지사항 알림</b> ({now})\n"]

    # 사이트별 그룹핑
    by_source = {}
    for n in new_notices:
        by_source.setdefault(n["source"], []).append(n)

    for source, items in by_source.items():
        lines.append(f"\n📌 <b>{source}</b> ({len(items)}건)")
        for item in items:
            lines.append(f'  • <a href="{item["url"]}">{item["title"]}</a>')

    lines.append(f"\n총 {len(new_notices)}건의 새 공지가 등록되었습니다.")
    return "\n".join(lines)


# ─── 메인 실행 ────────────────────────────────────────────


def main():
    print(f"=== 공지사항 모니터링 시작 ({datetime.now().isoformat()}) ===\n")

    # 1. 이전 데이터 로드
    known = load_known_notices()
    known_ids = known.get("notices", {})

    # 2. 각 사이트 스크래핑
    all_notices = []
    all_notices.extend(scrape_gov24())
    all_notices.extend(scrape_nhis())

    print(f"\n총 {len(all_notices)}건 수집됨")

    # 3. 신규 공지 확인
    new_notices = []
    current_ids = {}

    for notice in all_notices:
        nid = make_notice_id(notice)
        current_ids[nid] = {
            "title": notice["title"],
            "url": notice["url"],
            "source": notice["source"],
            "first_seen": known_ids.get(nid, {}).get(
                "first_seen", datetime.now().isoformat()
            ),
        }

        if nid not in known_ids:
            new_notices.append(notice)

    # 4. 첫 실행 여부 확인
    is_first_run = len(known_ids) == 0

    # 5. 알림 전송
    if is_first_run:
        print(f"\n⚡ 첫 실행: {len(all_notices)}건의 공지를 기준 데이터로 저장합니다.")
        print("   (첫 실행에서는 알림을 보내지 않습니다)")
        send_telegram_message(
            f"✅ 공지사항 모니터링 시작!\n\n"
            f"• 정부24: {sum(1 for n in all_notices if n['source'] == '정부24')}건\n"
            f"• 건강보험공단: {sum(1 for n in all_notices if n['source'] == '건강보험공단')}건\n\n"
            f"총 {len(all_notices)}건을 기준으로 모니터링합니다."
        )
    elif new_notices:
        print(f"\n🔔 신규 공지 {len(new_notices)}건 발견!")
        for n in new_notices:
            print(f"   [{n['source']}] {n['title']}")

        message = format_notification(new_notices)
        send_telegram_message(message)
    else:
        print("\n✅ 신규 공지 없음")

    # 6. 데이터 저장
    known["notices"] = current_ids
    save_known_notices(known)
    print(f"\n현재 추적 중인 공지: {len(current_ids)}건")
    print(f"=== 모니터링 완료 ===")


if __name__ == "__main__":
    main()
