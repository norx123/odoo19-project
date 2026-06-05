/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, onMounted, useRef, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// ── Helpers ──────────────────────────────────────────────────
function fmtTime(v) {
    if (!v) return "";
    const h = Math.floor(v), m = Math.round((v - h) * 60);
    return `${h % 12 || 12}:${String(m).padStart(2,"0")} ${h >= 12 ? "PM" : "AM"}`;
}
function dateStr(d) {
    return d.toISOString().split("T")[0];
}
function dateFmt(s) {
    if (!s) return "";
    const d = new Date(s + "T00:00:00");
    return d.toLocaleDateString("en-IN", { weekday:"short", day:"numeric", month:"short", year:"numeric" });
}
const TYPE_INFO = {
    client_meeting: { icon: "🤝", cls: "fv_tb_client",   label: "Client Meeting"  },
    project_site:   { icon: "🏗️", cls: "fv_tb_project",  label: "Project Site"    },
    shop_purchase:  { icon: "🛒", cls: "fv_tb_shop",     label: "Shop / Purchase" },
    delivery:       { icon: "🚚", cls: "fv_tb_delivery", label: "Delivery"        },
    office_visit:   { icon: "🏢", cls: "fv_tb_office",   label: "Office Visit"    },
    survey:         { icon: "📋", cls: "fv_tb_survey",   label: "Survey"          },
    other:          { icon: "📌", cls: "fv_tb_other",    label: "Other"           },
};
async function getGPS() {
    return new Promise((ok, fail) => {
        if (!navigator.geolocation) return fail(new Error("GPS not supported on this device."));
        navigator.geolocation.getCurrentPosition(
            p => ok({
                lat: p.coords.latitude,
                lng: p.coords.longitude,
                accuracy: p.coords.accuracy,
            }),
            (err) => {
                const msgs = {
                    1: "Location access denied. Please allow GPS in browser settings.",
                    2: "GPS position unavailable. Try outdoors or near a window.",
                    3: "GPS timed out. Try again.",
                };
                fail(new Error(msgs[err.code] || "GPS error."));
            },
            { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
        );
    });
}

// ── Camera ───────────────────────────────────────────────────
class FvCamera extends Component {
    static props = ["title", "color", "onPhoto", "onClose"];
    static template = xml`
<div class="fv_overlay" t-on-click.self="() => props.onClose()">
  <div class="fv_modal">
    <div t-attf-class="fv_modal_hd {{ props.color || 'fv_modal_hd_blue' }}">
      <span><t t-esc="props.title"/></span>
      <button class="fv_modal_x" t-on-click="() => props.onClose()">✕</button>
    </div>
    <div class="fv_cam_body" style="padding:16px">
      <t t-if="s.err"><div class="fv_cam_err"><t t-esc="s.err"/></div></t>
      <t t-elif="!s.snap">
        <video t-ref="vid" autoplay="1" playsinline="1" muted="1" class="fv_video" style="transform:scaleX(-1)"/>
        <canvas t-ref="cvs" style="display:none"/>
        <div class="fv_cam_btns">
          <button class="fv_cam_btn fv_cam_cap" t-on-click="() => this.shoot()">📷 Capture Photo</button>
        </div>
      </t>
      <t t-else="">
        <img t-att-src="s.snap" class="fv_preview"/>
        <div class="fv_cam_btns">
          <button class="fv_cam_btn fv_cam_ret" t-on-click="() => this.retake()">↺ Retake</button>
          <button class="fv_cam_btn fv_cam_ok"  t-on-click="() => this.confirm()">✓ Use Photo</button>
        </div>
      </t>
    </div>
  </div>
</div>`;
    setup() {
        this.vid = useRef("vid"); this.cvs = useRef("cvs");
        this.s = useState({ err: null, snap: null, stream: null, ready: false });
        onMounted(() => this.start());
    }
    async start() {
        try {
            const constraints = {
                video: {
                    facingMode: { ideal: "environment" },
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            };
            const st = await navigator.mediaDevices.getUserMedia(constraints);
            this.s.stream = st;
            if (this.vid.el) {
                this.vid.el.srcObject = st;
                // Wait for video to actually start playing before allowing capture
                this.vid.el.onloadedmetadata = () => {
                    this.vid.el.play().then(() => {
                        this.s.ready = true;
                    });
                };
            }
        } catch(e) {
            this.s.err = "Camera access denied. Please allow camera permission and reload.";
        }
    }
    shoot() {
        const v = this.vid.el, c = this.cvs.el;
        if (!v || v.videoWidth === 0) {
            // Video not ready yet, try again after short delay
            setTimeout(() => this.shoot(), 300);
            return;
        }
        c.width = v.videoWidth || 640;
        c.height = v.videoHeight || 480;
        const ctx = c.getContext("2d");
        ctx.drawImage(v, 0, 0, c.width, c.height);
        const snap = c.toDataURL("image/jpeg", 0.85);
        // Verify it's not a black image (all zeros)
        if (snap.length < 1000) {
            setTimeout(() => this.shoot(), 300);
            return;
        }
        this.s.snap = snap;
    }
    retake() { this.s.snap = null; }
    confirm() {
        const b64 = this.s.snap.split(",")[1];
        this.s.stream?.getTracks().forEach(t => t.stop());
        this.props.onPhoto(b64);
    }
}

// ── Add Visit Modal ──────────────────────────────────────────
class FvAddVisit extends Component {
    static props = ["visitDate", "onSave", "onClose"];
    static template = xml`
<div class="fv_overlay" t-on-click.self="() => props.onClose()">
  <div class="fv_modal">
    <div class="fv_modal_hd fv_modal_hd_blue">
      <span>➕ Add Visit</span>
      <button class="fv_modal_x" t-on-click="() => props.onClose()">✕</button>
    </div>
    <div class="fv_modal_body">

      <div class="fv_form_row">
        <label>Visit Type <span>*</span></label>
        <select class="fv_select" t-model="f.vtype">
          <option value="client_meeting">🤝 Client Meeting</option>
          <option value="project_site">🏗️ Project Site Visit</option>
          <option value="shop_purchase">🛒 Shop / Purchase</option>
          <option value="delivery">🚚 Delivery</option>
          <option value="office_visit">🏢 Office / Branch Visit</option>
          <option value="survey">📋 Survey / Inspection</option>
          <option value="other">📌 Other</option>
        </select>
      </div>

      <div class="fv_form_row">
        <label>Place Name <span>*</span></label>
        <input class="fv_input" t-model="f.place"
               placeholder="e.g. ABC Hardware Shop, XYZ Client Office, Site-3"/>
      </div>

      <div class="fv_form_row">
        <label>Title / Subject</label>
        <input class="fv_input" t-model="f.title"
               placeholder="e.g. Quarterly Review Meeting, Buy Cement"/>
      </div>

      <div class="fv_form_2col">
        <div class="fv_form_row">
          <label>City</label>
          <input class="fv_input" t-model="f.city" placeholder="City"/>
        </div>
        <div class="fv_form_row">
          <label>Priority</label>
          <select class="fv_select" t-model="f.priority">
            <option value="0">Normal</option>
            <option value="1">🟡 Important</option>
            <option value="2">🔴 Urgent</option>
          </select>
        </div>
      </div>

      <div class="fv_form_row">
        <label>Address</label>
        <input class="fv_input" t-model="f.address" placeholder="Full address (optional)"/>
      </div>

      <div class="fv_form_2col">
        <div class="fv_form_row">
          <label>Contact Person</label>
          <input class="fv_input" t-model="f.contact" placeholder="Name"/>
        </div>
        <div class="fv_form_row">
          <label>Contact Phone</label>
          <input class="fv_input" t-model="f.phone" placeholder="Phone"/>
        </div>
      </div>

      <div class="fv_form_2col">
        <div class="fv_form_row">
          <label>Start Time</label>
          <input class="fv_input" type="time" t-model="f.start_time"/>
        </div>
        <div class="fv_form_row">
          <label>End Time</label>
          <input class="fv_input" type="time" t-model="f.end_time"/>
        </div>
      </div>

      <div class="fv_form_row">
        <label>Purpose / Description</label>
        <textarea class="fv_textarea_sm" t-model="f.purpose"
                  placeholder="What needs to be done, items to buy, agenda..."/>
      </div>

      <div t-if="f.err" style="color:#dc2626;font-size:13px;margin-bottom:8px"><t t-esc="f.err"/></div>

      <div class="fv_form_btns">
        <button class="fv_btn_cancel" t-on-click="() => props.onClose()">Cancel</button>
        <button class="fv_btn_save" t-on-click="() => this.save()" t-att-disabled="f.saving">
          <t t-if="f.saving">Saving...</t>
          <t t-else="">✓ Add Visit</t>
        </button>
      </div>

    </div>
  </div>
</div>`;

    setup() {
        this.f = useState({
            vtype: "client_meeting", place: "", title: "", city: "",
            address: "", contact: "", phone: "",
            start_time: "", end_time: "", purpose: "",
            priority: "0", err: "", saving: false,
        });
    }

    timeToFloat(t) {
        if (!t) return 0;
        const [h, m] = t.split(":").map(Number);
        return h + m / 60;
    }

    async save() {
        if (!this.f.place.trim()) { this.f.err = "Place name is required."; return; }
        this.f.saving = true; this.f.err = "";
        try {
            await this.props.onSave({
                place:      this.f.place.trim(),
                address:    this.f.address.trim(),
                city:       this.f.city.trim(),
                vtype:      this.f.vtype,
                title:      this.f.title.trim(),
                purpose:    this.f.purpose.trim(),
                priority:   this.f.priority,
                contact:    this.f.contact.trim(),
                phone:      this.f.phone.trim(),
                start_time: this.timeToFloat(this.f.start_time),
                end_time:   this.timeToFloat(this.f.end_time),
            });
        } catch (e) {
            this.f.err = "Error: " + (e?.data?.message || e.message);
            this.f.saving = false;
        }
    }
}

// ── Main Dashboard ─────────────────────────────────────────────
class FvDashboard extends Component {
    static components = { FvCamera, FvAddVisit };
    static template = xml`
<div class="fv_app">

  <!-- Loading -->
  <t t-if="s.loading">
    <div class="fv_loading"><div class="fv_spinner"/><span>Loading visits...</span></div>
  </t>

  <!-- Error -->
  <t t-elif="s.err">
    <div class="fv_error">
      <div style="font-size:48px">⚠️</div>
      <div class="fv_err_msg"><t t-esc="s.err"/></div>
      <button class="fv_btn_retry" t-on-click="() => this.load()">↺ Retry</button>
    </div>
  </t>

  <!-- Dashboard -->
  <t t-else="">

    <!-- Header -->
    <div class="fv_hdr">
      <div>
        <h1>📋 Field Visit Management</h1>
        <div class="fv_hdr_sub"><t t-esc="s.emp_name and ('👤 ' + s.emp_name) or ''"/></div>
      </div>
      <div class="fv_hdr_actions">
        <button class="fv_btn_add" t-on-click="openAddVisit">➕ Add Visit</button>
        <button class="fv_btn_refresh" t-on-click="() => this.load()">↻</button>
      </div>
    </div>

    <!-- Date navigation -->
    <div class="fv_date_bar">
      <button class="fv_date_btn" t-on-click="prevDay">‹</button>
      <span class="fv_date_lbl"><t t-esc="getDateLabel()"/></span>
      <button class="fv_date_today_btn" t-on-click="goToday" t-if="!s.isToday">Today</button>
      <button class="fv_date_btn" t-on-click="nextDay" t-if="!s.isToday">›</button>
    </div>

    <!-- Stats -->
    <div class="fv_stats">
      <div class="fv_stat">
        <span class="fv_stat_n"><t t-esc="s.visits.length"/></span>
        <span class="fv_stat_l">Total</span>
      </div>
      <div class="fv_stat">
        <span t-attf-class="fv_stat_n fv_c_g"><t t-esc="doneCount"/></span>
        <span class="fv_stat_l">Done</span>
      </div>
      <div class="fv_stat">
        <span t-attf-class="fv_stat_n fv_c_a"><t t-esc="inCount"/></span>
        <span class="fv_stat_l">Active</span>
      </div>
      <div class="fv_stat">
        <span t-attf-class="fv_stat_n fv_c_r"><t t-esc="pendCount"/></span>
        <span class="fv_stat_l">Pending</span>
      </div>
    </div>

    <!-- Cards -->
    <div class="fv_grid">

      <t t-if="!s.visits.length">
        <div class="fv_empty">
          <div class="fv_empty_ico">📭</div>
          <h3>No visits scheduled</h3>
          <p>Tap <strong>+ Add Visit</strong> to add your visit, or ask your manager to assign one.</p>
        </div>
      </t>

      <t t-foreach="s.visits" t-as="v" t-key="v.id">
        <div class="fv_card">
          <div t-attf-class="fv_card_strip {{ v.status==='completed' ? 'fv_strip_completed' : v.status==='in_progress' ? 'fv_strip_progress' : 'fv_strip_planned' }}"/>
          <div class="fv_card_content">

            <!-- Head -->
            <div class="fv_card_hd">
              <div t-attf-class="fv_type_badge {{ typeInfo(v.vtype).cls }}">
                <t t-esc="typeInfo(v.vtype).icon"/>
              </div>
              <div class="fv_card_titles">
                <div class="fv_card_title"><t t-esc="v.title || v.place"/></div>
                <div class="fv_card_place" t-if="v.title">📍 <t t-esc="v.place"/></div>
              </div>
              <span t-attf-class="fv_status_badge {{ v.status==='completed' ? 'fv_sb_completed' : v.status==='in_progress' ? 'fv_sb_progress' : 'fv_sb_planned' }}">
                <t t-if="v.status==='completed'">✅ Done</t>
                <t t-elif="v.status==='in_progress'">🟡 Active</t>
                <t t-else="">⏳ Planned</t>
              </span>
            </div>

            <!-- Tags -->
            <div class="fv_tags">
              <span class="fv_tag fv_tag_type"><t t-esc="typeInfo(v.vtype).label"/></span>
              <span t-if="v.priority === '1'" class="fv_tag fv_tag_pri_1">🟡 Important</span>
              <span t-if="v.priority === '2'" class="fv_tag fv_tag_pri_2">🔴 Urgent</span>
              <span t-if="v.start_time" class="fv_tag fv_tag_time">
                🕐 <t t-esc="fmtTime(v.start_time)"/>
                <t t-if="v.end_time"> – <t t-esc="fmtTime(v.end_time)"/></t>
              </span>
            </div>

            <!-- Address -->
            <div class="fv_addr" t-if="v.address or v.city">
              📍 <t t-esc="v.address || ''"/>
              <t t-if="v.city"><t t-if="v.address">, </t><t t-esc="v.city"/></t>
              <t t-if="v.in_map">
                — <a t-att-href="v.in_map" target="_blank">📍 View Map ↗</a>
              </t>
              <t t-elif="v.out_map">
                — <a t-att-href="v.out_map" target="_blank">📍 View Map ↗</a>
              </t>
            </div>

            <!-- Contact -->
            <div class="fv_contact" t-if="v.contact">
              👤 <t t-esc="v.contact"/>
              <t t-if="v.phone"> · 📞 <t t-esc="v.phone"/></t>
            </div>

            <!-- Purpose -->
            <div class="fv_purpose_txt" t-if="v.purpose">
              📋 <t t-esc="v.purpose"/>
            </div>

            <!-- Check in/out times -->
            <div class="fv_times" t-if="v.check_in">
              <span class="fv_tin">IN: <t t-esc="v.check_in"/></span>
              <span class="fv_tout" t-if="v.check_out">OUT: <t t-esc="v.check_out"/></span>
              <span class="fv_tdur" t-if="v.check_out">⏱ <t t-esc="v.duration"/></span>
            </div>

            <!-- Outcome -->
            <div class="fv_outcome_txt" t-if="v.outcome">
              ✅ <t t-esc="v.outcome"/>
            </div>

            <!-- Actions -->
            <div class="fv_actions" style="margin-top:10px">
              <t t-if="v.status === 'planned'">
                <button class="fv_btn_in" t-on-click="() => this.startCheckIn(v)">✅ Check In</button>
              </t>
              <t t-elif="v.status === 'in_progress'">
                <button class="fv_btn_out" t-on-click="() => this.startCheckOut(v)">🚪 Check Out</button>
              </t>
              <t t-else="">
                <span class="fv_done_txt">✅ Visit Completed</span>
              </t>
            </div>

          </div>
        </div>
      </t>
    </div>

  </t><!-- end dashboard -->

  <!-- Saving -->
  <t t-if="s.saving"><div class="fv_saving"><div class="fv_spinner"/><span>Saving...</span></div></t>

  <!-- Add Visit Modal -->
  <t t-if="s.showAdd">
    <FvAddVisit visitDate="s.curDate" onSave.bind="saveNewVisit" onClose.bind="closeAdd"/>
  </t>

  <!-- Camera -->
  <t t-if="s.showCam">
    <FvCamera title="s.camTitle" color="s.camColor" onPhoto.bind="onPhoto" onClose.bind="closeCamera"/>
  </t>

  <!-- Outcome / Remarks -->
  <t t-if="s.showOutcome">
    <div class="fv_overlay">
      <div class="fv_modal">
        <div class="fv_modal_hd fv_modal_hd_orange">
          <span>🚪 Check Out — Add Outcome</span>
          <button class="fv_modal_x" t-on-click="cancelOutcome">✕</button>
        </div>
        <div class="fv_modal_body">
          <div class="fv_out_body">
            <h3>What did you accomplish?</h3>
            <p>Describe the visit outcome — meeting result, items purchased, work done, etc. (optional)</p>
            <textarea class="fv_textarea_sm" rows="4"
              placeholder="e.g. Met with client Ramesh, finalized contract. Bought 50 bags cement from ABC Store..."
              t-model="s.outcome"/>
            <div class="fv_out_btns">
              <button class="fv_out_cancel" t-on-click="cancelOutcome">Cancel</button>
              <button class="fv_out_confirm" t-on-click="() => this.submitOut()">Confirm Check Out</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </t>

</div>`;

    setup() {
        this.orm   = useService("orm");
        this.notif = useService("notification");
        const today = dateStr(new Date());
        this.s = useState({
            loading: true, err: null, visits: [], emp_name: '',
            curDate: today, isToday: true,
            saving: false,
            showAdd: false,
            showCam: false, camTitle: '', camColor: 'fv_modal_hd_green',
            showOutcome: false, outcome: '',
            _mode: null, _v: null, _loc: null, _photo: null,
        });
        onMounted(() => this.load());
    }

    typeInfo(t) { return TYPE_INFO[t] || TYPE_INFO.other; }
    fmtTime(v) { return fmtTime(v); }

    get doneCount() { return this.s.visits.filter(v => v.status === "completed").length; }
    get inCount()   { return this.s.visits.filter(v => v.status === "in_progress").length; }
    get pendCount() { return this.s.visits.filter(v => v.status === "planned").length; }

    getDateLabel() {
        const s = this.s.curDate;
        if (!s) return "";
        const d = new Date(s + "T00:00:00");
        return d.toLocaleDateString("en-IN", { weekday:"short", day:"numeric", month:"short", year:"numeric" });
    }

    async load() {
        this.s.loading = true; this.s.err = null;
        try {
            const r = await this.orm.call("fv.visit", "fv_get_my_visits", [this.s.curDate]);
            if (r.ok === false) { this.s.err = r.msg; }
            else {
                this.s.visits   = r.visits || [];
                this.s.emp_name = r.emp_name || '';
            }
        } catch (e) {
            this.s.err = "Server Error: " + (e?.data?.message || e?.message || "Unknown. Check Odoo server log.");
        }
        this.s.loading = false;
    }

    prevDay() {
        const d = new Date(this.s.curDate + "T00:00:00");
        d.setDate(d.getDate() - 1);
        this.s.curDate = dateStr(d);
        this.s.isToday = this.s.curDate === dateStr(new Date());
        this.load();
    }
    nextDay() {
        const d = new Date(this.s.curDate + "T00:00:00");
        d.setDate(d.getDate() + 1);
        this.s.curDate = dateStr(d);
        this.s.isToday = this.s.curDate === dateStr(new Date());
        this.load();
    }
    goToday() {
        this.s.curDate = dateStr(new Date());
        this.s.isToday = true;
        this.load();
    }

    openAddVisit() { this.s.showAdd = true; }
    closeAdd()     { this.s.showAdd = false; }

    async saveNewVisit(f) {
        const r = await this.orm.call("fv.visit", "fv_add_visit", [
            f.place, f.address, f.city, f.vtype, f.title,
            f.purpose, f.priority, this.s.curDate,
            f.start_time, f.end_time, f.contact, f.phone,
        ]);
        if (r.ok) {
            this.s.showAdd = false;
            this.notif.add(`✅ Visit "${r.name}" added!`, { type: "success" });
            await this.load();
        } else {
            throw new Error(r.msg);
        }
    }

    async startCheckIn(v) {
        this.s._mode = "in"; this.s._v = v;
        this.notif.add("📍 Getting your GPS location...", { type: "info" });
        try {
            this.s._loc = await getGPS();
            this.notif.add(`✅ Location found (±${Math.round(this.s._loc.accuracy||0)}m)`, { type: "success" });
        }
        catch (e) { this.notif.add(e.message, { type: "danger" }); return; }
        this.s.camTitle = `📸 Check In — ${v.title || v.place}`;
        this.s.camColor = "fv_modal_hd_green";
        this.s.showCam  = true;
    }

    async startCheckOut(v) {
        this.s._mode = "out"; this.s._v = v;
        this.notif.add("📍 Getting your GPS location...", { type: "info" });
        try {
            this.s._loc = await getGPS();
            this.notif.add(`✅ Location found (±${Math.round(this.s._loc.accuracy||0)}m)`, { type: "success" });
        }
        catch (e) { this.notif.add(e.message, { type: "danger" }); return; }
        this.s.camTitle = `📸 Check Out — ${v.title || v.place}`;
        this.s.camColor = "fv_modal_hd_orange";
        this.s.showCam  = true;
    }

    async onPhoto(b64) {
        this.s.showCam = false; this.s._photo = b64;
        if (this.s._mode === "in") { await this.submitIn(); }
        else { this.s.outcome = ""; this.s.showOutcome = true; }
    }

    closeCamera()    { this.s.showCam = false; this.s._mode = null; this.s._v = null; }
    cancelOutcome()  { this.s.showOutcome = false; this.s._mode = null; this.s._v = null; }

    async submitIn() {
        const { _v: v, _loc: l, _photo: p } = this.s;
        this.s.saving = true;
        try {
            const r = await this.orm.call("fv.visit", "fv_check_in",
                [v.id, l.lat, l.lng, p, navigator.userAgent]);
            if (r.ok) {
                this.notif.add(`✅ Checked In at ${r.check_in}`, { type: "success" });
                await this.load();
            } else { this.notif.add(r.msg, { type: "danger" }); }
        } catch (e) { this.notif.add("Error: " + (e?.data?.message || e.message), { type: "danger" }); }
        this.s.saving = false; this.s._v = null; this.s._mode = null;
    }

    async submitOut() {
        this.s.showOutcome = false;
        const { _v: v, _loc: l, _photo: p } = this.s;
        this.s.saving = true;
        try {
            const r = await this.orm.call("fv.visit", "fv_check_out",
                [v.id, l.lat, l.lng, p, this.s.outcome, navigator.userAgent]);
            if (r.ok) {
                this.notif.add(`✅ Checked Out. Duration: ${r.duration}`, { type: "success" });
                await this.load();
            } else { this.notif.add(r.msg, { type: "danger" }); }
        } catch (e) { this.notif.add("Error: " + (e?.data?.message || e.message), { type: "danger" }); }
        this.s.saving = false; this.s._v = null; this.s._mode = null;
    }
}

registry.category("actions").add("fv_dashboard", FvDashboard);
