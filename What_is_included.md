Let me read the relevant skills first.Good. Now let me understand the full scope — the user wants a complete local Ubuntu desktop environment at `/home/ariful/Desktop/local-dev` that uses OAuth (their personal Google account `ariful@cpintl.org`) — no service accounts, no GCP project needed — plus a full GUI for managing the CPI Drive system. Let me build this properly.Your complete local development environment is packaged and ready. Here is exactly what is inside and how to set it up on your Ubuntu machine.

---

## CONTEXT

This is a **fully isolated Ubuntu desktop environment** at `/home/ariful/Desktop/local-dev`. It uses your own Google account (`ariful@cpintl.org`) via Desktop OAuth — the same secure method Google uses for installed apps. No service account, no GCP billing, no command-line needed for day-to-day work. Everything runs through a native GTK4 GUI app.

---

## WHAT IS INCLUDED

The zip contains 7 files across a clean folder structure:

`install.sh` — one-time bootstrap that installs all Python packages, creates the virtual environment, and adds a desktop launcher icon. `scripts/auth.py` — handles OAuth login, saves the token, auto-refreshes it. `scripts/drive_engine.py` — every Drive/Sheets/Docs API operation (create, list, rename, move, trash, write headers, apply formatting, set permissions) in one reusable module. `gui/app.py` — the full GTK4 GUI with 9 pages: Dashboard, File Browser, Sheets, Forms Builder, Templates, Permissions, Template Registry, Activity Log, Settings. `scripts/000_BGD_CPMS_Phase2_v1.0.ipynb` — the continuation Colab notebook with Steps 15–19: rename the Global folders, upload exports to Drive, populate the INDEX sheet, and set permissions.

---

## STEP-BY-STEP SETUP ON YOUR UBUNTU MACHINE

**Step 1 — Extract the zip.** Download the zip, right-click it on your Desktop → Extract Here. You should see a `local-dev` folder at `~/Desktop/local-dev`.

**Step 2 — Run the installer.** Open a terminal and run:
```bash
cd ~/Desktop/local-dev
bash install.sh
```
This takes about 2 minutes. It installs Python packages, creates the virtual environment, and puts a `CPI-BGD-Manager` launcher on your Desktop.

**Step 3 — Get your OAuth credentials.** Read `config/oauth_setup_instructions.txt`. Go to [console.cloud.google.com](https://console.cloud.google.com), sign in as `ariful@cpintl.org`, create a free project, enable Drive + Sheets + Docs APIs, create a Desktop OAuth 2.0 client, and download `credentials.json`. Place it at `local-dev/config/credentials.json`.

**Step 4 — First login.** Run:
```bash
source venv/bin/activate
python3 scripts/auth.py
```
Your browser opens → sign in as `ariful@cpintl.org` → Allow. The token is saved automatically. You never need to do this again.

**Step 5 — Launch the GUI.** Double-click `CPI-BGD-Manager` on your Desktop, or run:
```bash
python3 gui/app.py
```

---

## ALSO — Run Phase 2 Colab Notebook

Upload `scripts/000_BGD_CPMS_Phase2_v1.0.ipynb` to your existing Colab session and run Steps 15–19 to fix the Global folder naming, upload your registry files to Drive permanently, and populate the INDEX sheet with all 99 folders.
