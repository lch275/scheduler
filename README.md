# 📢 정부24 & 건강보험공단 공지사항 모니터링

GitHub Actions로 정부24와 국민건강보험공단의 공지사항을 자동 수집하고,
매일 Telegram으로 전체 공지 목록을 전송합니다.

## 구조

```
scheduler/
├── .github/workflows/
│   └── monitor.yml   # GitHub Actions 스케줄러 (매일 KST 09:00)
├── scraper.py         # 메인 스크래퍼
├── requirements.txt   # Python 의존성
└── README.md
```

## 동작 방식

1. GitHub Actions가 매일 오전 9시(KST)에 자동 실행
2. 정부24 API 및 건강보험공단 웹사이트에서 최신 공지사항 수집
3. 수집된 전체 공지 목록을 Telegram으로 전송
4. 공지 수가 많아 메시지가 4,096자를 초과하면 출처별로 분리 전송

## 설정 방법

### 1단계: Telegram 봇 만들기

1. Telegram에서 **@BotFather**를 검색하여 대화 시작
2. `/newbot` 명령 입력 → 봇 이름과 username 설정
3. 발급된 **Bot Token** 메모 (예: `1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ`)
4. 생성된 봇에게 아무 메시지 하나 전송
5. 아래 URL에 접속하여 **Chat ID** 확인:
   ```
   https://api.telegram.org/bot{YOUR_TOKEN}/getUpdates
   ```
   → `"chat":{"id": 123456789}` 부분의 숫자가 Chat ID

### 2단계: GitHub Secrets 설정

1. GitHub 레포 → **Settings** → **Secrets and variables** → **Actions**
2. 아래 두 Secret을 추가:

| Secret 이름 | 값 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather에서 받은 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 위에서 확인한 Chat ID |

### 3단계: 첫 실행 테스트

1. 레포 → **Actions** 탭 → **공지사항 모니터링** 워크플로우 선택
2. **Run workflow** 버튼 클릭 (수동 실행)
3. Telegram으로 공지 목록 메시지가 오면 성공!

## 실행 스케줄

| KST | UTC (cron) | 설명 |
|---|---|---|
| 09:00 | 00:00 | 매일 오전 자동 실행 |

> 스케줄을 변경하려면 `.github/workflows/monitor.yml`의 cron 표현식을 수정하세요.
> GitHub Actions의 cron은 UTC 기준입니다 (KST = UTC + 9시간).

## 모니터링 대상

| 사이트 | 수집 방식 |
|---|---|
| 정부24 | plus.gov.kr JSON API (POST) |
| 건강보험공단 | nhis.or.kr 메인 페이지 HTML 파싱 |

## 알림 예시

```
📋 공지사항 목록 (2026-03-28 09:00)

📌 정부24 (10건)
  1. 2026년도 민원서식 개편 안내
  2. ...

📌 건강보험공단 (5건)
  1. 건강보험료 산정기준 변경 안내
  2. ...

총 15건
```

## 커스터마이징

### 스크래핑 주기 변경

`monitor.yml`의 cron 값을 변경합니다:

```yaml
schedule:
  - cron: '0 0,4,9 * * *'  # KST 09:00, 13:00, 18:00
```

### 모니터링 사이트 추가

`scraper.py`에 새 함수를 추가하고 `main()`에서 호출합니다:

```python
def scrape_new_site():
    notices = []
    # ... BeautifulSoup으로 파싱
    return notices  # [{"title": ..., "url": ..., "source": "사이트명"}]

# main()에서
all_notices.extend(scrape_new_site())
```

## 주의사항

- **HTML 구조 변경**: 정부 사이트의 구조가 변경되면 파싱이 깨질 수 있습니다.
  Actions 로그에서 "스크래핑 실패" 메시지를 확인하고 셀렉터를 수정하세요.
- **GitHub Actions 제한**: 퍼블릭 레포는 무제한, 프라이빗은 월 2,000분 무료.
  하루 1회 실행 시 월 약 5분으로 충분합니다.
- **Telegram 메시지 길이 제한**: 4,096자 초과 시 출처별로 자동 분할 전송됩니다.

## 비용

**완전 무료**입니다.
- GitHub Actions: 퍼블릭 레포 무제한 / 프라이빗 월 2,000분
- Telegram Bot API: 무료
- 별도 서버 불필요

## 라이선스

MIT License
