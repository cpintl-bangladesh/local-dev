# local-dev
A fully isolated local development environment

## CPI Bangladesh Mission — Local Development Environment
## `000_BGD_CPMS` Drive Manager · Ubuntu Desktop Edition

**Account:** ariful@cpintl.org | **Drive:** 000_BGD_CPMS | **Version:** v1.0

---

## What this environment does

A fully isolated Ubuntu desktop environment at `/home/ariful/Desktop/local-dev` that connects to your live `000_BGD_CPMS` Google Shared Drive using your own Google account — no service account, no GCP billing, no command-line API calls needed for day-to-day work.

Everything is controlled from a native GTK4 GUI application.

---

## Directory structure

```
local-dev/
├── install.sh              ← Run once to set up everything
├── README.md               ← This file
│
├── venv/                   ← Python virtual environment (auto-created)
│
├── config/
│   ├── credentials.json    ← YOUR OAuth credentials (you place this here)
│   ├── token.json          ← Auto-saved after first login
│   └── oauth_setup_instructions.txt
│
├── scripts/
│   ├── auth.py             ← OAuth login handler
│   ├── drive_engine.py     ← All Drive/Sheets/Docs API operations
│   └── 000_BGD_CPMS_Phase2_v1.0.ipynb  ← Phase 2 Colab notebook
│
├── gui/
│   └── app.py              ← Main GTK4 GUI application
│
├── templates/              ← Local copies of CPI templates
├── schemas/                ← JSON schema files
├── exports/                ← Downloaded registry exports
├── logs/                   ← Activity logs
└── assets/
    ├── icons/              ← App icons
    └── brand/              ← CPI brand assets
```

---

## Quick start (3 steps)

### Step 1 — Run the installer (once)
```bash
cd ~/Desktop/local-dev
bash install.sh
```

### Step 2 — Place your OAuth credentials
Follow the instructions in `config/oauth_setup_instructions.txt`
then place `credentials.json` in the `config/` folder.

### Step 3 — Launch the GUI
```bash
# From terminal:
cd ~/Desktop/local-dev
source venv/bin/activate
python3 gui/app.py

# Or: double-click "CPI-BGD-Manager" on your desktop
```

---

## GUI features

| Feature | What it does |
|---|---|
| Dashboard | Stats overview + quick actions |
| File Browser | Browse all 99 folders, create/rename/trash files |
| Sheets & Data | View and create Google Sheets, apply CPI formatting |
| Forms Builder | Links to all 7 data collection forms |
| Templates | Full list of 20 master sheets + 21 master docs |
| Permissions | Set folder-level access control |
| Template Registry | View + add entries to the master index |
| Activity Log | Full audit trail of all operations |
| Settings | Auth, Drive IDs, configuration |

---

## OAuth — No GCP project fees

This environment uses **Desktop OAuth** — the same method Google uses for
installed apps. It is completely free. You need to:

1. Create a GCP project (free tier)
2. Enable Drive + Sheets + Docs APIs (free)
3. Create OAuth 2.0 Desktop credentials
4. Download `credentials.json`

After first login, the token is cached in `config/token.json` and
automatically refreshed — no repeated logins.

---

## Naming convention (CPI standard)

```
CPI_BGD_[UNIT]_[DOCTYPE]_[Name]_[YYYY-MM]_v[X.Y]
```

Examples:
- `CPI_BGD_HOP_Sheet_DailyPatientLog_2026-04_v1.0`
- `CPI_BGD_MER_Doc_MELFramework_v1.0`
- `CPI_CXB_HOP_Camp01W_PatientLog_2026-04`  (working copy)

---

## Key Drive IDs

| Resource | ID |
|---|---|
| 000_BGD_CPMS root | `18N_9Eq4oOCPZoTBW4CbsVNqLVBkvb6KW` |
| Template Registry | `1kl39tYBZ2qVq5eq0LRv7e4Cv-jXeNUPGdIrZhrw1mIM` |
| INDEX Sheet | `1jq5y9rY5-WaTtukok7Sol0px5SM5fUG6tF3MQmvBJaQ` |

---

*CPI Bangladesh Mission Digital OS | ariful@cpintl.org*
