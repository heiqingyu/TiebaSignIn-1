#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""贴吧每日活跃任务：在指定吧的活跃楼里回复一条，并给主题点赞。

环境变量：
    BDUSS        贴吧 Cookie（必填，工作流已注入）
    TIEBA_FORUM  目标吧名（默认 情殇青羽）
    TIEBA_TID    目标主题 id（可选；留空则自动取该吧第一个主题）
"""

import json
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request

BDUSS = os.environ.get("BDUSS", "").strip()
FORUM = os.environ.get("TIEBA_FORUM", "情殇青羽").strip()
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

def request(url, data=None, timeout=20):
    body = urllib.parse.urlencode(data).encode("utf-8") if data else None
    req = urllib.request.Request(
        url, data=body, headers=HEADERS,
        method="POST" if body else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", "replace")
    try:
        return json.loads(raw)
    except ValueError:
        return raw

def get_tbs():
    info = request("https://tieba.baidu.com/dc/common/tbs")
    if not isinstance(info, dict) or info.get("is_login") != 1:
        raise RuntimeError(f"Cookie 无效或未登录：{info}")
    return info["tbs"]

def resolve_thread():
    """返回 (tid, fid)。优先使用 TIEBA_TID，否则取该吧首页第一个主题。"""
    url = "https://tieba.baidu.com/f?" + urllib.parse.urlencode(
        {"kw": FORUM, "ie": "utf-8"})
    page = request(url)
    if not isinstance(page, str):
        raise RuntimeError("打开吧首页失败，可能被要求验证")

    m = re.search(r'"forum_id"\s*:\s*(\d+)', page) or re.search(r'fid=(\d+)', page)
    fid = m.group(1) if m else ""

    tid = TID
    if not tid:
        ids = re.findall(r'href="/p/(\d+)', page)
        if not ids:
            raise RuntimeError("吧首页没找到任何主题帖")
        tid = ids[0]
    return tid, fid

def do_reply(tbs, tid, fid, content):
    data = {
        "ie": "utf-8",
        "kw": FORUM,
        "tid": tid,
        "content": content,
        "tbs": tbs,
        "__type__": "reply",
        "files": "[]",
    }
    if fid:
        data["fid"] = fid
    return request("https://tieba.baidu.com/f/commit/post/add", data)

def do_agree(tbs, tid):
    data = {
        "tbs": tbs,
        "thread_id": tid,
        "obj_type": 3,
        "agree_type": 1,
    }
    return request("https://tieba.baidu.com/f/commit/agree", data)

def main():
    if not BDUSS:
        print("[FAIL] 未提供 BDUSS")
        return 1

    tbs = get_tbs()
    print(f"[OK] 登录有效，tbs={tbs[:6]}...")

    tid, fid = resolve_thread()
    print(f"[OK] 目标吧={FORUM}，tid={tid}，fid={fid or '未解析到'}")

    content = f"{time.strftime('%Y-%m-%d')} {random.choice(CONTENTS)}"
    reply = do_reply(tbs, tid, fid, content)
    print(f"[回复] {reply}")

    time.sleep(random.randint(5, 15))

    agree = do_agree(tbs, tid)
    print(f"[点赞] {agree}")

    if isinstance(reply, dict) and reply.get("no") == 0:
        print("[OK] 今日活跃任务完成")
        return 0

    print("[FAIL] 回复未成功，请把上面的响应内容贴出来排查")
    return 1

if __name__ == "__main__":
    sys.exit(main())
