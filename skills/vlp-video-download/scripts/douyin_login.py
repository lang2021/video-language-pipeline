#!/usr/bin/env python3
"""准备 Douyin 下载需要的本地浏览器登录态。"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from site_downloaders.douyin import PROFILE_DIR


def logged_in(cookie_list: list[dict]) -> bool:
    valid_names = {"sessionid", "sessionid_ss", "sid_guard"}
    for cookie in cookie_list:
        name = cookie.get("name", "")
        value = cookie.get("value", "")
        domain = cookie.get("domain", "")
        if name in valid_names and value and len(value) > 10 and "douyin.com" in domain:
            return True
    return False


def run_login(timeout: int) -> int:
    try:
        from patchright.sync_api import sync_playwright
    except ImportError:
        print("failed: 系统未安装 patchright。请先安装：pip install patchright。", file=sys.stderr)
        return 1

    browser_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    user_agent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            channel="chrome",
            no_viewport=True,
            ignore_default_args=["--enable-automation"],
            user_agent=user_agent,
            args=browser_args,
        )
        page = context.pages[0] if context.pages else context.new_page()
        try:
            page.goto("https://www.douyin.com/", wait_until="domcontentloaded", timeout=60000)
            print("请在打开的 Chrome 窗口中完成 Douyin 登录。")
            start = time.time()
            while time.time() - start < timeout:
                cookies = context.cookies()
                session_cookies = [c for c in cookies if c.get("name") in {"sessionid", "sessionid_ss", "sid_guard"}]
                if logged_in(session_cookies):
                    cookies_file = PROFILE_DIR.parent / "douyin_cookies.json"
                    cookies_file.parent.mkdir(parents=True, exist_ok=True)
                    cookies_file.write_text(json.dumps(cookies, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    print(f"success: Douyin 登录态已保存到 {PROFILE_DIR}")
                    return 0
                time.sleep(3)
            print("failed: 等待登录超时，请重新运行脚本。", file=sys.stderr)
            return 1
        finally:
            context.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="准备 vlp-video-download 的 Douyin 登录态。")
    parser.add_argument("--timeout", type=int, default=120, help="等待手动登录的秒数，默认 120。")
    args = parser.parse_args(argv)
    return run_login(args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
