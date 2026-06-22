"""测试各接口响应速度"""
import time
import urllib.request

def test(name, url, referer, timeout=5):
    req = urllib.request.Request(url, headers={"Referer": referer})
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.time() - start
            body = resp.read().decode("utf-8")
            print(f"[{elapsed:.3f}s] ✅ {name}  (响应 {len(body)} 字节)")
            return body[:200]
    except Exception as e:
        elapsed = time.time() - start
        print(f"[{elapsed:.3f}s] ❌ {name}  失败: {e}")
        return None

code = "016874"
date = "2026-06-16"

print(f"测试基金代码: {code}\n")

# 接口1: 历史净值 (lsjz) - 当前使用的
test("1. 历史净值 api.fund.eastmoney.com/f10/lsjz",
     f"https://api.fund.eastmoney.com/f10/lsjz?fundCode={code}&pageIndex=1&pageSize=5&startDate={date}&endDate={date}",
     "https://fundf10.eastmoney.com/")

# 接口2: 基金名称 JSONP (fundgz)
test("2. 基金名称 fundgz.1234567.com.cn (JSONP)",
     f"https://fundgz.1234567.com.cn/js/{code}.js",
     "https://fund.eastmoney.com/")

# 接口3: 基金详情 (f10/jjjz)
test("3. 基金详情 f10/jjjz",
     f"https://api.fund.eastmoney.com/f10/jjjz?fundCode={code}&pageIndex=1&pageSize=1&startDate=2000-01-01&endDate=2000-01-01",
     "https://fundf10.eastmoney.com/")

# 接口4: 基金搜索 (fundsearch)
test("4. 基金搜索 fundsearch",
     f"https://fundsearch.eastmoney.com/api/FundSearchAPI?key={code}&m=1",
     "https://fund.eastmoney.com/")

# 接口5: 实时估值 (fundgz 另一个格式)
test("5. 实时估值 api.fund.eastmoney.com/f10/FundArchivesDatas",
     f"https://api.fund.eastmoney.com/f10/FundArchivesDatas?code={code}&type=jbgk",
     "https://fundf10.eastmoney.com/")
