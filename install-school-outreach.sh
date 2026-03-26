#!/usr/bin/env bash
# =============================================================================
# School Email Outreach — One-Command Installer
# =============================================================================
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/abc-elearning-app/agent-factory/project/school-email-outreach/install-school-outreach.sh | bash
#
# Or download and run:
#   bash install-school-outreach.sh
# =============================================================================

set -euo pipefail

# ── Re-exec if being piped (curl | bash loses interactivity) ─────────────────
if [ ! -t 0 ]; then
    SELF=$(mktemp /tmp/install-school-outreach-XXXX.sh)
    cat > "$SELF"
    exec bash "$SELF" "$@" </dev/tty
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
BRANCH="project/school-email-outreach"
DEFAULT_DIR="$HOME/school-outreach"

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
echo "  ║         School Email Outreach Agent                     ║"
echo "  ║       Discover contacts · Send personalized emails      ║"
echo "  ╚══════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo "  This tool runs two commands in Gemini CLI or Claude Code:"
echo ""
echo -e "  ${BOLD}/school-discover${RESET} — Find real contact emails for US schools"
echo -e "     Searches the web for school websites, scrapes contact pages,"
echo -e "     and writes verified emails to your Google Sheet."
echo ""
echo -e "  ${BOLD}/school-send${RESET} — Bulk-send personalized emails"
echo -e "     Reads rows you marked ${CYAN}\"To send\"${RESET} in the sheet and sends"
echo -e "     your email template via Gmail."
echo ""
echo "  The installer will:"
echo "  • Download the tool from GitHub"
echo "  • Install Python dependencies"
echo "  • Connect to your Google account (Sheets + Gmail)"
echo "  • Set up your Google Sheet ID and Gmail address"
echo "  • Copy the email template example for you to edit"
echo ""
echo -e "${DIM}  Estimated time: 5–10 minutes${RESET}"
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
INSTALL_DIR="${INSTALL_DIR/#\~/$HOME}"

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
    requests \
    google-auth \
    google-auth-httplib2 \
    google-api-python-client \
    google-auth-oauthlib \
    --quiet

success "All Python packages installed"

# ── Step 5: Google Cloud credentials ─────────────────────────────────────────
step "Step 5/7 — Google Cloud credentials"

EXISTING_SECRET=$(ls "$INSTALL_DIR"/client_secret*.json 2>/dev/null | head -1 || true)

if [ -n "$EXISTING_SECRET" ]; then
    success "Found credentials file: $(basename "$EXISTING_SECRET")"
else
    echo ""
    echo -e "${BOLD}  You need to create a Google Cloud OAuth credential.${RESET}"
    echo "  This is a one-time setup. Follow these steps:"
    echo ""
    echo -e "  ${CYAN}1.${RESET} Go to: ${BOLD}https://console.cloud.google.com${RESET}"
    echo -e "  ${CYAN}2.${RESET} Create a new project (any name, e.g. \"school-outreach\")"
    echo -e "  ${CYAN}3.${RESET} Enable these 2 APIs (APIs & Services → Library):"
    echo "       • Google Sheets API"
    echo "       • Gmail API"
    echo -e "  ${CYAN}4.${RESET} Go to APIs & Services → OAuth consent screen"
    echo -e "     Set User Type to ${BOLD}External${RESET}, fill in app name, add your email"
    echo -e "     Under Scopes, add: Gmail Send + Google Sheets"
    echo -e "  ${CYAN}5.${RESET} Go to APIs & Services → Credentials"
    echo -e "  ${CYAN}6.${RESET} Click \"+ Create Credentials\" → \"OAuth client ID\""
    echo -e "  ${CYAN}7.${RESET} Application type: ${BOLD}Desktop app${RESET}"
    echo -e "  ${CYAN}8.${RESET} Click Create → Download JSON"
    echo -e "  ${CYAN}9.${RESET} Rename the file to ${BOLD}client_secret.json${RESET}"
    echo -e "  ${CYAN}10.${RESET} Move it into: ${BOLD}$INSTALL_DIR/${RESET}"
    echo ""

    while true; do
        pause

        EXISTING_SECRET=$(ls "$INSTALL_DIR"/client_secret*.json 2>/dev/null | head -1 || true)
        if [ -n "$EXISTING_SECRET" ]; then
            success "Found: $(basename "$EXISTING_SECRET")"
            break
        else
            warn "No client_secret*.json found in $INSTALL_DIR"
            echo "  Please complete steps 1–10 above, then press Enter to try again."
        fi
    done
fi

# ── Step 6: Google OAuth authentication ───────────────────────────────────────
step "Step 6/7 — Connecting to your Google account"

if [ -f "$INSTALL_DIR/oauth_token.pickle" ]; then
    success "Already authenticated (oauth_token.pickle exists)"
    echo -e "  ${DIM}If you get auth errors later, delete oauth_token.pickle and re-run this installer.${RESET}"
else
    info "A browser window will open. Sign in with your Gmail account and click Allow."
    echo -e "  ${DIM}This grants access to: Google Sheets (read/write) + Gmail (send only)${RESET}"
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
    "https://www.googleapis.com/auth/gmail.send",
]

flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
creds = flow.run_local_server(port=0)

with open("oauth_token.pickle", "wb") as f:
    pickle.dump(creds, f)

print("  ✅ Authenticated successfully. oauth_token.pickle saved.")
PYEOF

fi

# ── Step 7: Config and template setup ─────────────────────────────────────────
step "Step 7/7 — Configuring your sheet and email template"

CONFIG_FILE="$INSTALL_DIR/school_outreach_config.env"

# ── 7a. school_outreach_config.env ───────────────────────────────────────────
if [ -f "$CONFIG_FILE" ]; then
    success "Config file already exists: school_outreach_config.env"
else
    echo ""
    echo -e "${BOLD}  Create a Google Sheet to store your contacts:${RESET}"
    echo "  1. Go to https://sheets.google.com and create a new blank sheet"
    echo "  2. Name it (e.g. \"School Contacts\")"
    echo "  3. Copy the Sheet ID from the URL:"
    echo -e "     ${DIM}https://docs.google.com/spreadsheets/d/${BOLD}YOUR_SHEET_ID${RESET}${DIM}/edit${RESET}"
    echo ""
    read -rp "  $(echo -e "${YELLOW}?${RESET}") Paste your Google Sheet ID: " SHEET_ID
    SHEET_ID="${SHEET_ID//[[:space:]]/}"

    if [ -z "$SHEET_ID" ]; then
        error "Sheet ID cannot be empty."
    fi

    echo ""
    read -rp "  $(echo -e "${YELLOW}?${RESET}") Gmail address to send from (e.g. you@gmail.com): " GMAIL_USER
    GMAIL_USER="${GMAIL_USER//[[:space:]]/}"

    if [ -z "$GMAIL_USER" ]; then
        error "Gmail address cannot be empty."
    fi

    cat > "$CONFIG_FILE" <<EOF
# School Outreach Agent Config
SCHOOL_OUTREACH_SHEET_ID=$SHEET_ID
GMAIL_USER=$GMAIL_USER
EOF

    success "Config saved to school_outreach_config.env"
    info "Sheet ID : $SHEET_ID"
    info "Gmail    : $GMAIL_USER"
fi

# ── 7b. email_template.txt ────────────────────────────────────────────────────
TEMPLATE_FILE="$INSTALL_DIR/email_template.txt"

if [ -f "$TEMPLATE_FILE" ]; then
    success "Email template already exists: email_template.txt"
else
    cp "$INSTALL_DIR/email_template.example.txt" "$TEMPLATE_FILE"
    success "Email template copied: email_template.txt"
    echo -e "  ${DIM}Edit this file before sending. Variables available: {school_name}, {school_type}, {city}, {state}${RESET}"
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
echo -e "  ${BOLD}Before your first run:${RESET}"
echo -e "  • Edit ${CYAN}email_template.txt${RESET} with your outreach message"
echo -e "  • Make sure Gemini CLI is logged in  ${DIM}(run: gemini)${RESET}"
echo -e "    ${DIM}or Claude Code is logged in (run: claude)${RESET}"
echo ""
echo -e "  ${DIM}$(printf '─%.0s' {1..58})${RESET}"
echo -e "  ${BOLD}Phase 1 — Discover contacts${RESET}"
echo ""
echo -e "  ${CYAN}cd $INSTALL_DIR${RESET}"
echo -e "  ${CYAN}/school-discover${RESET}   ${DIM}# find emails, write to Google Sheet${RESET}"
echo ""
echo -e "  ${DIM}$(printf '─%.0s' {1..58})${RESET}"
echo -e "  ${BOLD}Phase 2 — Send emails${RESET}"
echo -e "  ${DIM}Open the sheet → type \"To send\" in column L for each row you want to email${RESET}"
echo ""
echo -e "  ${CYAN}/school-send${RESET}       ${DIM}# send to all rows marked \"To send\"${RESET}"
echo ""
echo -e "  ${DIM}$(printf '─%.0s' {1..58})${RESET}"
echo -e "  ${BOLD}Full documentation:${RESET} $INSTALL_DIR/SCHOOL-OUTREACH-MANUAL.md"
echo -e "  ${BOLD}Google Sheet:${RESET} https://docs.google.com/spreadsheets/d/$(grep SHEET_ID "$CONFIG_FILE" | cut -d= -f2)"
echo ""
