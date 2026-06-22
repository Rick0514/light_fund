from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, date
from typing import Optional

# 基金名称缓存
FUND_NAME_CACHE: dict[str, str] = {}


def _http_get(url: str, referer: str = "", timeout: int = 10) -> str:
    """通过 curl 发起 HTTP GET 请求，返回响应内容"""
    cmd = ["curl", "-s", "--max-time", str(timeout)]
    if referer:
        cmd += ["-H", f"Referer: {referer}"]
    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
        return result.stdout
    except Exception as e:
        raise OSError(f"curl 请求失败: {e}")


def _get_fund_name(fund_code: str) -> str:
    """从基金详情页 title 获取基金名称（带缓存）"""
    if fund_code in FUND_NAME_CACHE:
        return FUND_NAME_CACHE[fund_code]

    try:
        html = _http_get(
            f"https://fund.eastmoney.com/{fund_code}.html",
            referer="https://fund.eastmoney.com/",
        )
        m = re.search(r"<title>([^<]*)</title>", html)
        if m:
            name = m.group(1).split("(")[0].strip()
        else:
            name = fund_code
    except Exception:
        name = fund_code

    FUND_NAME_CACHE[fund_code] = name
    return name


def get_fund_info(fund_code: str, target_date: str = "") -> Optional[dict]:
    """
    获取中国公募基金在指定日期的净值信息。

    Args:
        fund_code: 基金代码（如 "110003"）
        target_date: 日期 YYYY-MM-DD，空字符串表示最新交易日

    Returns:
        dict: {fund_code, name, date, nav, acc_nav, daily_return} 或 None
    """
    today = date.today().isoformat()
    if not target_date:
        target_date = today

    # 校验日期格式
    try:
        datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"日期格式错误: {target_date}，应为 YYYY-MM-DD")

    url = (
        f"https://api.fund.eastmoney.com/f10/lsjz"
        f"?fundCode={fund_code}&pageIndex=1&pageSize=5"
        f"&startDate={target_date}&endDate={target_date}"
    )

    try:
        content = _http_get(url, referer="https://fundf10.eastmoney.com/")
    except Exception as e:
        print(f"请求失败: {e}")
        return None

    data = json.loads(content)

    if data.get("ErrCode") != 0:
        return None

    records = data.get("Data", {}).get("LSJZList", [])
    if not records:
        return None

    # 取日期匹配的第一条记录
    target = None
    for r in records:
        if r.get("FSRQ") == target_date:
            target = r
            break
    if target is None:
        target = records[0]

    return {
        "fund_code": fund_code,
        "name": _get_fund_name(fund_code),
        "date": target["FSRQ"],
        "nav": float(target["DWJZ"]),
        "acc_nav": float(target["LJJZ"]),
        "daily_return": float(target.get("JZZZL", "0")) / 100 if target.get("JZZZL") else 0.0,
    }
