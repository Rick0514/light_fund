window.fundApp = () => ({
    funds: [],
    allTags: [],
    activeTags: [],
    newFundCode: "",
    loading: false,
    loadingFunds: false,
    error: "",
    successMsg: "",
    showPosCode: null,
    posData: null,
    opType: "buy",
    posDate: new Date().toISOString().split("T")[0],
    posMode: "amount",
    posAmount: "",
    posShares: "",
    posNote: "",
    posLoading: false,
    refreshing: false,
    valTime: "",
    showTagInput: false,
    newTagName: "",
    showTagPicker: null,
    pickedTag: "",

    get filteredFunds() {
        if (this.activeTags.length === 0) return this.funds;
        return this.funds.filter((f) => {
            if (!f.tags || f.tags.length === 0) return false;
            return this.activeTags.every((t) => f.tags.includes(t));
        });
    },

    async init() {
        await this.loadTags();
        await this.loadFunds();
    },

    async loadTags() {
        try {
            const resp = await fetch("/api/tags");
            if (resp.ok) this.allTags = await resp.json();
        } catch (e) {
            console.error("加载标签失败", e);
        }
    },

    async loadFunds() {
        this.loadingFunds = true;
        try {
            const resp = await fetch("/api/funds");
            if (resp.ok) {
                const currentValuations = Object.fromEntries(
                    this.funds.filter((f) => f.valuation).map((f) => [f.fund_code, f.valuation])
                );
                const funds = await resp.json();
                this.funds = funds.map((f) => ({
                    ...f,
                    tags: f.tags || [],
                    valuation: f.valuation || currentValuations[f.fund_code] || null,
                }));
            }
        } catch (e) {
            console.error("加载基金列表失败", e);
        } finally {
            this.loadingFunds = false;
        }
    },

    toggleTag(tag) {
        if (this.activeTags.includes(tag)) {
            this.activeTags = this.activeTags.filter((t) => t !== tag);
        } else {
            this.activeTags.push(tag);
        }
    },

    // ── 标签管理 ──

    async addTag() {
        const name = this.newTagName.trim();
        if (!name) return;
        try {
            const resp = await fetch("/api/tags", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name }),
            });
            const data = await resp.json();
            if (resp.ok) {
                this.allTags.push(data.name);
                this.newTagName = "";
                this.showTagInput = false;
                this.newTagName = "";
            } else {
            }
        } catch (e) {
        }
    },


    async commitTag() {
        const name = this.newTagName.trim();
        if (name) {
            await this.addTag();
        } else {
            this.showTagInput = false;
            this.newTagName = "";
        }
    },

    async deleteTag(tag) {
        if (!confirm(`确认删除标签 "${tag}"？所有基金上的此标签也将移除。`)) return;
        try {
            const resp = await fetch(`/api/tags/${tag}`, { method: "DELETE" });
            if (resp.ok) {
                this.allTags = this.allTags.filter((t) => t !== tag);
                this.activeTags = this.activeTags.filter((t) => t !== tag);
                this.funds.forEach((f) => {
                    if (f.tags) f.tags = f.tags.filter((t) => t !== tag);
                });
            }
        } catch (e) {
            console.error("删除标签失败", e);
        }
    },

    // ── 基金标签 ──

    availableTagsFor(fund) {
        return this.allTags.filter((t) => !(fund.tags || []).includes(t));
    },

    async addTagToFund(code, tag) {
        if (!tag) return;
        try {
            const resp = await fetch(`/api/funds/${code}/tags`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: tag }),
            });
            if (resp.ok) {
                const fund = this.funds.find((f) => f.fund_code === code);
                if (fund) {
                    if (!fund.tags) fund.tags = [];
                    fund.tags.push(tag);
                }
            }
        } catch (e) {
            console.error("添加基金标签失败", e);
        }
    },

    async removeTagFromFund(code, tag) {
        try {
            const resp = await fetch(`/api/funds/${code}/tags/${tag}`, { method: "DELETE" });
            if (resp.ok) {
                const fund = this.funds.find((f) => f.fund_code === code);
                if (fund && fund.tags) {
                    fund.tags = fund.tags.filter((t) => t !== tag);
                }
            }
        } catch (e) {
            console.error("移除基金标签失败", e);
        }
    },

    // ── 估值 ──

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
                this.valTime = new Date().toLocaleTimeString("zh-CN");
            }
        } catch (e) {
            console.error("刷新估值失败", e);
        } finally {
            this.refreshing = false;
        }
    },

    // ── 基金 ──

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
                this.funds = this.funds.filter((f) => f.fund_code !== code);
            }
        } catch (e) {
            console.error("删除失败", e);
        }
    },

    // ── 操作记录 ──

    async openPositions(code) {
        this.showPosCode = code;
        this.posData = null;
        this.opType = "buy";
        this.posMode = "amount";
        this.posAmount = "";
        this.posShares = "";
        this.posNote = "";
        await this._refreshPositions(code);
    },

    _updateFundFromPositionData(data) {
        const fund = this.funds.find((f) => f.fund_code === data.fund_code);
        if (!fund) return;
        fund.positions = data.positions || [];
        fund.tags = data.tags || [];
        fund.nav = data.nav;
        fund.nav_date = data.nav_date;
        fund.total_invested = data.total_invested || 0;
        fund.total_shares = data.total_shares || 0;
        fund.current_value = data.current_value || 0;
        fund.profit = data.profit || 0;
        fund.profit_pct = fund.total_invested > 0 ? (fund.profit / fund.total_invested) * 100 : 0;
        const pos = fund.positions;
        if (pos.length && data.nav) {
            const last = [...pos].sort((a, b) => a.date.localeCompare(b.date)).at(-1);
            fund.last_nav = last?.nav || null;
            fund.nav_change_since_last = fund.last_nav ? ((data.nav - fund.last_nav) / fund.last_nav) * 100 : null;
        } else {
            fund.last_nav = null;
            fund.nav_change_since_last = null;
        }
    },

    async _refreshPositions(code) {
        try {
            const resp = await fetch(`/api/funds/${code}/positions`);
            if (resp.ok) {
                const data = await resp.json();
                this.posData = data;
                this._updateFundFromPositionData(data);
            }
        } catch (e) {
            console.error("加载操作记录失败", e);
        }
    },

    async addPosition(code) {
        const mode = this.posMode;
        const amountInput = parseFloat(this.posAmount) || 0;
        const sharesInput = parseFloat(this.posShares) || 0;
        if (!this.posDate) return;
        if (mode === "amount" && amountInput <= 0) return;
        if (mode === "shares" && sharesInput <= 0) return;
        this.posLoading = true;
        this.error = "";
        try {
            const resp = await fetch(`/api/funds/${code}/positions`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    date: this.posDate,
                    amount: mode === "amount" ? amountInput : 0,
                    shares: mode === "shares" ? sharesInput : 0,
                    type: this.opType,
                    note: this.posNote,
                }),
            });
            if (resp.ok) {
                this.posAmount = "";
                this.posShares = "";
                this.posNote = "";
                this.posMode = "amount";
                this.opType = "buy";
                await this._refreshPositions(code);
            } else {
                const err = await resp.json();
                this.error = err.error || "操作失败";
            }
        } catch (e) {
            this.error = "网络错误";
        } finally {
            this.posLoading = false;
        }
    },

    async deletePosition(code, pid) {
        if (!confirm("确认删除该操作记录？")) return;
        try {
            const resp = await fetch(`/api/funds/${code}/positions/${pid}`, { method: "DELETE" });
            if (resp.ok) await this._refreshPositions(code);
        } catch (e) {
            console.error("删除失败", e);
        }
    },

    // ── 格式化 ──

    valuationCls(val) {
        if (val == null || val === "") return "";
        return parseFloat(val) >= 0 ? "up" : "down";
    },
    fmtValPct(val) {
        if (val == null || val === "") return "--";
        const n = parseFloat(val);
        return (n >= 0 ? "+" : "") + n.toFixed(2) + "%";
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
