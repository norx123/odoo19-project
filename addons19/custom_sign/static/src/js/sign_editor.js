/** @odoo-module **/

/* =============================================================
   SIGN_EDITOR.JS
   Template editor inside Odoo backend.
   - Renders the uploaded PDF
   - Lists available field types in the sidebar
   - Lets the user drag/drop fields onto the PDF
   - Lets the user click a placed field to edit / remove
   - SAVES the placed fields to the backend via RPC
     (this was the missing piece in the original module)
   ============================================================= */

(function () {
    "use strict";

    // -----------------------------------------------------
    // STATE
    // -----------------------------------------------------

    let currentTemplateId = null;     // Active custom.sign.template record
    let fieldTypes = [];              // custom.sign.item.type list
    let placedFields = [];            // {dom, data} per placed field on PDF
    let pdfRendered = false;

    let selectedField = null;
    let saveDebounce = null;

    // -----------------------------------------------------
    // PDF.JS LOAD
    // -----------------------------------------------------

    function loadPdfjsIfNeeded(cb) {
        if (window.pdfjsLib) { cb(); return; }
        const script = document.createElement("script");
        script.src = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js";
        script.onload = function () {
            pdfjsLib.GlobalWorkerOptions.workerSrc =
                "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
            cb();
        };
        document.head.appendChild(script);
    }

    // -----------------------------------------------------
    // RPC
    // -----------------------------------------------------

    function rpc(model, method, args, kwargs) {
        return fetch("/web/dataset/call_kw", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                jsonrpc: "2.0", method: "call", id: Date.now(),
                params: {
                    model: model,
                    method: method,
                    args: args || [],
                    kwargs: kwargs || {},
                },
            }),
        }).then(r => r.json()).then(d => {
            if (d.error) throw new Error(d.error.data && d.error.data.message || "RPC error");
            return d.result;
        });
    }

    // -----------------------------------------------------
    // FIELD TYPE METADATA
    // -----------------------------------------------------

    function typeIcon(it) {
        return ({
            signature: "fa-pencil-square-o", initial: "fa-font",
            text: "fa-text-width", multiline: "fa-align-left",
            checkbox: "fa-check-square-o", radio: "fa-dot-circle-o",
            selection: "fa-caret-square-o-down",
            strikethrough: "fa-strikethrough", stamp: "fa-certificate",
            date: "fa-calendar", name: "fa-user", email: "fa-envelope",
            phone: "fa-phone", company: "fa-building", upload: "fa-upload",
        })[it] || "fa-square-o";
    }

    function typeColor(it) {
        return ({
            signature: "#875A7B", initial: "#5C3D6E", text: "#6c757d",
            multiline: "#495057", checkbox: "#2d6a4f", radio: "#1d6fa4",
            selection: "#457b9d", strikethrough: "#c0392b", stamp: "#e76f51",
            date: "#2a9d8f", name: "#2d6a4f", email: "#1d6fa4",
            phone: "#457b9d", company: "#e76f51", upload: "#8e44ad",
        })[it] || "#6c757d";
    }

    // -----------------------------------------------------
    // RECORD ID FROM URL
    // -----------------------------------------------------

    function readTemplateIdFromUrl() {
        // Possible URLs:
        //   /odoo/sign/templates/47
        //   /odoo/action-618/47
        //   /web#id=47&model=custom.sign.template
        // Grab the LAST integer segment in the path - that's the record id.
        const path = window.location.pathname || "";
        const segments = path.split("/").filter(Boolean);
        for (let i = segments.length - 1; i >= 0; i--) {
            const seg = segments[i];
            if (/^\d+$/.test(seg)) {
                const candidate = parseInt(seg);
                if (!isNaN(candidate) && candidate > 0 && candidate < 1e9) {
                    return candidate;
                }
            }
        }
        const hash = window.location.hash || "";
        const m = hash.match(/[&#?]id=(\d+)/);
        if (m) return parseInt(m[1]);
        return null;
    }

    // -----------------------------------------------------
    // FETCH FIELD TYPES
    // -----------------------------------------------------

    async function fetchFieldTypes() {
        try {
            return await rpc("custom.sign.item.type", "search_read", [[]], {
                fields: ["id", "name", "item_type", "placeholder",
                         "mandatory", "alignment", "default_width", "default_height"],
                order: "sequence asc",
            });
        } catch (e) {
            console.error("fetchFieldTypes failed", e);
            return [];
        }
    }

    // -----------------------------------------------------
    // BUILD SIDEBAR (the "Fields" list of draggable buttons)
    // -----------------------------------------------------

    function buildSidebar() {
        const container = document.querySelector(".o_sign_field_list");
        if (!container) return;

        container.innerHTML = "";

        if (!fieldTypes.length) {
            container.innerHTML =
                "<div style='color:#999;font-size:12px;padding:8px'>" +
                "No field types defined. Go to Configuration &gt; Fields.</div>";
            return;
        }

        const grid = document.createElement("div");
        grid.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:6px;";

        fieldTypes.forEach(t => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "o_sign_field_btn";
            btn.draggable = true;

            btn.dataset.typeId = t.id;
            btn.dataset.itemType = t.item_type;
            btn.dataset.typeName = t.name;
            btn.dataset.placeholder = t.placeholder || t.name;
            btn.dataset.mandatory = t.mandatory ? "1" : "0";
            btn.dataset.alignment = t.alignment || "left";
            btn.dataset.defaultWidth = t.default_width || 18;
            btn.dataset.defaultHeight = t.default_height || 5;

            btn.style.cssText = `
                background:${typeColor(t.item_type)};display:flex;align-items:center;
                gap:6px;font-size:12px;padding:7px 10px;border-radius:5px;
                border:none;color:#fff;cursor:grab;width:100%;
                overflow:hidden;white-space:nowrap;`;

            btn.innerHTML = `<i class="fa ${typeIcon(t.item_type)}"></i><span>${escapeHtml(t.name)}</span>`;

            btn.addEventListener("dragstart", (e) => {
                e.dataTransfer.setData("application/json", JSON.stringify({
                    type_id: t.id,
                    item_type: t.item_type,
                    type_name: t.name,
                    placeholder: btn.dataset.placeholder,
                    mandatory: btn.dataset.mandatory === "1",
                    alignment: btn.dataset.alignment,
                    width: parseFloat(btn.dataset.defaultWidth) || 18,
                    height: parseFloat(btn.dataset.defaultHeight) || 5,
                }));
                e.dataTransfer.effectAllowed = "copy";
            });

            grid.appendChild(btn);
        });

        container.appendChild(grid);
    }

    function escapeHtml(s) {
        return (s || "").replace(/[&<>"']/g, c => ({
            "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"
        })[c]);
    }

    // -----------------------------------------------------
    // PDF RENDER
    // -----------------------------------------------------

    function renderPdfFromUrl(url) {
        const canvas = document.getElementById("o_sign_pdf_canvas");
        if (!canvas) return;

        const placeholder = document.getElementById("o_sign_pdf_placeholder");
        canvas.querySelectorAll(".o_sign_pdf_page").forEach(p => p.remove());
        if (placeholder) placeholder.style.display = "none";

        loadPdfjsIfNeeded(async () => {
            try {
                const pdf = await pdfjsLib.getDocument(url).promise;

                for (let i = 1; i <= pdf.numPages; i++) {
                    const page = await pdf.getPage(i);
                    const vp = page.getViewport({ scale: 1.5 });

                    const pageDiv = document.createElement("div");
                    pageDiv.className = "o_sign_pdf_page";
                    pageDiv.dataset.page = i;
                    pageDiv.style.cssText = `
                        position:relative;margin:10px auto;
                        width:${vp.width}px;height:${vp.height}px;
                        box-shadow:0 2px 8px rgba(0,0,0,0.2);background:#fff;`;

                    const cvs = document.createElement("canvas");
                    cvs.width = vp.width;
                    cvs.height = vp.height;
                    cvs.style.display = "block";
                    pageDiv.appendChild(cvs);
                    canvas.appendChild(pageDiv);

                    await page.render({
                        canvasContext: cvs.getContext("2d"),
                        viewport: vp,
                    }).promise;

                    initDropZone(pageDiv);
                }

                pdfRendered = true;

                // Once pages exist, restore previously placed fields
                await restorePlacedFields();
            } catch (e) {
                console.error("PDF render failed", e);
            }
        });
    }

    function tryRenderSavedPdf() {
        if (!currentTemplateId) return;

        rpc("custom.sign.template", "read",
            [[currentTemplateId]],
            { fields: ["document", "document_name"] }
        ).then(recs => {
            const rec = recs && recs[0];
            if (!rec || !rec.document) {
                const placeholder = document.getElementById("o_sign_pdf_placeholder");
                if (placeholder) placeholder.style.display = "";
                return;
            }
            const url = "/web/content?model=custom.sign.template&id=" + rec.id +
                        "&field=document&filename_field=document_name&download=false";
            renderPdfFromUrl(url);
        }).catch(e => console.error("Load saved PDF failed", e));
    }

    function bindUploadInputs() {
        // Bind the <input type=file> inside the Document binary widget
        const sidebar = document.querySelector(".o_sign_sidebar");
        if (!sidebar) return;

        sidebar.querySelectorAll("input[type=file]").forEach(input => {
            if (input._signBound) return;
            input._signBound = true;
            input.addEventListener("change", () => {
                const file = input.files && input.files[0];
                if (!file || file.type !== "application/pdf") return;
                renderPdfFromUrl(URL.createObjectURL(file));
            });
        });
    }

    // -----------------------------------------------------
    // DROP ZONE
    // -----------------------------------------------------

    function initDropZone(pageDiv) {
        pageDiv.addEventListener("dragover", (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = "copy";
        });
        pageDiv.addEventListener("drop", (e) => {
            e.preventDefault();
            let raw;
            try {
                raw = JSON.parse(e.dataTransfer.getData("application/json"));
            } catch (_) { return; }
            if (!raw || !raw.type_id) return;

            const rect = pageDiv.getBoundingClientRect();
            const px = e.clientX - rect.left;
            const py = e.clientY - rect.top;
            const pageW = rect.width;
            const pageH = rect.height;

            const width_pct = raw.width || 18;
            const height_pct = raw.height || 5;

            // Center the field on the drop point
            const w_px = (width_pct / 100) * pageW;
            const h_px = (height_pct / 100) * pageH;

            const x_pct = Math.max(0, Math.min(100 - width_pct, ((px - w_px / 2) / pageW) * 100));
            const y_pct = Math.max(0, Math.min(100 - height_pct, ((py - h_px / 2) / pageH) * 100));

            createPlacedField(pageDiv, {
                type_id: raw.type_id,
                item_type: raw.item_type,
                type_name: raw.type_name,
                placeholder: raw.placeholder,
                mandatory: raw.mandatory,
                readonly: false,
                alignment: raw.alignment || "left",
                pos_x: x_pct,
                pos_y: y_pct,
                width: width_pct,
                height: height_pct,
                page: parseInt(pageDiv.dataset.page) || 1,
                responsible_role: "Signer 1",
            });

            scheduleSave();
        });
    }

    // -----------------------------------------------------
    // CREATE PLACED FIELD
    // -----------------------------------------------------

    function createPlacedField(pageDiv, data) {
        const pageW = pageDiv.clientWidth;
        const pageH = pageDiv.clientHeight;

        const el = document.createElement("div");
        el.className = "o_sign_field_placed";
        el.style.cssText = `
            position:absolute;
            left:${(data.pos_x / 100) * pageW}px;
            top:${(data.pos_y / 100) * pageH}px;
            width:${(data.width / 100) * pageW}px;
            height:${(data.height / 100) * pageH}px;
            z-index:20;cursor:move;`;

        el.innerHTML = `
            <div class="o_sign_field_inner" style="
                background:${typeColor(data.item_type)};
                border-radius:4px;width:100%;height:100%;
                display:flex;align-items:center;gap:6px;padding:0 8px;
                color:#fff;font-size:12px;font-weight:500;
                box-shadow:0 2px 6px rgba(0,0,0,0.2);overflow:hidden;">
                <i class="fa ${typeIcon(data.item_type)}"></i>
                <span class="o_field_label_text" style="flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
                    ${escapeHtml(data.placeholder || data.type_name)}
                </span>
                <span class="o_remove_field" title="Remove" style="font-size:16px;cursor:pointer;opacity:.7;">×</span>
            </div>`;

        pageDiv.appendChild(el);

        const record = { dom: el, data: data, pageDiv: pageDiv };
        placedFields.push(record);

        attachFieldHandlers(record);

        return record;
    }

    function attachFieldHandlers(record) {
        const el = record.dom;
        const inner = el.querySelector(".o_sign_field_inner");

        inner.addEventListener("click", (e) => {
            if (e.target.classList.contains("o_remove_field")) return;
            selectField(record);
            openFieldPopup(record);
        });

        el.querySelector(".o_remove_field").addEventListener("click", (e) => {
            e.stopPropagation();
            removeField(record);
        });

        makeMovable(record);
    }

    function selectField(record) {
        document.querySelectorAll(".o_sign_field_placed").forEach(el => {
            el.classList.remove("o_field_selected");
        });
        record.dom.classList.add("o_field_selected");
        selectedField = record;
    }

    function removeField(record) {
        closeFieldPopup();
        record.dom.remove();
        placedFields = placedFields.filter(r => r !== record);
        if (selectedField === record) selectedField = null;
        scheduleSave();
    }

    // -----------------------------------------------------
    // DRAGGABLE / RESIZABLE PLACED FIELD
    // -----------------------------------------------------

    function makeMovable(record) {
        const el = record.dom;
        let sx = 0, sy = 0, sl = 0, st = 0;

        el.addEventListener("mousedown", (e) => {
            if (e.target.classList.contains("o_remove_field")) return;
            if (e.button !== 0) return;

            sx = e.clientX; sy = e.clientY;
            sl = parseInt(el.style.left || "0");
            st = parseInt(el.style.top || "0");

            const onMove = (ev) => {
                let nl = sl + (ev.clientX - sx);
                let nt = st + (ev.clientY - sy);
                const pageRect = record.pageDiv.getBoundingClientRect();
                const elRect = el.getBoundingClientRect();
                nl = Math.max(0, Math.min(pageRect.width - elRect.width, nl));
                nt = Math.max(0, Math.min(pageRect.height - elRect.height, nt));
                el.style.left = nl + "px";
                el.style.top = nt + "px";
            };
            const onUp = () => {
                document.removeEventListener("mousemove", onMove);
                document.removeEventListener("mouseup", onUp);
                syncPlacedDataFromDom(record);
                scheduleSave();
            };

            document.addEventListener("mousemove", onMove);
            document.addEventListener("mouseup", onUp);
        });
    }

    function syncPlacedDataFromDom(record) {
        const el = record.dom;
        const pageRect = record.pageDiv.getBoundingClientRect();
        const left = parseFloat(el.style.left) || 0;
        const top = parseFloat(el.style.top) || 0;
        const w = el.offsetWidth;
        const h = el.offsetHeight;

        record.data.pos_x = (left / pageRect.width) * 100;
        record.data.pos_y = (top / pageRect.height) * 100;
        record.data.width = (w / pageRect.width) * 100;
        record.data.height = (h / pageRect.height) * 100;
        record.data.page = parseInt(record.pageDiv.dataset.page) || 1;
    }

    // -----------------------------------------------------
    // FIELD CONFIG POPUP
    // -----------------------------------------------------

    function openFieldPopup(record) {
        closeFieldPopup();
        const d = record.data;

        const noPlaceholderTypes = ["signature", "initial", "stamp", "checkbox", "radio", "strikethrough"];
        const showPlaceholder = !noPlaceholderTypes.includes(d.item_type);
        const showAlign = !["signature", "initial", "stamp", "checkbox", "radio"].includes(d.item_type);

        const popup = document.createElement("div");
        popup.id = "o_sign_field_popup";

        popup.innerHTML = `
            <div class="o_popup_header">
                <span>${escapeHtml(d.type_name || d.item_type)}</span>
                <button class="o_popup_close" type="button">×</button>
            </div>

            ${showPlaceholder ? `
                <div class="o_popup_row">
                    <label>Placeholder</label>
                    <textarea id="o_popup_placeholder" rows="2">${escapeHtml(d.placeholder || "")}</textarea>
                </div>
            ` : ""}

            ${showAlign ? `
                <div class="o_popup_row">
                    <label>Alignment</label>
                    <div class="o_popup_align_btns">
                        <button type="button" class="o_align_btn ${d.alignment==='left'?'active':''}" data-align="left"><i class="fa fa-align-left"></i></button>
                        <button type="button" class="o_align_btn ${d.alignment==='center'?'active':''}" data-align="center"><i class="fa fa-align-center"></i></button>
                        <button type="button" class="o_align_btn ${d.alignment==='right'?'active':''}" data-align="right"><i class="fa fa-align-right"></i></button>
                    </div>
                </div>
            ` : ""}

            <div class="o_popup_row">
                <label>Responsible</label>
                <input type="text" id="o_popup_responsible" value="${escapeHtml(d.responsible_role || 'Signer 1')}"/>
            </div>

            <div class="o_popup_row o_popup_checks">
                <label class="o_check_label">
                    <input type="checkbox" id="o_popup_mandatory" ${d.mandatory?'checked':''}/>
                    Mandatory field
                </label>
                <label class="o_check_label">
                    <input type="checkbox" id="o_popup_readonly" ${d.readonly?'checked':''}/>
                    Read-only
                </label>
            </div>

            <div class="o_popup_actions">
                <button id="o_popup_save" type="button">Save</button>
                <button id="o_popup_copy" type="button" title="Duplicate"><i class="fa fa-copy"></i></button>
                <button id="o_popup_delete" type="button" title="Delete"><i class="fa fa-trash"></i></button>
            </div>
        `;

        const backdrop = document.createElement("div");
        backdrop.id = "o_sign_popup_backdrop";
        backdrop.style.cssText = "position:fixed;inset:0;z-index:9998;";
        backdrop.addEventListener("click", closeFieldPopup);

        document.body.appendChild(backdrop);
        document.body.appendChild(popup);

        popup.querySelector(".o_popup_close").addEventListener("click", closeFieldPopup);

        popup.querySelectorAll(".o_align_btn").forEach(btn => {
            btn.addEventListener("click", () => {
                popup.querySelectorAll(".o_align_btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
            });
        });

        popup.querySelector("#o_popup_save").addEventListener("click", () => {
            const phEl = popup.querySelector("#o_popup_placeholder");
            if (phEl) d.placeholder = phEl.value;

            const respEl = popup.querySelector("#o_popup_responsible");
            if (respEl) d.responsible_role = respEl.value || "Signer 1";

            d.mandatory = popup.querySelector("#o_popup_mandatory").checked;
            d.readonly = popup.querySelector("#o_popup_readonly").checked;

            const activeAlign = popup.querySelector(".o_align_btn.active");
            if (activeAlign) d.alignment = activeAlign.dataset.align;

            const labelEl = record.dom.querySelector(".o_field_label_text");
            if (labelEl) {
                labelEl.textContent = d.placeholder || d.type_name || d.item_type;
            }

            closeFieldPopup();
            scheduleSave();
        });

        popup.querySelector("#o_popup_copy").addEventListener("click", () => {
            const cloneData = Object.assign({}, d);
            cloneData.pos_x = Math.min(95, d.pos_x + 3);
            cloneData.pos_y = Math.min(95, d.pos_y + 3);
            createPlacedField(record.pageDiv, cloneData);
            closeFieldPopup();
            scheduleSave();
        });

        popup.querySelector("#o_popup_delete").addEventListener("click", () => {
            removeField(record);
        });
    }

    function closeFieldPopup() {
        const p = document.getElementById("o_sign_field_popup");
        if (p) p.remove();
        const b = document.getElementById("o_sign_popup_backdrop");
        if (b) b.remove();
    }

    // -----------------------------------------------------
    // SAVE TO BACKEND  (debounced)
    // -----------------------------------------------------

    function scheduleSave() {
        if (saveDebounce) clearTimeout(saveDebounce);
        saveDebounce = setTimeout(saveFieldsToBackend, 600);
    }

    async function saveFieldsToBackend() {
        if (!currentTemplateId) return;

        // Re-sync positions in case of any drift
        placedFields.forEach(syncPlacedDataFromDom);

        const payload = placedFields.map(r => ({
            type_id: r.data.type_id,
            placeholder: r.data.placeholder || "",
            mandatory: !!r.data.mandatory,
            readonly: !!r.data.readonly,
            alignment: r.data.alignment || "left",
            page: r.data.page || 1,
            pos_x: r.data.pos_x,
            pos_y: r.data.pos_y,
            width: r.data.width,
            height: r.data.height,
            responsible_role: r.data.responsible_role || "Signer 1",
        }));

        try {
            await rpc("custom.sign.template", "save_sign_items",
                [[currentTemplateId], payload], {});
            showSaveIndicator();
        } catch (e) {
            console.error("Save fields failed", e);
        }
    }

    function showSaveIndicator() {
        let el = document.getElementById("o_sign_save_indicator");
        if (!el) {
            el = document.createElement("div");
            el.id = "o_sign_save_indicator";
            el.style.cssText = `
                position:fixed;bottom:20px;right:20px;background:#28a745;
                color:#fff;padding:6px 14px;border-radius:4px;font-size:12px;
                z-index:9999;box-shadow:0 2px 8px rgba(0,0,0,0.2);
                opacity:0;transition:opacity .2s;`;
            el.textContent = "Saved ✓";
            document.body.appendChild(el);
        }
        el.style.opacity = "1";
        clearTimeout(el._t);
        el._t = setTimeout(() => { el.style.opacity = "0"; }, 1500);
    }

    // -----------------------------------------------------
    // RESTORE PREVIOUSLY PLACED FIELDS
    // -----------------------------------------------------

    async function restorePlacedFields() {
        if (!currentTemplateId) return;
        try {
            const items = await rpc(
                "custom.sign.template", "get_sign_items",
                [[currentTemplateId]], {}
            );

            (items || []).forEach(it => {
                const pageDiv = document.querySelector(
                    `.o_sign_pdf_page[data-page="${it.page || 1}"]`
                );
                if (!pageDiv) return;
                createPlacedField(pageDiv, {
                    type_id: it.type_id,
                    item_type: it.item_type,
                    type_name: it.type_name,
                    placeholder: it.placeholder,
                    mandatory: !!it.mandatory,
                    readonly: !!it.readonly,
                    alignment: it.alignment || "left",
                    pos_x: it.pos_x,
                    pos_y: it.pos_y,
                    width: it.width,
                    height: it.height,
                    page: it.page,
                    responsible_role: it.responsible_role || "Signer 1",
                });
            });
        } catch (e) {
            console.error("restorePlacedFields failed", e);
        }
    }

    // -----------------------------------------------------
    // KEYBOARD
    // -----------------------------------------------------

    document.addEventListener("keydown", (e) => {
        if ((e.key === "Delete" || e.key === "Backspace") && selectedField) {
            if (document.activeElement &&
                ["INPUT", "TEXTAREA", "SELECT"].indexOf(document.activeElement.tagName) >= 0) {
                return;
            }
            e.preventDefault();
            removeField(selectedField);
            selectedField = null;
        }
    });

    // -----------------------------------------------------
    // CSS injection
    // -----------------------------------------------------

    function injectStyles() {
        if (document.getElementById("o_sign_dyn_styles")) return;
        const s = document.createElement("style");
        s.id = "o_sign_dyn_styles";
        s.textContent = `
            .o_field_selected .o_sign_field_inner {
                outline: 3px solid #fff !important;
                box-shadow: 0 0 0 3px #875A7B !important;
            }
        `;
        document.head.appendChild(s);
    }

    // -----------------------------------------------------
    // BOOT for a template form
    // -----------------------------------------------------

    function bootForCurrent() {
        injectStyles();

        currentTemplateId = readTemplateIdFromUrl();
        placedFields = [];
        pdfRendered = false;
        selectedField = null;
        closeFieldPopup();

        fetchFieldTypes().then(types => {
            fieldTypes = types || [];
            buildSidebar();
        });

        bindUploadInputs();
        tryRenderSavedPdf();
    }

    // -----------------------------------------------------
    // Watch DOM for the editor showing up
    // -----------------------------------------------------

    let lastFieldListEl = null;

    function watchSidebar() {
        const editor = document.querySelector(".o_sign_editor_wrap");
        const fieldList = document.querySelector(".o_sign_field_list");

        if (editor && fieldList && fieldList !== lastFieldListEl) {
            lastFieldListEl = fieldList;
            bootForCurrent();
        }

        // Always try to bind newly-attached upload inputs
        if (editor) bindUploadInputs();

        setTimeout(watchSidebar, 300);
    }

    watchSidebar();

})();
