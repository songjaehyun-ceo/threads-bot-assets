"""오늘(KST) 날짜와 시간대(am/noon/night)에 해당하는 글을 Threads에 게시한다."""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

API = "https://graph.threads.net/v1.0"
KST = timezone(timedelta(hours=9))
# 워크플로 cron(UTC) → 시간대
CRON_SLOT = {"13 22 * * *": "am", "43 3 * * *": "noon", "47 13 * * *": "night"}


def call(path, params):
    params["access_token"] = os.environ["THREADS_ACCESS_TOKEN"]
    req = urllib.request.Request(f"{API}/{path}", data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Threads API 오류 {e.code}: {e.read().decode()}")


def main():
    now = datetime.now(KST)
    day = os.environ.get("POST_DATE") or now.strftime("%Y-%m-%d")
    slot = os.environ.get("POST_SLOT") or CRON_SLOT.get(os.environ.get("CRON", ""))
    if not slot:  # 수동 실행 시 현재 시각 기준
        slot = "am" if now.hour < 11 else "noon" if now.hour < 18 else "night"
    with open("posts.json", encoding="utf-8") as f:
        posts = [p for p in json.load(f) if p["date"] == day and p["slot"] == slot]
    if not posts:
        print(f"{day} {slot}: 예약된 글 없음")
        return
    for p in posts:
        container = call("me/threads", {"media_type": "TEXT", "text": p["text"]})
        time.sleep(5)
        result = call("me/threads_publish", {"creation_id": container["id"]})
        print(f"{day} {slot} 게시 완료: {result.get('id')}")


if __name__ == "__main__":
    main()
