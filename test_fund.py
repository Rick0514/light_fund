from __future__ import annotations

import sys

from fund_api import get_fund_info


def test_get_fund_info():
    """测试 get_fund_info 函数"""
    # test_code = "016874"
    test_code = "017076"
    test_date = "2026-06-16"

    print("=" * 50)
    print(f"测试 1: 正常查询（代码 {test_code}，日期 {test_date}）")
    result = get_fund_info(test_code, test_date)
    if result:
        print(f"  基金名称: {result['name']}")
        print(f"  基金代码: {result['fund_code']}")
        print(f"  日期: {result['date']}")
        print(f"  单位净值: {result['nav']}")
        print(f"  累计净值: {result['acc_nav']}")
        print(f"  日增长率: {result['daily_return']:.4%}")
    else:
        print("  未获取到数据")

    print()
    print("=" * 50)
    print("测试 2: 无效日期格式")
    try:
        get_fund_info(test_code, "20250616")
    except ValueError as e:
        print(f"  捕获到预期的异常: {e}")

    print()
    print("=" * 50)
    print("测试 3: 无效基金代码")
    result = get_fund_info("999999", test_date)
    if result is None:
        print("  正确返回 None")


if __name__ == "__main__":
    test_get_fund_info()
