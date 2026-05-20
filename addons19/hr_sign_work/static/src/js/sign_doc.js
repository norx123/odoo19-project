/** @odoo-module **/

(function () {

    // Module-level refs so image insert helper can call them
    let drawStripes   = function() {};
    let fixPageBreaks = function() {};

    // ?? Odoo Action Navigate ??????????????????????????????????
    // XML id se action ID fetch karke navigate karta hai
    function odooNavigate(xmlId) {
        fetch('/web/dataset/call_kw', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0', method: 'call', id: 1,
                params: {
                    model: 'ir.model.data',
                    method: 'search_read',
                    args: [[
                        ['module', '=', 'hr_sign_work'],
                        ['name', '=', xmlId],
                        ['model', '=', 'ir.actions.act_window']
                    ]],
                    kwargs: { fields: ['res_id'], limit: 1 }
                }
            })
        })
        .then(r => r.json())
        .then(data => {
            const rec = data.result && data.result[0];
            if (rec && rec.res_id) {
                window.location.href = '/odoo/action-' + rec.res_id;
            } else {
                window.location.href = '/odoo/sign';
            }
        })
        .catch(() => { window.location.href = '/odoo/sign'; });
    }

    function el(tag, attrs, ...children) {
        const node = document.createElement(tag);
        Object.entries(attrs || {}).forEach(([k, v]) => {
            if (k === 'cls') node.className = v;
            else if (k === 'html') node.innerHTML = v;
            else if (k === 'style') node.style.cssText = v;
            else node.setAttribute(k, v);
        });
        children.forEach(c => c && node.appendChild(
            typeof c === 'string' ? document.createTextNode(c) : c
        ));
        return node;
    }

    // ?? Inject hide-style immediately to kill flash of raw Odoo layout ??
    (function injectHideStyle() {
        if (document.getElementById('gdoc_hide_style')) return;
        const s = document.createElement('style');
        s.id = 'gdoc_hide_style';
        // While on a sign.doc form, hide the raw Odoo page/chrome instantly.
        // The shell will replace them. Visibility:hidden keeps layout so
        // Odoo can still measure & render the editor in background.
        s.textContent = [
            '.o_sign_doc_form .o_sign_doc_page_wrap{visibility:hidden!important}',
            '.o_sign_doc_form .o_sign_doc_title_wrap{visibility:hidden!important}',
            '.o_sign_doc_form .o_sign_doc_meta{visibility:hidden!important}',
        ].join('\n');
        (document.head || document.documentElement).appendChild(s);
    })();

    function isSignDocForm() {
        return !!(document.querySelector('.o_sign_doc_page_wrap') ||
                  document.querySelector('.o_sign_doc_form'));
    }

    function alreadyDone() {
        return !!document.getElementById('gdoc_shell');
    }

    function destroyShell() {
        const shell = document.getElementById('gdoc_shell');
        if (shell) shell.remove();

        // Remove hide-style ? we are no longer on doc form
        const hs = document.getElementById('gdoc_hide_style');
        if (hs) hs.remove();

        // Restore Odoo chrome
        const cp = document.querySelector('.o_control_panel');
        if (cp) cp.style.display = '';
        const navbar = document.querySelector('.o_main_navbar');
        if (navbar) navbar.style.display = '';

        // Restore page wrap
        const pageWrap = document.querySelector('.o_sign_doc_page_wrap');
        const sheet    = document.querySelector('.o_sign_doc_sheet, .o_form_sheet');
        if (pageWrap && sheet && !sheet.contains(pageWrap)) sheet.appendChild(pageWrap);
        if (pageWrap) pageWrap.style.cssText = '';

        // Restore title/meta
        const titleWrap = document.querySelector('.o_sign_doc_title_wrap');
        const metaWrap  = document.querySelector('.o_sign_doc_meta');
        if (titleWrap) titleWrap.style.display = '';
        if (metaWrap)  metaWrap.style.display  = '';
    }

    // ── IMAGE INSERT DIALOG ──────────────────────────────────────────
    function showImageInsertDialog() {
        // Remove existing dialog if any
        const existing = document.getElementById('gdoc_img_dialog');
        if (existing) existing.remove();

        const overlay = document.createElement('div');
        overlay.id = 'gdoc_img_dialog';
        overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.45);z-index:999999;display:flex;align-items:center;justify-content:center;';

        overlay.innerHTML = `
            <div style="background:#fff;border-radius:12px;width:480px;max-width:95vw;box-shadow:0 8px 40px rgba(0,0,0,0.28);overflow:hidden;font-family:Arial,sans-serif;">
                <div style="background:#1a73e8;color:#fff;padding:14px 18px;display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:15px;font-weight:600;">Insert Image</span>
                    <button id="gdoc_img_close" style="background:none;border:none;color:#fff;font-size:22px;cursor:pointer;line-height:1;opacity:0.85;">×</button>
                </div>
                <div style="padding:20px 22px;">
                    <!-- TAB BUTTONS -->
                    <div style="display:flex;gap:0;border:1px solid #dadce0;border-radius:8px;overflow:hidden;margin-bottom:18px;">
                        <button id="gdoc_tab_upload" style="flex:1;padding:9px;background:#1a73e8;color:#fff;border:none;font-size:13px;font-weight:600;cursor:pointer;">Upload from device</button>
                        <button id="gdoc_tab_url" style="flex:1;padding:9px;background:#f1f3f4;color:#444;border:none;font-size:13px;font-weight:500;cursor:pointer;border-left:1px solid #dadce0;">Insert from URL</button>
                    </div>

                    <!-- UPLOAD PANEL -->
                    <div id="gdoc_panel_upload">
                        <div id="gdoc_drop_zone" style="border:2px dashed #1a73e8;border-radius:10px;padding:36px 20px;text-align:center;cursor:pointer;background:#f8fbff;transition:background 0.15s;">
                            <div style="font-size:40px;margin-bottom:8px;">📁</div>
                            <div style="font-size:14px;font-weight:600;color:#1a73e8;margin-bottom:4px;">Click to choose image</div>
                            <div style="font-size:12px;color:#888;">or drag & drop here</div>
                            <div style="font-size:11px;color:#aaa;margin-top:6px;">PNG, JPG, GIF, WebP, SVG supported</div>
                        </div>
                        <input id="gdoc_file_input" type="file" accept="image/*" style="display:none;">
                        <div id="gdoc_img_preview" style="display:none;margin-top:14px;text-align:center;">
                            <img id="gdoc_preview_img" src="" style="max-width:100%;max-height:180px;border-radius:6px;border:1px solid #dadce0;">
                            <div id="gdoc_preview_name" style="font-size:12px;color:#666;margin-top:6px;"></div>
                        </div>
                    </div>

                    <!-- URL PANEL -->
                    <div id="gdoc_panel_url" style="display:none;">
                        <input id="gdoc_url_input" type="text" placeholder="Paste image URL here..." style="width:100%;border:1px solid #dadce0;border-radius:8px;padding:10px 12px;font-size:14px;outline:none;box-sizing:border-box;font-family:inherit;">
                        <div id="gdoc_url_preview" style="display:none;margin-top:14px;text-align:center;">
                            <img id="gdoc_url_preview_img" src="" style="max-width:100%;max-height:180px;border-radius:6px;border:1px solid #dadce0;">
                        </div>
                    </div>

                    <!-- IMAGE SIZE OPTIONS -->
                    <div style="margin-top:16px;display:flex;flex-direction:column;gap:8px;">
                        <label style="font-size:12px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.5px;">Size</label>
                        <div style="display:flex;gap:8px;flex-wrap:wrap;">
                            <button class="gdoc_size_btn gdoc_size_active" data-size="original" style="padding:5px 12px;border-radius:20px;border:1px solid #1a73e8;background:#e8f0fe;color:#1a73e8;font-size:12px;cursor:pointer;">Original</button>
                            <button class="gdoc_size_btn" data-size="small" style="padding:5px 12px;border-radius:20px;border:1px solid #dadce0;background:#fff;color:#444;font-size:12px;cursor:pointer;">Small (25%)</button>
                            <button class="gdoc_size_btn" data-size="medium" style="padding:5px 12px;border-radius:20px;border:1px solid #dadce0;background:#fff;color:#444;font-size:12px;cursor:pointer;">Medium (50%)</button>
                            <button class="gdoc_size_btn" data-size="large" style="padding:5px 12px;border-radius:20px;border:1px solid #dadce0;background:#fff;color:#444;font-size:12px;cursor:pointer;">Full width</button>
                        </div>
                    </div>

                    <!-- ALIGNMENT OPTIONS -->
                    <div style="margin-top:14px;display:flex;flex-direction:column;gap:8px;">
                        <label style="font-size:12px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.5px;">Alignment</label>
                        <div style="display:flex;gap:8px;">
                            <button class="gdoc_align_btn gdoc_align_active" data-align="none" style="padding:5px 12px;border-radius:20px;border:1px solid #1a73e8;background:#e8f0fe;color:#1a73e8;font-size:12px;cursor:pointer;">Inline</button>
                            <button class="gdoc_align_btn" data-align="left" style="padding:5px 12px;border-radius:20px;border:1px solid #dadce0;background:#fff;color:#444;font-size:12px;cursor:pointer;">Float Left</button>
                            <button class="gdoc_align_btn" data-align="center" style="padding:5px 12px;border-radius:20px;border:1px solid #dadce0;background:#fff;color:#444;font-size:12px;cursor:pointer;">Center</button>
                            <button class="gdoc_align_btn" data-align="right" style="padding:5px 12px;border-radius:20px;border:1px solid #dadce0;background:#fff;color:#444;font-size:12px;cursor:pointer;">Float Right</button>
                        </div>
                    </div>
                </div>
                <div style="padding:14px 22px 18px;display:flex;justify-content:flex-end;gap:10px;border-top:1px solid #f1f3f4;">
                    <button id="gdoc_img_cancel" style="padding:8px 22px;border-radius:6px;border:1px solid #dadce0;background:#fff;font-size:13px;cursor:pointer;color:#444;">Cancel</button>
                    <button id="gdoc_img_insert" style="padding:8px 22px;border-radius:6px;border:none;background:#1a73e8;color:#fff;font-size:13px;font-weight:600;cursor:pointer;">Insert</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        let selectedSize = 'original';
        let selectedAlign = 'none';
        let currentSrc = '';

        // Tab switching
        overlay.querySelector('#gdoc_tab_upload').addEventListener('click', () => {
            overlay.querySelector('#gdoc_panel_upload').style.display = '';
            overlay.querySelector('#gdoc_panel_url').style.display = 'none';
            overlay.querySelector('#gdoc_tab_upload').style.cssText += 'background:#1a73e8;color:#fff;';
            overlay.querySelector('#gdoc_tab_url').style.cssText += 'background:#f1f3f4;color:#444;';
        });
        overlay.querySelector('#gdoc_tab_url').addEventListener('click', () => {
            overlay.querySelector('#gdoc_panel_upload').style.display = 'none';
            overlay.querySelector('#gdoc_panel_url').style.display = '';
            overlay.querySelector('#gdoc_tab_url').style.cssText += 'background:#1a73e8;color:#fff;';
            overlay.querySelector('#gdoc_tab_upload').style.cssText += 'background:#f1f3f4;color:#444;';
        });

        // Size buttons
        overlay.querySelectorAll('.gdoc_size_btn').forEach(btn => {
            btn.addEventListener('click', () => {
                overlay.querySelectorAll('.gdoc_size_btn').forEach(b => {
                    b.style.cssText = 'padding:5px 12px;border-radius:20px;border:1px solid #dadce0;background:#fff;color:#444;font-size:12px;cursor:pointer;';
                });
                btn.style.cssText = 'padding:5px 12px;border-radius:20px;border:1px solid #1a73e8;background:#e8f0fe;color:#1a73e8;font-size:12px;cursor:pointer;';
                selectedSize = btn.dataset.size;
            });
        });

        // Align buttons
        overlay.querySelectorAll('.gdoc_align_btn').forEach(btn => {
            btn.addEventListener('click', () => {
                overlay.querySelectorAll('.gdoc_align_btn').forEach(b => {
                    b.style.cssText = 'padding:5px 12px;border-radius:20px;border:1px solid #dadce0;background:#fff;color:#444;font-size:12px;cursor:pointer;';
                });
                btn.style.cssText = 'padding:5px 12px;border-radius:20px;border:1px solid #1a73e8;background:#e8f0fe;color:#1a73e8;font-size:12px;cursor:pointer;';
                selectedAlign = btn.dataset.align;
            });
        });

        // File drop zone
        const dropZone = overlay.querySelector('#gdoc_drop_zone');
        const fileInput = overlay.querySelector('#gdoc_file_input');

        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.style.background = '#e8f0fe'; });
        dropZone.addEventListener('dragleave', () => { dropZone.style.background = '#f8fbff'; });
        dropZone.addEventListener('drop', e => {
            e.preventDefault();
            dropZone.style.background = '#f8fbff';
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) loadFilePreview(file);
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files[0]) loadFilePreview(fileInput.files[0]);
        });

        function loadFilePreview(file) {
            const reader = new FileReader();
            reader.onload = ev => {
                currentSrc = ev.target.result;
                overlay.querySelector('#gdoc_preview_img').src = currentSrc;
                overlay.querySelector('#gdoc_preview_name').textContent = file.name;
                overlay.querySelector('#gdoc_img_preview').style.display = '';
                dropZone.style.display = 'none';
            };
            reader.readAsDataURL(file);
        }

        // URL input preview
        let urlTimer;
        overlay.querySelector('#gdoc_url_input').addEventListener('input', function() {
            clearTimeout(urlTimer);
            urlTimer = setTimeout(() => {
                const url = this.value.trim();
                if (url) {
                    const prevImg = overlay.querySelector('#gdoc_url_preview_img');
                    prevImg.src = url;
                    prevImg.onload = () => { currentSrc = url; overlay.querySelector('#gdoc_url_preview').style.display = ''; };
                    prevImg.onerror = () => { overlay.querySelector('#gdoc_url_preview').style.display = 'none'; currentSrc = ''; };
                }
            }, 500);
        });

        // Close
        const closeDialog = () => overlay.remove();
        overlay.querySelector('#gdoc_img_close').addEventListener('click', closeDialog);
        overlay.querySelector('#gdoc_img_cancel').addEventListener('click', closeDialog);
        overlay.addEventListener('click', e => { if (e.target === overlay) closeDialog(); });

        // Insert
        overlay.querySelector('#gdoc_img_insert').addEventListener('click', () => {
            const src = currentSrc || overlay.querySelector('#gdoc_url_input').value.trim();
            if (!src) { alert('Please select or enter an image.'); return; }
            insertImageIntoEditor(src, selectedSize, selectedAlign);
            closeDialog();
        });
    }

    function insertImageIntoEditor(src, size, align) {
        const mainEd = document.getElementById('gdoc_main_editor');
        if (!mainEd) return;

        // Size
        let widthStyle = 'max-width:100%;';
        if (size === 'small')  widthStyle = 'width:25%;';
        if (size === 'medium') widthStyle = 'width:50%;';
        if (size === 'large')  widthStyle = 'width:100%;';

        // Alignment wrapper styles
        let wrapStyle = 'display:block;margin:8px 0;';
        let imgExtraStyle = '';

        if (align === 'left') {
            wrapStyle = 'display:block;float:left;margin:4px 12px 4px 0;';
        } else if (align === 'right') {
            wrapStyle = 'display:block;float:right;margin:4px 0 4px 12px;';
        } else if (align === 'center') {
            wrapStyle = 'display:flex;justify-content:center;margin:8px 0;';
        }

        // Build resizable image HTML
        const imgHtml = `<div class="gdoc_img_wrap" contenteditable="false" style="${wrapStyle}cursor:default;" data-gdoc-img="1">
            <img src="${src}" style="${widthStyle}height:auto;display:block;border-radius:2px;cursor:nwse-resize;max-width:100%;" 
                 class="gdoc_inserted_img"
                 draggable="false">
        </div><p><br></p>`;

        mainEd.focus();
        const sel = window.getSelection();
        if (sel && sel.rangeCount > 0) {
            const range = sel.getRangeAt(0);
            const frag = range.createContextualFragment(imgHtml);
            range.insertNode(frag);
            range.collapse(false);
        } else {
            mainEd.insertAdjacentHTML('beforeend', imgHtml);
        }

        // Trigger reflow
        setTimeout(() => {
            if (typeof drawStripes === 'function') drawStripes();
            if (typeof fixPageBreaks === 'function') fixPageBreaks();
        }, 200);
    }

    // ── IMAGE TOOLBAR (click on image to show resize/align options) ──
    function setupImageToolbar(mainEd) {
        const toolbar = document.createElement('div');
        toolbar.id = 'gdoc_img_toolbar';
        toolbar.style.cssText = 'display:none;position:fixed;z-index:99999;background:#fff;border:1px solid #dadce0;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,0.18);padding:6px 10px;gap:6px;align-items:center;font-size:12px;';
        toolbar.innerHTML = `
            <span style="color:#888;font-size:11px;margin-right:4px;">Size:</span>
            <button data-size="25%"  title="Small"      style="padding:4px 8px;border-radius:4px;border:1px solid #dadce0;background:#fff;cursor:pointer;font-size:11px;">S</button>
            <button data-size="50%"  title="Medium"     style="padding:4px 8px;border-radius:4px;border:1px solid #dadce0;background:#fff;cursor:pointer;font-size:11px;">M</button>
            <button data-size="75%"  title="Large"      style="padding:4px 8px;border-radius:4px;border:1px solid #dadce0;background:#fff;cursor:pointer;font-size:11px;">L</button>
            <button data-size="100%" title="Full width" style="padding:4px 8px;border-radius:4px;border:1px solid #dadce0;background:#fff;cursor:pointer;font-size:11px;">Full</button>
            <div style="width:1px;height:18px;background:#dadce0;margin:0 4px;"></div>
            <span style="color:#888;font-size:11px;margin-right:4px;">Align:</span>
            <button data-align="left"   title="Float left"  style="padding:4px 8px;border-radius:4px;border:1px solid #dadce0;background:#fff;cursor:pointer;font-size:11px;">⬅</button>
            <button data-align="center" title="Center"      style="padding:4px 8px;border-radius:4px;border:1px solid #dadce0;background:#fff;cursor:pointer;font-size:11px;">↔</button>
            <button data-align="right"  title="Float right" style="padding:4px 8px;border-radius:4px;border:1px solid #dadce0;background:#fff;cursor:pointer;font-size:11px;">➡</button>
            <button data-align="none"   title="Inline"      style="padding:4px 8px;border-radius:4px;border:1px solid #dadce0;background:#fff;cursor:pointer;font-size:11px;">☰</button>
            <div style="width:1px;height:18px;background:#dadce0;margin:0 4px;"></div>
            <button id="gdoc_img_delete" title="Delete image" style="padding:4px 8px;border-radius:4px;border:1px solid #fadce0;background:#fff3f3;cursor:pointer;font-size:11px;color:#d93025;">🗑</button>
        `;
        document.body.appendChild(toolbar);

        let activeImg = null;
        let activeWrap = null;

        function showToolbar(img, wrap) {
            activeImg = img;
            activeWrap = wrap;
            const rect = img.getBoundingClientRect();
            toolbar.style.display = 'flex';
            toolbar.style.top = (rect.top - 48) + 'px';
            toolbar.style.left = rect.left + 'px';
            img.style.outline = '2px solid #1a73e8';
        }

        function hideToolbar() {
            toolbar.style.display = 'none';
            if (activeImg) activeImg.style.outline = '';
            activeImg = null; activeWrap = null;
        }

        mainEd.addEventListener('click', e => {
            if (e.target.classList.contains('gdoc_inserted_img')) {
                const wrap = e.target.closest('.gdoc_img_wrap');
                showToolbar(e.target, wrap || e.target.parentElement);
                e.stopPropagation();
            }
        });

        document.addEventListener('click', e => {
            if (!toolbar.contains(e.target) && !e.target.classList.contains('gdoc_inserted_img')) {
                hideToolbar();
            }
        });

        // Size buttons
        toolbar.querySelectorAll('[data-size]').forEach(btn => {
            btn.addEventListener('click', e => {
                e.stopPropagation();
                if (!activeImg) return;
                activeImg.style.width = btn.dataset.size;
                activeImg.style.maxWidth = '100%';
                setTimeout(() => { drawStripes(); fixPageBreaks(); }, 100);
            });
        });

        // Align buttons
        toolbar.querySelectorAll('[data-align]').forEach(btn => {
            btn.addEventListener('click', e => {
                e.stopPropagation();
                if (!activeWrap) return;
                const a = btn.dataset.align;
                if (a === 'left')   { activeWrap.style.cssText = 'display:block;float:left;margin:4px 12px 4px 0;cursor:default;'; }
                if (a === 'right')  { activeWrap.style.cssText = 'display:block;float:right;margin:4px 0 4px 12px;cursor:default;'; }
                if (a === 'center') { activeWrap.style.cssText = 'display:flex;justify-content:center;margin:8px 0;cursor:default;'; }
                if (a === 'none')   { activeWrap.style.cssText = 'display:block;margin:8px 0;cursor:default;'; }
                setTimeout(() => { drawStripes(); fixPageBreaks(); }, 100);
            });
        });

        // Delete
        toolbar.querySelector('#gdoc_img_delete').addEventListener('click', e => {
            e.stopPropagation();
            if (activeWrap) activeWrap.remove();
            hideToolbar();
            setTimeout(() => { drawStripes(); fixPageBreaks(); }, 100);
        });
    }

    function buildShell() {
        const shell = el('div', { id: 'gdoc_shell', cls: 'gdoc_shell' });

        // ?? ODOO-STYLE PURPLE NAVBAR (Sign | Documents | Templates | Configuration) ??
        const odooNavbar = document.createElement('div');
        odooNavbar.className = 'gdoc_odoo_navbar';
        odooNavbar.innerHTML = `
            <div class="gdoc_odoo_navbar_inner">
                <span class="gdoc_odoo_app_name">Sign</span>
                <nav class="gdoc_odoo_nav_tabs">
                    <a class="gdoc_odoo_tab" id="gnav_documents" href="#">Documents</a>
                    <a class="gdoc_odoo_tab" id="gnav_templates" href="#">Templates</a>
                    <a class="gdoc_odoo_tab" id="gnav_configuration" href="#">Configuration</a>
                </nav>
            </div>
        `;
        // Click handlers
        odooNavbar.querySelector('#gnav_documents').addEventListener('click', e => {
            e.preventDefault(); odooNavigate('action_sign_doc');
        });
        odooNavbar.querySelector('#gnav_templates').addEventListener('click', e => {
            e.preventDefault(); odooNavigate('action_sign_template');
        });
        odooNavbar.querySelector('#gnav_configuration').addEventListener('click', e => {
            e.preventDefault(); odooNavigate('action_sign_settings');
        });

        // ?? TOP BAR ??????????????????????????????????????????????
        const topBar = el('div', { cls: 'gdoc_topbar' });

        const logo = document.createElement('div');
        logo.className = 'gdoc_logo';
        logo.innerHTML = `
            <svg width="36" height="36" viewBox="0 0 48 48">
                <path fill="#4285F4" d="M30 2H10a2 2 0 0 0-2 2v40a2 2 0 0 0 2 2h28a2 2 0 0 0 2-2V18L30 2z"/>
                <path fill="#A8C7FA" d="M30 2v16h16L30 2z"/>
                <path fill="#fff" d="M14 28h20v2H14zm0 6h20v2H14zm0-12h8v2h-8z"/>
            </svg>`;

        const titleInp = el('input', {
            cls: 'gdoc_title_input',
            type: 'text',
            placeholder: 'Untitled document',
        });

        const titleIcons = document.createElement('div');
        titleIcons.className = 'gdoc_title_icons';
        titleIcons.innerHTML = `
            <button class="gdoc_icon_btn" title="Star">
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#5f6368" d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
            </button>
            <button class="gdoc_icon_btn" title="Move to folder">
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#5f6368" d="M20 6h-8l-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2z"/></svg>
            </button>
            <button class="gdoc_icon_btn" title="Saved to Drive">
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#5f6368" d="M19.35 10.04A7.49 7.49 0 0 0 12 4C9.11 4 6.6 5.64 5.35 8.04A5.994 5.994 0 0 0 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/></svg>
            </button>`;

        const topRight = document.createElement('div');
        topRight.className = 'gdoc_topbar_right';
        topRight.innerHTML = `
            <button class="gdoc_share_btn" id="gdoc_share_btn">
                <svg width="16" height="16" viewBox="0 0 24 24" style="margin-right:6px"><path fill="currentColor" d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z"/></svg>
                Share
            </button>
            <div class="gdoc_avatar">A</div>`;

        topBar.append(logo, titleInp, titleIcons, topRight);

        topRight.querySelector('#gdoc_share_btn').addEventListener('click', () => {
            const odooShare = document.querySelector('button[name="action_share"]');
            if (odooShare) odooShare.click();
        });

        // ?? MENU BAR ? fully working dropdowns ???????????????????
        const menuBar = el('div', { cls: 'gdoc_menubar' });

        const menuData = {
            'File': [
                { label: 'New', action: () => { window.open(location.href.replace(/\/\d+$/, '/new'), '_blank'); } },
                { label: 'Print', shortcut: 'Ctrl+P', action: () => window.print() },
                { sep: true },
                { label: 'Download as PDF', action: () => { window.print(); } },
            ],
            'Edit': [
                { label: 'Undo', shortcut: 'Ctrl+Z', action: () => document.execCommand('undo') },
                { label: 'Redo', shortcut: 'Ctrl+Y', action: () => document.execCommand('redo') },
                { sep: true },
                { label: 'Cut', shortcut: 'Ctrl+X', action: () => document.execCommand('cut') },
                { label: 'Copy', shortcut: 'Ctrl+C', action: () => document.execCommand('copy') },
                { label: 'Paste', shortcut: 'Ctrl+V', action: () => document.execCommand('paste') },
                { sep: true },
                { label: 'Select all', shortcut: 'Ctrl+A', action: () => document.execCommand('selectAll') },
                { sep: true },
                { label: 'Find and replace', shortcut: 'Ctrl+H', action: () => {
                    const find = prompt('Find:');
                    if (!find) return;
                    const replace = prompt('Replace with:');
                    if (replace === null) return;
                    const editor = document.querySelector('.odoo-editor-editable, .o_editable');
                    if (editor) editor.innerHTML = editor.innerHTML.split(find).join(replace);
                }},
            ],
            'View': [
                { label: 'Show ruler', action: () => {
                    const r = document.querySelector('.gdoc_ruler_wrap');
                    if (r) r.style.display = r.style.display === 'none' ? '' : 'none';
                }},
                { label: 'Full screen', action: () => {
                    if (!document.fullscreenElement) document.documentElement.requestFullscreen();
                    else document.exitFullscreen();
                }},
            ],
            'Insert': [
                { label: 'Link', shortcut: 'Ctrl+K', action: () => {
                    const url = prompt('Enter URL:');
                    if (url) document.execCommand('createLink', false, url);
                }},
                { label: 'Horizontal line', action: () => document.execCommand('insertHorizontalRule') },
                { sep: true },
                { label: 'Table', action: () => {
                    const rows = parseInt(prompt('Rows:', '3')) || 3;
                    const cols = parseInt(prompt('Columns:', '3')) || 3;
                    let html = '<table border="1" style="border-collapse:collapse;width:100%">';
                    for (let r = 0; r < rows; r++) {
                        html += '<tr>';
                        for (let c = 0; c < cols; c++) html += '<td style="padding:6px;min-width:60px">&nbsp;</td>';
                        html += '</tr>';
                    }
                    html += '</table><p><br></p>';
                    document.execCommand('insertHTML', false, html);
                }},
                { label: '🖼️ Insert Image', shortcut: 'Ctrl+Shift+I', action: () => showImageInsertDialog() },
                { sep: true },
                { label: 'Comment', shortcut: 'Ctrl+Alt+M', action: () => {
                    const sel = window.getSelection();
                    if (!sel.toString()) { alert('Please select text first to add a comment.'); return; }
                    const note = prompt('Add comment:');
                    if (note) document.execCommand('insertHTML', false,
                        `<mark title="${note}" style="background:#fff2cc">${sel.toString()}</mark>`);
                }},
            ],
            'Format': [
                { label: 'Bold', shortcut: 'Ctrl+B', action: () => document.execCommand('bold') },
                { label: 'Italic', shortcut: 'Ctrl+I', action: () => document.execCommand('italic') },
                { label: 'Underline', shortcut: 'Ctrl+U', action: () => document.execCommand('underline') },
                { label: 'Strikethrough', action: () => document.execCommand('strikeThrough') },
                { sep: true },
                { label: 'Heading 1', action: () => document.execCommand('formatBlock', false, 'h1') },
                { label: 'Heading 2', action: () => document.execCommand('formatBlock', false, 'h2') },
                { label: 'Heading 3', action: () => document.execCommand('formatBlock', false, 'h3') },
                { label: 'Normal text', action: () => document.execCommand('formatBlock', false, 'p') },
                { sep: true },
                { label: 'Align left', action: () => document.execCommand('justifyLeft') },
                { label: 'Align center', action: () => document.execCommand('justifyCenter') },
                { label: 'Align right', action: () => document.execCommand('justifyRight') },
                { sep: true },
                { label: 'Clear formatting', shortcut: 'Ctrl+\\', action: () => document.execCommand('removeFormat') },
            ],
            'Tools': [
                { label: 'Word count', action: () => {
                    const editor = document.querySelector('.odoo-editor-editable, .o_editable');
                    const text = editor ? editor.innerText : '';
                    const words = text.trim().split(/\s+/).filter(w => w).length;
                    const chars = text.length;
                    alert(`Words: ${words}\nCharacters: ${chars}`);
                }},
                { label: 'Spelling & grammar (Ctrl+Alt+X)', action: () => alert('Use browser spell check (right-click on underlined words).') },
            ],
            'Extensions': [
                { label: 'No extensions available', action: () => {} },
            ],
            'Help': [
                { label: 'Keyboard shortcuts', action: () => {
                    alert('Ctrl+B Bold\nCtrl+I Italic\nCtrl+U Underline\nCtrl+Z Undo\nCtrl+Y Redo\nCtrl+A Select All\nCtrl+K Insert Link\nCtrl+P Print');
                }},
            ],
        };

        // Dropdown close helper
        function closeAllMenus() {
            document.querySelectorAll('.gdoc_dropdown').forEach(d => d.remove());
        }

        Object.entries(menuData).forEach(([name, items]) => {
            const btn = el('button', { cls: 'gdoc_menu_item' }, name);
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                closeAllMenus();
                const dropdown = document.createElement('div');
                dropdown.className = 'gdoc_dropdown';
                items.forEach(item => {
                    if (item.sep) {
                        dropdown.appendChild(el('div', { cls: 'gdoc_dropdown_sep' }));
                        return;
                    }
                    const row = document.createElement('div');
                    row.className = 'gdoc_dropdown_item';
                    row.innerHTML = `<span>${item.label}</span>${item.shortcut ? `<span class="gdoc_dropdown_shortcut">${item.shortcut}</span>` : ''}`;
                    row.addEventListener('click', (ev) => {
                        ev.stopPropagation();
                        closeAllMenus();
                        item.action();
                    });
                    dropdown.appendChild(row);
                });
                const rect = btn.getBoundingClientRect();
                dropdown.style.cssText = `position:fixed;top:${rect.bottom}px;left:${rect.left}px;z-index:99999;`;
                document.body.appendChild(dropdown);
            });
            menuBar.appendChild(btn);
        });

        document.addEventListener('click', closeAllMenus);

        // ?? TOOLBAR ??????????????????????????????????????????????
        const toolbar = document.createElement('div');
        toolbar.className = 'gdoc_toolbar';
        toolbar.innerHTML = `
            <button class="gdoc_tb_btn" title="Undo" onclick="document.execCommand('undo')">
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#444" d="M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C21.08 11.03 17.15 8 12.5 8z"/></svg>
            </button>
            <button class="gdoc_tb_btn" title="Redo" onclick="document.execCommand('redo')">
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#444" d="M18.4 10.6C16.55 8.99 14.15 8 11.5 8c-4.65 0-8.58 3.03-9.96 7.22L3.9 16c1.05-3.19 4.05-5.5 7.6-5.5 1.95 0 3.73.72 5.12 1.88L13 16h9V7l-3.6 3.6z"/></svg>
            </button>
            <button class="gdoc_tb_btn" title="Print" onclick="window.print()">
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#444" d="M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3zm-3 11H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm-1-9H6v4h12V3z"/></svg>
            </button>
            <div class="gdoc_tb_sep"></div>
            <select class="gdoc_tb_select" style="width:130px" onchange="document.execCommand('formatBlock',false,this.value)">
                <option value="p">Normal text</option>
                <option value="h1">Heading 1</option>
                <option value="h2">Heading 2</option>
                <option value="h3">Heading 3</option>
                <option value="h4">Heading 4</option>
            </select>
            <div class="gdoc_tb_sep"></div>
            <select class="gdoc_tb_select" style="width:110px" onchange="document.execCommand('fontName',false,this.value)">
                <option value="Arial">Arial</option>
                <option value="Times New Roman">Times New Roman</option>
                <option value="Courier New">Courier New</option>
                <option value="Georgia">Georgia</option>
                <option value="Verdana">Verdana</option>
            </select>
            <div class="gdoc_tb_sep"></div>
            <button class="gdoc_tb_btn" onclick="document.execCommand('fontSize',false,'2')">?</button>
            <input class="gdoc_font_size" type="number" value="11" min="6" max="96"/>
            <button class="gdoc_tb_btn" onclick="document.execCommand('fontSize',false,'4')">+</button>
            <div class="gdoc_tb_sep"></div>
            <button class="gdoc_tb_btn" title="Bold" onclick="document.execCommand('bold')"><b>B</b></button>
            <button class="gdoc_tb_btn" title="Italic" onclick="document.execCommand('italic')"><i>I</i></button>
            <button class="gdoc_tb_btn" title="Underline" onclick="document.execCommand('underline')"><u>U</u></button>
            <button class="gdoc_tb_btn" title="Strikethrough" onclick="document.execCommand('strikeThrough')"><s>S</s></button>
            <div class="gdoc_tb_sep"></div>
            <button class="gdoc_tb_btn" title="Align left" onclick="document.execCommand('justifyLeft')">
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#444" d="M15 15H3v2h12v-2zm0-8H3v2h12V7zM3 13h18v-2H3v2zm0 8h18v-2H3v2zM3 3v2h18V3H3z"/></svg>
            </button>
            <button class="gdoc_tb_btn" title="Center" onclick="document.execCommand('justifyCenter')">
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#444" d="M7 15v2h10v-2H7zm-4 6h18v-2H3v2zm0-8h18v-2H3v2zm4-6v2h10V7H7zM3 3v2h18V3H3z"/></svg>
            </button>
            <button class="gdoc_tb_btn" title="Align right" onclick="document.execCommand('justifyRight')">
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#444" d="M3 21h18v-2H3v2zm6-4h12v-2H9v2zm-6-4h18v-2H3v2zm6-4h12V7H9v2zM3 3v2h18V3H3z"/></svg>
            </button>
            <div class="gdoc_tb_sep"></div>
            <button class="gdoc_tb_btn" title="Bullet list" onclick="document.execCommand('insertUnorderedList')">
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#444" d="M4 10.5c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5 1.5-.67 1.5-1.5-.67-1.5-1.5-1.5zm0-6c-.83 0-1.5.67-1.5 1.5S3.17 7.5 4 7.5 5.5 6.83 5.5 6 4.83 4.5 4 4.5zm0 12c-.83 0-1.5.68-1.5 1.5s.68 1.5 1.5 1.5 1.5-.68 1.5-1.5-.67-1.5-1.5-1.5zM7 19h14v-2H7v2zm0-6h14v-2H7v2zm0-8v2h14V5H7z"/></svg>
            </button>
            <button class="gdoc_tb_btn" title="Numbered list" onclick="document.execCommand('insertOrderedList')">
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#444" d="M2 17h2v.5H3v1h1v.5H2v1h3v-4H2v1zm1-9h1V4H2v1h1v3zm-1 3h1.8L2 13.1v.9h3v-1H3.2L5 10.9V10H2v1zm5-7v2h14V4H7zm0 14h14v-2H7v2zm0-6h14v-2H7v2z"/></svg>
            </button>
            <div class="gdoc_tb_sep"></div>
            <button class="gdoc_tb_btn" id="gdoc_tb_img_btn" title="Insert Image (Ctrl+Shift+I)" style="font-size:17px;padding:4px 6px;">🖼️</button>`;

        // ?? RULER ????????????????????????????????????????????????
        const rulerWrap = el('div', { cls: 'gdoc_ruler_wrap' });
        const ruler = el('canvas', { cls: 'gdoc_ruler', id: 'gdoc_ruler', width: '1200', height: '22' });
        rulerWrap.appendChild(ruler);
        setTimeout(() => {
            const ctx = ruler.getContext('2d');
            ctx.fillStyle = '#bdc1c6';
            ctx.font = '9px Arial';
            ctx.textAlign = 'center';
            const startX = 290;
            for (let i = 0; i <= 8; i++) {
                const x = startX + i * 96;
                ctx.fillRect(x, 14, 1, 8);
                if (i > 0 && i < 8) ctx.fillText(i + '"', x, 11);
                if (i < 8) ctx.fillRect(x + 48, 17, 1, 5);
            }
        }, 300);

        // ?? BODY ?????????????????????????????????????????????????
        const body = el('div', { cls: 'gdoc_body' });

        // LEFT SIDEBAR
        const sidebar = document.createElement('div');
        sidebar.className = 'gdoc_sidebar';
        sidebar.innerHTML = `
            <button class="gdoc_sidebar_back" id="gdoc_back_btn" title="Back">
                <svg width="20" height="20" viewBox="0 0 24 24"><path fill="#444" d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
            </button>

            <div class="gdoc_sidebar_header">
                <span class="gdoc_sidebar_title">Document tabs</span>
                <button class="gdoc_sidebar_add" title="Add tab">+</button>
            </div>
            <div class="gdoc_tab_list">
                <div class="gdoc_tab gdoc_tab_active">
                    <svg width="14" height="14" viewBox="0 0 24 24" style="margin-right:6px;flex-shrink:0"><path fill="#4285F4" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/></svg>
                    Tab 1
                    <button class="gdoc_tab_more">?</button>
                </div>
                <div class="gdoc_tab_hint">Headings you add to the document will appear here.</div>
            </div>`;

        sidebar.querySelector('#gdoc_back_btn').addEventListener('click', () => {
            if (window.history.length > 1) {
                window.history.back();
            } else {
                odooNavigate('action_sign_doc');
            }
        });

        // PAGE AREA ? scrollable grey canvas
        const pageArea = el('div', { cls: 'gdoc_page_area' });
        body.append(sidebar, pageArea);

        // ?? Shell assemble ????????????????????????????????????????
        shell.append(odooNavbar, topBar, menuBar, toolbar, rulerWrap, body);

        // ?? Hide Odoo chrome ??????????????????????????????????????
        const titleWrap = document.querySelector('.o_sign_doc_title_wrap');
        const metaWrap  = document.querySelector('.o_sign_doc_meta');
        if (titleWrap) titleWrap.style.display = 'none';
        if (metaWrap)  metaWrap.style.display  = 'none';
        const cp = document.querySelector('.o_control_panel');
        if (cp) cp.style.display = 'none';
        const navbar = document.querySelector('.o_main_navbar');
        if (navbar) navbar.style.display = 'none';

        // Shell inject
        document.body.insertAdjacentElement('afterbegin', shell);

        // ?? Title sync ????????????????????????????????????????????
        setTimeout(() => {
            const odooInp = document.querySelector('.o_sign_doc_title input, .o_field_char input');
            if (odooInp) {
                titleInp.value = odooInp.value || 'Untitled document';
                odooInp.addEventListener('input', () => { titleInp.value = odooInp.value; });
            }
        }, 600);
        titleInp.addEventListener('blur', () => {
            const odooInp = document.querySelector('.o_sign_doc_title input, .o_field_char input');
            if (odooInp && odooInp.value !== titleInp.value) {
                odooInp.value = titleInp.value;
                odooInp.dispatchEvent(new Event('input', { bubbles: true }));
                odooInp.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        // ?????????????????????????????????????????????????????????
        //  GOOGLE DOCS LAYOUT ENGINE  v4  ? final
        //
        //  One SINGLE <div contenteditable> lives inside ONE white card.
        //  The card is tall enough to always show a clean A4 sheet.
        //  We do NOT try to split DOM nodes across multiple cards.
        //
        //  How page-break VISUALS work:
        //    ? The editor has NO clipping ? it grows naturally.
        //    ? We draw thin horizontal grey bands every PAGE_H pixels
        //      OVER the white card using a CSS repeating-linear-gradient
        //      on the card background.  Each band is PAGE_GAP px tall
        //      and has the same grey as the outer canvas.
        //    ? The editor has matching top padding repeated every PAGE_H
        //      by giving it a tall repeating padding via a pseudo-element
        //      ? actually we achieve this with a ::before overlay trick:
        //      we inject a <canvas> that draws the grey stripes absolutely.
        //
        //  Result: text flows naturally, grey bands visually separate pages,
        //  proper 96px left/right margins enforced by editor padding.
        // ?????????????????????????????????????????????????????????
        const PAGE_W    = 794;   // A4 content area (595pt = 793px @ 96dpi)
        const PAGE_H    = 1123;  // A4 height (842pt = 1122px @ 96dpi)
        const MARGIN_V  = 96;    // top/bottom margin ~1 inch
        const MARGIN_S  = 96;    // left/right margin ~1 inch
        // Total card width = PAGE_W + 2*MARGIN_S
        const CARD_W    = PAGE_W + MARGIN_S * 2; // 986px
        const GAP       = 24;    // grey gap height between pages (px)

        let _paginationOk = false;

        // ?? pageArea styling ??????????????????????????????????????
        pageArea.style.cssText = [
            'flex:1', 'overflow-y:auto', 'overflow-x:auto',
            'background:#f0f4f9',
            'padding:30px 40px 80px',
            'box-sizing:border-box',
            'min-height:0',
            'display:flex',
            'flex-direction:column',
            'align-items:center',
            'height:100%'
        ].join(';');

        // ?? Outer wrapper — full card width (content + margins)
        const docWrap = document.createElement('div');
        docWrap.id = 'gdoc_doc_wrap';
        docWrap.style.cssText = [
            `width:${CARD_W}px`,
            'position:relative',
            'flex-shrink:0',
            `min-height:${PAGE_H}px`
        ].join(';');
        pageArea.appendChild(docWrap);

        // ?? Stripe canvas — same width as card
        const stripeCanvas = document.createElement('canvas');
        stripeCanvas.id = 'gdoc_stripe_canvas';
        stripeCanvas.width  = CARD_W;
        stripeCanvas.height = 0;
        stripeCanvas.style.cssText = [
            'position:absolute',
            'top:0', 'left:0',
            'pointer-events:none',
            `min-height:${PAGE_H}px`,
            'z-index:3',
            `width:${CARD_W}px`
        ].join(';');
        docWrap.appendChild(stripeCanvas);

        // ?? White background card
        const bgCard = document.createElement('div');
        bgCard.id = 'gdoc_bg_card';
        bgCard.style.cssText = [
            'position:absolute',
            'top:0', 'left:0', `width:${CARD_W}px`, 'bottom:0',
            'background:#fff',
            'box-shadow:0 1px 4px rgba(0,0,0,0.22),0 2px 10px rgba(0,0,0,0.10)',
            'z-index:1',
            'pointer-events:none',
            `min-height:${PAGE_H}px`
        ].join(';');
        docWrap.appendChild(bgCard);

        // ?? The ONE editor div — full card width, padding = margins
        const mainEd = document.createElement('div');
        mainEd.id = 'gdoc_main_editor';
        mainEd.contentEditable = 'true';
        mainEd.spellcheck      = true;
        mainEd.style.cssText   = [
            'position:relative',
            'z-index:2',
            `width:${CARD_W}px`,
            // padding = the visual margin inside the white card
            `padding:${MARGIN_V}px ${MARGIN_S}px ${MARGIN_V}px ${MARGIN_S}px`,
            `min-height:${PAGE_H}px`,
            'font-size:11pt',
            'font-family:Arial,sans-serif',
            'line-height:1.6',
            'color:#202124',
            'outline:none',
            'word-wrap:break-word',
            'overflow-wrap:break-word',
            // content-box: width includes only content, padding is ADDED on top
            // So actual typed content stays within PAGE_W = CARD_W - 2*MARGIN_S
            'box-sizing:content-box',
            'cursor:text',
            'caret-color:#202124'
        ].join(';');
        docWrap.appendChild(mainEd);

        // Draw initial stripes so white page is visible immediately
        setTimeout(drawStripes, 50);

        // ── PAGE BREAK FIX ──────────────────────────────────────────
        // Ye function har block element (p, div, img, h1-h6, ul, ol, table)
        // ko check karta hai. Agar element page boundary ke oopar ya beech mein
        // aata hai to usse padding-top de ke next page pe push kar deta hai.
        // Images aur large blocks kabhi do pages ke beech split nahi honge.
        // ─────────────────────────────────────────────────────────────
        fixPageBreaks = function() {

            // Sirf direct block children ko target karo
            const blocks = mainEd.querySelectorAll(
                ':scope > p, :scope > div, :scope > h1, :scope > h2, :scope > h3,' +
                ':scope > h4, :scope > h5, :scope > h6, :scope > ul, :scope > ol,' +
                ':scope > li, :scope > table, :scope > figure, :scope > img,' +
                ':scope > blockquote, :scope > hr'
            );

            // Pehle saare injected padding-top clear karo
            blocks.forEach(b => {
                if (b.dataset.pbPadded) {
                    b.style.paddingTop = b.dataset.pbOrigPad || '';
                    delete b.dataset.pbPadded;
                    delete b.dataset.pbOrigPad;
                }
            });

            // Ab re-check karo page collisions
            // (clearing ke baad layout settle hone do)
            requestAnimationFrame(() => {
                blocks.forEach(block => {
                    const rect   = block.getBoundingClientRect();
                    const relTop = rect.top + window.scrollY - editorTop + mainEd.scrollTop;
                    const relBot = relTop + rect.height;

                    // Ye block kis page mein hai?
                    const pageOfTop = Math.floor(relTop / PAGE_H);
                    const pageOfBot = Math.floor(relBot / PAGE_H);

                    // Agar block page ke bottom margin zone mein start hota hai
                    // (i.e. page boundary kaatne wala hai) to next page push karo
                    const BOTTOM_MARGIN = MARGIN_V; // 96px safe zone
                    const pageBottom    = (pageOfTop + 1) * PAGE_H - BOTTOM_MARGIN;

                    if (relTop > MARGIN_V && relTop < pageBottom && relBot > (pageOfTop + 1) * PAGE_H) {
                        // Block page boundary cross kar raha hai — push to next page
                        const spaceLeft   = (pageOfTop + 1) * PAGE_H - relTop;
                        const origPad     = parseInt(window.getComputedStyle(block).paddingTop) || 0;
                        const neededPad   = spaceLeft + MARGIN_V + origPad;

                        block.dataset.pbPadded  = '1';
                        block.dataset.pbOrigPad = block.style.paddingTop || '';
                        block.style.paddingTop  = neededPad + 'px';
                    }
                });

                // Padding adjust ke baad stripes redraw karo
                drawStripes();
            });
        }

        // ?? Draw grey page-break stripes on the canvas ????????????
        drawStripes = function() {
            const totalH  = mainEd.scrollHeight;
            const pages   = Math.ceil(totalH / PAGE_H);
            const canvasH = pages * PAGE_H + (pages - 1) * GAP;

            stripeCanvas.width        = CARD_W;
            stripeCanvas.height       = canvasH;
            stripeCanvas.style.height = canvasH + 'px';
            stripeCanvas.style.width  = CARD_W + 'px';
            bgCard.style.height       = canvasH + 'px';
            bgCard.style.width        = CARD_W + 'px';
            docWrap.style.height      = canvasH + 'px';
            docWrap.style.width       = CARD_W + 'px';
            mainEd.style.minHeight    = canvasH + 'px';

            const ctx = stripeCanvas.getContext('2d');
            ctx.clearRect(0, 0, CARD_W, canvasH);

            // Grey gap bands between pages
            ctx.fillStyle = '#f0f4f9';
            for (let i = 1; i < pages; i++) {
                const y = i * PAGE_H - GAP / 2;
                ctx.fillRect(0, y, CARD_W, GAP);

                // Separator lines
                ctx.fillStyle = '#c8cdd3';
                ctx.fillRect(0, y, CARD_W, 1);
                ctx.fillRect(0, y + GAP - 1, CARD_W, 1);
                ctx.fillStyle = '#f0f4f9';
            }

            // Page number badge (bottom-right of each page)
            ctx.fillStyle = '#9aa0a6';
            ctx.font      = '11px Arial';
            ctx.textAlign = 'right';
            for (let i = 0; i < pages; i++) {
                const badgeY = (i + 1) * PAGE_H - 16;
                ctx.fillText('Page ' + (i + 1), CARD_W - 16, badgeY);
            }
        }

        // ?? Sync editor ? hidden Odoo field ??????????????????????
        function syncToOdoo() {
            const odooEd = document.querySelector(
                '.o_sign_doc_page_wrap [contenteditable="true"],' +
                '.o_field_html [contenteditable="true"],' +
                '.odoo-editor-editable'
            );
            if (odooEd) {
                odooEd.innerHTML = mainEd.innerHTML;
                odooEd.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }

        // ?? Watch editor height ???????????????????????????????????
        // if (typeof ResizeObserver !== 'undefined') {
        //     new ResizeObserver(() => {
        //         drawStripes();
        //         fixPageBreaks();
        //     }).observe(mainEd);
        // }

        // Image load pe bhi page breaks fix karo
        mainEd.addEventListener('load', e => {
            if (e.target && (e.target.tagName === 'IMG')) {
                drawStripes();
                fixPageBreaks();
            }
        }, true);

        // ?? Input / paste / tab ???????????????????????????????????
        let _syncTimer = null;
        let _pbTimer   = null;
        function onInput() {
            drawStripes();
            // Page break fix thodi der baad — layout settle hone ke baad
            clearTimeout(_pbTimer);
            _pbTimer = setTimeout(fixPageBreaks, 150);
            clearTimeout(_syncTimer);
            _syncTimer = setTimeout(syncToOdoo, 400);
        }

        mainEd.addEventListener('input', onInput);
        mainEd.addEventListener('paste', () => setTimeout(() => {
            onInput();
            // Pasted images ke load hone ka wait
            setTimeout(fixPageBreaks, 600);
        }, 80));
        mainEd.addEventListener('keydown', e => {
            if (e.key === 'Tab') {
                e.preventDefault();
                document.execCommand('insertHTML', false, '\u00a0\u00a0\u00a0\u00a0');
            }
            if (e.ctrlKey && e.shiftKey && e.key === 'I') {
                e.preventDefault();
                showImageInsertDialog();
            }
        });

        // ?? Bootstrap: wait for Odoo editor, then seed ???????????
        const EDITOR_SEL =
            '.o_sign_doc_page_wrap [contenteditable="true"],' +
            '.o_field_html [contenteditable="true"],' +
            '.odoo-editor-editable';

        let _initAttempts = 0;
        const _initTimer  = setInterval(() => {
            _initAttempts++;
            if (_initAttempts > 75) { clearInterval(_initTimer); return; }
            if (!document.getElementById('gdoc_shell')) { clearInterval(_initTimer); return; }
            if (_paginationOk) { clearInterval(_initTimer); return; }

            const odooEd = document.querySelector(EDITOR_SEL);
            if (!odooEd) return;

            clearInterval(_initTimer);
            _paginationOk = true;

            // Stash Odoo page wrap off-screen
            const origWrap = document.querySelector('.o_sign_doc_page_wrap');
            if (origWrap) {
                origWrap.style.cssText =
                    'position:fixed!important;left:-99999px!important;top:0!important;' +
                    'width:624px!important;visibility:hidden!important;' +
                    'pointer-events:none!important;z-index:-1!important;';
            }
            const cp   = document.querySelector('.o_control_panel');
            const mnav = document.querySelector('.o_main_navbar');
            if (cp)   cp.style.display   = 'none';
            if (mnav) mnav.style.display = 'none';

            // Seed
            const seedHTML = (odooEd.innerHTML && odooEd.innerHTML.trim())
                ? odooEd.innerHTML : '<p><br></p>';
            mainEd.innerHTML = seedHTML;

            requestAnimationFrame(() => requestAnimationFrame(() => {
                drawStripes();
                // Initial page break fix — images load hone ke baad bhi dobara
                fixPageBreaks();
                setTimeout(fixPageBreaks, 800);
                mainEd.focus();
                try {
                    const r = document.createRange();
                    r.setStart(mainEd, 0);
                    r.collapse(true);
                    const sel = window.getSelection();
                    if (sel) { sel.removeAllRanges(); sel.addRange(r); }
                } catch(e) {}

                // Image toolbar setup
                setupImageToolbar(mainEd);

                // Toolbar image button
                const tbImgBtn = document.getElementById('gdoc_tb_img_btn');
                if (tbImgBtn) tbImgBtn.addEventListener('click', () => showImageInsertDialog());
            }));
        }, 200);
    }

    // ?? Poller ?????????????????????????????????????????????????????
    let _lastUrl = location.href;

    setInterval(() => {
        const urlChanged = location.href !== _lastUrl;

        if (urlChanged) {
            _lastUrl = location.href;
            destroyShell();
            return;
        }

        // Build shell if we're on a sign.doc form and shell not yet built
        if (!alreadyDone() && isSignDocForm()) {
            buildShell();
            return;
        }

        // Destroy shell if we navigated away from sign.doc form
        if (alreadyDone() && !isSignDocForm()) {
            destroyShell();
        }
    }, 300);

})();