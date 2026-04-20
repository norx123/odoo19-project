/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState } from "@odoo/owl";

class ApprovalDashboard extends Component {
    static template = "custom_approval.Dashboard";

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.state = useState({
            advanceSalaryCount: 0,
            loanRequestCount: 0,
            resignationCount: 0,
            travelRequestCount: 0,
        });

        onMounted(async () => {
            await this._loadCounts();
        });
    }

    async _loadCounts() {
        const [advCount, loanCount, resCount, trvCount] = await Promise.all([
            this.orm.searchCount("custom.advance.salary", [["state", "in", ["draft", "submitted"]]]),
            this.orm.searchCount("custom.loan.request", [["state", "in", ["draft", "submitted"]]]),
            this.orm.searchCount("custom.resignation", [["state", "in", ["draft", "confirmed"]]]),
            this.orm.searchCount("custom.travel.request", [["state", "in", ["draft", "submitted"]]]),
        ]);
        this.state.advanceSalaryCount = advCount;
        this.state.loanRequestCount = loanCount;
        this.state.resignationCount = resCount;
        this.state.travelRequestCount = trvCount;
    }

    openNewAdvanceSalary() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Advance Salary",
            res_model: "custom.advance.salary",
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
        });
    }

    openAdvanceSalaryList() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Advance Salary",
            res_model: "custom.advance.salary",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain: [["state", "in", ["draft", "submitted"]]],
        });
    }

    openNewLoanRequest() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Request for Loan",
            res_model: "custom.loan.request",
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
        });
    }

    openLoanRequestList() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Request for Loan",
            res_model: "custom.loan.request",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain: [["state", "in", ["draft", "submitted"]]],
        });
    }

    openNewResignation() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Employee Resignation",
            res_model: "custom.resignation",
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
        });
    }

    openResignationList() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Employee Resignation",
            res_model: "custom.resignation",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain: [["state", "in", ["draft", "confirmed"]]],
        });
    }

    openNewTravelRequest() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Travel Request",
            res_model: "custom.travel.request",
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
        });
    }

    openTravelRequestList() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Travel Request",
            res_model: "custom.travel.request",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain: [["state", "in", ["draft", "submitted"]]],
        });
    }
}

registry.category("actions").add("custom_approval.dashboard", ApprovalDashboard);
