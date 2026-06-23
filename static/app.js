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

    async init() {
        await this.loadFunds();
    },

    async loadFunds() {
        this.loadingFunds = true;
        try {
            const resp = await fetch("/api/funds");
            if (resp.ok) {
                this.funds = await resp.json();
            }
        } catch (e) {
            console.error("加载基金列表失败", e);
        } finally {
            this.loadingFunds = false;
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
        try {
            const resp = await fetch(`/api/funds/${code}/positions`);
            if (resp.ok) {
                this.posData = await resp.json();
            }
        } catch (e) {
            console.error("加载加仓记录失败", e);
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
                await this.loadFunds();
                await this.openPositions(code);
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
                await this.loadFunds();
                await this.openPositions(code);
            }
        } catch (e) {
            console.error("删除失败", e);
        }
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
