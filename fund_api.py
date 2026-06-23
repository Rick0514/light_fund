from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, date, timedelta
from typing import Optional

FUND_NAME_CACHE: dict[str, str] = {}


def _http_get(url: str, referer: str = "", timeout: int = 10) -> str:
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


def _query_fund_nav(fund_code: str, start_date: str, end_date: str) -> Optional[dict]:
    """查询基金在日期范围内的净值数据，返回第一条记录"""
    url = (
        f"https://api.fund.eastmoney.com/f10/lsjz"
        f"?fundCode={fund_code}&pageIndex=1&pageSize=5"
        f"&startDate={start_date}&endDate={end_date}"
    )

    try:
        content = _http_get(url, referer="https://fundf10.eastmoney.com/")
    except Exception as e:
        print(f"请求失败: {e}")
        return None

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return None

    if data.get("ErrCode") != 0:
        return None

    records = data.get("Data", {}).get("LSJZList", [])
    if not records:
        return None

    # 取日期最新的记录
    records.sort(key=lambda r: r.get("FSRQ", ""), reverse=True)
    latest = records[0]

    return {
        "fund_code": fund_code,
        "name": _get_fund_name(fund_code),
        "date": latest["FSRQ"],
        "nav": float(latest["DWJZ"]),
        "acc_nav": float(latest["LJJZ"]),
        "daily_return": float(latest.get("JZZZL", "0")) / 100 if latest.get("JZZZL") else 0.0,
    }


def get_fund_info(fund_code: str, target_date: str = "") -> Optional[dict]:
    """
    获取基金在指定日期（或最近交易日）的净值信息。

    Args:
        fund_code: 基金代码
        target_date: 日期 YYYY-MM-DD，空字符串表示最新交易日

    Returns:
        dict 或 None
    """
    today = date.today().isoformat()
    if not target_date:
        target_date = today

    # 校验格式
    try:
        datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"日期格式错误: {target_date}，应为 YYYY-MM-DD")

    # 查最近 10 天内最新净值（指定日期往前10天）
    dt = datetime.strptime(target_date, "%Y-%m-%d")
    start = (dt - timedelta(days=10)).strftime("%Y-%m-%d")
    result = _query_fund_nav(fund_code, start, target_date)
    if result:
        return result

    # 放宽到最近 30 天
    start = (dt - timedelta(days=30)).strftime("%Y-%m-%d")
    result = _query_fund_nav(fund_code, start, target_date)
    return result

    # 如果当天没数据（非交易日），往前回退最多 10 天查最近交易日
    dt = datetime.strptime(target_date, "%Y-%m-%d")
    for _ in range(10):
        dt -= timedelta(days=1)
        prev = dt.strftime("%Y-%m-%d")
        result = _query_fund_nav(fund_code, prev, prev)
        if result:
            return result

    # 放宽到最近 30 天
    fallback_start = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
    result = _query_fund_nav(fund_code, fallback_start, target_date)
    return result


def get_fund_valuation(code: str) -> dict:
    """
    获取单只基金的实时估值和涨跌幅。

    参数：
        code: 基金代码，如 "000001"

    返回：
        dict，包含：
            - code:      基金代码
            - name:      基金名称
            - dwjz:      最新单位净值（通常为前一交易日）
            - gsz:       实时估算净值
            - gszzl:     估算涨跌幅（%）
            - gztime:    估值时间
            - jzrq:      净值日期

        若获取失败返回 {"code": code, "error": "..."}
    """
    # 1. 东方财富基金估值接口（JSONP 格式）
    ts = int(datetime.now().timestamp() * 1000)
    url = f"https://fundgz.1234567.com.cn/js/{code}.js?rt={ts}"
    referer = "https://fundgz.1234567.com.cn/"

    try:
        raw = _http_get(url, referer=referer, timeout=10)
    except OSError as e:
        return {"code": code, "error": str(e)}

    if not raw or "jsonpgz" not in raw:
        return {"code": code, "error": f"估值接口未返回有效数据，原始响应: {raw[:200]}"}

    # 剥掉 jsonpgz(...) 的外壳
    json_str = re.sub(r'^jsonpgz\(', '', raw)
    json_str = re.sub(r'\);?\s*$', '', json_str)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return {"code": code, "error": f"JSON 解析失败: {e}"}

    if not data or not isinstance(data, dict):
        return {"code": code, "error": "接口返回数据格式异常"}

    return {
        "code": data.get("fundcode", code),
        "name": data.get("name", ""),
        "dwjz": data.get("dwjz", ""),
        "gsz": data.get("gsz", ""),
        "gszzl": data.get("gszzl", ""),
        "gztime": data.get("gztime", ""),
        "jzrq": data.get("jzrq", ""),
    }