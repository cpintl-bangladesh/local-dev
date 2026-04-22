#!/usr/bin/env bash
# =============================================================
#  CPI Bangladesh Mission — Local Dev Environment Installer
#  Run this ONCE on your Ubuntu machine as yourself (not sudo)
#  Usage: bash install.sh
# =============================================================

set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; exit 1; }
step() { echo -e "\n${YELLOW}━━━ $1 ━━━${NC}"; }

INSTALL_DIR="$HOME/Desktop/local-dev"
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   CPI Bangladesh Mission — Local Dev Bootstrap           ║"
echo "║   Target: $INSTALL_DIR"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: System packages ───────────────────────────────────
step "1/6 — Checking system packages"

if ! command -v python3 &>/dev/null; then
    warn "python3 not found — installing..."
    sudo apt-get update -qq && sudo apt-get install -y python3 python3-pip python3-venv
else
    ok "python3 $(python3 --version)"
fi

if ! command -v git &>/dev/null; then
    sudo apt-get install -y git
fi
ok "git $(git --version)"

# Chrome / Chromium for OAuth browser flow
if ! command -v google-chrome &>/dev/null && ! command -v chromium-browser &>/dev/null; then
    warn "No Chrome/Chromium found — GUI OAuth will use default browser"
fi

# ── Step 2: Create directory structure ────────────────────────
step "2/6 — Creating project directory structure"

mkdir -p "$INSTALL_DIR"/{scripts,gui,config,templates,schemas,logs,assets,exports,backups}
mkdir -p "$INSTALL_DIR/assets/"{icons,brand}
ok "Directories created at $INSTALL_DIR"

# ── Step 3: Python virtual environment ────────────────────────
step "3/6 — Setting up Python virtual environment"

cd "$INSTALL_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    ok "Virtual environment created"
else
    ok "Virtual environment already exists"
fi

source venv/bin/activate

pip install --quiet --upgrade pip
pip install --quiet \
    google-auth \
    google-auth-oauthlib \
    google-auth-httplib2 \
    google-api-python-client \
    google-api-core \
    PyGObject \
    requests \
    colorama \
    rich \
    tabulate \
    openpyxl \
    python-dotenv

ok "Python packages installed"
deactivate

# ── Step 4: Check for PyGObject (for GTK GUI) ─────────────────
step "4/6 — GTK / PyGObject for GUI"

if ! python3 -c "import gi" 2>/dev/null; then
    warn "PyGObject not found — installing system package..."
    sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 \
         gir1.2-webkit2-4.1 2>/dev/null || \
    sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 2>/dev/null
fi
ok "GTK Python bindings ready"

# ── Step 5: OAuth credentials file ────────────────────────────
step "5/6 — OAuth setup (no GCP project needed)"

CONFIG="$INSTALL_DIR/config"

cat > "$CONFIG/oauth_setup_instructions.txt" << 'EOF'
=======================================================
  HOW TO GET YOUR OAuth credentials.json (ONE TIME)
=======================================================

OPTION A — Use the CPI organization Google Account (recommended)
-----------------------------------------------------------------
1. Open: https://console.cloud.google.com/
2. Sign in as ariful@cpintl.org
3. Create a new project named "CPI-BGD-LocalDev" (free)
4. Go to: APIs & Services → Library
5. Enable: Google Drive API, Google Sheets API, Google Docs API
6. Go to: APIs & Services → Credentials
7. Click: + CREATE CREDENTIALS → OAuth 2.0 Client ID
8. Application type: Desktop app
9. Name: CPI-BGD-OS-LocalDev
10. Download the JSON → save as: config/credentials.json
11. Go to: OAuth consent screen → Add test user: ariful@cpintl.org

OPTION B — Use existing credentials from the Colab notebook
------------------------------------------------------------
If you already have credentials from the Colab run, you can
reuse the same OAuth flow — just make sure Drive + Sheets
APIs are enabled in that project.

After placing credentials.json, run:
  python3 scripts/auth.py
This opens your browser to authorize ariful@cpintl.org.
The token is saved to config/token.json and reused automatically.
=======================================================
EOF

ok "OAuth instructions written to config/oauth_setup_instructions.txt"

# ── Step 6: Create desktop launcher ───────────────────────────
step "6/6 — Creating desktop launcher"

DESKTOP_FILE="$HOME/Desktop/CPI-BGD-Manager.desktop"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=CPI Bangladesh Drive Manager
Comment=CPI BGD Mission OS — Google Drive GUI Manager
Exec=bash -c "cd $INSTALL_DIR && source venv/bin/activate && python3 gui/app.py"
Icon=$INSTALL_DIR/assets/icons/cpi_icon.png
Terminal=false
Categories=Utility;Office;
StartupNotify=true
EOF
chmod +x "$DESKTOP_FILE"
ok "Desktop launcher created: CPI-BGD-Manager.desktop"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Installation complete!                                 ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║   Next steps:                                            ║"
echo "║   1. Read: config/oauth_setup_instructions.txt           ║"
echo "║   2. Place credentials.json in: config/                  ║"
echo "║   3. Run: python3 scripts/auth.py   (one-time login)     ║"
echo "║   4. Run: python3 gui/app.py        (launch the GUI)     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
