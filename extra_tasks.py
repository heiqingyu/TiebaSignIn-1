#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""贴吧每日活跃任务：在指定吧的活跃楼里回复一条，并给主题点赞。

环境变量：
    BDUSS        贴吧 Cookie（必填）
    TIEBA_FORUM  目标吧名（必填，建议放在 Secrets 中）
    TIEBA_TID    目标主题 id（建议放在 Secrets 中）
"""

import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BDUSS = os.environ.get("BDUSS", "").strip()
FORUM = os.environ.get("TIEBA_FORUM", "").strip()
TID = os.environ.get("TIEBA_TID", "").strip()

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

HEADERS = {
    "User-Agent": UA,
    "Referer": "https://tieba.baidu.com/",
    "Cookie": f"BDUSS={BDUSS}",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}

CONTENTS = [
    "今日打卡，继续保持",
    "签到打卡，今天也在",
    "每日一签，保持活跃",
    "打卡记录，路过留个脚印",
]

class RequestError(Exception):
    pass

def request(url, data=None, timeout=20):
    body = urllib.parse.urlencode(data).encode("utf-8") if data else None
    req = urllib.request.Request(
        url, data=body, headers=HEADERS,
        method="POST" if body else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise RequestError(f"HTTP {e.code}") from None
    except Exception as e:
        raise RequestError(type(e).__name__) from None
    try:
        return json.loads(raw)
    except ValueError:
        return raw

def get_tbs():
    info = request("https://tieba.baidu.com/dc/common/tbs")
    if not isinstance(info, dict) or info.get("is_login") != 1:
        raise RequestError(f"Cookie 无效或未登录：{info}")
    return info["tbs"]

def do_reply(tbs, content):
    data = {
        "ie": "utf-8",
        "kw": FORUM,
        "tid": TID,
        "content": content,
        "tbs": tbs,
        "__type__": "reply",
        "files": "[]",
    }
    return request("https://tieba.baidu.com/f/commit/post/add", data)

def do_agree(tbs):
    data = {
        "tbs": tbs,
        "thread_id": TID,
        "obj_type": 3,
        "agree_type": 1,
    }
    return request("https://tieba.baidu.com/f/commit/agree", data)

def main():
    missing = [k for k, v in
               (("BDUSS", BDUSS), ("TIEBA_FORUM", FORUM), ("TIEBA_TID", TID)) if not v]
    if missing:
        print(f"[FAIL] 缺少环境变量: {', '.join(missing)}")
        return 1

    try:
        tbs = get_tbs()
        print("[OK] 登录有效")

        content = f"{time.strftime('%Y-%m-%d')} {random.choice(CONTENTS)}"
        reply = do_reply(tbs, content)
        print(f"[回复] {reply}")

        time.sleep(random.randint(5, 15))

        agree = do_agree(tbs)
        print(f"[点赞] {agree}")

    except RequestError as e:
        print(f"[FAIL] 请求失败: {e}")
        return 1

    if isinstance(reply, dict) and reply.get("no") == 0:
        print("[OK] 今日活跃任务完成")
        return 0

    print("[FAIL] 回复未成功，请检查上面的响应内容")
    return 1

if __name__ == "__main__":
    sys.exit(main())
