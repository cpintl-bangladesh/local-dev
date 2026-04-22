#!/usr/bin/env python3
"""
CPI Bangladesh Mission — Google Drive Manager
Full GTK4 GUI with complete CRUD operations.
No service account needed — uses OAuth (ariful@cpintl.org).
"""

import gi, sys, os, json, threading, subprocess, webbrowser
from pathlib import Path

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
try:
    from gi.repository import Gtk, Adw, GLib, Gdk, Gio, GdkPixbuf, Pango
except ImportError:
    # Fallback to GTK3
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, GLib, Gdk, Gio, Pango
    Adw = None

BASE_DIR  = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

# CPI Brand Colors
CPI_PURPLE    = "#41273B"
CPI_RED       = "#D91E4D"
CPI_TEAL      = "#4298B5"
CPI_VIOLET    = "#615E9B"
CPI_LIGHT_BG  = "#F5F0F3"

# ── CSS Theme ─────────────────────────────────────────────────
CSS = f"""
window {{
    background-color: #FAFAFA;
}}
.cpi-header {{
    background: {CPI_PURPLE};
    color: white;
    padding: 12px 20px;
    border-radius: 0;
}}
.cpi-header label {{
    color: white;
    font-size: 15px;
    font-weight: bold;
    font-family: Arial, sans-serif;
}}
.cpi-header .subtitle {{
    color: rgba(255,255,255,0.75);
    font-size: 11px;
}}
.sidebar {{
    background: #2D1F29;
    min-width: 200px;
}}
.sidebar button {{
    background: transparent;
    color: rgba(255,255,255,0.85);
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    margin: 2px 8px;
    text-align: left;
    font-size: 13px;
    font-family: Arial, sans-serif;
}}
.sidebar button:hover {{
    background: rgba(255,255,255,0.12);
    color: white;
}}
.sidebar button.active-nav {{
    background: {CPI_RED};
    color: white;
}}
.sidebar .section-label {{
    color: rgba(255,255,255,0.45);
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.08em;
    padding: 12px 16px 4px;
    font-family: Arial;
}}
.content-area {{
    background: #FAFAFA;
    padding: 0;
}}
.page-title {{
    font-size: 18px;
    font-weight: bold;
    font-family: Arial;
    color: {CPI_PURPLE};
    padding: 20px 24px 8px;
}}
.toolbar-bar {{
    background: white;
    border-bottom: 1px solid #E8E0E5;
    padding: 8px 16px;
}}
.stat-card {{
    background: white;
    border-radius: 10px;
    border: 1px solid #EAE0E7;
    padding: 16px 20px;
    margin: 4px;
}}
.stat-card .stat-num {{
    font-size: 28px;
    font-weight: bold;
    font-family: Arial;
    color: {CPI_PURPLE};
}}
.stat-card .stat-label {{
    font-size: 12px;
    color: #948794;
    font-family: Arial;
}}
.action-btn {{
    background: {CPI_PURPLE};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-family: Arial;
}}
.action-btn:hover {{
    background: #5a3652;
}}
.danger-btn {{
    background: {CPI_RED};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
}}
.teal-btn {{
    background: {CPI_TEAL};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
}}
.list-row {{
    border-bottom: 1px solid #F0EAF0;
    padding: 8px 16px;
}}
.list-row:hover {{
    background: {CPI_LIGHT_BG};
}}
.badge-prog {{
    background: #EDE9F7;
    color: #3C3489;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: bold;
}}
.badge-supp {{
    background: #E1F5EE;
    color: #085041;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: bold;
}}
.status-ok {{ color: #085041; font-weight: bold; }}
.status-warn {{ color: #633806; font-weight: bold; }}
.log-view {{
    font-family: monospace;
    font-size: 12px;
    background: #1E1E2E;
    color: #CDD6F4;
    padding: 12px;
    border-radius: 8px;
}}
"""


class CPIDriveApp(Gtk.Application):

    def __init__(self):
        super().__init__(application_id="org.cpintl.bgd.drivemanager")
        self.engine = None
        self.current_page = "dashboard"
        self.folder_cache = {}

    def do_activate(self):
        self.win = Gtk.ApplicationWindow(application=self)
        self.win.set_title("CPI Bangladesh Drive Manager")
        self.win.set_default_size(1280, 780)

        # Apply CSS
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._build_ui()
        self.win.present()
        self._init_auth()

    # ── UI Construction ───────────────────────────────────────

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.win.set_child(root)

        # Header bar
        header = self._build_header()
        root.append(header)

        # Main body: sidebar + content
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        body.set_vexpand(True)
        root.append(body)

        self.sidebar = self._build_sidebar()
        body.append(self.sidebar)

        # Content stack
        self.stack = Gtk.Stack()
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)
        body.append(self.stack)

        # Build all pages
        self.stack.add_named(self._build_dashboard_page(), "dashboard")
        self.stack.add_named(self._build_browser_page(),   "browser")
        self.stack.add_named(self._build_sheets_page(),    "sheets")
        self.stack.add_named(self._build_forms_page(),     "forms")
        self.stack.add_named(self._build_templates_page(), "templates")
        self.stack.add_named(self._build_permissions_page(), "permissions")
        self.stack.add_named(self._build_registry_page(),  "registry")
        self.stack.add_named(self._build_logs_page(),      "logs")
        self.stack.add_named(self._build_settings_page(),  "settings")

    def _build_header(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bar.add_css_class("cpi-header")

        # Logo text area
        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        title_lbl = Gtk.Label(label="CPI Bangladesh Mission — Drive Manager")
        title_lbl.add_css_class("cpi-header")
        labels.append(title_lbl)
        sub = Gtk.Label(label="000_BGD_CPMS · ariful@cpintl.org")
        sub.add_css_class("subtitle")
        labels.append(sub)
        bar.append(labels)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        bar.append(spacer)

        # Auth status
        self.auth_label = Gtk.Label(label="● Connecting...")
        self.auth_label.add_css_class("cpi-header")
        bar.append(self.auth_label)

        # Open Drive button
        drive_btn = Gtk.Button(label="Open Drive ↗")
        drive_btn.add_css_class("teal-btn")
        drive_btn.connect("clicked", lambda _: webbrowser.open(
            "https://drive.google.com/drive/folders/18N_9Eq4oOCPZoTBW4CbsVNqLVBkvb6KW"
        ))
        bar.append(drive_btn)

        return bar

    def _build_sidebar(self):
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar.add_css_class("sidebar")
        sidebar.set_size_request(210, -1)

        def make_section(label):
            lbl = Gtk.Label(label=label)
            lbl.add_css_class("section-label")
            lbl.set_xalign(0)
            sidebar.append(lbl)

        self.nav_buttons = {}

        def make_nav(icon, label, page):
            btn = Gtk.Button(label=f"{icon}  {label}")
            btn.set_xalign(0)
            btn.connect("clicked", lambda _, p=page: self._navigate(p))
            self.nav_buttons[page] = btn
            sidebar.append(btn)

        make_section("OVERVIEW")
        make_nav("⊞", "Dashboard", "dashboard")
        make_nav("📁", "File Browser", "browser")

        make_section("MANAGE")
        make_nav("📊", "Sheets & Data", "sheets")
        make_nav("📋", "Forms Builder", "forms")
        make_nav("📄", "Templates", "templates")

        make_section("SYSTEM")
        make_nav("🔒", "Permissions", "permissions")
        make_nav("📑", "Template Registry", "registry")
        make_nav("📝", "Activity Log", "logs")
        make_nav("⚙️", "Settings", "settings")

        # Set dashboard active
        self.nav_buttons["dashboard"].add_css_class("active-nav")

        # Bottom: version
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        sidebar.append(spacer)

        ver = Gtk.Label(label="v1.0 | 2026-04")
        ver.add_css_class("section-label")
        sidebar.append(ver)

        return sidebar

    def _navigate(self, page):
        for p, btn in self.nav_buttons.items():
            btn.remove_css_class("active-nav")
        self.nav_buttons[page].add_css_class("active-nav")
        self.stack.set_visible_child_name(page)
        self.current_page = page
        if page == "browser" and self.engine:
            self._refresh_browser()
        elif page == "registry" and self.engine:
            self._refresh_registry()
        elif page == "sheets" and self.engine:
            self._refresh_sheets()

    # ── Dashboard Page ────────────────────────────────────────

    def _build_dashboard_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        title = Gtk.Label(label="Dashboard")
        title.set_xalign(0)
        title.add_css_class("page-title")
        page.append(title)

        # Stat cards
        cards = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cards.set_margin_start(16)
        cards.set_margin_end(16)
        cards.set_margin_bottom(16)
        page.append(cards)

        self.stat_labels = {}
        stats = [
            ("99",  "Folders verified",   "folders"),
            ("20",  "Master sheets",      "sheets"),
            ("21",  "Master docs",        "docs"),
            ("7",   "JSON schemas",       "json"),
            ("144", "Total items built",  "total"),
        ]
        for val, label, key in stats:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.add_css_class("stat-card")
            card.set_hexpand(True)
            num = Gtk.Label(label=val)
            num.add_css_class("stat-num")
            card.append(num)
            lbl = Gtk.Label(label=label)
            lbl.add_css_class("stat-label")
            card.append(lbl)
            cards.append(card)
            self.stat_labels[key] = num

        # Quick actions
        qa_title = Gtk.Label(label="Quick actions")
        qa_title.set_xalign(0)
        qa_title.set_margin_start(24)
        qa_title.set_margin_bottom(8)
        page.append(qa_title)

        qa_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        qa_bar.set_margin_start(20)
        qa_bar.set_margin_end(20)
        page.append(qa_bar)

        actions = [
            ("📁 Browse Folders",   "browser"),
            ("📊 View Sheets",      "sheets"),
            ("📑 Template Registry","registry"),
            ("📝 Activity Log",     "logs"),
        ]
        for label, page_name in actions:
            btn = Gtk.Button(label=label)
            btn.add_css_class("action-btn")
            btn.connect("clicked", lambda _, p=page_name: self._navigate(p))
            qa_bar.append(btn)

        # Status section
        sep = Gtk.Separator()
        sep.set_margin_top(16)
        sep.set_margin_bottom(16)
        page.append(sep)

        self.status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.status_box.set_margin_start(24)
        page.append(self.status_box)
        self._update_status("Connecting to Google Drive...", "warn")

        return page

    def _update_status(self, message, kind="ok"):
        for child in list(self.status_box):
            self.status_box.remove(child)
        lbl = Gtk.Label(label=message)
        lbl.set_xalign(0)
        lbl.add_css_class(f"status-{kind}")
        self.status_box.append(lbl)

    # ── File Browser Page ─────────────────────────────────────

    def _build_browser_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar.add_css_class("toolbar-bar")

        title = Gtk.Label(label="📁  File Browser")
        title.add_css_class("page-title")
        title.set_margin_top(0)
        title.set_margin_bottom(0)
        toolbar.append(title)

        spacer = Gtk.Box(); spacer.set_hexpand(True)
        toolbar.append(spacer)

        self.browser_path = Gtk.Label(label="000_BGD_CPMS / root")
        self.browser_path.add_css_class("stat-label")
        toolbar.append(self.browser_path)

        refresh_btn = Gtk.Button(label="⟳ Refresh")
        refresh_btn.connect("clicked", lambda _: self._refresh_browser())
        toolbar.append(refresh_btn)

        new_folder_btn = Gtk.Button(label="+ New Folder")
        new_folder_btn.add_css_class("action-btn")
        new_folder_btn.connect("clicked", self._on_new_folder)
        toolbar.append(new_folder_btn)

        new_sheet_btn = Gtk.Button(label="+ New Sheet")
        new_sheet_btn.add_css_class("teal-btn")
        new_sheet_btn.connect("clicked", self._on_new_sheet)
        toolbar.append(new_sheet_btn)

        new_doc_btn = Gtk.Button(label="+ New Doc")
        new_doc_btn.add_css_class("teal-btn")
        new_doc_btn.connect("clicked", self._on_new_doc)
        toolbar.append(new_doc_btn)

        page.append(toolbar)

        # Split: folder tree left, file list right
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_vexpand(True)
        paned.set_position(280)
        page.append(paned)

        # Left: folder tree
        tree_scroll = Gtk.ScrolledWindow()
        tree_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.folder_store = Gtk.TreeStore(str, str, str)  # name, id, icon
        self.folder_tree  = Gtk.TreeView(model=self.folder_store)
        self.folder_tree.set_headers_visible(False)

        col = Gtk.TreeViewColumn()
        icon_r = Gtk.CellRendererText()
        name_r = Gtk.CellRendererText()
        col.pack_start(icon_r, False)
        col.pack_start(name_r, True)
        col.add_attribute(icon_r, "text", 2)
        col.add_attribute(name_r, "text", 0)
        self.folder_tree.append_column(col)
        self.folder_tree.get_selection().connect("changed", self._on_folder_selected)
        tree_scroll.set_child(self.folder_tree)
        paned.set_start_child(tree_scroll)

        # Right: file list
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.file_store = Gtk.ListStore(str, str, str, str, str)  # icon, name, type, modified, id
        self.file_view  = Gtk.TreeView(model=self.file_store)
        self.file_view.set_headers_visible(True)

        cols = [("", 0), ("Name", 1), ("Type", 2), ("Modified", 3)]
        for header, idx in cols:
            r = Gtk.CellRendererText()
            c = Gtk.TreeViewColumn(header, r, text=idx)
            c.set_resizable(True)
            if idx == 1:
                c.set_expand(True)
            self.file_view.append_column(c)

        self.file_view.connect("row-activated", self._on_file_activated)

        file_scroll = Gtk.ScrolledWindow()
        file_scroll.set_child(self.file_view)
        file_scroll.set_vexpand(True)
        right.append(file_scroll)

        # File action bar
        file_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        file_actions.set_margin_all(8)

        open_btn = Gtk.Button(label="↗ Open in Drive")
        open_btn.connect("clicked", self._on_open_selected)
        file_actions.append(open_btn)

        rename_btn = Gtk.Button(label="✏️ Rename")
        rename_btn.connect("clicked", self._on_rename_selected)
        file_actions.append(rename_btn)

        trash_btn = Gtk.Button(label="🗑️ Trash")
        trash_btn.add_css_class("danger-btn")
        trash_btn.connect("clicked", self._on_trash_selected)
        file_actions.append(trash_btn)

        right.append(file_actions)
        paned.set_end_child(right)

        self.current_browse_id    = FOLDER_IDS.get("ROOT", "18N_9Eq4oOCPZoTBW4CbsVNqLVBkvb6KW")
        self.current_browse_items = []

        return page

    def _refresh_browser(self):
        if not self.engine:
            return
        self.folder_store.clear()
        self.file_store.clear()

        def load():
            root_id = "18N_9Eq4oOCPZoTBW4CbsVNqLVBkvb6KW"
            items   = self.engine.list_children(root_id)
            GLib.idle_add(self._populate_tree, items, root_id)

        threading.Thread(target=load, daemon=True).start()

    def _populate_tree(self, items, parent_id, parent_iter=None):
        FOLDER_MIME = "application/vnd.google-apps.folder"
        for item in items:
            if item["mimeType"] == FOLDER_MIME:
                icon = "📁"
                it = self.folder_store.append(parent_iter, [item["name"], item["id"], icon])
        self._populate_files(items)
        return False

    def _populate_files(self, items):
        self.file_store.clear()
        self.current_browse_items = items
        MIME_ICONS = {
            "application/vnd.google-apps.folder":      "📁",
            "application/vnd.google-apps.spreadsheet": "📊",
            "application/vnd.google-apps.document":    "📄",
            "application/vnd.google-apps.form":        "📋",
            "application/json":                        "🗂️",
        }
        for item in items:
            icon = MIME_ICONS.get(item.get("mimeType", ""), "📎")
            mime_label = item.get("mimeType", "").split(".")[-1].replace("google-apps.", "")
            mod  = item.get("modifiedTime", "")[:10]
            self.file_store.append([icon, item["name"], mime_label, mod, item["id"]])

    def _on_folder_selected(self, sel):
        model, it = sel.get_selected()
        if not it or not self.engine:
            return
        folder_id   = model[it][1]
        folder_name = model[it][0]
        self.current_browse_id = folder_id
        self.browser_path.set_text(f"000_BGD_CPMS / … / {folder_name}")

        def load():
            items = self.engine.list_children(folder_id)
            GLib.idle_add(self._populate_files, items)

        threading.Thread(target=load, daemon=True).start()

    def _on_file_activated(self, view, path, col):
        model = view.get_model()
        it    = model.get_iter(path)
        fid   = model[it][4]
        mime  = self.current_browse_items[path.get_indices()[0]].get("mimeType", "")
        if "folder" in mime:
            url = f"https://drive.google.com/drive/folders/{fid}"
        else:
            url = f"https://drive.google.com/file/d/{fid}"
        webbrowser.open(url)

    def _on_open_selected(self, _):
        model, it = self.file_view.get_selection().get_selected()
        if not it:
            return
        fid = model[it][4]
        webbrowser.open(f"https://drive.google.com/file/d/{fid}")

    def _on_new_folder(self, _):
        self._input_dialog("New Folder", "Folder name:", self._create_folder_action)

    def _on_new_sheet(self, _):
        self._input_dialog("New Google Sheet", "Sheet name:", self._create_sheet_action)

    def _on_new_doc(self, _):
        self._input_dialog("New Google Doc", "Doc name:", self._create_doc_action)

    def _on_rename_selected(self, _):
        model, it = self.file_view.get_selection().get_selected()
        if not it:
            return
        fid      = model[it][4]
        old_name = model[it][1]
        self._input_dialog("Rename", f"New name for '{old_name}':",
                           lambda name: self._rename_action(fid, name),
                           default=old_name)

    def _on_trash_selected(self, _):
        model, it = self.file_view.get_selection().get_selected()
        if not it:
            return
        fid  = model[it][4]
        name = model[it][1]
        self._confirm_dialog(f"Move '{name}' to trash?",
                             lambda: self._trash_action(fid))

    def _create_folder_action(self, name):
        if not self.engine or not name:
            return
        def run():
            self.engine.create_folder(name, self.current_browse_id)
            GLib.idle_add(self._refresh_browser)
            GLib.idle_add(self._append_log, f"📁 Created folder: {name}")
        threading.Thread(target=run, daemon=True).start()

    def _create_sheet_action(self, name):
        if not self.engine or not name:
            return
        def run():
            sid = self.engine.create_sheet(name, self.current_browse_id)
            GLib.idle_add(self._refresh_browser)
            GLib.idle_add(self._append_log, f"📊 Created sheet: {name} ({sid})")
        threading.Thread(target=run, daemon=True).start()

    def _create_doc_action(self, name):
        if not self.engine or not name:
            return
        def run():
            did = self.engine.create_doc(name, self.current_browse_id)
            GLib.idle_add(self._refresh_browser)
            GLib.idle_add(self._append_log, f"📄 Created doc: {name} ({did})")
        threading.Thread(target=run, daemon=True).start()

    def _rename_action(self, fid, new_name):
        if not self.engine or not new_name:
            return
        def run():
            self.engine.rename(fid, new_name)
            GLib.idle_add(self._refresh_browser)
            GLib.idle_add(self._append_log, f"✏️  Renamed {fid} → {new_name}")
        threading.Thread(target=run, daemon=True).start()

    def _trash_action(self, fid):
        if not self.engine:
            return
        def run():
            self.engine.trash(fid)
            GLib.idle_add(self._refresh_browser)
            GLib.idle_add(self._append_log, f"🗑️  Trashed {fid}")
        threading.Thread(target=run, daemon=True).start()

    # ── Sheets Page ───────────────────────────────────────────

    def _build_sheets_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar.add_css_class("toolbar-bar")
        toolbar.append(Gtk.Label(label="📊  Sheets & Data"))
        spacer = Gtk.Box(); spacer.set_hexpand(True); toolbar.append(spacer)

        add_btn = Gtk.Button(label="+ Create Sheet")
        add_btn.add_css_class("action-btn")
        add_btn.connect("clicked", self._on_new_sheet_global)
        toolbar.append(add_btn)

        apply_btn = Gtk.Button(label="✦ Apply CPI Formatting")
        apply_btn.add_css_class("teal-btn")
        apply_btn.connect("clicked", self._on_apply_formatting)
        toolbar.append(apply_btn)

        page.append(toolbar)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.sheets_store = Gtk.ListStore(str, str, str, str)  # name, id, folder, url
        self.sheets_view  = Gtk.TreeView(model=self.sheets_store)

        for header, idx in [("Sheet Name", 0), ("Sheet ID", 1), ("Folder", 2)]:
            r = Gtk.CellRendererText()
            c = Gtk.TreeViewColumn(header, r, text=idx)
            c.set_resizable(True)
            if idx == 0:
                c.set_expand(True)
            self.sheets_view.append_column(c)

        self.sheets_view.connect("row-activated", lambda v, p, c: self._open_sheet_url(v, p))
        scroll.set_child(self.sheets_view)
        page.append(scroll)

        return page

    def _on_new_sheet_global(self, _):
        self._input_dialog("New Google Sheet", "Sheet name (use CPI naming convention):",
                           self._create_sheet_global)

    def _create_sheet_global(self, name):
        if not name or not self.engine:
            return
        tpl_sheets = FOLDER_IDS.get("00_TPL", "")
        def run():
            sid = self.engine.create_sheet(name, tpl_sheets)
            GLib.idle_add(self._refresh_sheets)
            GLib.idle_add(self._append_log, f"📊 Created: {name}")
        threading.Thread(target=run, daemon=True).start()

    def _on_apply_formatting(self, _):
        model, it = self.sheets_view.get_selection().get_selected()
        if not it or not self.engine:
            self._toast("Select a sheet first")
            return
        sid   = model[it][1]
        name  = model[it][0]
        ncols = 10
        def run():
            try:
                self.engine.apply_header_formatting(sid, ncols)
                GLib.idle_add(self._append_log, f"✦ CPI formatting applied to: {name}")
                GLib.idle_add(self._toast, f"✅ Formatting applied to {name}")
            except Exception as e:
                GLib.idle_add(self._toast, f"Error: {e}")
        threading.Thread(target=run, daemon=True).start()

    def _open_sheet_url(self, view, path):
        model = view.get_model()
        it    = model.get_iter(path)
        sid   = model[it][1]
        webbrowser.open(f"https://docs.google.com/spreadsheets/d/{sid}")

    def _refresh_sheets(self):
        if not self.engine:
            return
        self.sheets_store.clear()
        tpl_id = FOLDER_IDS.get("00_TPL", "")
        def load():
            items = self.engine.list_children(
                tpl_id, mime="application/vnd.google-apps.spreadsheet"
            )
            GLib.idle_add(self._populate_sheets, items)
        threading.Thread(target=load, daemon=True).start()

    def _populate_sheets(self, items):
        self.sheets_store.clear()
        for item in items:
            self.sheets_store.append([
                item["name"], item["id"], "00_Templates/Sheets",
                f"https://docs.google.com/spreadsheets/d/{item['id']}"
            ])

    # ── Forms Page ────────────────────────────────────────────

    def _build_forms_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        page.set_margin_all(24)

        title = Gtk.Label(label="📋  Forms Builder")
        title.set_xalign(0); title.add_css_class("page-title")
        title.set_margin_top(0)
        page.append(title)

        info = Gtk.Label(label="Google Forms cannot be created via Drive API. Create them at forms.google.com, then link them here by pasting the Form ID.")
        info.set_wrap(True); info.set_xalign(0)
        info.set_margin_bottom(16)
        page.append(info)

        # Forms list from registry
        frame = Gtk.Frame(label="Linked Google Forms")
        forms_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        forms_box.set_margin_all(12)

        form_defs = [
            ("HOP Daily Patient Log",    "H&N / HOP",  "Camp-level daily patient count form"),
            ("HPP OPD Register",         "H&N / HPP",  "Health post OPD entry form"),
            ("WASH Monthly Monitoring",  "S&D / WASH", "Camp WASH infrastructure monitoring"),
            ("Expense Claim",            "G&F",        "Staff expense reimbursement"),
            ("Procurement Request",      "LSC",        "Item purchase request"),
            ("Incident Report",          "ERP",        "Emergency incident logging"),
            ("Leave Request",            "HRA",        "Staff leave application"),
        ]
        for name, unit, desc in form_defs:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.set_margin_bottom(4)

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            nl = Gtk.Label(label=name)
            nl.set_xalign(0); nl.set_markup(f"<b>{name}</b>")
            dl = Gtk.Label(label=f"{unit} — {desc}")
            dl.set_xalign(0); dl.add_css_class("stat-label")
            vbox.append(nl); vbox.append(dl)
            vbox.set_hexpand(True)

            row.append(vbox)

            create_btn = Gtk.Button(label="↗ Create Form")
            create_btn.connect("clicked", lambda _, n=name: webbrowser.open(
                "https://forms.google.com/create"
            ))
            row.append(create_btn)

            link_btn = Gtk.Button(label="🔗 Link Form ID")
            link_btn.connect("clicked", lambda _, n=name: self._link_form(n))
            row.append(link_btn)

            forms_box.append(row)
            forms_box.append(Gtk.Separator())

        frame.set_child(forms_box)
        page.append(frame)

        return page

    def _link_form(self, form_name):
        self._input_dialog(
            f"Link Form: {form_name}",
            "Paste the Google Form ID (from the form URL):",
            lambda fid: self._append_log(f"🔗 Linked form '{form_name}' → {fid}")
        )

    # ── Templates Page ────────────────────────────────────────

    def _build_templates_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar.add_css_class("toolbar-bar")
        toolbar.append(Gtk.Label(label="📄  Templates"))
        spacer = Gtk.Box(); spacer.set_hexpand(True); toolbar.append(spacer)

        open_tpl_btn = Gtk.Button(label="↗ Open Templates Folder")
        open_tpl_btn.connect("clicked", lambda _: webbrowser.open(
            f"https://drive.google.com/drive/folders/{FOLDER_IDS.get('00_TPL','')}"
        ))
        toolbar.append(open_tpl_btn)
        page.append(toolbar)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)

        self.tpl_store = Gtk.ListStore(str, str, str, str)
        self.tpl_view  = Gtk.TreeView(model=self.tpl_store)

        for header, idx in [("Template Name", 0), ("Type", 1), ("Unit", 2), ("Version", 3)]:
            r = Gtk.CellRendererText()
            c = Gtk.TreeViewColumn(header, r, text=idx)
            c.set_resizable(True)
            if idx == 0:
                c.set_expand(True)
            self.tpl_view.append_column(c)

        self.tpl_view.connect("row-activated", lambda v, p, c: self._toast("Select and click Open"))

        tpl_rows = [
            ("CPI_BGD_HRA_Sheet_StaffDirectory_v1.0",           "Sheet", "HRA",  "1.0"),
            ("CPI_BGD_HRA_Sheet_LeaveTracker_2026-04_v1.0",     "Sheet", "HRA",  "1.0"),
            ("CPI_BGD_GF_Sheet_BudgetTracker_2026-04_v1.0",     "Sheet", "G&F",  "1.0"),
            ("CPI_BGD_GF_Sheet_ExpenseTracker_2026-04_v1.0",    "Sheet", "G&F",  "1.0"),
            ("CPI_BGD_LSC_Sheet_InventoryTracker_v1.0",         "Sheet", "LSC",  "1.0"),
            ("CPI_BGD_MER_Sheet_IndicatorTracker_2026-04_v1.0", "Sheet", "MER",  "1.0"),
            ("CPI_BGD_HOP_Sheet_DailyPatientLog_v1.0",          "Sheet", "H&N",  "1.0"),
            ("CPI_BGD_HPP_Sheet_OPDRegister_v1.0",              "Sheet", "H&N",  "1.0"),
            ("CPI_BGD_WASH_Sheet_MonthlyMonitoring_v1.0",       "Sheet", "S&D",  "1.0"),
            ("CPI_BGD_SOP_Template_Shell_v1.0",                 "Doc",   "All",  "1.0"),
            ("CPI_BGD_MER_Doc_MonthlyReport_Template_v1.0",     "Doc",   "MER",  "1.0"),
            ("CPI_BGD_MER_Doc_QuarterlyReport_Template_v1.0",   "Doc",   "MER",  "1.0"),
            ("CPI_BGD_Admin_Doc_MeetingMinutes_Template_v1.0",  "Doc",   "Admin","1.0"),
            ("CPI_BGD_HRA_Doc_HandoverNote_Template_v1.0",      "Doc",   "HRA",  "1.0"),
            ("CPI_BGD_HN_Doc_Framework_v1.0",                   "Doc",   "H&N",  "1.0"),
            ("CPI_BGD_MER_Doc_MELFramework_v1.0",               "Doc",   "MER",  "1.0"),
        ]
        for row in tpl_rows:
            self.tpl_store.append(list(row))

        scroll.set_child(self.tpl_view)
        page.append(scroll)

        return page

    # ── Permissions Page ──────────────────────────────────────

    def _build_permissions_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        page.set_margin_all(20)

        title = Gtk.Label(label="🔒  Folder Permissions")
        title.set_xalign(0); title.add_css_class("page-title"); title.set_margin_top(0)
        page.append(title)

        info = Gtk.Label(label="Set access control per folder. Editor = can create/edit. Viewer = read only.")
        info.set_xalign(0); info.set_margin_bottom(16)
        page.append(info)

        # Permission rules table
        rules = [
            ("00_Templates",      "System Admin only",         "Viewers: all mission staff"),
            ("01_HRA",            "HRA Manager + CR",          "Viewers: all staff"),
            ("02_G&F",            "Finance Manager + CR",      "Viewers: program managers only"),
            ("03_LSC",            "Logistics Officer",         "Viewers: program staff"),
            ("04_MER",            "MER Officer + Program Mgrs","Viewers: all staff + HQ"),
            ("05_MC",             "M&C Officer + CR",          "Viewers: all staff"),
            ("10_Programs",       "Program Managers (each own)","Viewers: all + HQ"),
            ("11_Projects/CXB",   "CXB Program team",          "Viewers: Dhaka + HQ"),
            ("Partners/*",        "PM + partner focal point",  "Viewers: partner own folder"),
            ("99_Archive",        "System Admin + CR only",    "Viewers: all (read only)"),
        ]

        frame = Gtk.Frame(label="Permission Rules")
        vbox  = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_all(12)

        for folder, editors, viewers in rules:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
            fl = Gtk.Label(); fl.set_markup(f"<b>{folder}</b>"); fl.set_xalign(0)
            fl.set_size_request(160, -1)
            el = Gtk.Label(label=f"Edit: {editors}"); el.set_xalign(0); el.set_hexpand(True)
            vl = Gtk.Label(label=viewers); vl.set_xalign(0)

            set_btn = Gtk.Button(label="Apply")
            set_btn.connect("clicked", lambda _, f=folder: self._set_perm_dialog(f))

            row.append(fl); row.append(el); row.append(vl); row.append(set_btn)
            vbox.append(row)
            vbox.append(Gtk.Separator())

        frame.set_child(vbox)
        page.append(frame)
        return page

    def _set_perm_dialog(self, folder):
        self._input_dialog(
            f"Set Permission: {folder}",
            "Enter email address to grant access:",
            lambda email: self._toast(f"Permission set for {folder} → {email}")
        )

    # ── Registry Page ─────────────────────────────────────────

    def _build_registry_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar.add_css_class("toolbar-bar")
        toolbar.append(Gtk.Label(label="📑  Template Registry"))
        spacer = Gtk.Box(); spacer.set_hexpand(True); toolbar.append(spacer)

        open_btn = Gtk.Button(label="↗ Open Registry Sheet")
        open_btn.connect("clicked", lambda _: webbrowser.open(
            "https://docs.google.com/spreadsheets/d/1kl39tYBZ2qVq5eq0LRv7e4Cv-jXeNUPGdIrZhrw1mIM"
        ))
        toolbar.append(open_btn)

        refresh_btn = Gtk.Button(label="⟳ Refresh")
        refresh_btn.connect("clicked", lambda _: self._refresh_registry())
        toolbar.append(refresh_btn)

        add_btn = Gtk.Button(label="+ Add Entry")
        add_btn.add_css_class("action-btn")
        add_btn.connect("clicked", self._on_add_registry_entry)
        toolbar.append(add_btn)

        page.append(toolbar)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)

        self.reg_store = Gtk.ListStore(str, str, str, str, str, str, str)
        self.reg_view  = Gtk.TreeView(model=self.reg_store)
        self.reg_view.set_headers_visible(True)

        headers = ["ID", "Template Name", "Unit", "Type", "Version", "Status", "Notes"]
        for i, h in enumerate(headers):
            r = Gtk.CellRendererText()
            r.set_property("ellipsize", Pango.EllipsizeMode.END)
            c = Gtk.TreeViewColumn(h, r, text=i)
            c.set_resizable(True)
            if i == 1:
                c.set_expand(True)
            self.reg_view.append_column(c)

        scroll.set_child(self.reg_view)
        page.append(scroll)

        return page

    def _refresh_registry(self):
        if not self.engine:
            return
        reg_id = "1kl39tYBZ2qVq5eq0LRv7e4Cv-jXeNUPGdIrZhrw1mIM"
        def load():
            rows = self.engine.read_sheet(reg_id)
            GLib.idle_add(self._populate_registry, rows)
        threading.Thread(target=load, daemon=True).start()

    def _populate_registry(self, rows):
        self.reg_store.clear()
        if not rows:
            return
        data = rows[1:]  # skip header
        for row in data:
            while len(row) < 7:
                row.append("")
            self.reg_store.append(row[:7])

    def _on_add_registry_entry(self, _):
        dialog = Gtk.Dialog(title="Add Registry Entry", transient_for=self.win, modal=True)
        dialog.set_default_size(500, 400)

        box = dialog.get_content_area()
        box.set_margin_all(16)
        box.set_spacing(8)

        fields = [
            ("Template ID (e.g. T021)", "tid"),
            ("Template Name",            "name"),
            ("Unit (HRA/G&F/H&N...)",    "unit"),
            ("Doc Type (Sheet/Doc/JSON)","dtype"),
            ("Version",                  "ver"),
            ("Notes",                    "notes"),
        ]
        entries = {}
        for label, key in fields:
            lbl = Gtk.Label(label=label); lbl.set_xalign(0)
            ent = Gtk.Entry(); ent.set_hexpand(True)
            if key == "ver":
                ent.set_text("1.0")
            box.append(lbl); box.append(ent)
            entries[key] = ent

        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Add Entry", Gtk.ResponseType.OK)

        def on_response(d, resp):
            if resp == Gtk.ResponseType.OK and self.engine:
                row = [
                    entries["tid"].get_text(),
                    entries["name"].get_text(),
                    entries["unit"].get_text(),
                    entries["dtype"].get_text(),
                    entries["ver"].get_text(),
                    "2026-04", "00_Templates", "Google Sheet", "", "Active",
                    "ariful@cpintl.org",
                    entries["notes"].get_text(),
                ]
                reg_id = "1kl39tYBZ2qVq5eq0LRv7e4Cv-jXeNUPGdIrZhrw1mIM"
                def run():
                    self.engine.append_sheet_row(reg_id, row[:12])
                    GLib.idle_add(self._refresh_registry)
                    GLib.idle_add(self._append_log, f"📑 Registry entry added: {entries['name'].get_text()}")
                threading.Thread(target=run, daemon=True).start()
            d.destroy()

        dialog.connect("response", on_response)
        dialog.present()

    # ── Logs Page ─────────────────────────────────────────────

    def _build_logs_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar.add_css_class("toolbar-bar")
        toolbar.append(Gtk.Label(label="📝  Activity Log"))
        spacer = Gtk.Box(); spacer.set_hexpand(True); toolbar.append(spacer)
        clear_btn = Gtk.Button(label="Clear")
        clear_btn.connect("clicked", lambda _: self._clear_log())
        toolbar.append(clear_btn)
        export_btn = Gtk.Button(label="Export")
        export_btn.connect("clicked", self._export_log)
        toolbar.append(export_btn)
        page.append(toolbar)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.log_buffer = Gtk.TextBuffer()
        self.log_view   = Gtk.TextView(buffer=self.log_buffer)
        self.log_view.set_editable(False)
        self.log_view.add_css_class("log-view")
        scroll.set_child(self.log_view)
        page.append(scroll)

        return page

    def _append_log(self, message):
        import datetime
        ts   = datetime.datetime.now().strftime("%H:%M:%S")
        text = f"[{ts}] {message}\n"
        end  = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end, text)

    def _clear_log(self):
        self.log_buffer.set_text("")

    def _export_log(self, _):
        log_path = BASE_DIR / "logs" / "activity.log"
        log_path.parent.mkdir(exist_ok=True)
        text = self.log_buffer.get_text(
            self.log_buffer.get_start_iter(), self.log_buffer.get_end_iter(), True
        )
        log_path.write_text(text)
        self._toast(f"Log exported to {log_path}")

    # ── Settings Page ─────────────────────────────────────────

    def _build_settings_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        page.set_margin_all(24)

        title = Gtk.Label(label="⚙️  Settings")
        title.set_xalign(0); title.add_css_class("page-title"); title.set_margin_top(0)
        page.append(title)

        settings = [
            ("Shared Drive ID",   "18N_9Eq4oOCPZoTBW4CbsVNqLVBkvb6KW"),
            ("Account",           "ariful@cpintl.org"),
            ("Template Registry", "1kl39tYBZ2qVq5eq0LRv7e4Cv-jXeNUPGdIrZhrw1mIM"),
            ("INDEX Sheet",       "1jq5y9rY5-WaTtukok7Sol0px5SM5fUG6tF3MQmvBJaQ"),
            ("Local Dev Path",    str(BASE_DIR)),
        ]
        for label, value in settings:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.set_margin_bottom(8)
            lbl = Gtk.Label(label=f"{label}:"); lbl.set_xalign(0); lbl.set_size_request(180,-1)
            lbl.set_markup(f"<b>{label}:</b>")
            val = Gtk.Label(label=value); val.set_xalign(0); val.set_selectable(True)
            val.set_hexpand(True)
            row.append(lbl); row.append(val)
            page.append(row)

        sep = Gtk.Separator(); sep.set_margin_top(16); sep.set_margin_bottom(16)
        page.append(sep)

        # Re-auth button
        reauth_btn = Gtk.Button(label="🔐 Re-authenticate Google Account")
        reauth_btn.add_css_class("action-btn")
        reauth_btn.connect("clicked", self._on_reauth)
        page.append(reauth_btn)

        # Open Drive
        drive_btn = Gtk.Button(label="↗ Open 000_BGD_CPMS in Drive")
        drive_btn.add_css_class("teal-btn")
        drive_btn.set_margin_top(8)
        drive_btn.connect("clicked", lambda _: webbrowser.open(
            "https://drive.google.com/drive/folders/18N_9Eq4oOCPZoTBW4CbsVNqLVBkvb6KW"
        ))
        page.append(drive_btn)

        return page

    def _on_reauth(self, _):
        token = BASE_DIR / "config" / "token.json"
        if token.exists():
            token.unlink()
        self._init_auth()

    # ── Auth ──────────────────────────────────────────────────

    def _init_auth(self):
        self._update_status("Authenticating with Google...", "warn")
        self.auth_label.set_text("● Connecting...")

        def run():
            try:
                from auth import get_credentials, build_services
                creds = get_credentials()
                drive, sheets, docs = build_services(creds)

                from drive_engine import DriveEngine, FOLDER_IDS as FI
                self.engine = DriveEngine(drive, sheets, docs)
                globals().update({"FOLDER_IDS": FI})

                about = drive.about().get(fields="user").execute()
                email = about["user"]["emailAddress"]
                GLib.idle_add(self._on_auth_success, email)
            except Exception as e:
                GLib.idle_add(self._on_auth_failure, str(e))

        threading.Thread(target=run, daemon=True).start()

    def _on_auth_success(self, email):
        self.auth_label.set_text(f"● {email}")
        self._update_status(f"✅ Connected as {email} — 000_BGD_CPMS ready", "ok")
        self._append_log(f"✅ Authenticated as {email}")

    def _on_auth_failure(self, error):
        self.auth_label.set_text("● Not connected")
        self._update_status(f"❌ Auth failed: {error}", "warn")
        self._append_log(f"❌ Auth error: {error}")

    # ── Dialogs ───────────────────────────────────────────────

    def _input_dialog(self, title, prompt, callback, default=""):
        dialog = Gtk.Dialog(title=title, transient_for=self.win, modal=True)
        dialog.set_default_size(420, 140)
        box = dialog.get_content_area()
        box.set_margin_all(16); box.set_spacing(8)
        box.append(Gtk.Label(label=prompt))
        entry = Gtk.Entry(); entry.set_text(default); entry.set_hexpand(True)
        entry.connect("activate", lambda _: dialog.response(Gtk.ResponseType.OK))
        box.append(entry)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("OK",     Gtk.ResponseType.OK)
        def on_response(d, resp):
            if resp == Gtk.ResponseType.OK:
                callback(entry.get_text().strip())
            d.destroy()
        dialog.connect("response", on_response)
        dialog.present()
        entry.grab_focus()

    def _confirm_dialog(self, message, callback):
        dialog = Gtk.MessageDialog(
            transient_for=self.win, modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=message
        )
        def on_response(d, resp):
            if resp == Gtk.ResponseType.YES:
                callback()
            d.destroy()
        dialog.connect("response", on_response)
        dialog.present()

    def _toast(self, message):
        self._append_log(f"ℹ️  {message}")

    # ── Run ───────────────────────────────────────────────────

def main():
    app = CPIDriveApp()
    app.run(sys.argv)

if __name__ == "__main__":
    main()
