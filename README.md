# 基金持仓管理 light_fund

一个轻量级的个人基金持仓管理工具，支持自选基金追踪、实时估值、加仓记录和盈亏计算。

## 功能

- **自选基金管理**：输入基金代码添加，自动获取基金名称、净值、涨跌幅
- **实时估值**：点击刷新获取盘中实时估值和涨幅（交易时段有效）
- **加仓记录**：记录每次加仓的日期和金额，自动按当日净值折算份额
- **持仓汇总**：累计投入、当前市值、持仓盈亏一目了然
- **数据持久化**：所有数据存储在本地 JSON 文件，重启不丢失

## 环境要求

- Python 3.8+
- `curl`（系统自带）

无需安装任何第三方依赖。

## 快速开始

```bash
# 1. 进入项目目录
cd light_fund

# 2. 启动服务
python3 server.py

# 3. 浏览器打开
# http://localhost:8080
```

## 项目结构

```
light_fund/
├── fund_api.py           # 基金数据 API（净值、估值、名称）
├── server.py             # HTTP 服务 + REST API
├── test_fund.py          # 基金接口测试
├── data/
│   └── funds.json        # 持久化数据（自动生成）
├── static/
│   ├── index.html        # 前端页面
│   ├── app.js            # 前端逻辑
│   ├── style.css         # 样式
│   ├── pico.min.css      # Pico.css 框架
│   └── alpine.min.js     # Alpine.js 框架
└── README.md
```

## 接口测试

```bash
python3 test_fund.py
```

## 数据来源

基金净值、估值数据来源于东方财富公开接口，仅供参考。

