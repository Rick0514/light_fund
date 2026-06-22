import json, urllib.request

fund_code = "016874"
date = "2026-06-16"

# 接口5: FundArchivesDatas
print("=== 接口5: FundArchivesDatas ===")
url = f"https://api.fund.eastmoney.com/f10/FundArchivesDatas?code={fund_code}&type=jbgk"
req = urllib.request.Request(url, headers={"Referer": "https://fundf10.eastmoney.com/"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(json.dumps(data, ensure_ascii=False, indent=2)[:600])
except Exception as e:
    print(f"失败: {e}")

# 接口3: jjjz
print("\n=== 接口3: f10/jjjz ===")
url = f"https://api.fund.eastmoney.com/f10/jjjz?fundCode={fund_code}&pageIndex=1&pageSize=1&startDate=2000-01-01&endDate=2000-01-01"
req = urllib.request.Request(url, headers={"Referer": "https://fundf10.eastmoney.com/"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(json.dumps(data, ensure_ascii=False, indent=2)[:600])
except Exception as e:
    print(f"失败: {e}")

# 接口1: lsjz 看看有没有额外字段
print("\n=== 接口1: lsjz (完整响应) ===")
url = f"https://api.fund.eastmoney.com/f10/lsjz?fundCode={fund_code}&pageIndex=1&pageSize=1&startDate={date}&endDate={date}"
req = urllib.request.Request(url, headers={"Referer": "https://fundf10.eastmoney.com/"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(json.dumps(data, ensure_ascii=False, indent=2))
except Exception as e:
    print(f"失败: {e}")
