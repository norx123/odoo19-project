/** @odoo-module **/

/**
 * attendance_path_map.js
 *
 * Renders an interactive map inside the Attendance form view showing the
 * employee's complete GPS movement path from check-in to check-out.
 *
 * Uses Leaflet.js (loaded from CDN) and OpenStreetMap tiles (free, no API key required).
 */

import { registry } from "@web/core/registry";
import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

// ── Leaflet Loader ────────────────────────────────────────────────────────────

let _leafletPromise = null;

function loadLeaflet() {
    if (_leafletPromise) return _leafletPromise;
    _leafletPromise = new Promise((resolve, reject) => {
        if (window.L) { resolve(window.L); return; }

        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
        document.head.appendChild(link);

        const script = document.createElement("script");
        script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
        script.onload = () => resolve(window.L);
        script.onerror = reject;
        document.head.appendChild(script);
    });
    return _leafletPromise;
}

// ── Component ─────────────────────────────────────────────────────────────────

class AttendancePathMap extends Component {
    static props = {
        record: Object,
        readonly: { type: Boolean, optional: true },
    };

    setup() {
        this.mapRef = useRef("mapContainer");
        this._map = null;

        onMounted(async () => {
            await this._renderMap();
        });

        onWillUnmount(() => {
            if (this._map) {
                this._map.remove();
                this._map = null;
            }
        });
    }

    async _renderMap() {
        const attendanceId = this.props.record.data.id;
        if (!attendanceId) return;

        let pathData;
        try {
            pathData = await rpc("/attendance/geofence/path", { attendance_id: attendanceId });
        } catch (e) {
            console.error("[PathMap] Failed to load path data:", e);
            return;
        }

        const points = pathData.points || [];
        if (points.length === 0) {
            this._showNoDataMessage();
            return;
        }

        const L = await loadLeaflet();
        const container = this.mapRef.el;
        if (!container) return;

        container.style.height = "380px";
        container.style.borderRadius = "8px";
        container.style.overflow = "hidden";

        if (this._map) { this._map.remove(); this._map = null; }

        const map = L.map(container);
        this._map = map;

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap contributors",
            maxZoom: 19,
        }).addTo(map);

        const latlngs = points.map(p => [p.lat, p.lng]);

        // Draw the movement path as a polyline
        L.polyline(latlngs, {
            color: "#714B67",
            weight: 4,
            opacity: 0.85,
        }).addTo(map);

        // Draw a marker for each recorded point
        points.forEach((p) => {
            let color, label;

            if (p.type === "checkin") {
                color = "#2e7d32";
                label = "Check-In — " + p.time;
            } else if (p.type === "checkout") {
                color = "#c62828";
                label = "Check-Out — " + p.time;
            } else {
                color = "#714B67";
                label = "Movement — " + p.time;
            }

            const size = p.type === "track" ? 10 : 16;
            const icon = L.divIcon({
                className: "",
                html: `<div style="
                    width:${size}px; height:${size}px;
                    border-radius:50%;
                    background:${color};
                    border:2px solid #fff;
                    box-shadow:0 1px 4px rgba(0,0,0,0.4);
                "></div>`,
                iconSize: [size, size],
                iconAnchor: [size / 2, size / 2],
            });

            const popup = `<b>${label}</b>` +
                (p.accuracy ? `<br>Accuracy: ${Math.round(p.accuracy)} m` : "");

            L.marker([p.lat, p.lng], { icon }).addTo(map).bindPopup(popup);
        });

        // Legend
        const legend = L.control({ position: "bottomright" });
        legend.onAdd = () => {
            const div = L.DomUtil.create("div");
            div.style.cssText =
                "background:#fff; padding:8px 12px; border-radius:8px;" +
                "font-size:11px; box-shadow:0 2px 8px rgba(0,0,0,0.2); line-height:1.9;";
            div.innerHTML =
                `<div><span style="color:#2e7d32;font-weight:700;">●</span> Check-In</div>` +
                `<div><span style="color:#714B67;font-weight:700;">●</span> Movement ` +
                    `(${points.filter(p => p.type === "track").length} points)</div>` +
                `<div><span style="color:#c62828;font-weight:700;">●</span> Check-Out</div>` +
                `<div style="margin-top:5px;color:#555;border-top:1px solid #eee;padding-top:5px;">` +
                    `<b>${pathData.employee_name || ""}</b><br>` +
                    `In: ${pathData.check_in || "—"}<br>` +
                    `Out: ${pathData.check_out || "—"}` +
                `</div>`;
            return div;
        };
        legend.addTo(map);

        if (latlngs.length > 0) {
            map.fitBounds(L.latLngBounds(latlngs), { padding: [30, 30] });
        }
    }

    _showNoDataMessage() {
        const container = this.mapRef.el;
        if (!container) return;
        container.style.cssText =
            "height:120px; border-radius:8px; background:#f7f0f5;" +
            "display:flex; align-items:center; justify-content:center;" +
            "color:#b090a8; font-size:13px; border:1.5px dashed #d6c2d0;";
        container.innerHTML =
            `<div style="text-align:center;">` +
            `📍<br>` +
            `<span style="font-size:12px;">No GPS path data available for this attendance record.</span><br>` +
            `<span style="font-size:11px;color:#c0a0b8;">Path tracking is recorded for new check-ins going forward.</span>` +
            `</div>`;
    }
}

// ── OWL Template ─────────────────────────────────────────────────────────────

const { xml } = owl;

AttendancePathMap.template = xml`
    <div class="o_field_widget o_attendance_path_map" style="padding:8px 0;">
        <div t-ref="mapContainer" style="
            height: 580px;
            width: 700px;
            border-radius: 8px;
            background: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
            font-size: 13px;
        ">
            Loading map...
        </div>
    </div>
`;

registry.category("fields").add("attendance_path_map", {
    component: AttendancePathMap,
    supportedTypes: ["integer"],
});
