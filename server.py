from __future__ import annotations

import json
import os
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote
from pathlib import Path

from fund_api import get_fund_info, get_fund_valuation

DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "funds.json"
STATIC_DIR = Path(__file__).parent / "static"


def load_data() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"funds": {}, "tags": []}  # tags 全局标签列表


def save_data(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class FundHandler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filepath: Path, content_type: str):
        if not filepath.exists():
            self.send_response(404)
            self.end_headers()
            return
        body = filepath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        body = self.rfile.read(length)
        return json.loads(body)

    def _parse_path(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        return path, parsed

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ────────────────────────── GET ──────────────────────────

    def do_GET(self):
        path, _ = self._parse_path()

        if path == "" or path == "/":
            return self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        if path.startswith("/static/"):
            filename = path[len("/static/"):]
            ct = "text/css" if filename.endswith(".css") else "application/javascript"
            return self._send_file(STATIC_DIR / filename, ct)

        parts = path.split("/")

        # ─── 标签 ───
        if path == "/api/tags":
            data = load_data()
            return self._send_json(data.get("tags", []))

        # ─── 估值 ───
        if path == "/api/valuations":
            data = load_data()
            result = {}
            for code in data["funds"]:
                try:
                    val = get_fund_valuation(code)
                    if val and "error" not in val:
                        result[code] = val
                except Exception:
                    pass
            return self._send_json(result)

        # ─── 基金列表 ───
        if path == "/api/funds":
            data = load_data()
            result = []
            for code, info in data["funds"].items():
                fund_info = get_fund_info(code)
                positions = info.get("positions", [])
                tags = info.get("tags", [])
                entry = {
                    "fund_code": code,
                    "name": info.get("name", code),
                    "added_at": info.get("added_at", ""),
                    "tags": tags,
                    "positions": positions,
                }
                if fund_info:
                    entry["nav"] = fund_info["nav"]
                    entry["daily_return"] = fund_info["daily_return"]
                    entry["nav_date"] = fund_info["date"]
                    buy_amount = sum(p["amount"] for p in positions if p.get("type") != "sell")
                    sell_amount = sum(p["amount"] for p in positions if p.get("type") == "sell")
                    buy_shares = sum(p["shares"] for p in positions if p.get("type") != "sell")
                    sell_shares = sum(p["shares"] for p in positions if p.get("type") == "sell")
                    total_invested = round(buy_amount - sell_amount, 2)
                    total_shares = round(buy_shares - sell_shares, 4)
                    entry["total_invested"] = total_invested
                    entry["total_shares"] = total_shares
                    entry["current_value"] = round(total_shares * fund_info["nav"], 2)
                    entry["profit"] = round(entry["current_value"] - total_invested, 2)
                    entry["profit_pct"] = round(entry["profit"] / total_invested * 100, 2) if total_invested > 0 else 0
                    if positions:
                        last_pos = sorted(positions, key=lambda p: p["date"])[-1]
                        if last_pos.get("nav") and last_pos["nav"] > 0:
                            entry["last_nav"] = last_pos["nav"]
                            entry["nav_change_since_last"] = round((fund_info["nav"] - last_pos["nav"]) / last_pos["nav"] * 100, 2)
                        else:
                            entry["last_nav"] = None
                            entry["nav_change_since_last"] = None
                    else:
                        entry["last_nav"] = None
                        entry["nav_change_since_last"] = None
                entry["valuation"] = None
                result.append(entry)
            return self._send_json(result)

        # ─── 操作记录 ───
        if len(parts) == 5 and parts[1] == "api" and parts[2] == "funds" and parts[4] == "positions":
            code = parts[3]
            data = load_data()
            if code not in data["funds"]:
                return self._send_json({"error": "基金不存在"}, 404)
            positions = data["funds"][code].get("positions", [])
            fund_info = get_fund_info(code)
            result = {
                "fund_code": code,
                "name": data["funds"][code].get("name", code),
                "tags": data["funds"][code].get("tags", []),
                "positions": positions,
            }
            if fund_info:
                buy_amount = sum(p["amount"] for p in positions if p.get("type") != "sell")
                sell_amount = sum(p["amount"] for p in positions if p.get("type") == "sell")
                buy_shares = sum(p["shares"] for p in positions if p.get("type") != "sell")
                sell_shares = sum(p["shares"] for p in positions if p.get("type") == "sell")
                total_invested = round(buy_amount - sell_amount, 2)
                total_shares = round(buy_shares - sell_shares, 4)
                result["nav"] = fund_info["nav"]
                result["nav_date"] = fund_info["date"]
                result["total_invested"] = total_invested
                result["total_shares"] = total_shares
                result["current_value"] = round(total_shares * fund_info["nav"], 2)
                result["profit"] = round(result["current_value"] - total_invested, 2)
            return self._send_json(result)

        self._send_json({"error": "Not Found"}, 404)

    # ────────────────────────── POST ──────────────────────────

    def do_POST(self):
        path, _ = self._parse_path()
        parts = path.split("/")

        # ─── 添加自选 ───
        if path == "/api/funds":
            body = self._read_body()
            fund_code = body.get("fund_code", "").strip()
            if not fund_code:
                return self._send_json({"error": "基金代码不能为空"}, 400)
            data = load_data()
            if fund_code in data["funds"]:
                return self._send_json({"error": "该基金已在自选列表中"}, 400)
            fund_info = get_fund_info(fund_code)
            if not fund_info:
                return self._send_json({"error": f"无法获取基金 {fund_code} 的信息"}, 400)
            data["funds"][fund_code] = {
                "name": fund_info["name"],
                "added_at": fund_info["date"],
                "tags": [],
                "positions": [],
            }
            save_data(data)
            return self._send_json({
                "fund_code": fund_code,
                "name": fund_info["name"],
                "nav": fund_info["nav"],
                "daily_return": fund_info["daily_return"],
            }, 201)

        # ─── 新增标签 ───
        if path == "/api/tags":
            body = self._read_body()
            tag_name = body.get("name", "").strip()
            if not tag_name:
                return self._send_json({"error": "标签名称不能为空"}, 400)
            data = load_data()
            if "tags" not in data:
                data["tags"] = []
            if tag_name in data["tags"]:
                return self._send_json({"error": f"标签 '{tag_name}' 已存在"}, 400)
            data["tags"].append(tag_name)
            save_data(data)
            return self._send_json({"name": tag_name}, 201)

        # ─── 给基金加标签 ───
        if len(parts) == 5 and parts[1] == "api" and parts[2] == "funds" and parts[4] == "tags":
            code = parts[3]
            body = self._read_body()
            tag_name = body.get("name", "").strip()
            if not tag_name:
                return self._send_json({"error": "标签名称不能为空"}, 400)
            data = load_data()
            if code not in data["funds"]:
                return self._send_json({"error": "基金不存在"}, 404)
            if "tags" not in data["funds"][code]:
                data["funds"][code]["tags"] = []
            if tag_name in data["funds"][code]["tags"]:
                return self._send_json({"error": f"该基金已有标签 '{tag_name}'"}, 400)
            data["funds"][code]["tags"].append(tag_name)
            save_data(data)
            return self._send_json({"fund_code": code, "tag": tag_name}, 201)

        # ─── 添加操作记录 ───
        if len(parts) == 5 and parts[1] == "api" and parts[2] == "funds" and parts[4] == "positions":
            code = parts[3]
            body = self._read_body()
            pos_date = body.get("date", "").strip()
            amount = body.get("amount", 0)
            shares_input = body.get("shares", 0)
            op_type = body.get("type", "buy")
            note = body.get("note", "").strip()

            if amount <= 0 and shares_input <= 0:
                return self._send_json({"error": "金额或份额不能为空"}, 400)
            if not pos_date:
                return self._send_json({"error": "日期不能为空"}, 400)
            if op_type not in ("buy", "sell"):
                return self._send_json({"error": "操作类型无效"}, 400)

            data = load_data()
            if code not in data["funds"]:
                return self._send_json({"error": "基金不存在"}, 404)

            fund_info = get_fund_info(code, pos_date)
            if not fund_info:
                return self._send_json({"error": f"无法获取 {code} 在 {pos_date} 的净值"}, 400)

            nav = fund_info["nav"]
            if shares_input > 0:
                shares = round(shares_input, 4)
                amount = round(shares * nav, 2)
            else:
                shares = round(amount / nav, 4) if nav > 0 else 0

            position = {
                "id": uuid.uuid4().hex[:8],
                "date": pos_date,
                "type": op_type,
                "amount": round(amount, 2),
                "nav": nav,
                "shares": shares,
                "note": note,
            }
            data["funds"][code].setdefault("positions", []).append(position)
            save_data(data)
            return self._send_json(position, 201)

        self._send_json({"error": "Not Found"}, 404)

    # ───────────────────────── DELETE ──────────────────────────

    def do_DELETE(self):
        path, _ = self._parse_path()
        parts = path.split("/")

        # ─── 删除标签 ───
        if len(parts) == 4 and parts[1] == "api" and parts[2] == "tags":
            tag_name = parts[3]
            data = load_data()
            if tag_name not in data.get("tags", []):
                return self._send_json({"error": f"标签 '{tag_name}' 不存在"}, 404)
            data["tags"].remove(tag_name)
            # 同时清理所有基金上挂的这个标签
            for info in data["funds"].values():
                if "tags" in info and tag_name in info["tags"]:
                    info["tags"].remove(tag_name)
            save_data(data)
            return self._send_json({"ok": True})

        # ─── 删除基金上的某个标签 ───
        if len(parts) == 6 and parts[1] == "api" and parts[2] == "funds" and parts[4] == "tags":
            code, tag_name = parts[3], unquote(parts[5])
            data = load_data()
            if code not in data["funds"]:
                return self._send_json({"error": "基金不存在"}, 404)
            tags = data["funds"][code].get("tags", [])
            if tag_name not in tags:
                return self._send_json({"error": f"标签 '{tag_name}' 不存在于此基金"}, 404)
            tags.remove(tag_name)
            save_data(data)
            return self._send_json({"ok": True})

        # ─── 删除自选 ───
        if len(parts) == 4 and parts[1] == "api" and parts[2] == "funds":
            code = parts[3]
            data = load_data()
            if code not in data["funds"]:
                return self._send_json({"error": "基金不存在"}, 404)
            del data["funds"][code]
            save_data(data)
            return self._send_json({"ok": True})

        # ─── 删除操作记录 ───
        if len(parts) == 6 and parts[1] == "api" and parts[2] == "funds" and parts[4] == "positions":
            code, pid = parts[3], parts[5]
            data = load_data()
            if code not in data["funds"]:
                return self._send_json({"error": "基金不存在"}, 404)
            positions = data["funds"][code].get("positions", [])
            data["funds"][code]["positions"] = [p for p in positions if p["id"] != pid]
            save_data(data)
            return self._send_json({"ok": True})

        self._send_json({"error": "Not Found"}, 404)

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")


def main():
    os.chdir(Path(__file__).parent)
    port = 8080
    server = HTTPServer(("0.0.0.0", port), FundHandler)
    print(f"基金持仓管理服务已启动: http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
        server.server_close()


if __name__ == "__main__":
    main()
