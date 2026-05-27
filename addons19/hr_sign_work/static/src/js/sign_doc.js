/** @odoo-module **/

/* =============================================================
   SIGN_DOC.JS
   Lightweight enhancements for the sign.doc form view:
   - Wraps the HTML editor in a "paper" style page
   - Lets the user type freely
   - Adds a simple toolbar for common formatting
   ============================================================= */

(function () {
    "use strict";

    function isDocForm() {
        return !!document.querySelector(".o_sign_doc_form");
    }

    function injectStyles() {
        if (document.getElementById("o_sign_doc_styles")) return;
        const s = document.createElement("style");
        s.id = "o_sign_doc_styles";
        s.textContent = `
            .o_sign_doc_form .o_form_sheet_bg { background: #f6f7f9 !important; }
            .o_sign_doc_form .o_form_sheet {
                max-width: 100% !important;
                background: transparent !important;
                box-shadow: none !important;
                padding: 0 !important;
            }
            .o_sign_doc_form .o_sign_doc_sheet { padding: 0 !important; }

            .o_sign_doc_title_wrap {
                background:#fff; padding:14px 24px;
                border-bottom:1px solid #e2e2e2;
            }
            .o_sign_doc_title .o_input,
            .o_sign_doc_title input {
                font-size:22px !important; font-weight:600 !important;
                border:none !important; background:transparent !important;
                padding:4px 0 !important; outline:none !important;
                width:100% !important;
            }
            .o_sign_doc_meta {
                background:#fff; padding:6px 24px 14px;
                border-bottom:1px solid #e2e2e2;
                display:flex; gap:16px; align-items:center;
            }

            #o_sign_doc_toolbar {
                position:sticky; top:0; z-index:50;
                background:#fff; border-bottom:1px solid #e2e2e2;
                padding:6px 24px; display:flex; gap:6px; flex-wrap:wrap;
            }
            #o_sign_doc_toolbar button {
                background:#f1f3f5; border:1px solid #dee2e6;
                width:32px; height:32px; border-radius:4px;
                cursor:pointer; color:#444; font-size:13px;
            }
            #o_sign_doc_toolbar button:hover { background:#e9ecef; }
            #o_sign_doc_toolbar select {
                height:32px; border:1px solid #dee2e6; border-radius:4px;
                padding:0 6px; background:#f1f3f5; color:#444;
            }
            #o_sign_doc_toolbar .sep {
                width:1px; height:24px; background:#dee2e6;
                margin:4px 4px 0;
            }

            .o_sign_doc_page_wrap {
                padding:30px 0; background:#f6f7f9;
                min-height:calc(100vh - 200px);
            }
            .o_sign_doc_page {
                background:#fff;
                width: 816px;            /* US Letter at 96dpi-ish */
                max-width: 100%;
                margin: 0 auto;
                box-shadow: 0 1px 4px rgba(0,0,0,0.12);
                padding: 60px 72px;
                min-height: 1000px;
            }
            .o_sign_doc_editor .note-editing-area,
            .o_sign_doc_editor .o_field_html,
            .o_sign_doc_editor .odoo-editor-editable {
                min-height: 880px;
                font-size: 14px;
                line-height: 1.6;
                color: #222;
            }
            .o_sign_doc_editor .odoo-editor-editable:focus { outline: none; }
        `;
        document.head.appendChild(s);
    }

    // -------- Simple toolbar --------

    const TOOLBAR_BTNS = [
        { cmd: "bold",            icon: "<b>B</b>",            title: "Bold (Ctrl+B)" },
        { cmd: "italic",          icon: "<i>I</i>",            title: "Italic (Ctrl+I)" },
        { cmd: "underline",       icon: "<u>U</u>",            title: "Underline (Ctrl+U)" },
        { cmd: "strikeThrough",   icon: "<s>S</s>",            title: "Strikethrough" },
        { sep: true },
        { cmd: "insertUnorderedList", icon: "•",               title: "Bulleted list" },
        { cmd: "insertOrderedList",   icon: "1.",              title: "Numbered list" },
        { sep: true },
        { cmd: "justifyLeft",     icon: "&#8676;",             title: "Align left" },
        { cmd: "justifyCenter",   icon: "&#8596;",             title: "Align center" },
        { cmd: "justifyRight",    icon: "&#8677;",             title: "Align right" },
        { sep: true },
    ];

    function findEditable() {
        return document.querySelector(
            ".o_sign_doc_editor .odoo-editor-editable, " +
            ".o_sign_doc_editor [contenteditable=true], " +
            ".o_sign_doc_editor .note-editable"
        );
    }

    function injectToolbar() {
        if (document.getElementById("o_sign_doc_toolbar")) return;

        const pageWrap = document.querySelector(".o_sign_doc_page_wrap");
        if (!pageWrap) return;

        const tb = document.createElement("div");
        tb.id = "o_sign_doc_toolbar";

        TOOLBAR_BTNS.forEach(b => {
            if (b.sep) {
                const s = document.createElement("span");
                s.className = "sep";
                tb.appendChild(s);
                return;
            }
            const btn = document.createElement("button");
            btn.type = "button";
            btn.title = b.title;
            btn.innerHTML = b.icon;
            btn.addEventListener("mousedown", (e) => e.preventDefault());
            btn.addEventListener("click", () => {
                const ed = findEditable();
                if (ed) ed.focus();
                document.execCommand(b.cmd, false, null);
            });
            tb.appendChild(btn);
        });

        // Heading select
        const headSel = document.createElement("select");
        headSel.title = "Paragraph style";
        ["Normal", "Heading 1", "Heading 2", "Heading 3"].forEach((label, i) => {
            const o = document.createElement("option");
            o.textContent = label;
            o.value = i === 0 ? "P" : "H" + i;
            headSel.appendChild(o);
        });
        headSel.addEventListener("change", () => {
            const ed = findEditable();
            if (ed) ed.focus();
            document.execCommand("formatBlock", false, "<" + headSel.value + ">");
            headSel.value = "P";
        });
        tb.appendChild(headSel);

        // Font size select
        const sizeSel = document.createElement("select");
        sizeSel.title = "Font size";
        [
            ["Small", "2"], ["Normal", "3"], ["Large", "5"], ["Huge", "7"],
        ].forEach(([label, val]) => {
            const o = document.createElement("option");
            o.textContent = label; o.value = val;
            if (val === "3") o.selected = true;
            sizeSel.appendChild(o);
        });
        sizeSel.addEventListener("change", () => {
            const ed = findEditable();
            if (ed) ed.focus();
            document.execCommand("fontSize", false, sizeSel.value);
        });
        tb.appendChild(sizeSel);

        pageWrap.parentNode.insertBefore(tb, pageWrap);
    }

    // -------- Boot --------

    let lastForm = null;

    function tick() {
        if (isDocForm()) {
            injectStyles();
            const form = document.querySelector(".o_sign_doc_form");
            if (form !== lastForm) {
                lastForm = form;
            }
            injectToolbar();
        } else {
            lastForm = null;
            const tb = document.getElementById("o_sign_doc_toolbar");
            if (tb) tb.remove();
        }
        setTimeout(tick, 400);
    }

    tick();

})();
