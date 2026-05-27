/* =============================================================
   SIGN_SIGNER_PAGE.JS
   Standalone signing page (no Odoo web client).
   - Renders the PDF with pdf.js
   - Loads sign items from backend
   - Lets the user fill fields & draw a signature
   - Submits everything via /sign/submit/<id>
   ============================================================= */

(function () {
    "use strict";

    const REQUEST_ID = window.SIGN_REQUEST_ID;
    const PDF_URL = window.SIGN_PDF_URL;
    const ALREADY_SIGNED = window.SIGN_ALREADY_SIGNED;

    let pdfDoc = null;
    let signItems = [];                // server-loaded item metadata
    const filledValues = {};           // {item_id: {value, signature_data}}
    const fieldElements = {};          // {item_id: HTMLElement}

    let activeSigItemId = null;        // currently drawing-signature item
    let sigCtx = null;
    let sigDrawing = false;
    let lastX = 0, lastY = 0;
    let sigHasContent = false;

    // ---------------------------------------------------------
    // PDF.js setup
    // ---------------------------------------------------------

    if (window.pdfjsLib && pdfjsLib.GlobalWorkerOptions) {
        pdfjsLib.GlobalWorkerOptions.workerSrc =
            "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
    }

    // ---------------------------------------------------------
    // Toast
    // ---------------------------------------------------------

    function showToast(msg, isSuccess) {
        const t = document.getElementById("sign_toast");
        t.textContent = msg;
        t.className = isSuccess ? "success" : "";
        t.style.display = "block";
        setTimeout(() => { t.style.display = "none"; }, 3000);
    }

    // ---------------------------------------------------------
    // RPC helper
    // ---------------------------------------------------------

    function rpc(url, params) {
        return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                jsonrpc: "2.0", method: "call",
                params: params || {},
            }),
        }).then(r => r.json()).then(data => {
            if (data.error) throw new Error(data.error.data && data.error.data.message || "RPC error");
            return data.result;
        });
    }

    // ---------------------------------------------------------
    // PDF render
    // ---------------------------------------------------------

    async function renderPdf() {
        if (!PDF_URL) {
            document.getElementById("sign_pdf_container").innerHTML =
                "<div style='color:#fff;padding:40px;'>No PDF available for this document.</div>";
            return;
        }

        try {
            pdfDoc = await pdfjsLib.getDocument(PDF_URL).promise;
        } catch (e) {
            console.error("PDF load failed", e);
            showToast("Could not load PDF");
            return;
        }

        const container = document.getElementById("sign_pdf_container");
        container.innerHTML = "";

        for (let i = 1; i <= pdfDoc.numPages; i++) {
            const page = await pdfDoc.getPage(i);
            const viewport = page.getViewport({ scale: 1.5 });

            const pageDiv = document.createElement("div");
            pageDiv.className = "sign_pdf_page";
            pageDiv.dataset.page = i;
            pageDiv.style.width = viewport.width + "px";
            pageDiv.style.height = viewport.height + "px";

            const canvas = document.createElement("canvas");
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            canvas.style.display = "block";
            pageDiv.appendChild(canvas);
            container.appendChild(pageDiv);

            await page.render({
                canvasContext: canvas.getContext("2d"),
                viewport: viewport,
            }).promise;
        }

        placeAllFields();
    }

    // ---------------------------------------------------------
    // Place sign fields on the rendered pages
    // ---------------------------------------------------------

    function placeAllFields() {
        signItems.forEach(item => placeField(item));
    }

    function placeField(item) {
        const pageDiv = document.querySelector(
            `.sign_pdf_page[data-page="${item.page || 1}"]`
        );
        if (!pageDiv) return;

        const pageW = pageDiv.clientWidth;
        const pageH = pageDiv.clientHeight;

        const x = (item.pos_x / 100) * pageW;
        const y = (item.pos_y / 100) * pageH;
        const w = (item.width / 100) * pageW;
        const h = (item.height / 100) * pageH;

        const el = document.createElement("div");
        el.className = "sign_field_placed";
        el.dataset.itemId = item.id;
        el.dataset.itemType = item.item_type;
        el.style.left = x + "px";
        el.style.top = y + "px";
        el.style.width = w + "px";
        el.style.height = h + "px";
        el.style.textAlign = item.alignment || "left";

        renderFieldContent(el, item);
        pageDiv.appendChild(el);
        fieldElements[item.id] = el;
    }

    function renderFieldContent(el, item) {
        const t = item.item_type;
        el.innerHTML = "";

        // Already signed? show stored value/sig in read-only mode
        if (ALREADY_SIGNED) {
            if ((t === "signature" || t === "initial" || t === "stamp") && item.has_signature) {
                const img = document.createElement("img");
                img.src = "/web/image/sign.item/" + item.id + "/signature_data";
                el.appendChild(img);
                el.classList.add("filled");
            } else if (item.value) {
                el.textContent = item.value;
                el.classList.add("filled");
            } else {
                el.textContent = item.placeholder || "";
            }
            el.style.cursor = "default";
            el.onclick = null;
            return;
        }

        if (t === "signature" || t === "initial" || t === "stamp") {
            const stored = filledValues[item.id] && filledValues[item.id].signature_data;
            if (stored) {
                const img = document.createElement("img");
                img.src = stored;
                el.appendChild(img);
                el.classList.add("filled");
            } else {
                el.textContent = item.placeholder ||
                    (t === "signature" ? "Sign here" :
                     t === "initial" ? "Initials" : "Stamp");
            }
            el.onclick = () => openSigModal(item.id);
            return;
        }

        if (t === "checkbox") {
            const cb = document.createElement("input");
            cb.type = "checkbox";
            const v = filledValues[item.id] && filledValues[item.id].value;
            cb.checked = (v === "1" || v === "true");
            cb.style.width = "auto";
            cb.style.height = "auto";
            cb.onchange = () => {
                filledValues[item.id] = { value: cb.checked ? "1" : "0" };
                if (cb.checked) el.classList.add("filled");
                else el.classList.remove("filled");
            };
            el.appendChild(cb);
            el.style.justifyContent = "center";
            if (cb.checked) el.classList.add("filled");
            return;
        }

        if (t === "multiline") {
            const ta = document.createElement("textarea");
            ta.value = (filledValues[item.id] && filledValues[item.id].value) || "";
            ta.placeholder = item.placeholder || "";
            ta.oninput = () => {
                filledValues[item.id] = { value: ta.value };
                if (ta.value.trim()) el.classList.add("filled");
                else el.classList.remove("filled");
            };
            el.appendChild(ta);
            if (ta.value.trim()) el.classList.add("filled");
            return;
        }

        if (t === "date") {
            const inp = document.createElement("input");
            inp.type = "date";
            inp.value = (filledValues[item.id] && filledValues[item.id].value) ||
                        new Date().toISOString().substring(0, 10);
            inp.onchange = () => {
                filledValues[item.id] = { value: inp.value };
                if (inp.value) el.classList.add("filled");
            };
            el.appendChild(inp);
            // Pre-fill today's date
            filledValues[item.id] = { value: inp.value };
            el.classList.add("filled");
            return;
        }

        if (t === "strikethrough") {
            // Display as a line — value is implicit "1"
            el.innerHTML = "<span style='display:inline-block;width:90%;border-top:2px solid #333;'></span>";
            filledValues[item.id] = { value: "1" };
            el.classList.add("filled");
            return;
        }

        // Default: single-line text-style field (text, name, email, phone, company, selection)
        const inp = document.createElement("input");
        inp.type = (t === "email") ? "email" :
                   (t === "phone") ? "tel" : "text";
        inp.value = (filledValues[item.id] && filledValues[item.id].value) || "";
        inp.placeholder = item.placeholder || "";
        inp.oninput = () => {
            filledValues[item.id] = { value: inp.value };
            if (inp.value.trim()) el.classList.add("filled");
            else el.classList.remove("filled");
        };
        el.appendChild(inp);
        if (inp.value.trim()) el.classList.add("filled");
    }

    // ---------------------------------------------------------
    // Signature drawing modal
    // ---------------------------------------------------------

    function openSigModal(itemId) {
        activeSigItemId = itemId;
        const backdrop = document.getElementById("sig_modal_backdrop");
        backdrop.style.display = "flex";

        const canvas = document.getElementById("sig_canvas");
        sigCtx = canvas.getContext("2d");
        // Reset canvas (transparent so the exported PNG stamps cleanly)
        sigCtx.clearRect(0, 0, canvas.width, canvas.height);
        sigCtx.strokeStyle = "#000";
        sigCtx.lineWidth = 2.2;
        sigCtx.lineCap = "round";
        sigCtx.lineJoin = "round";
        sigHasContent = false;

        if (!canvas._signBound) {
            canvas._signBound = true;

            const getPos = (e) => {
                const r = canvas.getBoundingClientRect();
                const cx = (e.touches ? e.touches[0].clientX : e.clientX) - r.left;
                const cy = (e.touches ? e.touches[0].clientY : e.clientY) - r.top;
                // canvas internal vs displayed coords
                return {
                    x: cx * (canvas.width / r.width),
                    y: cy * (canvas.height / r.height),
                };
            };

            const start = (e) => {
                e.preventDefault();
                sigDrawing = true;
                const p = getPos(e);
                lastX = p.x; lastY = p.y;
            };
            const move = (e) => {
                if (!sigDrawing) return;
                e.preventDefault();
                const p = getPos(e);
                sigCtx.beginPath();
                sigCtx.moveTo(lastX, lastY);
                sigCtx.lineTo(p.x, p.y);
                sigCtx.stroke();
                lastX = p.x; lastY = p.y;
                sigHasContent = true;
            };
            const end = (e) => {
                if (sigDrawing) e && e.preventDefault();
                sigDrawing = false;
            };

            canvas.addEventListener("mousedown", start);
            canvas.addEventListener("mousemove", move);
            canvas.addEventListener("mouseup", end);
            canvas.addEventListener("mouseleave", end);
            canvas.addEventListener("touchstart", start, { passive: false });
            canvas.addEventListener("touchmove", move, { passive: false });
            canvas.addEventListener("touchend", end, { passive: false });
        }
    }

    window._signerClearCanvas = function () {
        const canvas = document.getElementById("sig_canvas");
        sigCtx.clearRect(0, 0, canvas.width, canvas.height);
        sigHasContent = false;
    };

    window._signerCloseSigModal = function () {
        document.getElementById("sig_modal_backdrop").style.display = "none";
        activeSigItemId = null;
    };

    window._signerConfirmSig = function () {
        if (!sigHasContent) {
            showToast("Please draw your signature first.");
            return;
        }
        if (!activeSigItemId) return;

        const canvas = document.getElementById("sig_canvas");
        // Make background transparent for stamping by re-rendering to a clean canvas
        const tmp = document.createElement("canvas");
        tmp.width = canvas.width;
        tmp.height = canvas.height;
        const tctx = tmp.getContext("2d");
        // We'll just keep the white-ish bg here; reportlab handles it OK.
        tctx.drawImage(canvas, 0, 0);
        const dataUrl = tmp.toDataURL("image/png");

        filledValues[activeSigItemId] = { signature_data: dataUrl };

        const item = signItems.find(s => s.id === activeSigItemId);
        const el = fieldElements[activeSigItemId];
        if (el && item) {
            renderFieldContent(el, item);
        }

        window._signerCloseSigModal();
    };

    // ---------------------------------------------------------
    // Submit
    // ---------------------------------------------------------

    async function submitSignature() {
        // Validate mandatory fields client-side
        const missing = [];
        signItems.forEach(it => {
            if (!it.mandatory) return;
            const v = filledValues[it.id];
            if (it.item_type === "signature" ||
                it.item_type === "initial" ||
                it.item_type === "stamp") {
                if (!v || !v.signature_data) missing.push(it.type_name);
            } else if (it.item_type === "checkbox") {
                if (!v || (v.value !== "1" && v.value !== "true")) missing.push(it.type_name);
            } else {
                if (!v || !(v.value || "").trim()) missing.push(it.type_name);
            }
        });

        if (missing.length) {
            showToast("Please fill: " + missing.join(", "));
            return;
        }

        const payload = signItems.map(it => {
            const v = filledValues[it.id] || {};
            return {
                id: it.id,
                value: v.value || "",
                signature_data: v.signature_data || "",
            };
        });

        const btn = document.getElementById("btn_sign");
        btn.disabled = true;
        btn.innerHTML = "<i class='fa fa-spinner fa-spin'></i> Signing...";

        try {
            const result = await rpc("/sign/submit/" + REQUEST_ID, {
                items: payload,
            });

            if (result && result.ok) {
                showToast("Signed successfully! Downloading...", true);
                setTimeout(() => {
                    window.location.href = "/sign/download/" + REQUEST_ID;
                }, 1200);
            } else {
                showToast("Signing failed.");
                btn.disabled = false;
                btn.innerHTML = "<i class='fa fa-check'></i> Sign & Submit";
            }
        } catch (e) {
            showToast(e.message || "Signing failed.");
            btn.disabled = false;
            btn.innerHTML = "<i class='fa fa-check'></i> Sign & Submit";
        }
    }

    // ---------------------------------------------------------
    // Init
    // ---------------------------------------------------------

    async function init() {
        try {
            const data = await rpc("/sign/data/" + REQUEST_ID, {});
            signItems = (data && data.items) || [];
        } catch (e) {
            console.error("Failed to load sign data", e);
        }

        await renderPdf();

        document.getElementById("btn_sign").addEventListener("click", submitSignature);

        if (ALREADY_SIGNED) {
            const btn = document.getElementById("btn_sign");
            btn.disabled = true;
            btn.innerHTML = "<i class='fa fa-check'></i> Already Signed";
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

})();
