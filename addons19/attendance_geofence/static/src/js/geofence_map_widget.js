/** @odoo-module **/

import { registry } from "@web/core/registry";
import { loadJS, loadCSS } from "@web/core/assets";
import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

// ─────────────────────────────────────────────────────────────────────────────
// GeofenceMapWidget — Professional Geofence Map with persistent location
// ─────────────────────────────────────────────────────────────────────────────

class GeofenceMapWidget extends Component {
    static template = "geofence.MapWidget";
    static props = { ...standardFieldProps };

    setup() {
        this.mapRef = useRef("mapContainer");
        this.map = null;
        this.marker = null;
        this.circle = null;
        this.searchTimeout = null;
        this.abortController = null;

        this.state = useState({
            query: "",
            suggestions: [],
            showDropdown: false,
            lat: null,
            lng: null,
            radius: 100,
            locationName: "",
            loading: false,
            mapReady: false,
            activeSuggIndex: -1,
        });

        onMounted(async () => {
            await loadCSS("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css");
            await loadJS("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js");

            // Always read fresh from record so that navigating back shows the latest saved values
            this._loadFromRecord();
            this.initMap();
        });

        onWillUnmount(() => {
            if (this.map) {
                this.map.remove();
                this.map = null;
            }
            if (this.abortController) {
                this.abortController.abort();
            }
        });
    }

    // Load the latest saved values from the record into component state
    _loadFromRecord() {
        const record = this.props.record;
        const lat = record.data.geofence_latitude || null;
        const lng = record.data.geofence_longitude || null;
        const radius = record.data.geofence_radius || 100;
        const savedName = record.data.geofence_location_name || "";

        this.state.lat = lat ? parseFloat(lat) : null;
        this.state.lng = lng ? parseFloat(lng) : null;
        this.state.radius = radius ? parseFloat(radius) : 100;
        this.state.locationName = savedName;
        this.state.query = savedName;
    }

    initMap() {
        const container = this.mapRef.el;
        if (!container || !window.L) return;

        const defaultLat = this.state.lat || 28.6139;
        const defaultLng = this.state.lng || 77.2090;
        const zoom = this.state.lat ? 16 : 5;

        this.map = L.map(container, {
            zoomControl: true,
            scrollWheelZoom: true,
        }).setView([defaultLat, defaultLng], zoom);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 19,
        }).addTo(this.map);

        if (this.state.lat && this.state.lng) {
            this._placeMarkerAndCircle(this.state.lat, this.state.lng);
        }

        // Click on map to set location
        this.map.on("click", (e) => {
            this._reverseGeocode(e.latlng.lat, e.latlng.lng);
        });

        this.state.mapReady = true;
    }

    _placeMarkerAndCircle(lat, lng) {
        if (!this.map || !window.L) return;

        if (this.marker) this.map.removeLayer(this.marker);
        if (this.circle) this.map.removeLayer(this.circle);

        // Professional pin marker
        const pinIcon = L.divIcon({
            className: "",
            html: `<div style="
                position:relative;
                width:28px;height:28px;
                display:flex;align-items:center;justify-content:center;
            ">
                <div style="
                    width:16px;height:16px;
                    background:linear-gradient(135deg,#e74c3c,#c0392b);
                    border:2.5px solid #fff;
                    border-radius:50%;
                    box-shadow:0 2px 8px rgba(231,76,60,0.6),0 0 0 4px rgba(231,76,60,0.15);
                "></div>
                <div style="
                    position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);
                    width:2px;height:6px;background:#c0392b;border-radius:1px;
                "></div>
            </div>`,
            iconSize: [28, 34],
            iconAnchor: [14, 34],
        });

        this.marker = L.marker([lat, lng], { icon: pinIcon, draggable: true }).addTo(this.map);

        this.marker.on("dragend", (e) => {
            const pos = e.target.getLatLng();
            this._reverseGeocode(pos.lat, pos.lng);
        });

        // Smooth animated circle
        this.circle = L.circle([lat, lng], {
            radius: this.state.radius,
            color: "#e74c3c",
            fillColor: "#e74c3c",
            fillOpacity: 0.10,
            weight: 2.5,
            dashArray: "6,4",
        }).addTo(this.map);

        this.map.setView([lat, lng], 16, { animate: true });
    }

    // Reverse geocode using Photon (map click ya marker drag)
    async _reverseGeocode(lat, lng) {
        this._placeMarkerAndCircle(lat, lng);
        this.state.lat = lat;
        this.state.lng = lng;

        try {
            // Photon reverse geocode
            const res = await fetch(
                `https://photon.komoot.io/reverse?lat=${lat}&lon=${lng}&limit=1&lang=en`
            );
            const data = await res.json();
            const feature = data.features && data.features[0];
            let name;
            if (feature) {
                const p = feature.properties;
                const parts = [p.name, p.city || p.town || p.village, p.state, p.country].filter(Boolean);
                name = parts.join(", ");
            } else {
                name = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
            }
            this.state.query = name;
            this.state.locationName = name;
            await this._saveToRecord(lat, lng, this.state.radius, name);
        } catch {
            const fallback = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
            this.state.query = fallback;
            this.state.locationName = fallback;
            await this._saveToRecord(lat, lng, this.state.radius, fallback);
        }
    }

    _updateCircleRadius(radius) {
        if (this.circle) {
            this.circle.setRadius(radius);
        }
    }

    async _setLocation(lat, lng, name) {
        this.state.lat = lat;
        this.state.lng = lng;
        this.state.locationName = name;
        this._placeMarkerAndCircle(lat, lng);
        await this._saveToRecord(lat, lng, this.state.radius, name);
    }

    // Auto-save: update + save to DB immediately
    async _saveToRecord(lat, lng, radius, locationName) {
        const record = this.props.record;
        await record.update({
            geofence_latitude: lat,
            geofence_longitude: lng,
            geofence_radius: radius,
            geofence_location_name: locationName || "",
        });
        try {
            await record.save();
            // Force widget state to match saved values so back-nav shows correct location
            this.state.lat = lat;
            this.state.lng = lng;
            this.state.radius = radius;
            this.state.locationName = locationName || "";
            this.state.query = locationName || "";
        } catch (e) {
            console.warn("Geofence auto-save failed:", e);
        }
    }

    // ── Search — smooth debounce + abort on new input ────────────────────────

    onSearchInput(ev) {
        const q = ev.target.value;
        this.state.query = q;
        this.state.showDropdown = false;
        this.state.activeSuggIndex = -1;

        // Cancel previous request
        if (this.abortController) this.abortController.abort();
        clearTimeout(this.searchTimeout);

        if (q.length < 2) {
            this.state.suggestions = [];
            this.state.loading = false;
            return;
        }

        this.state.loading = true;
        // ✅ FIX: Shorter debounce (250ms) for snappier feel like Google Maps
        this.searchTimeout = setTimeout(() => this._fetchSuggestions(q), 250);
    }

    async _fetchSuggestions(q) {
        this.abortController = new AbortController();
        try {
            // Photon API (by Komoot) — fast, free geocoder with no rate-limit concerns
            // Lang=en + India bbox bias (lat 8-37, lon 68-97)
            const url = `https://photon.komoot.io/api/?q=${encodeURIComponent(q)}&limit=10&lang=en&bbox=68,8,97,37`;
            const res = await fetch(url, { signal: this.abortController.signal });
            const data = await res.json();

            this.state.suggestions = (data.features || []).map((feature) => {
                const p = feature.properties;
                // Build readable name: name, city, state, country
                const parts = [p.name, p.city || p.town || p.village, p.state, p.country]
                    .filter(Boolean);
                const shortName = parts.slice(0, 2).join(", ");
                const fullAddress = parts.join(", ");
                const [lng, lat] = feature.geometry.coordinates;
                return { name: fullAddress, shortName, fullAddress, lat, lng };
            });
            this.state.showDropdown = this.state.suggestions.length > 0;
        } catch (e) {
            if (e.name !== "AbortError") {
                // Fallback to Nominatim if Photon fails
                try {
                    const url2 = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=8&addressdetails=1`;
                    const res2 = await fetch(url2, {
                        headers: { "Accept-Language": "en", "User-Agent": "OdooGeofenceWidget/1.0" },
                    });
                    const data2 = await res2.json();
                    this.state.suggestions = data2.map((item) => {
                        const parts = item.display_name.split(",");
                        return {
                            name: item.display_name,
                            shortName: parts.slice(0, 2).join(",").trim(),
                            fullAddress: parts.slice(0, 5).join(",").trim(),
                            lat: parseFloat(item.lat),
                            lng: parseFloat(item.lon),
                        };
                    });
                    this.state.showDropdown = this.state.suggestions.length > 0;
                } catch { this.state.suggestions = []; }
            }
        } finally {
            this.state.loading = false;
        }
    }

    async onSelectSuggestion(suggestion) {
        const displayName = suggestion.fullAddress || suggestion.name;
        this.state.query = displayName;
        this.state.showDropdown = false;
        this.state.suggestions = [];
        this.state.activeSuggIndex = -1;
        await this._setLocation(suggestion.lat, suggestion.lng, displayName);
    }

    // Keyboard navigation for dropdown
    onSearchKeydown(ev) {
        const list = this.state.suggestions;
        if (!this.state.showDropdown || !list.length) return;

        if (ev.key === "ArrowDown") {
            ev.preventDefault();
            this.state.activeSuggIndex = Math.min(this.state.activeSuggIndex + 1, list.length - 1);
        } else if (ev.key === "ArrowUp") {
            ev.preventDefault();
            this.state.activeSuggIndex = Math.max(this.state.activeSuggIndex - 1, 0);
        } else if (ev.key === "Enter" && this.state.activeSuggIndex >= 0) {
            ev.preventDefault();
            this.onSelectSuggestion(list[this.state.activeSuggIndex]);
        } else if (ev.key === "Escape") {
            this.state.showDropdown = false;
        }
    }

    onRadiusChange(ev) {
        const val = Math.max(10, parseInt(ev.target.value) || 10);
        this.state.radius = val;
        this._updateCircleRadius(val);
        if (this.state.lat) {
            this._saveToRecord(this.state.lat, this.state.lng, val, this.state.locationName);
        }
    }

    onClearLocation() {
        this.state.query = "";
        this.state.locationName = "";
        this.state.lat = null;
        this.state.lng = null;
        this.state.suggestions = [];
        this.state.showDropdown = false;
        if (this.marker) { this.map.removeLayer(this.marker); this.marker = null; }
        if (this.circle) { this.map.removeLayer(this.circle); this.circle = null; }
        this.map.setView([28.6139, 77.2090], 5, { animate: true });
        this._saveToRecord(null, null, this.state.radius, "");
    }

    onCloseDropdown() {
        setTimeout(() => { this.state.showDropdown = false; }, 180);
    }

    // Icon for place type
    _getPlaceIcon(type) {
        const icons = { city: "🏙️", town: "🏘️", village: "🏡", suburb: "🏢", building: "🏗️" };
        return icons[type] || "📍";
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Template
// ─────────────────────────────────────────────────────────────────────────────

GeofenceMapWidget.template = owl.xml`
<div class="geo-widget-root">

    <!-- ── Search Box ── -->
    <div class="geo-search-outer" t-att-class="state.showDropdown ? 'geo-search-outer--open' : ''">
        <div class="geo-search-box">
            <span class="geo-search-ico">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
            </span>
            <input
                type="text"
                class="geo-search-input"
                placeholder="Search location (e.g. Connaught Place, New Delhi)…"
                t-att-value="state.query"
                t-on-input="onSearchInput"
                t-on-keydown="onSearchKeydown"
                t-on-blur="onCloseDropdown"
                autocomplete="off"
            />
            <span t-if="state.loading" class="geo-spinner">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#714B67" stroke-width="2.5" stroke-linecap="round">
                    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83">
                        <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="0.7s" repeatCount="indefinite"/>
                    </path>
                </svg>
            </span>
            <button t-if="state.query and !state.loading" class="geo-clear-btn" t-on-mousedown="onClearLocation" title="Clear location">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        </div>

        <!-- Suggestions Dropdown -->
        <div t-if="state.showDropdown and state.suggestions.length" class="geo-dropdown">
            <div t-foreach="state.suggestions" t-as="s" t-key="s_index"
                class="geo-sugg-item"
                t-att-class="state.activeSuggIndex === s_index ? 'geo-sugg-item--active' : ''"
                t-on-mousedown="() => this.onSelectSuggestion(s)"
            >
                <span class="geo-sugg-dot"/>
                <div class="geo-sugg-text">
                    <span class="geo-sugg-primary" t-esc="s.shortName"/>
                    <span class="geo-sugg-secondary" t-esc="s.name"/>
                </div>
            </div>
        </div>
    </div>

    <!-- ── Location Info Bar ── -->
    <div t-if="state.lat" class="geo-info-bar">
        <div class="geo-coords-chip">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="#714B67"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
            <b t-esc="state.lat.toFixed(6)"/>, <b t-esc="state.lng.toFixed(6)"/>
        </div>
        <span class="geo-drag-hint">Drag the pin or click on map to adjust</span>
    </div>

    <!-- ── Radius Control ── -->
    <div class="geo-radius-card">
        <div class="geo-radius-header">
            <span class="geo-radius-title">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#714B67" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                Allowed Radius
            </span>
            <span class="geo-radius-val-badge">
                <span t-esc="state.radius"/> m
            </span>
        </div>
        <div class="geo-radius-body">
            <input
                type="range"
                class="geo-slider"
                min="10"
                max="5000"
                step="10"
                t-att-value="state.radius"
                t-on-input="onRadiusChange"
            />
            <input
                type="number"
                class="geo-number-input"
                min="10"
                t-att-value="state.radius"
                t-on-change="onRadiusChange"
            />
        </div>
        <div class="geo-radius-markers">
            <span>10m</span><span>500m</span><span>1km</span><span>2.5km</span><span>5km</span>
        </div>
    </div>

    <!-- ── Map ── -->
    <div class="geo-map-wrap">
        <div class="geo-map-container" t-ref="mapContainer"/>
        <div t-if="!state.lat" class="geo-map-placeholder">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#c5a8bb" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            <p>Search a location above or click on the map to set geofence</p>
        </div>
    </div>

    <style>
        /* ── Root ── */
        .geo-widget-root {
            display: flex;
            flex-direction: column;
            gap: 12px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif;
            margin-top: 8px;
            max-width: 100%;
        }

        /* ── Search ── */
        .geo-search-outer {
            position: relative;
            z-index: 100;
        }
        .geo-search-box {
            display: flex;
            align-items: center;
            background: #fff;
            border: 1.5px solid #ddd;
            border-radius: 10px;
            padding: 0 12px;
            gap: 8px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .geo-search-outer--open .geo-search-box {
            border-color: #714B67;
            box-shadow: 0 0 0 3px rgba(113,75,103,0.1), 0 1px 4px rgba(0,0,0,0.06);
            border-bottom-left-radius: 0;
            border-bottom-right-radius: 0;
        }
        .geo-search-ico {
            color: #999;
            display: flex;
            align-items: center;
            flex-shrink: 0;
        }
        .geo-search-input {
            flex: 1;
            border: none;
            outline: none;
            font-size: 13.5px;
            padding: 11px 0;
            color: #222;
            background: transparent;
            min-width: 0;
        }
        .geo-search-input::placeholder { color: #bbb; }
        .geo-spinner { display: flex; align-items: center; flex-shrink: 0; }
        .geo-clear-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f0e8ed;
            border: none;
            border-radius: 50%;
            width: 22px;
            height: 22px;
            cursor: pointer;
            color: #714B67;
            flex-shrink: 0;
            transition: background 0.15s;
        }
        .geo-clear-btn:hover { background: #e3d0dc; }

        /* Dropdown */
        .geo-dropdown {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: #fff;
            border: 1.5px solid #714B67;
            border-top: 1px solid #eee;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 8px 24px rgba(113,75,103,0.14);
            overflow: hidden;
            max-height: 280px;
            overflow-y: auto;
        }
        .geo-sugg-item {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 10px 14px;
            cursor: pointer;
            border-bottom: 1px solid #f5f5f5;
            transition: background 0.1s;
        }
        .geo-sugg-item:last-child { border-bottom: none; }
        .geo-sugg-item:hover,
        .geo-sugg-item--active { background: #faf3f8; }
        .geo-sugg-dot {
            flex-shrink: 0;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #e74c3c;
            margin-top: 5px;
            box-shadow: 0 0 0 3px rgba(231,76,60,0.15);
        }
        .geo-sugg-text {
            display: flex;
            flex-direction: column;
            gap: 2px;
            min-width: 0;
        }
        .geo-sugg-primary {
            font-size: 13px;
            font-weight: 600;
            color: #222;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .geo-sugg-secondary {
            font-size: 11.5px;
            color: #999;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* ── Info Bar ── */
        .geo-info-bar {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        .geo-coords-chip {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: linear-gradient(135deg, #f5eef8, #ede0ea);
            color: #714B67;
            border: 1px solid #d6c2d0;
            border-radius: 20px;
            padding: 4px 12px;
            font-size: 12px;
            font-weight: 600;
            font-feature-settings: "tnum";
        }
        .geo-drag-hint {
            font-size: 11.5px;
            color: #bbb;
            font-style: italic;
        }

        /* ── Radius Card ── */
        .geo-radius-card {
            background: #fff;
            border: 1.5px solid #ede0ea;
            border-radius: 10px;
            padding: 12px 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .geo-radius-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .geo-radius-title {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 12.5px;
            font-weight: 700;
            color: #555;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .geo-radius-val-badge {
            background: #714B67;
            color: #fff;
            border-radius: 12px;
            padding: 2px 12px;
            font-size: 12px;
            font-weight: 700;
            font-feature-settings: "tnum";
            min-width: 60px;
            text-align: center;
        }
        .geo-radius-body {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .geo-slider {
            flex: 1;
            -webkit-appearance: none;
            height: 5px;
            border-radius: 3px;
            background: linear-gradient(to right, #714B67, #c5a8bb);
            outline: none;
            cursor: pointer;
        }
        .geo-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #714B67;
            border: 3px solid #fff;
            box-shadow: 0 1px 5px rgba(113,75,103,0.4);
            cursor: pointer;
        }
        .geo-number-input {
            width: 72px;
            border: 1.5px solid #ddd;
            border-radius: 8px;
            padding: 5px 8px;
            font-size: 13px;
            font-weight: 600;
            color: #333;
            outline: none;
            text-align: center;
            transition: border-color 0.15s;
        }
        .geo-number-input:focus { border-color: #714B67; }
        .geo-radius-markers {
            display: flex;
            justify-content: space-between;
            font-size: 10.5px;
            color: #ccc;
        }

        /* ── Map ── */
        .geo-map-wrap {
            position: relative;
            border-radius: 12px;
            overflow: hidden;
            border: 1.5px solid #e0d4dc;
            box-shadow: 0 2px 12px rgba(113,75,103,0.10);
        }
        .geo-map-container {
            width: 100%;
            height: 360px;
            background: #f8f4f7;
        }
        .geo-map-placeholder {
            position: absolute;
            inset: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 10px;
            background: #faf5f8;
            pointer-events: none;
        }   
        .geo-map-placeholder p {
            font-size: 13px;
            color: #c5a8bb;
            text-align: center;
            max-width: 220px;
            line-height: 1.5;
        }
    </style>
</div>
`;

// ─────────────────────────────────────────────────────────────────────────────
// Register as Odoo field widget
// ─────────────────────────────────────────────────────────────────────────────

registry.category("fields").add("geofence_map", {
    component: GeofenceMapWidget,
    supportedTypes: ["float"],
    extractProps: ({ attrs }) => ({}),
});