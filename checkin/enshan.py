# -*- coding: utf-8 -*-
"""恩山无线论坛每日签到。"""

import os

from checkin.enshan_api import EnshanAPI


def main():
    cookies = os.environ.get("ENSHAN_COOKIES", "").strip()
    if not cookies:
        return "未配置 ENSHAN_COOKIES"

    api = EnshanAPI(cookies=cookies)
    result = api.sign_in()
    if result.get("success"):
        details = result.get("result", {})
        return f"签到请求已成功返回：{details}"

    return f"签到失败：{result.get('error', '论坛未确认签到成功')}"


if __name__ == "__main__":
    print(main())
