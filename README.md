# 📢 정부24 & 건강보험공단 공지사항 모니터링

GitHub Actions로 정부24와 국민건강보험공단의 공지사항을 자동 모니터링하고,
신규 공지가 등록되면 Telegram으로 알림을 받습니다.

## 구조

```
notice-monitor/
├── .github/workflows/
│   └── monitor.yml        # GitHub Actions 스케줄러
├── data/
│   └── known_notices.json # 수집된 공지 데이터 (자동 업데이트)
├── scraper.py             # 메인 스크래퍼
├── requirements.txt       # Python 의존성
└── README.md
```

## 설정 방법

### 1단계: Telegram 봇 만들기

1. Telegram에서 **@BotFather**를 검색하여 대화 시작
2. `/newbot` 명령 입력 → 봇 이름과 username 설정
3. 발급된 **Bot Token**을 메모 (예: `1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ`)
4. 생성된 봇에게 아무 메시지 하나 전송
5. 브라우저에서 아래 URL 접속하여 **Chat ID** 확인:
   ```
   https://api.telegram.org/bot{YOUR_TOKEN}/getUpdates
   ```
   → `"chat":{"id": 123456789}` 부분의 숫자가 Chat ID

### 2단계: GitHub 레포 생성 및 코드 업로드

```bash
# 새 레포 생성 후
git clone https://github.com/{YOUR_USERNAME}/notice-monitor.git
cd notice-monitor

# 이 프로젝트의 파일들을 복사한 뒤
git add .
git commit -m "init: 공지사항 모니터링 프로젝트"
git push
```

### 3단계: GitHub Secrets 설정

1. GitHub 레포 → **Settings** → **Secrets and variables** → **Actions**
2. 아래 두 Secret을 추가:

| Secret 이름 | 값 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather에서 받은 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 위에서 확인한 Chat ID |

### 4단계: 첫 실행 테스트

1. 레포 → **Actions** 탭 → **공지사항 모니터링** 워크플로우 선택
2. **Run workflow** 버튼 클릭 (수동 실행)
3. Telegram으로 "모니터링 시작" 메시지가 오면 성공!

## 실행 스케줄

| KST | UTC | 설명 |
|---|---|---|
| 09:00 | 00:00 | 오전 체크 |
| 13:00 | 04:00 | 오후 체크 |
| 18:00 | 09:00 | 퇴근 전 체크 |

> 스케줄을 변경하려면 `.github/workflows/monitor.yml`의 cron 표현식을 수정하세요.
> GitHub Actions의 cron은 UTC 기준입니다 (KST = UTC + 9시간).

## 모니터링 대상

| 사이트 | 공지사항 URL |
|---|---|
| 정부24 | https://www.gov.kr/portal/ntcItm |
| 건강보험공단 | https://www.nhis.or.kr |

## 알림 예시

```
🔔 신규 공지사항 알림 (2026-03-13 09:00)

📌 정부24 (1건)
  • 2026년도 민원서식 개편 안내

📌 건강보험공단 (2건)
  • 건강보험료 산정기준 변경 안내
  • 2026년 건강검진 대상자 안내

총 3건의 새 공지가 등록되었습니다.
```

## 커스터마이징

### 스크래핑 주기 변경
`monitor.yml`의 cron 값을 변경합니다:
```yaml
schedule:
  - cron: '0 */2 * * *'  # 2시간마다
```

### 모니터링 사이트 추가
`scraper.py`에 새 함수를 추가하고 `main()`에서 호출하면 됩니다:
```python
def scrape_new_site():
    # ... BeautifulSoup으로 파싱
    return notices

# main()에서
all_notices.extend(scrape_new_site())
```

## 주의사항

- **HTML 구조 변경**: 정부 사이트의 HTML이 변경되면 파싱이 깨질 수 있습니다.
  Actions 로그에서 "스크래핑 실패" 메시지를 확인하고 셀렉터를 수정하세요.
- **GitHub Actions 제한**: 퍼블릭 레포는 무제한, 프라이빗은 월 2,000분 무료.
  하루 3회 실행 시 월 약 15분으로 넉넉합니다.
- **정부24 신/구버전**: 현재 정부24가 plus.gov.kr로 전환 중이므로
  두 URL을 모두 시도하도록 구현되어 있습니다.

## 비용

**완전 무료**입니다.
- GitHub Actions: 퍼블릭 레포 무제한 / 프라이빗 월 2,000분
- Telegram Bot API: 무료
- 별도 서버 불필요

## 라이선스

MIT License - 자유롭게 사용하세요.
