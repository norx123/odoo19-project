/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

console.log("Attendance Geofence + Path Tracker loaded.");

let _processing = false;
let _locationsCache = null;
let _trackingInterval = null;
const TRACK_INTERVAL_MS = 2 * 60 * 1000; // Save a GPS point every 2 minutes

// ── Geolocation Helper ────────────────────────────────────────────────────────

async function getCurrentPosition() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error("Geolocation is not supported by this browser."));
            return;
        }
        navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true,
            timeout: 10000,
        });
    });
}

// ── Background GPS Tracking ───────────────────────────────────────────────────

async function sendTrackPoint() {
    try {
        const position = await getCurrentPosition();
        await rpc("/attendance/geofence/track", {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
        });
    } catch (e) {
        // Fail silently — do not disturb the user during background tracking
        console.debug("[GeoTrack] Could not save track point:", e.message);
    }
}

function startTracking() {
    if (_trackingInterval) return;
    console.debug("[GeoTrack] Background GPS tracking started.");
    sendTrackPoint(); // Save an immediate point on check-in
    _trackingInterval = setInterval(sendTrackPoint, TRACK_INTERVAL_MS);
}

function stopTracking() {
    if (_trackingInterval) {
        clearInterval(_trackingInterval);
        _trackingInterval = null;
        console.debug("[GeoTrack] Background GPS tracking stopped.");
    }
}

// Resume tracking after a page reload if the employee is already checked in
async function resumeTrackingIfCheckedIn() {
    try {
        const status = await rpc("/attendance/geofence/status", {});
        if (status && status.checked_in) {
            startTracking();
        }
    } catch (e) {
        // Ignore — tracking is best-effort
    }
}

// ── Styles ────────────────────────────────────────────────────────────────────

function injectStyles() {
    if (document.getElementById("geo-inline-styles")) return;
    const style = document.createElement("style");
    style.id = "geo-inline-styles";
    style.textContent = `
        #geo-widget-wrapper {
            position: fixed;
            top: 54px;
            right: 12px;
            z-index: 1050;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #fff;
            border: 1.5px solid #d6c2d0;
            border-radius: 12px;
            box-shadow: 0 4px 18px rgba(113,75,103,0.15);
            overflow: hidden;
            min-width: 260px;
            max-width: 320px;
        }
        #geo-tab-headers {
            display: flex;
            background: #f7f0f5;
            border-bottom: 1.5px solid #e8dce4;
        }
        .geo-tab-btn {
            flex: 1;
            padding: 7px 8px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            border: none;
            background: transparent;
            color: #b090a8;
            cursor: pointer;
            transition: background 0.15s, color 0.15s;
            white-space: nowrap;
        }
        .geo-tab-btn:first-child { border-right: 1px solid #e8dce4; }
        .geo-tab-btn.active { background: #714B67; color: #fff; }
        .geo-tab-btn:hover:not(.active) { background: #ecdde8; color: #714B67; }
        .geo-tab-content {
            display: none;
            padding: 8px 12px 10px;
            align-items: center;
            gap: 8px;
            background: #fff;
        }
        .geo-tab-content.active { display: flex; }
        .geo-pin { font-size: 15px; flex-shrink: 0; }
        .geo-tab-content select {
            flex: 1;
            border: none;
            outline: none;
            font-size: 13px;
            font-weight: 600;
            color: #333;
            background: transparent;
            cursor: pointer;
            padding: 2px 22px 2px 2px;
            appearance: none;
            -webkit-appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='11' height='11' viewBox='0 0 24 24' fill='none' stroke='%23714B67' stroke-width='2.5'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 2px center;
            min-width: 0;
        }
        .geo-tab-content select option { font-weight: 500; color: #222; }
        #geo-tracking-badge {
            display: flex;
            align-items: center;
            gap: 5px;
            padding: 4px 12px 6px;
            font-size: 10px;
            color: #2e7d32;
            background: #f1f8f1;
            border-top: 1px solid #c8e6c9;
        }
        #geo-tracking-badge .geo-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #4caf50;
            animation: geo-pulse 1.5s infinite;
        }
        @keyframes geo-pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50%       { opacity: 0.4; transform: scale(0.8); }
        }
    `;
    document.head.appendChild(style);
}

// ── Widget ────────────────────────────────────────────────────────────────────

async function injectLocationWidget() {
    const existing = document.getElementById("geo-widget-wrapper");
    if (existing) existing.remove();
    if (!_locationsCache || _locationsCache.length === 0) return;

    injectStyles();

    const wrapper = document.createElement("div");
    wrapper.id = "geo-widget-wrapper";

    // Tab headers
    const tabHeaders = document.createElement("div");
    tabHeaders.id = "geo-tab-headers";

    const checkinTab = document.createElement("button");
    checkinTab.className = "geo-tab-btn active";
    checkinTab.textContent = "\uD83D\uDCCD Check-In Location";
    checkinTab.dataset.tab = "checkin";

    const checkoutTab = document.createElement("button");
    checkoutTab.className = "geo-tab-btn";
    checkoutTab.textContent = "\uD83C\uDFC1 Check-Out Location";
    checkoutTab.dataset.tab = "checkout";

    tabHeaders.appendChild(checkinTab);
    tabHeaders.appendChild(checkoutTab);

    // Check-In tab
    const checkinContent = document.createElement("div");
    checkinContent.className = "geo-tab-content active";
    checkinContent.id = "geo-tab-checkin";

    const pinIn = document.createElement("span");
    pinIn.className = "geo-pin";
    pinIn.textContent = "\uD83D\uDCCD";

    const selectIn = document.createElement("select");
    selectIn.id = "geo-select-checkin";
    _locationsCache.forEach((loc) => {
        const opt = document.createElement("option");
        opt.value = String(loc.id);
        opt.textContent = loc.name + (loc.geofence_enabled ? " (" + loc.radius + "m)" : "");
        opt._loc = loc;
        selectIn.appendChild(opt);
    });
    selectIn.addEventListener("click", (e) => e.stopPropagation());
    selectIn.addEventListener("mousedown", (e) => e.stopPropagation());
    checkinContent.appendChild(pinIn);
    checkinContent.appendChild(selectIn);

    // Check-Out tab
    const checkoutContent = document.createElement("div");
    checkoutContent.className = "geo-tab-content";
    checkoutContent.id = "geo-tab-checkout";

    const pinOut = document.createElement("span");
    pinOut.className = "geo-pin";
    pinOut.textContent = "\uD83C\uDFC1";

    const selectOut = document.createElement("select");
    selectOut.id = "geo-select-checkout";
    _locationsCache.forEach((loc) => {
        const opt = document.createElement("option");
        opt.value = String(loc.id);
        opt.textContent = loc.name + (loc.geofence_enabled ? " (" + loc.radius + "m)" : "");
        opt._loc = loc;
        selectOut.appendChild(opt);
    });
    selectOut.addEventListener("click", (e) => e.stopPropagation());
    selectOut.addEventListener("mousedown", (e) => e.stopPropagation());
    checkoutContent.appendChild(pinOut);
    checkoutContent.appendChild(selectOut);

    // Tracking badge — visible only when employee is checked in
    const trackingBadge = document.createElement("div");
    trackingBadge.id = "geo-tracking-badge";
    trackingBadge.style.display = "none";
    trackingBadge.innerHTML = `<span class="geo-dot"></span> Path tracking active`;

    wrapper.appendChild(tabHeaders);
    wrapper.appendChild(checkinContent);
    wrapper.appendChild(checkoutContent);
    wrapper.appendChild(trackingBadge);
    document.body.appendChild(wrapper);

    // Show tracking badge if already checked in
    try {
        const status = await rpc("/attendance/geofence/status", {});
        if (status && status.checked_in) {
            trackingBadge.style.display = "flex";
        }
    } catch (e) { /* ignore */ }

    // Tab switching
    [checkinTab, checkoutTab].forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            document.querySelectorAll(".geo-tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".geo-tab-content").forEach(c => c.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById("geo-tab-" + btn.dataset.tab).classList.add("active");
        });
    });
}

// ── Get Selected Location ─────────────────────────────────────────────────────

function getCheckinLocation() {
    const select = document.getElementById("geo-select-checkin");
    if (select && select.options.length > 0) {
        return select.options[select.selectedIndex]._loc || null;
    }
    return (_locationsCache && _locationsCache[0]) || null;
}

function getCheckoutLocation() {
    const select = document.getElementById("geo-select-checkout");
    if (select && select.options.length > 0) {
        return select.options[select.selectedIndex]._loc || null;
    }
    return (_locationsCache && _locationsCache[0]) || null;
}

// ── Check-In Flow ─────────────────────────────────────────────────────────────

async function doCheckin(selectedLocation) {
    let capturedPosition = null;

    if (selectedLocation.geofence_enabled && selectedLocation.has_coordinates) {
        let position;
        try {
            position = await getCurrentPosition();
        } catch (err) {
            alert(
                "Location permission denied. Please allow location access and try again.\n" +
                "Error: " + err.message
            );
            return;
        }
        capturedPosition = position;

        let geoResult;
        try {
            geoResult = await rpc("/attendance/geofence/check", {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                work_location_id: selectedLocation.id,
            });
        } catch (e) {
            // Fail open — allow check-in if the server cannot be reached
        }

        if (geoResult && !geoResult.allowed) {
            alert(
                "Attendance Restricted\n\n" +
                "Location: " + selectedLocation.name + "\n" +
                "Your distance: " + geoResult.distance + " m\n" +
                "Allowed radius: " + geoResult.radius + " m\n\n" +
                "Please move closer to the location and try again."
            );
            return;
        }
    } else {
        // No geofence — still capture GPS for path tracking
        try {
            capturedPosition = await getCurrentPosition();
        } catch (e) {
            // GPS unavailable — allow check-in without a starting point
        }
    }

    const payload = { work_location_id: selectedLocation.id };
    if (capturedPosition) {
        payload.latitude = capturedPosition.coords.latitude;
        payload.longitude = capturedPosition.coords.longitude;
        payload.accuracy = capturedPosition.coords.accuracy;
    }

    try {
        const result = await rpc("/attendance/geofence/checkin", payload);
        if (result.success) {
            startTracking(); // Begin background GPS tracking
            window.location.reload();
        } else {
            alert("Check-in failed: " + (result.error || "Unknown error."));
        }
    } catch (e) {
        alert("Check-in error: " + e.message);
    }
}

async function handleCheckIn(btn) {
    if (_processing) return;
    _processing = true;
    try {
        if (!_locationsCache) {
            try {
                const locData = await rpc("/attendance/geofence/locations", {});
                _locationsCache = locData.locations || [];
            } catch (e) {
                triggerOriginalClick(btn);
                return;
            }
        }
        if (_locationsCache.length === 0) { triggerOriginalClick(btn); return; }
        const selectedLocation = getCheckinLocation();
        if (!selectedLocation) { triggerOriginalClick(btn); return; }
        await doCheckin(selectedLocation);
    } finally {
        _processing = false;
    }
}

// ── Check-Out Flow ────────────────────────────────────────────────────────────

async function doCheckout(selectedLocation, originalBtn) {
    let position = null;
    try {
        position = await getCurrentPosition();
    } catch (e) {
        // GPS unavailable — proceed with check-out without a final point
    }

    const payload = { work_location_id: selectedLocation.id };
    if (position) {
        payload.latitude = position.coords.latitude;
        payload.longitude = position.coords.longitude;
        payload.accuracy = position.coords.accuracy;
    }

    try {
        const result = await rpc("/attendance/geofence/checkout", payload);
        if (result && result.success) {
            stopTracking(); // Stop background GPS tracking
            window.location.reload();
        } else {
            originalBtn.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: false }));
            setTimeout(() => { _processing = false; }, 1500);
        }
    } catch (e) {
        originalBtn.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: false }));
        setTimeout(() => { _processing = false; }, 1500);
    }
}

async function handleCheckOut(btn) {
    if (_processing) return;
    _processing = true;
    try {
        if (!_locationsCache) {
            try {
                const locData = await rpc("/attendance/geofence/locations", {});
                _locationsCache = locData.locations || [];
            } catch (e) {
                triggerOriginalClick(btn);
                return;
            }
        }
        if (_locationsCache.length === 0) { triggerOriginalClick(btn); return; }
        const selectedLocation = getCheckoutLocation();
        if (!selectedLocation) { triggerOriginalClick(btn); return; }
        await doCheckout(selectedLocation, btn);
    } finally {
        _processing = false;
    }
}

function triggerOriginalClick(btn) {
    btn.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: false }));
}

// ── Button Detection ──────────────────────────────────────────────────────────

function isCheckInBtn(el) {
    if (!el) return false;
    const text = (el.textContent || "").trim().toLowerCase();
    const cls = el.className || "";
    if (text.includes("check in")) return true;
    if (cls.includes("o_hr_attendance_sign") || cls.includes("o_attendance_sign")) return true;
    return false;
}

function isCheckOutBtn(el) {
    if (!el) return false;
    return (el.textContent || "").trim().toLowerCase().includes("check out");
}

// ── Initialise ────────────────────────────────────────────────────────────────

async function init() {
    await new Promise(r => setTimeout(r, 1500));
    try {
        const locData = await rpc("/attendance/geofence/locations", {});
        _locationsCache = locData.locations || [];
    } catch (e) {
        return;
    }
    await injectLocationWidget();
    await resumeTrackingIfCheckedIn();
}

init();

// ── Global Click Interceptor ──────────────────────────────────────────────────

document.addEventListener("click", async (event) => {
    if (_processing) return;
    const btn = event.target.closest("a, button");
    if (!btn) return;
    if (btn.closest("#geo-widget-wrapper")) return;

    if (isCheckInBtn(btn)) {
        event.stopImmediatePropagation();
        event.preventDefault();
        await handleCheckIn(btn);
    } else if (isCheckOutBtn(btn)) {
        event.stopImmediatePropagation();
        event.preventDefault();
        await handleCheckOut(btn);
    }
}, true);
