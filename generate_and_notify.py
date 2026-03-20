"""
연금복권720+ 번호 생성 & 텔레그램 알림
- 동행복권 API에서 최신 당첨번호 자동 수집
- 당첨번호 제외한 번호 생성
- 텔레그램 봇으로 알림 발송
"""
import os
import json
import random
import ssl
from urllib.request import urlopen, Request
from datetime import datetime, timezone, timedelta

# 한국 시간대
KST = timezone(timedelta(hours=9))

# 환경변수에서 설정 읽기 (GitHub Secrets)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def fetch_winners():
    """동행복권 API에서 역대 1등 당첨번호 가져오기"""
    url = "https://www.dhlottery.co.kr/pt720/selectPstPt720WnList.do"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        winners = set()
        results = data.get("data", {}).get("result", [])
        for item in results:
            group = item.get("wnBndNo", 0)
            number = item.get("wnRnkVl", "")
            if group and number:
                winners.add(f"{group}{number}")
        latest = max((item.get("psltEpsd", 0) for item in results), default=0)
        return winners, latest, len(results)
    except Exception as e:
        print(f"API 호출 실패: {e}")
        return set(), 0, 0


def generate_number(past_winners):
    """당첨번호 제외 랜덤 번호 생성"""
    while True:
        group = random.randint(1, 5)
        number = random.randint(0, 999999)
        key = f"{group}{number:06d}"
        if key not in past_winners:
            return group, f"{number:06d}"


def send_telegram(message):
    """텔레그램 봇으로 메시지 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }).encode("utf-8")
    req = Request(url, data=payload, headers={"Content-Type": "application/json"})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urlopen(req, timeout=10, context=ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("ok"):
                print("텔레그램 전송 성공!")
            else:
                print(f"텔레그램 전송 실패: {result}")
    except Exception as e:
        print(f"텔레그램 전송 에러: {e}")


def main():
    now = datetime.now(KST)
    print(f"실행 시간: {now.strftime('%Y-%m-%d %H:%M:%S')} (KST)")

    # 1. 당첨번호 수집
    winners, latest_round, total = fetch_winners()
    print(f"수집 완료: {latest_round}회까지 {total}개 당첨번호")

    # 2. 번호 생성
    group, number = generate_number(winners)
    print(f"생성 번호: {group}조 {number}")

    # 3. 텔레그램 메시지 구성
    message = (
        f"<b>🎰 연금복권720+ 추천번호</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"\n"
        f"<b>★ {group}조  {number}</b>\n"
        f"\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📅 {now.strftime('%Y년 %m월 %d일 %H:%M')}\n"
        f"📊 {latest_round}회까지 {total}개 당첨번호 제외\n"
        f"\n"
        f"행운을 빕니다! 🍀"
    )

    # 4. 전송
    if TELEGRAM_TOKEN and CHAT_ID:
        send_telegram(message)
    else:
        print("환경변수 TELEGRAM_TOKEN, TELEGRAM_CHAT_ID 미설정")
        print(f"메시지 미리보기:\n{message}")


if __name__ == "__main__":
    main()
