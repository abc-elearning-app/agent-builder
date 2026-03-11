#!/usr/bin/env bash
# =============================================================================
# GEO Blog Post Optimizer — One-Command Installer
# =============================================================================
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/abc-elearning-app/agent-factory/project/geo-blog-post-optimizer/install-geo-optimizer.sh | bash
#
# Or download and run:
#   bash install-geo-optimizer.sh
# =============================================================================

set -euo pipefail

# ── Re-exec if being piped (curl | bash loses interactivity) ─────────────────
if [ ! -t 0 ]; then
    SELF=$(mktemp /tmp/install-geo-optimizer-XXXX.sh)
    cat > "$SELF"
    exec bash "$SELF" "$@"
fi

# ── Colors ────────────────────────────────────────────────────────────────────
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
DIM='\033[2m'
RESET='\033[0m'

REPO_URL="https://github.com/abc-elearning-app/agent-factory.git"
BRANCH="project/geo-blog-post-optimizer"
DEFAULT_DIR="$HOME/geo-optimizer"

# ── Helpers ───────────────────────────────────────────────────────────────────
info()    { echo -e "${CYAN}→${RESET} $*"; }
success() { echo -e "${GREEN}✅${RESET} $*"; }
warn()    { echo -e "${YELLOW}⚠️  $*${RESET}"; }
error()   { echo -e "${RED}❌ $*${RESET}"; exit 1; }
step()    { echo -e "\n${BOLD}${CYAN}$*${RESET}"; echo -e "${DIM}$(printf '─%.0s' {1..60})${RESET}"; }
ask()     { echo -e "${YELLOW}?${RESET} $*"; }

pause() {
    echo ""
    read -rp "$(echo -e "${YELLOW}Press Enter to continue...${RESET}")" _
}

# ── Banner ────────────────────────────────────────────────────────────────────
clear
echo -e "${BOLD}${CYAN}"
echo "  ╔══════════════════════════════════════════════════════════╗"
echo "  ║         GEO Blog Post Optimizer — Installer             ║"
echo "  ║         Worksheetzone.org  ·  AI Search Visibility      ║"
echo "  ╚══════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo "  This installer will set up the full GEO optimization pipeline:"
echo "  • Download the tool from GitHub"
echo "  • Install Python dependencies"
echo "  • Connect to Google Sheets, Docs & Drive"
echo "  • Build the internal link cache (~24,000 URLs)"
echo ""
echo -e "${DIM}  Estimated time: 5–15 minutes (most steps are automatic)${RESET}"
echo ""

# ── Step 1: Prerequisites ─────────────────────────────────────────────────────
step "Step 1/7 — Checking prerequisites"

MISSING=0

# Python 3.9+
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 9 ]; then
        success "Python $PY_VERSION found"
    else
        error "Python 3.9+ required (found $PY_VERSION). Please upgrade Python first."
    fi
else
    echo -e "${RED}❌ Python 3 not found${RESET}"
    echo ""
    echo "  Install Python 3 first:"
    echo "  • macOS:  brew install python3"
    echo "  • Ubuntu: sudo apt install python3 python3-pip"
    echo ""
    error "Python 3 is required."
fi

# pip3
if command -v pip3 &>/dev/null; then
    success "pip3 found"
else
    warn "pip3 not found — trying to install..."
    python3 -m ensurepip --upgrade 2>/dev/null || error "Could not install pip3. Install it manually and re-run."
fi

# Git
if command -v git &>/dev/null; then
    success "Git $(git --version | awk '{print $3}') found"
else
    echo -e "${RED}❌ Git not found${RESET}"
    echo ""
    echo "  Install Git first:"
    echo "  • macOS:  brew install git  (or: xcode-select --install)"
    echo "  • Ubuntu: sudo apt install git"
    echo ""
    error "Git is required."
fi

# ── Step 2: Install directory ─────────────────────────────────────────────────
step "Step 2/7 — Choose install location"

echo ""
ask "Where should the tool be installed?"
echo -e "  ${DIM}Press Enter to use the default: $DEFAULT_DIR${RESET}"
echo ""
read -rp "  Install path: " INSTALL_DIR
INSTALL_DIR="${INSTALL_DIR:-$DEFAULT_DIR}"
INSTALL_DIR="${INSTALL_DIR/#\~/$HOME}"   # expand ~ if user typed it

if [ -d "$INSTALL_DIR/.git" ]; then
    warn "Directory already exists — updating instead of cloning."
    UPDATE_ONLY=true
else
    UPDATE_ONLY=false
fi

info "Install path: $INSTALL_DIR"

# ── Step 3: Clone / update repo ───────────────────────────────────────────────
step "Step 3/7 — Downloading the tool"

if [ "$UPDATE_ONLY" = true ]; then
    info "Pulling latest changes..."
    cd "$INSTALL_DIR"
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
    success "Repository updated"
else
    info "Cloning repository..."
    git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    success "Repository downloaded to $INSTALL_DIR"
fi

# ── Step 4: Python dependencies ───────────────────────────────────────────────
step "Step 4/7 — Installing Python dependencies"

info "Installing packages (this may take 30–60 seconds)..."
pip3 install \
    google-auth \
    google-auth-httplib2 \
    google-api-python-client \
    google-auth-oauthlib \
    --quiet

success "All Python packages installed"

# ── Step 5: Google Cloud credentials ─────────────────────────────────────────
step "Step 5/7 — Google Cloud credentials"

# Check if credentials already exist
EXISTING_SECRET=$(ls "$INSTALL_DIR"/client_secret*.json 2>/dev/null | head -1 || true)

if [ -n "$EXISTING_SECRET" ]; then
    success "Found credentials file: $(basename "$EXISTING_SECRET")"
else
    echo ""
    echo -e "${BOLD}  You need to create a Google Cloud OAuth credential.${RESET}"
    echo "  This is a one-time setup. Follow these steps:"
    echo ""
    echo -e "  ${CYAN}1.${RESET} Go to: ${BOLD}https://console.cloud.google.com${RESET}"
    echo -e "  ${CYAN}2.${RESET} Create a new project (any name, e.g. \"geo-optimizer\")"
    echo -e "  ${CYAN}3.${RESET} Enable these 3 APIs (APIs & Services → Library):"
    echo "       • Google Sheets API"
    echo "       • Google Docs API"
    echo "       • Google Drive API"
    echo -e "  ${CYAN}4.${RESET} Go to APIs & Services → Credentials"
    echo -e "  ${CYAN}5.${RESET} Click \"+ Create Credentials\" → \"OAuth client ID\""
    echo -e "  ${CYAN}6.${RESET} Application type: ${BOLD}Desktop app${RESET}"
    echo -e "  ${CYAN}7.${RESET} Click Create → Download JSON"
    echo -e "  ${CYAN}8.${RESET} Rename the file to ${BOLD}client_secret.json${RESET}"
    echo -e "  ${CYAN}9.${RESET} Move it into: ${BOLD}$INSTALL_DIR/${RESET}"
    echo ""
    echo -e "  ${DIM}(See GEO-OPTIMIZER-MANUAL.md Step 3 for detailed screenshots guide)${RESET}"
    echo ""

    while true; do
        pause

        EXISTING_SECRET=$(ls "$INSTALL_DIR"/client_secret*.json 2>/dev/null | head -1 || true)
        if [ -n "$EXISTING_SECRET" ]; then
            success "Found: $(basename "$EXISTING_SECRET")"
            break
        else
            warn "No client_secret*.json found in $INSTALL_DIR"
            echo "  Please complete steps 1–9 above, then press Enter to try again."
        fi
    done
fi

# ── Step 6: Google OAuth authentication ───────────────────────────────────────
step "Step 6/7 — Connecting to your Google account"

if [ -f "$INSTALL_DIR/oauth_token.pickle" ]; then
    success "Already authenticated (oauth_token.pickle exists)"
    echo -e "  ${DIM}If you get auth errors later, delete oauth_token.pickle and re-run this installer.${RESET}"
else
    info "A browser window will open. Sign in and click Allow."
    echo -e "  ${DIM}(If no browser opens automatically, copy the URL shown in the terminal)${RESET}"
    echo ""

    python3 - <<'PYEOF'
import sys, glob, pickle
sys.path.insert(0, ".")

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("ERROR: google-auth-oauthlib not installed.")
    sys.exit(1)

matches = glob.glob("client_secret*.json")
if not matches:
    print("ERROR: No client_secret*.json found.")
    sys.exit(1)

secret_file = matches[0]
print(f"  Using credentials: {secret_file}")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]

flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
creds = flow.run_local_server(port=0)

with open("oauth_token.pickle", "wb") as f:
    pickle.dump(creds, f)

print("  ✅ Authenticated successfully. oauth_token.pickle saved.")
PYEOF

fi

# ── Step 7: Build sitemap cache ───────────────────────────────────────────────
step "Step 7/7 — Building internal link cache"

if [ -f "$INSTALL_DIR/scripts/wzorg_link_cache.json" ]; then
    CACHE_SIZE=$(python3 -c "import json; d=json.load(open('scripts/wzorg_link_cache.json')); print(d['total'])" 2>/dev/null || echo "?")
    CACHE_DATE=$(python3 -c "import json; d=json.load(open('scripts/wzorg_link_cache.json')); print(d.get('last_updated','unknown'))" 2>/dev/null || echo "unknown")
    success "Cache already exists — $CACHE_SIZE URLs (built $CACHE_DATE)"
    echo -e "  ${DIM}To rebuild: python3 scripts/build_sitemap_cache.py${RESET}"
else
    info "Fetching all worksheetzone.org URLs (~24,000 URLs, takes ~60s)..."
    echo ""
    python3 scripts/build_sitemap_cache.py
    echo ""
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}"
echo "  ╔══════════════════════════════════════════════════════════╗"
echo "  ║              ✅  Installation complete!                  ║"
echo "  ╚══════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "  ${BOLD}Installed to:${RESET} $INSTALL_DIR"
echo ""
echo -e "  ${BOLD}Before your first run, make sure:${RESET}"
echo -e "  • The team lead has shared the Google Sheet with your Google account"
echo -e "  • The team lead has shared the \"GEO Optimized Posts\" Drive folder with you"
echo -e "  • Gemini CLI is logged in  ${DIM}(run: gemini)${RESET}"
echo -e "    ${DIM}or Claude CLI is logged in (run: claude)${RESET}"
echo ""
echo -e "  ${BOLD}Run the optimizer:${RESET}"
echo ""
echo -e "  ${CYAN}cd $INSTALL_DIR${RESET}"
echo -e "  ${CYAN}python3 scripts/run_batch.py${RESET}              ${DIM}# process next 10 rows${RESET}"
echo -e "  ${CYAN}python3 scripts/run_batch.py --limit 50${RESET}   ${DIM}# process 50 rows${RESET}"
echo -e "  ${CYAN}python3 scripts/run_batch.py --dry-run${RESET}    ${DIM}# test without writing${RESET}"
echo ""
echo -e "  ${BOLD}Full documentation:${RESET} $INSTALL_DIR/GEO-OPTIMIZER-MANUAL.md"
echo ""
