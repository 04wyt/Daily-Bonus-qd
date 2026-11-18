# -*- coding: utf-8 -*-
# @File     : message.py
# @Time     : 2021/10/17 19:24
# @Author   : Jckling

import asyncio
import os
import sys
import time

from datetime import datetime, timedelta, timezone
from checkin import bilibili, netease, pica, uma, v2ex, yamibo
from telegram import Bot

# info
TG_USER_ID = os.environ.get("TG_USER_ID")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")

# These messages indicate that the check-in/login did not complete reliably.
# Balance/statistics lookup failures are intentionally excluded: they do not
# necessarily mean the daily check-in itself failed.
FAILURE_MARKERS = (
    "签到失败",
    "登录失败",
    "无法连接网站",
    "模块异常",
    "页面被拦截",
    "WAF 挑战失败",
    "签到可能失败",
    "签到结果未知",
    "无法获取 once 参数",
)


def is_checkin_failure(result):
    """Return True when a module's result reports a check-in/login failure."""
    return any(marker in result for marker in FAILURE_MARKERS)


def run_module(main, attempts=3, delay=10):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            result = main()
            result = str(result or "模块未返回结果")
            return result, is_checkin_failure(result)
        except Exception as e:
            last_error = e
            if attempt < attempts:
                time.sleep(delay)

    result = f"模块异常（重试 {attempts} 次后仍失败）：{last_error}"
    return result, True


def send_message(content, attempts=3, delay=15):
    bot = Bot(token=TG_BOT_TOKEN)
    for attempt in range(1, attempts + 1):
        try:
            asyncio.run(bot.send_message(chat_id=TG_USER_ID, text=content))
            return True
        except Exception as e:
            if attempt < attempts:
                time.sleep(delay)
            else:
                print(f"Telegram 发送失败：{e}")
    return False


if __name__ == "__main__":
    start_time = time.time()
    utc_time = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    content_lst = []
    failed_modules = []

    def add_module(name, main):
        result, failed = run_module(main)
        status = "❌" if failed else "✅"
        content_lst.append(f"{status}「{name}」\n{result}")
        if failed:
            failed_modules.append(name)

    if os.environ.get("UMA_COOKIES"):
        add_module("賽馬娘每日簽到", uma.main)
    if os.environ.get("YAMIBO_USERNAME") and os.environ.get("YAMIBO_PASSWORD"):
        add_module("Yamibo", yamibo.main)
    if os.environ.get("V2EX_COOKIES"):
        add_module("V2EX", v2ex.main)
    if os.environ.get("BILIBILI_COOKIES"):
        add_module("Bilibili", bilibili.main)
    if os.environ.get("PICA_USERNAME") and os.environ.get("PICA_PASSWORD"):
        add_module("哔咔漫画", pica.main)
    if os.environ.get("NETEASE_MUSIC_COOKIES"):
        add_module("网易云音乐", netease.main)

    content_lst.append(
        f"开始时间: {utc_time}\n"
        f"任务用时: {int(time.time() - start_time)} 秒\n"
    )

    if failed_modules:
        content_lst.append("失败项目: " + "、".join(failed_modules))
        content_lst.append("⚠️ 本次存在签到/登录失败，请检查上方详情。")
    else:
        content_lst.append("✅ 本次已启用项目未检测到签到/登录失败。")

    content = "\n————————————\n\n".join(content_lst)

    print(content)

    # Send the report before returning a failing exit code, so Telegram still
    # receives the failure details when a check-in fails.
    if TG_BOT_TOKEN:
        if not send_message(content):
            sys.exit(1)

    if failed_modules:
        sys.exit(1)
