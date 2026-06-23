window.fundApp = () => ({
    funds: [],
    newFundCode: "",
    loading: false,
    loadingFunds: false,
    error: "",
    successMsg: "",
    showPosCode: null,
    posData: null,
    posDate: new Date().toISOString().split("T")[0],
    posAmount: "",
    posNote: "",
    posLoading: false,
    refreshing: false,
    valTime: "",

    async init() {
        await this.loadFunds();
    },

    async loadFunds() {
        this.loadingFunds = true;
        try {
            const resp = await fetch("/api/funds");
            if (resp.ok) {
                const currentValuations = Object.fromEntries(
                    this.funds
                        .filter((fund) => fund.valuation)
                        .map((fund) => [fund.fund_code, fund.valuation])
                );
                const funds = await resp.json();
                this.funds = funds.map((fund) => ({
                    ...fund,
                    valuation: fund.valuation || currentValuations[fund.fund_code] || null,
                }));
            }
        } catch (e) {
            console.error("加载基金列表失败", e);
        } finally {
            this.loadingFunds = false;
        }
    },

    async refreshValuation() {
        this.refreshing = true;
        try {
            const resp = await fetch("/api/valuations");
            if (resp.ok) {
                const vals = await resp.json();
                for (const f of this.funds) {
                    if (vals[f.fund_code]) {
                        f.valuation = {
                            gsz: vals[f.fund_code].gsz,
                            gszzl: vals[f.fund_code].gszzl,
                            gztime: vals[f.fund_code].gztime,
                        };
                    }
                }
                const now = new Date();
                this.valTime = now.toLocaleTimeString("zh-CN");
            }
        } catch (e) {
            console.error("刷新估值失败", e);
        } finally {
            this.refreshing = false;
        }
    },

    async addFund() {
        const code = this.newFundCode.trim();
        if (!code) return;
        this.loading = true;
        this.error = "";
        this.successMsg = "";
        try {
            const resp = await fetch("/api/funds", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ fund_code: code }),
            });
            const data = await resp.json();
            if (resp.ok) {
                this.successMsg = `已添加 ${code} ${data.name}，净值: ${data.nav}`;
                this.newFundCode = "";
                await this.loadFunds();
                setTimeout(() => this.successMsg = "", 3000);
            } else {
                this.error = data.error || "添加失败";
            }
        } catch (e) {
            this.error = "网络错误，请稍后重试";
        } finally {
            this.loading = false;
        }
    },

    async deleteFund(code) {
        if (!confirm(`确认删除自选基金 ${code}？`)) return;
        try {
            const resp = await fetch(`/api/funds/${code}`, { method: "DELETE" });
            if (resp.ok) {
                this.showPosCode = null;
                this.posData = null;
                await this.loadFunds();
            }
        } catch (e) {
            console.error("删除失败", e);
        }
    },

    async openPositions(code) {
        this.showPosCode = code;
        this.posData = null;
        this.posAmount = "";
        this.posNote = "";
        await this.refreshPositions(code);
    },

    async refreshPositions(code) {
        try {
            const resp = await fetch(`/api/funds/${code}/positions`);
            if (resp.ok) {
                const data = await resp.json();
                this.posData = data;
                this.updateFundFromPositionData(data);
            }
        } catch (e) {
            console.error("加载加仓记录失败", e);
        }
    },

    updateFundFromPositionData(data) {
        const fund = this.funds.find((item) => item.fund_code === data.fund_code);
        if (!fund) return;

        fund.positions = data.positions || [];
        fund.nav = data.nav;
        fund.nav_date = data.nav_date;
        fund.total_invested = data.total_invested || 0;
        fund.total_shares = data.total_shares || 0;
        fund.current_value = data.current_value || 0;
        fund.profit = data.profit || 0;
        fund.profit_pct = fund.total_invested > 0 ? (fund.profit / fund.total_invested) * 100 : 0;

        const positions = fund.positions;
        if (positions.length && data.nav) {
            const lastPos = [...positions].sort((a, b) => a.date.localeCompare(b.date)).at(-1);
            fund.last_nav = lastPos?.nav || null;
            fund.nav_change_since_last = fund.last_nav
                ? ((data.nav - fund.last_nav) / fund.last_nav) * 100
                : null;
        } else {
            fund.last_nav = null;
            fund.nav_change_since_last = null;
        }
    },

    async addPosition(code) {
        const amount = parseFloat(this.posAmount);
        if (!this.posDate || isNaN(amount) || amount <= 0) return;
        this.posLoading = true;
        this.error = "";
        try {
            const resp = await fetch(`/api/funds/${code}/positions`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ date: this.posDate, amount: amount, note: this.posNote }),
            });
            const data = await resp.json();
            if (resp.ok) {
                this.posAmount = "";
                this.posNote = "";
                await this.refreshPositions(code);
            } else {
                this.error = data.error || "添加加仓失败";
            }
        } catch (e) {
            this.error = "网络错误";
        } finally {
            this.posLoading = false;
        }
    },

    async deletePosition(code, pid) {
        if (!confirm("确认删除该加仓记录？")) return;
        try {
            const resp = await fetch(`/api/funds/${code}/positions/${pid}`, { method: "DELETE" });
            if (resp.ok) {
                await this.refreshPositions(code);
            }
        } catch (e) {
            console.error("删除失败", e);
        }
    },

    valuationCls(val) {
        if (val == null || val === "") return "";
        const n = parseFloat(val);
        return n >= 0 ? "up" : "down";
    },

    fmtValPct(val) {
        if (val == null || val === "") return "--";
        const n = parseFloat(val);
        const prefix = n >= 0 ? "+" : "";
        return prefix + n.toFixed(2) + "%";
    },

    fmtPct(val) {
        if (val == null) return "--";
        const pct = (val * 100).toFixed(2);
        return (val >= 0 ? "+" : "") + pct + "%";
    },

    fmtNum(val) {
        if (val == null || val === 0) return "0.00";
        return val.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },

    fmtProfit(profit, pct) {
        if (profit == null) return "--";
        const prefix = profit >= 0 ? "+" : "";
        return `${prefix}¥${this.fmtNum(Math.abs(profit))} (${prefix}${(pct || 0).toFixed(2)}%)`;
    },

    fmtNavChange(val) {
        if (val == null) return "--";
        const prefix = val >= 0 ? "+" : "";
        return prefix + val.toFixed(2) + "%";
    },
});
