#!/bin/bash
code="016874"
date="2026-06-16"

echo "测试基金代码: $code"
echo ""

# 1. 历史净值
echo "=== 1. 历史净值 lsjz ==="
curl -s -o /dev/null -w "time_total: %{time_total}s  size: %{size_download}B  http: %{http_code}\n" \
  -H "Referer: https://fundf10.eastmoney.com/" \
  "https://api.fund.eastmoney.com/f10/lsjz?fundCode=${code}&pageIndex=1&pageSize=5&startDate=${date}&endDate=${date}"

# 2. 基金名称 JSONP
echo "=== 2. 基金名称 JSONP fundgz ==="
curl -s -o /dev/null -w "time_total: %{time_total}s  size: %{size_download}B  http: %{http_code}\n" \
  -H "Referer: https://fund.eastmoney.com/" \
  "https://fundgz.1234567.com.cn/js/${code}.js"

# 3. 基金详情 jjjz
echo "=== 3. 基金详情 jjjz ==="
curl -s -o /dev/null -w "time_total: %{time_total}s  size: %{size_download}B  http: %{http_code}\n" \
  -H "Referer: https://fundf10.eastmoney.com/" \
  "https://api.fund.eastmoney.com/f10/jjjz?fundCode=${code}&pageIndex=1&pageSize=1&startDate=2000-01-01&endDate=2000-01-01"

# 4. 基金搜索 fundsearch
echo "=== 4. 基金搜索 fundsearch ==="
curl -s -o /dev/null -w "time_total: %{time_total}s  size: %{size_download}B  http: %{http_code}\n" \
  -H "Referer: https://fund.eastmoney.com/" \
  "https://fundsearch.eastmoney.com/api/FundSearchAPI?key=${code}&m=1"

# 5. 基金概况 FundArchivesDatas
echo "=== 5. 基金概况 FundArchivesDatas ==="
curl -s -o /dev/null -w "time_total: %{time_total}s  size: %{size_download}B  http: %{http_code}\n" \
  -H "Referer: https://fundf10.eastmoney.com/" \
  "https://api.fund.eastmoney.com/f10/FundArchivesDatas?code=${code}&type=jbgk"

echo ""
echo "=== 6. fundf10 页面 (域名连通性) ==="
curl -s -o /dev/null -w "time_total: %{time_total}s  size: %{size_download}B  http: %{http_code}\n" \
  "https://fundf10.eastmoney.com/jjjz_${code}.html"

echo ""
echo "完成"
