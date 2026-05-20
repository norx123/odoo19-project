/** @odoo-module **/

// =============================================================
// PDF.js LOAD
// =============================================================

function loadPdfjsIfNeeded(cb) {
    if (window.pdfjsLib) { cb(); return; }
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
    script.onload = function () {
        pdfjsLib.GlobalWorkerOptions.workerSrc =
            'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        cb();
    };
    document.head.appendChild(script);
}

// =============================================================
// PDF RENDER
// =============================================================

function renderPdfFromUrl(url) {
    const placeholder = document.getElementById('o_sign_pdf_placeholder');
    const canvas = document.getElementById('o_sign_pdf_canvas');
    if (!canvas) return;

    canvas.querySelectorAll('.o_sign_pdf_page').forEach(p => p.remove());
    if (placeholder) placeholder.style.display = 'none';

    loadPdfjsIfNeeded(function () {
        pdfjsLib.getDocument(url).promise.then(function (pdf) {
            for (let i = 1; i <= pdf.numPages; i++) {
                pdf.getPage(i).then(function (page) {
                    const vp = page.getViewport({ scale: 1.5 });
                    const pageDiv = document.createElement('div');
                    pageDiv.className = 'o_sign_pdf_page';
                    pageDiv.style.cssText = `
                        position:relative;
                        margin:10px auto;
                        width:${vp.width}px;
                        height:${vp.height}px;
                        box-shadow:0 2px 8px rgba(0,0,0,0.2);
                        background:#fff;
                    `;
                    const cvs = document.createElement('canvas');
                    cvs.width = vp.width;
                    cvs.height = vp.height;
                    cvs.style.display = 'block';
                    pageDiv.appendChild(cvs);
                    canvas.appendChild(pageDiv);
                    page.render({ canvasContext: cvs.getContext('2d'), viewport: vp });
                });
            }
            setTimeout(initDragDrop, 500);
        }).catch(function (err) {
            console.error('PDF render error:', err);
        });
    });
}

function initPdfPreview() {
    function tryBindInput(input) {
        if (!input || input._signBound) return;
        input._signBound = true;
        input.addEventListener('change', function () {
            const file = input.files && input.files[0];
            if (!file || file.type !== 'application/pdf') return;
            renderPdfFromUrl(URL.createObjectURL(file));
        });
    }

    // Abhi jo inputs hain unhe bind karo
    document.querySelectorAll('input[type="file"]').forEach(tryBindInput);

    // Saved record: URL se record ID nikalo aur backend se PDF fetch karo
    function tryRenderSaved() {
        if (document._signPdfRendered) return;

        // URL mein record ID dhundo — /action-618/23 ya ?id=23
        const match = window.location.href.match(/\/(\d+)(?:\?|$|#|\/)/);
        if (!match) return;
        const recordId = parseInt(match[1]);
        if (!recordId) return;

        document._signPdfRendered = true;

        fetch('/web/dataset/call_kw', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0', method: 'call', id: 1,
                params: {
                    model: 'sign.template',
                    method: 'search_read',
                    args: [[['id', '=', recordId]]],
                    kwargs: { fields: ['id', 'document'], limit: 1 }
                }
            })
        })
        .then(r => r.json())
        .then(data => {
            const rec = data.result && data.result[0];
            if (!rec || !rec.document) return;
            const url = '/web/content?model=sign.template&id=' + rec.id + '&field=document&filename_field=document_name&download=false';
            renderPdfFromUrl(url);
        })
        .catch(function(e) { console.error('PDF load error:', e); });
    }

    // Future mein Odoo jo bhi inject kare usse handle karo
    const observer = new MutationObserver(function () {
        document.querySelectorAll('input[type="file"]').forEach(tryBindInput);
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // Saved PDF render karo
    tryRenderSaved();
}

// =============================================================
// FETCH FIELD TYPES FROM sign.item.type
// =============================================================

let selectedField = null;

function selectField(field) {
    document.querySelectorAll('.o_sign_field_placed').forEach((el) => {
        el.classList.remove('o_field_selected');
    });

    selectedField = field;

    if (field) {
        field.classList.add('o_field_selected');
    }
}

document.addEventListener('keydown', function (e) {
    if (e.key === "Delete" && selectedField) {
        closeFieldPopup();
        selectedField.remove();
        selectedField = null;
    }
});

async function fetchFieldTypes() {
    try {
        const res = await fetch('/web/dataset/call_kw', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                id: 1,
                params: {
                    model: 'sign.item.type',
                    method: 'search_read',
                    args: [[]],
                    kwargs: {
                        fields: [
                            'id',
                            'name',
                            'item_type',
                            'placeholder',
                            'mandatory',
                            'alignment',
                            'field_size'
                        ],
                        order: 'sequence asc',
                    }
                }
            })
        });

        const data = await res.json();
        return (data.result || []);
    } catch (e) {
        return [];
    }
}

function typeIcon(item_type) {
    return {
        signature: 'fa-pencil-square-o',
        initial: 'fa-font',
        text: 'fa-text-width',
        multiline: 'fa-align-left',
        checkbox: 'fa-check-square-o',
        radio: 'fa-dot-circle-o',
        selection: 'fa-caret-square-o-down',
        strikethrough: 'fa-strikethrough',
        stamp: 'fa-certificate',
        date: 'fa-calendar',
        name: 'fa-user',
        email: 'fa-envelope',
        phone: 'fa-phone',
        company: 'fa-building',
    }[item_type] || 'fa-square-o';
}

function typeColor(item_type) {
    return {
        signature: '#875A7B',
        initial: '#5C3D6E',
        text: '#6c757d',
        multiline: '#495057',
        checkbox: '#2d6a4f',
        radio: '#1d6fa4',
        selection: '#457b9d',
        strikethrough: '#c0392b',
        stamp: '#e76f51',
        date: '#2a9d8f',
        name: '#2d6a4f',
        email: '#1d6fa4',
        phone: '#457b9d',
        company: '#e76f51',
    }[item_type] || '#6c757d';
}

// =============================================================
// DRAG & DROP
// =============================================================

function initDragDrop() {
    document.querySelectorAll('.o_sign_field_btn').forEach((btn) => {
        btn.setAttribute('draggable', 'true');
        btn.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('application/json', JSON.stringify({
                type:        btn.dataset.type,
                typeId:      btn.dataset.typeId,
                typeName:    btn.dataset.typeName,
                placeholder: btn.dataset.placeholder,
                mandatory:   btn.dataset.mandatory,
                alignment:   btn.dataset.alignment,
            }));
            e.dataTransfer.effectAllowed = 'copy';
        });
    });

    document.querySelectorAll('.o_sign_pdf_page, .page, .o_sign_canvas, #o_sign_pdf_canvas').forEach((page) => {
        page.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
        });
        page.addEventListener('drop', (e) => {
            e.preventDefault();
            let raw;
            try { raw = JSON.parse(e.dataTransfer.getData('application/json')); } catch (_) { return; }
            const rect = page.getBoundingClientRect();
            createField(page, {
                type:        raw.type,
                name:        raw.typeName,
                placeholder: raw.placeholder,
                mandatory:   raw.mandatory === '1',
                alignment:   raw.alignment,
                x:           e.clientX - rect.left - 80,
                y:           e.clientY - rect.top - 17,
            });
        });
    });
}

// =============================================================
// BUILD SIDEBAR
// =============================================================

async function buildSidebarFields() {
    const container = document.querySelector('.o_sign_field_list');
    if (!container) return;

    const types = await fetchFieldTypes();
    if (!types.length) return;

    container.innerHTML = '';

    const grid = document.createElement('div');
    grid.style.cssText = `
        display:grid;
        grid-template-columns:1fr 1fr;
        gap:6px;
    `;

    types.forEach((t) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'o_sign_field_btn';

        btn.dataset.type = t.item_type;
        btn.dataset.typeId = t.id;
        btn.dataset.typeName = t.name;
        btn.dataset.placeholder = t.placeholder || t.name;
        btn.dataset.mandatory = t.mandatory ? '1' : '0';
        btn.dataset.alignment = t.alignment || 'left';

        btn.style.cssText = `
            background:${typeColor(t.item_type)};
            display:flex;
            align-items:center;
            gap:6px;
            font-size:12px;
            padding:7px 10px;
            border-radius:5px;
            border:none;
            color:#fff;
            cursor:grab;
            width:100%;
            overflow:hidden;
            white-space:nowrap;
        `;

        btn.innerHTML = `
            <i class="fa ${typeIcon(t.item_type)}"></i>
            ${t.name}
        `;

        grid.appendChild(btn);
    });

    container.appendChild(grid);
    initDragDrop();
}

// =============================================================
// CREATE FIELD
// =============================================================

function createField(container, opts) {
    const {
        type,
        name,
        placeholder,
        mandatory,
        alignment,
        x,
        y
    } = opts;

    const color = typeColor(type);
    const icon = typeIcon(type);
    const label = name || capitalize(type);

    const field = document.createElement('div');
    field.className = 'o_sign_field_placed';

    field.dataset.type = type;
    field.dataset.placeholder = placeholder || label;
    field.dataset.mandatory = mandatory ? '1' : '0';
    field.dataset.alignment = alignment || 'left';
    field.dataset.label = label;

    field.style.cssText = `
        position:absolute;
        left:${x}px;
        top:${y}px;
        width:160px;
        height:34px;
        z-index:20;
        cursor:move;
    `;

    field.innerHTML = `
        <div class="o_sign_field_inner" style="
            background:${color};
            border-radius:4px;
            width:100%;
            height:100%;
            display:flex;
            align-items:center;
            gap:6px;
            padding:0 10px;
            color:#fff;
            font-size:13px;
            font-weight:500;
            box-shadow:0 2px 6px rgba(0,0,0,0.25);
            overflow:hidden;
        ">
            <i class="fa ${icon}"></i>

            <span class="o_field_label_text"
                style="
                    flex:1;
                    white-space:nowrap;
                    overflow:hidden;
                    text-overflow:ellipsis;
                ">
                ${placeholder || label}
            </span>

            <span class="o_remove_field"
                title="Remove"
                style="
                    font-size:16px;
                    cursor:pointer;
                    opacity:.7;
                ">
                ×
            </span>
        </div>
    `;

    container.appendChild(field);

    field.querySelector('.o_sign_field_inner').addEventListener('click', (e) => {
        if (e.target.classList.contains('o_remove_field')) return;

        selectField(field);
        openFieldPopup(field);
    });

    field.querySelector('.o_remove_field').addEventListener('click', (e) => {
        e.stopPropagation();
        closeFieldPopup();
        field.remove();
    });

    makeMovable(field);

    return field;
}

// =============================================================
// POPUP
// =============================================================

function openFieldPopup(fieldEl) {
    closeFieldPopup();

    const type = fieldEl.dataset.type;
    const placeholder = fieldEl.dataset.placeholder || '';
    const mandatory = fieldEl.dataset.mandatory === '1';
    const readonly = fieldEl.dataset.readonly === '1';
    const alignment = fieldEl.dataset.alignment || 'left';

    const popup = document.createElement('div');
    popup.id = 'o_sign_field_popup';

    let inputHtml = '';
    if (type === 'date') {
        inputHtml = `<div class="o_popup_row">
            <label>Placeholder</label>
            <textarea id="o_popup_placeholder">${placeholder}</textarea>
        </div>`;
    } else if (type !== 'signature' && type !== 'initial' && type !== 'stamp') {
        inputHtml = `<div class="o_popup_row">
            <label>Placeholder</label>
            <textarea id="o_popup_placeholder">${placeholder}</textarea>
        </div>`;
    }

    const showAlignment = !['signature','initial','stamp','checkbox','radio'].includes(type);
    const alignHtml = showAlignment ? `
        <div class="o_popup_row">
            <label>Alignment</label>
            <div class="o_popup_align_btns">
                <button class="o_align_btn ${alignment==='left'?'active':''}" data-align="left"><i class="fa fa-align-left"></i></button>
                <button class="o_align_btn ${alignment==='center'?'active':''}" data-align="center"><i class="fa fa-align-center"></i></button>
                <button class="o_align_btn ${alignment==='right'?'active':''}" data-align="right"><i class="fa fa-align-right"></i></button>
            </div>
        </div>` : '';

    popup.innerHTML = `
        <div class="o_popup_header">
            <span>${fieldEl.dataset.label}</span>
            <button class="o_popup_close">×</button>
        </div>

        ${inputHtml}
        ${alignHtml}

        <div class="o_popup_row o_popup_checks">
            <label class="o_check_label">
                <input type="checkbox" id="o_popup_mandatory" ${mandatory ? 'checked' : ''}/>
                Mandatory field
            </label>
            <label class="o_check_label">
                <input type="checkbox" id="o_popup_readonly" ${readonly ? 'checked' : ''}/>
                Read-only
            </label>
        </div>

        <div class="o_popup_actions">
            <button id="o_popup_save">Save</button>
            <button id="o_popup_copy" title="Duplicate"><i class="fa fa-copy"></i></button>
            <button id="o_popup_delete" title="Delete"><i class="fa fa-trash"></i></button>
        </div>
    `;

    const backdrop = document.createElement('div');
    backdrop.id = 'o_sign_popup_backdrop';
    backdrop.style.cssText = `position:fixed;inset:0;z-index:9998;`;
    backdrop.addEventListener('click', closeFieldPopup);
    document.body.appendChild(backdrop);
    document.body.appendChild(popup);

    popup.querySelector('.o_popup_close').addEventListener('click', closeFieldPopup);

    popup.querySelectorAll('.o_align_btn').forEach(btn => {
        btn.addEventListener('click', () => {
            popup.querySelectorAll('.o_align_btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    popup.querySelector('#o_popup_save').addEventListener('click', () => {
        const placeholderEl = popup.querySelector('#o_popup_placeholder');
        const newPlaceholder = placeholderEl ? placeholderEl.value : placeholder;
        const newMandatory = popup.querySelector('#o_popup_mandatory').checked ? '1' : '0';
        const newReadonly = popup.querySelector('#o_popup_readonly').checked ? '1' : '0';
        const activeAlign = popup.querySelector('.o_align_btn.active');
        const newAlignment = activeAlign ? activeAlign.dataset.align : alignment;

        fieldEl.dataset.placeholder = newPlaceholder;
        fieldEl.dataset.mandatory = newMandatory;
        fieldEl.dataset.readonly = newReadonly;
        fieldEl.dataset.alignment = newAlignment;

        const textEl = fieldEl.querySelector('.o_field_label_text');
        if (textEl) {
            textEl.textContent = newPlaceholder || fieldEl.dataset.label || capitalize(type);
        }
        closeFieldPopup();
    });

    popup.querySelector('#o_popup_copy').addEventListener('click', () => {
        const container = fieldEl.parentElement;
        const clone = fieldEl.cloneNode(true);
        clone.style.left = (parseInt(fieldEl.style.left) + 20) + 'px';
        clone.style.top = (parseInt(fieldEl.style.top) + 20) + 'px';
        container.appendChild(clone);
        makeMovable(clone);
        clone.querySelector('.o_sign_field_inner').addEventListener('click', (e) => {
            if (e.target.classList.contains('o_remove_field')) return;
            selectField(clone);
            openFieldPopup(clone);
        });
        clone.querySelector('.o_remove_field').addEventListener('click', (e) => {
            e.stopPropagation();
            closeFieldPopup();
            clone.remove();
        });
        closeFieldPopup();
    });

    popup.querySelector('#o_popup_delete').addEventListener('click', () => {
        closeFieldPopup();
        fieldEl.remove();
        selectedField = null;
    });
}

function closeFieldPopup() {
    const popup = document.getElementById('o_sign_field_popup');
    if (popup) popup.remove();
    const backdrop = document.getElementById('o_sign_popup_backdrop');
    if (backdrop) backdrop.remove();
}

// =============================================================
// MOVE
// =============================================================

function makeMovable(el) {
    let sx, sy, sl, st;

    el.addEventListener('mousedown', (e) => {
        if (e.target.classList.contains('o_remove_field')) return;

        sx = e.clientX;
        sy = e.clientY;
        sl = parseInt(el.style.left || 0);
        st = parseInt(el.style.top || 0);

        const onMove = (e) => {
            el.style.left = (sl + e.clientX - sx) + 'px';
            el.style.top = (st + e.clientY - sy) + 'px';
        };

        const onUp = () => {
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
        };

        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    });
}

// =============================================================
// HELPERS
// =============================================================

function capitalize(s) {
    return s ? s[0].toUpperCase() + s.slice(1) : '';
}

// =============================================================
// CSS
// =============================================================

function injectStyles() {
    if (document.getElementById('o_sign_dyn_styles')) return;

    const style = document.createElement('style');
    style.id = 'o_sign_dyn_styles';

    style.textContent = `
        .o_field_selected .o_sign_field_inner {
            outline: 3px solid #ffffff !important;
            box-shadow: 0 0 0 3px #875A7B !important;
        }
    `;

    document.head.appendChild(style);
}

// =============================================================
// BOOT
// =============================================================

function boot() {
    injectStyles();
    buildSidebarFields();
    initPdfPreview();
}

// Har baar naya template open ho tab boot() chalao
let _lastFieldList = null;

function watchSidebar() {
    const el = document.querySelector('.o_sign_field_list');

    if (el && el !== _lastFieldList) {
        _lastFieldList = el;
        document._signPdfRendered = null;  // naye template ke liye reset karo
        boot();
    }

    setTimeout(watchSidebar, 100);
}

watchSidebar();