/** @odoo-module **/
/**
 * attendance_path_map.js — v7 (Final)
 * Google Maps tiles · Thick blue path · Green IN pin · Red OUT pin · White waypoints
 */

import { registry } from "@web/core/registry";
import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
const { xml } = owl;

// ── Leaflet loader ─────────────────────────────────────────────────────────────
let _lP = null;
function loadLeaflet() {
    if (_lP) return _lP;
    _lP = new Promise((res, rej) => {
        if (window.L) { res(window.L); return; }
        const lnk = document.createElement("link");
        lnk.rel = "stylesheet";
        lnk.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
        document.head.appendChild(lnk);
        const sc = document.createElement("script");
        sc.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
        sc.onload = () => res(window.L);
        sc.onerror = rej;
        document.head.appendChild(sc);
    });
    return _lP;
}

// ── CSS ────────────────────────────────────────────────────────────────────────
(function() {
    if (document.getElementById("_gpm_css")) return;
    const s = document.createElement("style");
    s.id = "_gpm_css";
    s.textContent = `
        ._gpm_shell { width:100%;border-radius:12px;overflow:hidden;border:1.5px solid #dde3ec;
            box-shadow:0 4px 20px rgba(0,0,0,.09);background:#fff;
            font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
        ._gpm_tb { display:flex;align-items:center;gap:6px;padding:7px 12px;
            background:#f5f7fa;border-bottom:1px solid #e4e9f0; }
        ._gpm_tb button { padding:3px 13px;border-radius:16px;border:1.5px solid #c8d0db;
            background:#fff;font-size:11px;font-weight:600;color:#555;cursor:pointer; }
        ._gpm_tb button.on { background:#1a73e8;border-color:#1a73e8;color:#fff; }
        ._gpm_tb span { margin-left:auto;font-size:10.5px;color:#aaa; }
        ._gpm_map { width:100%;height:480px;display:block; }
        ._gpm_map .leaflet-container { width:100%!important;height:100%!important; }
        ._gpm_bar { display:flex;flex-wrap:wrap;border-top:1.5px solid #edf0f5; }
        ._gpm_bc  { flex:1;min-width:130px;display:flex;align-items:center;gap:9px;
            padding:11px 15px;border-right:1px solid #edf0f5; }
        ._gpm_bc:last-child { border-right:none; }
        ._gpm_bi  { width:32px;height:32px;border-radius:50%;display:flex;
            align-items:center;justify-content:center;font-size:14px;flex-shrink:0; }
        ._gpm_bi.e{background:#f3e5f5;} ._gpm_bi.i{background:#e8f5e9;}
        ._gpm_bi.o{background:#ffebee;} ._gpm_bi.p{background:#e3f2fd;}
        ._gpm_bt { display:flex;flex-direction:column; }
        ._gpm_bl { font-size:10px;color:#999;font-weight:700;text-transform:uppercase;letter-spacing:.4px; }
        ._gpm_bv { font-size:12.5px;color:#111;font-weight:700; }
        ._gpm_bs { font-size:10.5px;color:#888; }
        ._gpm_emp { min-height:160px;display:flex;flex-direction:column;align-items:center;
            justify-content:center;gap:6px;background:#f8f9fb;border-radius:12px;
            border:1.5px dashed #cdd3dc;color:#9aa5b4;font-size:13px; }
        .leaflet-popup-content-wrapper{border-radius:10px!important;box-shadow:0 6px 24px rgba(0,0,0,.13)!important;padding:0!important;}
        .leaflet-popup-content{margin:0!important;}
        ._gpp{min-width:220px;padding:12px 14px;font-family:-apple-system,sans-serif;}
        ._gpp_hdr{font-size:13px;font-weight:800;padding-bottom:7px;margin-bottom:7px;border-bottom:1.5px solid #eee;}
        ._gpp_row{display:flex;align-items:flex-start;gap:7px;font-size:12px;margin-bottom:4px;line-height:1.5;}
        ._gpp_ic{flex-shrink:0;width:16px;text-align:center;}
        ._gpp_v{color:#333;} ._gpp_v b{color:#111;} ._gpp_v .c{font-size:11px;font-family:monospace;color:#555;}
        ._gpp_v a{color:#1a73e8;font-size:11px;text-decoration:none;font-weight:600;}
        ._gpp_div{margin-top:6px;padding-top:6px;border-top:1px solid #f0f0f0;}
    `;
    document.head.appendChild(s);
})();

// ── Google tile ────────────────────────────────────────────────────────────────
function gTile(L, t) {
    const ly = t==="sat"?"s":t==="hyb"?"y":"m";
    return L.tileLayer(`https://{s}.google.com/vt/lyrs=${ly}&x={x}&y={y}&z={z}`,
        {maxZoom:20,subdomains:["mt0","mt1","mt2","mt3"],attribution:"© Google Maps"});
}

// ── Pin icon (tall teardrop) ───────────────────────────────────────────────────
function pin(L, color, label) {
    const uid = "p"+Math.random().toString(36).slice(2,6);
    const fs = label.length > 2 ? 9 : 12;
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="44" height="60" viewBox="0 0 44 60">
        <defs><filter id="${uid}"><feDropShadow dx="0" dy="3" stdDeviation="3" flood-opacity=".4"/></filter></defs>
        <path d="M22 2 C11 2 2 11 2 22 C2 37 22 58 22 58 C22 58 42 37 42 22 C42 11 33 2 22 2 Z"
              fill="${color}" stroke="white" stroke-width="2.5" filter="url(#${uid})"/>
        <circle cx="22" cy="22" r="9" fill="rgba(255,255,255,0.25)"/>
        <text x="22" y="${fs<=9?27:27}" text-anchor="middle" font-size="${fs}"
              font-weight="800" fill="white" font-family="Arial,sans-serif">${label}</text>
    </svg>`;
    return L.divIcon({className:"",html:svg,iconSize:[44,60],iconAnchor:[22,60],popupAnchor:[0,-62]});
}

// ── Popup builder ──────────────────────────────────────────────────────────────
function popup(type, time, lat, lng, loc, acc) {
    const C = {
        checkin:  ["#2e7d32","✅","Check-In"],
        checkout: ["#c62828","🔴","Check-Out"],
        track:    ["#1a73e8","📍","Movement Point"],
    };
    const [col,ico,ttl] = C[type]||C.track;
    const gUrl = `https://www.google.com/maps?q=${lat},${lng}`;
    const locTxt = loc ? (loc.length>65?loc.slice(0,65)+"…":loc) : null;
    const row = (ic,html) => `<div class="_gpp_row"><span class="_gpp_ic">${ic}</span><span class="_gpp_v">${html}</span></div>`;
    return `<div class="_gpp">
        <div class="_gpp_hdr" style="color:${col};">${ico} ${ttl}</div>
        ${row("🕐",`<b>${time||"—"}</b>`)}
        ${locTxt?row("📍",locTxt):""}
        ${row("📡",`<span class="c">${parseFloat(lat).toFixed(7)}, ${parseFloat(lng).toFixed(7)}</span>`)}
        ${acc?row("🎯",`GPS ±${Math.round(acc)} m`):""}
        <div class="_gpp_div">${row("🗺️",`<a href="${gUrl}" target="_blank">Open in Google Maps →</a>`)}</div>
    </div>`;
}

// ── Component ──────────────────────────────────────────────────────────────────
class AttendancePathMap extends Component {
    static props = {
        id:       { type: Number, optional: true },
        name:     { type: String, optional: true },
        record:   { type: Object },
        readonly: { type: Boolean, optional: true },
    };

    setup() {
        this.root = useRef("root");
        this._map = null; this._tile = null;
        onMounted(() => this._init());
        onWillUnmount(() => { if(this._map){try{this._map.remove();}catch(_){}this._map=null;} });
    }

    async _init() {
        // Small delay to let Odoo form fully render
        await new Promise(r => setTimeout(r, 400));
        const el = this.root.el;
        if (el) await this._build(el);
    }

    async _build(el) {
        const aid = this.props.record && this.props.record.data && this.props.record.data.id;
        if (!aid) { this._empty(el,"📋","No record selected."); return; }

        let d;
        try { d = await rpc("/attendance/geofence/path", {attendance_id: aid}); }
        catch(e) { this._empty(el,"⚠️","Could not load path data. Please refresh."); return; }

        const pts = (d && d.points) || [];
        if (!pts.length) {
            this._empty(el,"🗺️","No GPS path recorded for this attendance.",
                "Path tracking starts automatically on next check-in.");
            return;
        }

        // ── Build DOM ───────────────────────────────────────────────────────
        el.innerHTML = ""; el.className = "_gpm_shell";

        const tb = document.createElement("div"); tb.className = "_gpm_tb";
        tb.innerHTML = `<button class="on" data-t="road">🗺️ Road</button>
            <button data-t="sat">🛰️ Satellite</button>
            <button data-t="hyb">🌍 Hybrid</button>
            <span>© Google Maps · Click any marker for details</span>`;
        el.appendChild(tb);

        const md = document.createElement("div");
        md.className = "_gpm_map";
        md.style.cssText = "width:100%;height:480px;display:block;";
        el.appendChild(md);

        el.appendChild(this._bar(d, pts));

        // ── Leaflet init ────────────────────────────────────────────────────
        const L = await loadLeaflet();
        if (this._map) { try{this._map.remove();}catch(_){} }

        const map = L.map(md, {zoomControl:true, preferCanvas:false});
        this._map = map;
        this._tile = gTile(L, "road");
        this._tile.addTo(map);

        const ll = pts.map(p => [p.lat, p.lng]);
        const ci = pts.find(p => p.type === "checkin");
        const co = pts.find(p => p.type === "checkout");
        const trackPts = pts.filter(p => p.type === "track");

        // ── Set view & invalidate FIRST ─────────────────────────────────────
        if (ll.length > 1) map.fitBounds(L.latLngBounds(ll), {padding:[60,60]});
        else map.setView(ll[0], 17);

        map.invalidateSize();
        await new Promise(r => setTimeout(r, 350));
        map.invalidateSize();

        // ── Draw thick Google Maps style polyline ───────────────────────────
        if (ll.length > 1) {
            L.polyline(ll, {color:"#fff",    weight:13, opacity:0.8,  lineJoin:"round",lineCap:"round"}).addTo(map);
            L.polyline(ll, {color:"#1a73e8", weight:7,  opacity:1.0,  lineJoin:"round",lineCap:"round"}).addTo(map);
            L.polyline(ll, {color:"#74b3ff", weight:3,  opacity:0.55, lineJoin:"round",lineCap:"round"}).addTo(map);
        }

        // ── Waypoint dots (white + blue border like Google Maps) ────────────
        trackPts.forEach(p => {
            const ico = L.divIcon({
                className:"",
                html:`<div style="width:16px;height:16px;border-radius:50%;background:#fff;
                    border:3.5px solid #1a73e8;box-shadow:0 2px 8px rgba(26,115,232,.5);"></div>`,
                iconSize:[16,16], iconAnchor:[8,8], popupAnchor:[0,-12],
            });
            L.marker([p.lat,p.lng], {icon:ico, zIndexOffset:500})
                .addTo(map)
                .bindPopup(popup("track",p.time,p.lat,p.lng,p.location_name,p.accuracy),{maxWidth:280});
        });

        // ── Check-In pin (Green) ────────────────────────────────────────────
        if (ci) {
            const m = L.marker([ci.lat,ci.lng], {icon:pin(L,"#2e7d32","IN"), zIndexOffset:2000})
                .addTo(map)
                .bindPopup(popup("checkin",ci.time,ci.lat,ci.lng,ci.location_name,ci.accuracy),{maxWidth:300});
            setTimeout(() => { try{m.openPopup();}catch(_){} }, 600);
        }

        // ── Check-Out pin (Red) ─────────────────────────────────────────────
        if (co) {
            L.marker([co.lat,co.lng], {icon:pin(L,"#c62828","OUT"), zIndexOffset:2000})
                .addTo(map)
                .bindPopup(popup("checkout",co.time,co.lat,co.lng,co.location_name,co.accuracy),{maxWidth:300});
        }

        // Final size fix after everything renders
        setTimeout(() => map.invalidateSize(), 800);

        // ── Tile switcher ───────────────────────────────────────────────────
        tb.querySelectorAll("button").forEach(b => b.addEventListener("click", () => {
            tb.querySelectorAll("button").forEach(x => x.classList.remove("on"));
            b.classList.add("on");
            if (this._tile) map.removeLayer(this._tile);
            this._tile = gTile(L, b.dataset.t);
            this._tile.addTo(map);
            this._tile.bringToBack();
        }));
    }

    _bar(d, pts) {
        const ci = pts.find(p=>p.type==="checkin");
        const co = pts.find(p=>p.type==="checkout");
        const cnt = pts.filter(p=>p.type==="track").length;
        const bar = document.createElement("div"); bar.className="_gpm_bar";
        const cell = (cls,ico,lbl,val,sub) => `<div class="_gpm_bc">
            <div class="_gpm_bi ${cls}">${ico}</div>
            <div class="_gpm_bt">
                <span class="_gpm_bl">${lbl}</span>
                <span class="_gpm_bv">${val}</span>
                ${sub?`<span class="_gpm_bs">${sub}</span>`:""}
            </div></div>`;
        bar.innerHTML =
            cell("e","👤","Employee",   d.employee_name||"—","") +
            cell("i","✅","Check-In",   ci?ci.time:(d.check_in||"—"), ci&&ci.location_name?ci.location_name.split(",")[0]:"") +
            cell("o","🏁","Check-Out",  co?co.time:(d.check_out||"—"), co&&co.location_name?co.location_name.split(",")[0]:"") +
            cell("p","📍","Path Points",`${cnt} waypoint${cnt!==1?"s":""}`, "Recorded every 2 min");
        return bar;
    }

    _empty(el, ico, l1, l2) {
        el.innerHTML=""; el.className="_gpm_emp";
        el.innerHTML=`<div style="font-size:34px;">${ico}</div>
            <div style="font-weight:700;color:#5a6475;">${l1}</div>
            ${l2?`<div style="font-size:11.5px;color:#9aa5b4;">${l2}</div>`:""}`;
    }
}

AttendancePathMap.template = xml`
    <div t-ref="root" class="_gpm_emp">
        <div style="font-size:30px;">🗺️</div>
        <div>Loading movement path…</div>
    </div>`;

registry.category("fields").add("attendance_path_map", {
    component: AttendancePathMap,
    supportedTypes: ["integer"],
});
