/** @odoo-module **/
/**
 * attendance_device_info.js
 * "📱 Device Information" tab for the Attendance form.
 * Uses same integer-field binding as attendance_path_map.js (proven working).
 */

import { registry } from "@web/core/registry";
import { Component, onMounted, useRef } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

const { xml } = owl;

// ── CSS ────────────────────────────────────────────────────────────────────────

(function injectCSS() {
    if (document.getElementById("_gdi_css")) return;
    const s = document.createElement("style");
    s.id = "_gdi_css";
    s.textContent = `
        ._gdi_root {
            width: 100%;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        ._gdi_grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }
        @media (max-width: 860px) { ._gdi_grid { grid-template-columns: 1fr; } }

        ._gdi_card {
            border-radius: 14px;
            overflow: hidden;
            border: 1.5px solid #e4e9f0;
            background: #fff;
            box-shadow: 0 3px 14px rgba(0,0,0,.07);
        }
        ._gdi_hdr {
            display: flex; align-items: center; gap: 10px; padding: 13px 18px;
        }
        ._gdi_hdr.ci { background: linear-gradient(120deg,#e8f5e9,#f1f8e9); }
        ._gdi_hdr.co { background: linear-gradient(120deg,#ffebee,#fce4ec); }
        ._gdi_hdr_dot { width:12px;height:12px;border-radius:50%;flex-shrink:0; }
        ._gdi_hdr.ci ._gdi_hdr_dot { background:#2e7d32; }
        ._gdi_hdr.co ._gdi_hdr_dot { background:#c62828; }
        ._gdi_hdr_title { font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.5px; }
        ._gdi_hdr.ci ._gdi_hdr_title { color:#2e7d32; }
        ._gdi_hdr.co ._gdi_hdr_title { color:#c62828; }
        ._gdi_hdr_time { margin-left:auto;font-size:11px;color:#888;font-weight:500; }

        ._gdi_section { padding:8px 18px 4px; border-bottom:1px solid #f2f4f8; }
        ._gdi_section:last-child { border-bottom:none; padding-bottom:12px; }
        ._gdi_sec_title { font-size:10px;font-weight:800;text-transform:uppercase;
                          letter-spacing:.5px;color:#aab;margin-bottom:6px; }

        ._gdi_row { display:flex;align-items:flex-start;gap:8px;padding:4px 0;
                    border-bottom:1px solid #f7f8fb;font-size:12.5px;line-height:1.5; }
        ._gdi_row:last-child { border-bottom:none; }
        ._gdi_ic  { font-size:14px;flex-shrink:0;width:20px;text-align:center;margin-top:1px; }
        ._gdi_lbl { color:#999;font-size:11.5px;min-width:130px;flex-shrink:0; }
        ._gdi_val { color:#1a1a1a;font-weight:600;word-break:break-word; }
        ._gdi_val .dim { color:#aaa;font-weight:400;font-size:11px; }

        ._gdi_bat { display:flex;align-items:center;gap:8px; }
        ._gdi_bat_track { width:80px;height:10px;background:#eee;border-radius:5px;
                          overflow:hidden;flex-shrink:0;border:1px solid #ddd; }
        ._gdi_bat_fill  { height:100%;border-radius:5px;transition:width .4s; }
        ._gdi_bat_pct   { font-weight:700;font-size:12.5px; }
        ._gdi_bat_chg   { font-size:12px; }

        ._gdi_empty { padding:28px 18px;text-align:center;color:#b0b8c8;font-size:12.5px; }
        ._gdi_nodata { padding:22px 18px;text-align:center;color:#c0c8d4;font-size:12px; }
        ._gdi_ua { font-size:10.5px;color:#999;word-break:break-all;padding:2px 0 4px; }
    `;
    document.head.appendChild(s);
})();

// ── HTML builders ──────────────────────────────────────────────────────────────

function batColor(lv) {
    return lv >= 60 ? "#4caf50" : lv >= 25 ? "#ff9800" : "#f44336";
}

function row(ic, lbl, val, dim) {
    return `<div class="_gdi_row">
        <span class="_gdi_ic">${ic}</span>
        <span class="_gdi_lbl">${lbl}</span>
        <span class="_gdi_val">${val}${dim ? ` <span class="dim">${dim}</span>` : ""}</span>
    </div>`;
}

function buildCard(log, cls, title) {
    if (!log) {
        return `<div class="_gdi_card">
            <div class="_gdi_hdr ${cls}">
                <div class="_gdi_hdr_dot"></div>
                <span class="_gdi_hdr_title">${title}</span>
            </div>
            <div class="_gdi_nodata">📵 No device data recorded for this event.</div>
        </div>`;
    }

    const batLv  = log.battery_level || 0;
    const batHtml = batLv > 0
        ? `<div class="_gdi_bat">
            <div class="_gdi_bat_track">
                <div class="_gdi_bat_fill" style="width:${Math.min(100,batLv)}%;background:${batColor(batLv)};"></div>
            </div>
            <span class="_gdi_bat_pct" style="color:${batColor(batLv)};">${batLv}%</span>
            <span class="_gdi_bat_chg" style="color:${log.battery_charging ? '#4caf50' : '#999'};">
                ${log.battery_charging ? "⚡ Charging" : "Not Charging"}
            </span>
           </div>`
        : `<span style="color:#bbb;">Not available</span>`;

    const osStr  = [log.os_name, log.os_version].filter(Boolean).join(" ");
    const brwStr = [log.browser, log.browser_ver].filter(Boolean).join(" ");

    return `<div class="_gdi_card">
        <div class="_gdi_hdr ${cls}">
            <div class="_gdi_hdr_dot"></div>
            <span class="_gdi_hdr_title">${title}</span>
            <span class="_gdi_hdr_time">${log.logged_at || ""}</span>
        </div>

        <div class="_gdi_section">
            <div class="_gdi_sec_title">📱 Device</div>
            ${row("💻", "Device Name",       log.device_name  || "—")}
            ${log.device_model ? row("🏷️",  "Model",          log.device_model, log.device_type ? `(${log.device_type})` : "") : ""}
            ${log.device_type  ? row("📲",  "Device Type",    log.device_type) : ""}
            ${osStr            ? row("⚙️",  "Operating System", osStr) : ""}
        </div>

        <div class="_gdi_section">
            <div class="_gdi_sec_title">🌐 Browser & Network</div>
            ${brwStr           ? row("🖥️",  "Browser",        brwStr) : ""}
            ${row("🌐",         "IP Address",    log.ip_address || "—")}
            ${log.wifi_ssid    ? row("📶",  "WiFi SSID",      log.wifi_ssid) : ""}
            ${log.carrier      ? row("📡",  "Network",        log.carrier) : ""}
        </div>

        <div class="_gdi_section">
            <div class="_gdi_sec_title">🔋 Battery</div>
            <div class="_gdi_row">
                <span class="_gdi_ic">🔋</span>
                <span class="_gdi_lbl">Battery Level</span>
                <span class="_gdi_val">${batHtml}</span>
            </div>
        </div>

        ${log.user_agent ? `<div class="_gdi_section">
            <div class="_gdi_sec_title">🔍 User Agent</div>
            <div class="_gdi_ua">${log.user_agent}</div>
        </div>` : ""}
    </div>`;
}

// ── Async renderer ─────────────────────────────────────────────────────────────

async function renderDeviceInfo(container, attendanceId) {
    container.innerHTML = `<div class="_gdi_empty" style="padding:16px 0;">Loading device information…</div>`;

    let logs = [];
    try {
        const data = await rpc("/attendance/geofence/device_info", { attendance_id: attendanceId });
        logs = (data && data.logs) || [];
    } catch (e) {
        container.innerHTML = `<div class="_gdi_empty">⚠️ Could not load device info. Please refresh the page.</div>`;
        return;
    }

    const ci = logs.find(l => l.event_type === "checkin")  || null;
    const co = logs.find(l => l.event_type === "checkout") || null;

    if (!ci && !co) {
        container.innerHTML = `<div class="_gdi_empty">
            <div style="font-size:36px;margin-bottom:10px;">📱</div>
            <div style="font-weight:700;color:#5a6475;font-size:14px;">No device information recorded yet.</div>
            <div style="font-size:12px;color:#b0b8c8;margin-top:6px;">
                Device details will be captured automatically on the next check-in.
            </div>
        </div>`;
        return;
    }

    const grid = document.createElement("div");
    grid.className = "_gdi_grid";
    grid.innerHTML =
        buildCard(ci, "ci", "✅ Check-In Device") +
        buildCard(co, "co", "🏁 Check-Out Device");
    container.innerHTML = "";
    container.appendChild(grid);
}

// ── OWL Component ──────────────────────────────────────────────────────────────

class AttendanceDeviceInfo extends Component {
    static props = {
        id:       { type: Number, optional: true },
        name:     { type: String, optional: true },
        record:   { type: Object },
        readonly: { type: Boolean, optional: true },
    };

    setup() {
        this.containerRef = useRef("diContainer");

        onMounted(async () => {
            // Match path map timing — let form fully render first
            await new Promise(r => setTimeout(r, 400));
            const el = this.containerRef.el;
            if (!el) return;

            const aid = this.props.record && this.props.record.data && this.props.record.data.id;
            if (!aid) {
                el.innerHTML = `<div class="_gdi_empty">No attendance record selected.</div>`;
                return;
            }

            console.log("[DeviceInfo] Loading for attendance ID:", aid);
            await renderDeviceInfo(el, aid);
        });
    }
}

AttendanceDeviceInfo.template = xml`
    <div class="_gdi_root">
        <div t-ref="diContainer">
            <div class="_gdi_empty" style="padding:16px 0;">Loading device information…</div>
        </div>
    </div>
`;

registry.category("fields").add("attendance_device_info", {
    component:      AttendanceDeviceInfo,
    supportedTypes: ["integer"],
});
